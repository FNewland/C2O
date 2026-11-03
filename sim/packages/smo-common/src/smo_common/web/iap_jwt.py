"""Verify the IAP-signed identity header ``X-Goog-IAP-JWT-Assertion``.

Behind Google's Identity-Aware Proxy every request carries two identity
headers. ``X-Goog-Authenticated-User-Email`` is plain text: anything that
reaches the app without going through IAP (a misconfigured firewall, another
VM in the VPC) can set it. ``X-Goog-IAP-JWT-Assertion`` is a JWT that IAP
signs, so only IAP can produce it. Google's guidance ("Securing your app with
signed headers", cloud.google.com/iap/docs/signed-headers-howto, checked
2026-11-03) is to verify it as follows, which is what this module does:

* header ``alg`` is ``ES256`` and ``kid`` names one of IAP's public keys,
  published as JWK at https://www.gstatic.com/iap/verify/public_key-jwk
  (keys rotate: cache them and refresh, here every 12 h and on an unknown
  ``kid``, at most once a minute);
* the signature verifies with that key;
* ``exp`` is in the future and ``iat`` in the past, each with a 30 s
  allowance, and the lifetime is at most 10 min + 2 x 30 s;
* ``iss`` is ``https://cloud.google.com/iap``;
* ``aud`` is the expected audience. For a load-balancer backend service it
  is ``/projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID``. One
  process may be reached through several backends (the MCS directly at
  ops.<domain>, and its ``/api/seats*`` through the GSG at sim.<domain>), so
  a set of audiences is accepted;
* the user is the ``email`` claim (no ``accounts.google.com:`` prefix, unlike
  the plain header). When the plain header is present too it must name the
  same account.

The crypto is ``cryptography`` (the ``iap`` extra of smo-mcs). Nothing here
logs a token.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

logger = logging.getLogger(__name__)

__all__ = ["IAP_JWT_HEADER", "ISSUER", "JWK_URL", "LEEWAY_S", "IapJwtError",
           "KeySet", "IapVerifier", "audiences_from_env", "b64url"]

IAP_JWT_HEADER = "X-Goog-IAP-JWT-Assertion"
ISSUER = "https://cloud.google.com/iap"
JWK_URL = "https://www.gstatic.com/iap/verify/public_key-jwk"
LEEWAY_S = 30
MAX_LIFETIME_S = 600 + 2 * LEEWAY_S
REFRESH_S = 12 * 3600
UNKNOWN_KID_REFETCH_S = 60
_AUD_RE = re.compile(r"^/projects/\d{1,20}/(global/backendServices/\d{1,25}|apps/[a-z][a-z0-9-]{3,62}"
                     r"|locations/[a-z0-9-]{1,40}/services/[a-z0-9-]{1,63})$")


class IapJwtError(Exception):
    """The assertion is missing, malformed or does not verify. ``code`` is a
    short machine word for logs and the JSON error."""

    def __init__(self, code: str, msg: str = ""):
        super().__init__(msg or code)
        self.code = code


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(s: str) -> bytes:
    if not isinstance(s, str) or not re.fullmatch(r"[A-Za-z0-9_-]*", s):
        raise IapJwtError("malformed", "not base64url")
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def audiences_from_env(env: Optional[Mapping[str, str]] = None) -> frozenset:
    """``SMO_IAP_AUDIENCES``: space/comma separated audience strings."""
    env = os.environ if env is None else env
    raw = str(env.get("SMO_IAP_AUDIENCES", "") or "")
    out = set()
    for a in re.split(r"[\s,;]+", raw):
        a = a.strip()
        if not a:
            continue
        if not _AUD_RE.match(a):
            logger.warning("SMO_IAP_AUDIENCES: %r does not look like an IAP audience; ignored", a)
            continue
        out.add(a)
    return frozenset(out)


class KeySet:
    """IAP's public keys by ``kid`` (P-256 only)."""

    def __init__(self, keys: Optional[dict] = None):
        self.keys: dict = dict(keys or {})

    @classmethod
    def from_jwks(cls, doc: Any) -> "KeySet":
        from cryptography.hazmat.primitives.asymmetric import ec
        keys = {}
        for k in (doc or {}).get("keys", []) if isinstance(doc, dict) else []:
            try:
                if k.get("kty") != "EC" or k.get("crv") != "P-256" or not k.get("kid"):
                    continue
                x = int.from_bytes(_unb64(k["x"]), "big")
                y = int.from_bytes(_unb64(k["y"]), "big")
                keys[str(k["kid"])] = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
            except Exception as e:  # noqa: BLE001 -- one bad key never voids the set
                logger.warning("IAP JWK %r skipped: %s", k.get("kid") if isinstance(k, dict) else k, e)
        return cls(keys)

    def __contains__(self, kid: str) -> bool:
        return kid in self.keys

    def __len__(self) -> int:
        return len(self.keys)


def verify_token(token: str, keys: KeySet, audiences: Iterable[str], *,
                 now: Optional[float] = None, leeway: int = LEEWAY_S) -> dict:
    """Verify one assertion against ``keys``; return its claims or raise."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

    if not token or not isinstance(token, str) or len(token) > 8192:
        raise IapJwtError("missing", "no IAP assertion")
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise IapJwtError("malformed", "not a JWS compact token")
    try:
        header = json.loads(_unb64(parts[0]))
        claims = json.loads(_unb64(parts[1]))
    except (ValueError, IapJwtError) as e:
        raise IapJwtError("malformed", f"undecodable token: {e}") from None
    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise IapJwtError("malformed", "header and claims must be objects")
    if header.get("alg") != "ES256":
        raise IapJwtError("alg", f"alg {header.get('alg')!r} is not ES256")
    kid = str(header.get("kid") or "")
    key = keys.keys.get(kid)
    if key is None:
        raise IapJwtError("kid", "unknown key id")
    sig = _unb64(parts[2])
    if len(sig) != 64:
        raise IapJwtError("signature", "ES256 signature must be 64 bytes")
    der = encode_dss_signature(int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big"))
    try:
        key.verify(der, f"{parts[0]}.{parts[1]}".encode("ascii"), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        raise IapJwtError("signature", "signature does not verify") from None
    now = time.time() if now is None else now
    try:
        exp, iat = float(claims["exp"]), float(claims["iat"])
    except (KeyError, TypeError, ValueError):
        raise IapJwtError("claims", "exp and iat are required numbers") from None
    if exp + leeway < now:
        raise IapJwtError("expired", "token expired")
    if iat - leeway > now:
        raise IapJwtError("iat", "token issued in the future")
    if exp - iat > MAX_LIFETIME_S:
        raise IapJwtError("lifetime", "token lifetime too long")
    if claims.get("iss") != ISSUER:
        raise IapJwtError("iss", "wrong issuer")
    aud = claims.get("aud")
    auds = set(audiences)
    if not auds:
        raise IapJwtError("audience-unset", "no expected audience configured (SMO_IAP_AUDIENCES)")
    if aud not in auds:
        raise IapJwtError("aud", "wrong audience")
    email = str(claims.get("email") or "").strip().lower()
    if "@" not in email or len(email) > 254:
        raise IapJwtError("email", "no email claim")
    claims["email"] = email
    return claims


class IapVerifier:
    """Verifies assertions, with IAP's key set cached and refreshed.

    ``keys``: a fixed :class:`KeySet` (tests, offline). Otherwise the JWK set
    is read from ``jwks_file`` (``SMO_IAP_JWKS_FILE``) or fetched from
    ``jwk_url`` with aiohttp."""

    def __init__(self, audiences: Iterable[str], *, keys: Optional[KeySet] = None,
                 jwks_file: Optional[str] = None, jwk_url: str = JWK_URL,
                 clock: Callable[[], float] = time.time,
                 fetch: Optional[Callable[[], Any]] = None):
        self.audiences = frozenset(audiences)
        self._fixed = keys
        self._file = jwks_file
        self._url = jwk_url
        self._clock = clock
        self._fetch = fetch
        self._keys: Optional[KeySet] = keys
        self._fetched_at = 0.0
        self._last_forced = -1e18
        self._lock = asyncio.Lock()

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "IapVerifier":
        env = os.environ if env is None else env
        return cls(audiences_from_env(env), jwks_file=(env.get("SMO_IAP_JWKS_FILE") or None),
                   jwk_url=env.get("SMO_IAP_JWK_URL") or JWK_URL)

    async def _load(self) -> Optional[KeySet]:
        if self._fixed is not None:
            return self._fixed
        if self._file:
            doc = json.loads(Path(self._file).read_text(encoding="utf-8"))
            return KeySet.from_jwks(doc)
        if self._fetch is not None:
            doc = self._fetch()
            if asyncio.iscoroutine(doc):
                doc = await doc
            return KeySet.from_jwks(doc)
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(self._url) as r:
                if r.status != 200:
                    raise IapJwtError("keys", f"key fetch HTTP {r.status}")
                return KeySet.from_jwks(await r.json(content_type=None))

    async def keys(self, *, force: bool = False) -> KeySet:
        now = self._clock()
        fresh = self._keys is not None and now - self._fetched_at < REFRESH_S
        if fresh and not force:
            return self._keys  # type: ignore[return-value]
        async with self._lock:
            now = self._clock()
            if self._keys is not None and not force and now - self._fetched_at < REFRESH_S:
                return self._keys
            if force:
                if now - self._last_forced < UNKNOWN_KID_REFETCH_S and self._keys is not None:
                    return self._keys              # at most one forced refetch a minute
                self._last_forced = now
            try:
                ks = await self._load()
                if ks is not None and len(ks):
                    self._keys, self._fetched_at = ks, now
            except Exception as e:  # noqa: BLE001
                logger.warning("IAP public keys not refreshed: %s", e)
            if self._keys is None:
                raise IapJwtError("keys", "IAP public keys unavailable")
            return self._keys

    async def verify(self, token: str) -> dict:
        ks = await self.keys()
        try:
            return verify_token(token, ks, self.audiences, now=self._clock())
        except IapJwtError as e:
            if e.code != "kid" or self._fixed is not None:
                raise
        ks = await self.keys(force=True)          # IAP rotated its keys
        return verify_token(token, ks, self.audiences, now=self._clock())
