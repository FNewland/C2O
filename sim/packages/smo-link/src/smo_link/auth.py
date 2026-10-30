"""HMAC upgrade credential (LINK_DESIGN §3.3 step 1).

``Authorization: SMO-Link v=2, session=<id>, ts=<unix>, nonce=<16 hex>,
sig=<hex HMAC-SHA256(secret, "v2\\nGET\\n/link\\n<session>\\n<ts>\\n<nonce>")>``

The GSG rejects (HTTP 401) a malformed header, a bad signature, a timestamp
more than ``MAX_SKEW_S`` from its clock, or a nonce seen within
``NONCE_TTL_S``. This check is a cheap, stateless-ish **fail-fast filter**
only: the session is authenticated by the mutual challenge-response and the
per-frame tags of :mod:`smo_link.channel`, so a replayed header (for example
after a GSG restart empties the nonce cache) gets no further than the
challenge. Secrets and signatures are never logged.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time
from collections import OrderedDict
from pathlib import Path

SCHEME = "SMO-Link"
MAX_SKEW_S = 120
NONCE_TTL_S = 600
SECRET_BYTES = 32
_NONCE_RE = re.compile(r"[0-9a-f]{16}", re.ASCII)
_SIG_RE = re.compile(r"[0-9a-fA-F]{64}", re.ASCII)
_TS_RE = re.compile(r"[0-9]{1,12}", re.ASCII)
_SESSION_RE = re.compile(r"[A-Za-z0-9._-]{1,128}", re.ASCII)
CRED_VERSION = "2"


class AuthError(Exception):
    """Credential refused. ``str(e)`` is a short, loggable reason."""


def new_secret() -> str:
    return secrets.token_hex(SECRET_BYTES)


def new_session_id() -> str:
    return "s-" + secrets.token_hex(8)


def parse_secret(value: str) -> bytes:
    value = (value or "").strip()
    try:
        key = bytes.fromhex(value)
    except ValueError as e:
        raise AuthError("secret is not hex") from e
    if len(key) < SECRET_BYTES:
        raise AuthError(f"secret too short (need >= {SECRET_BYTES} bytes, i.e. 64 hex digits)")
    return key


def load_secret(secret: str | None = None, secret_file: str | None = None,
                env: dict | None = None) -> bytes:
    """Secret from explicit value, explicit file, $SMO_LINK_SECRET, or
    $SMO_LINK_SECRET_FILE (first one set wins)."""
    env = os.environ if env is None else env
    if secret:
        return parse_secret(secret)
    if secret_file:
        return parse_secret(Path(secret_file).read_text(encoding="utf-8"))
    if env.get("SMO_LINK_SECRET"):
        return parse_secret(env["SMO_LINK_SECRET"])
    if env.get("SMO_LINK_SECRET_FILE"):
        return parse_secret(Path(env["SMO_LINK_SECRET_FILE"]).read_text(encoding="utf-8"))
    raise AuthError("no secret: set SMO_LINK_SECRET or SMO_LINK_SECRET_FILE")


def signing_string(session: str, ts: int, nonce: str,
                   method: str = "GET", path: str = "/link") -> bytes:
    return f"v{CRED_VERSION}\n{method}\n{path}\n{session}\n{ts}\n{nonce}".encode()


def sign(secret: bytes, session: str, ts: int, nonce: str,
         method: str = "GET", path: str = "/link") -> str:
    return hmac.new(secret, signing_string(session, ts, nonce, method, path),
                    hashlib.sha256).hexdigest()


def make_header(secret: bytes, session: str, now: float | None = None,
                nonce: str | None = None, path: str = "/link") -> str:
    ts = int(time.time() if now is None else now)
    nonce = nonce or secrets.token_hex(8)
    sig = sign(secret, session, ts, nonce, "GET", path)
    return f"{SCHEME} v={CRED_VERSION}, session={session}, ts={ts}, nonce={nonce}, sig={sig}"


def parse_header(value: str | None) -> dict[str, str]:
    if not value:
        raise AuthError("missing Authorization")
    if len(value) > 1024 or not value.isascii() or not value.isprintable():
        raise AuthError("malformed Authorization")
    scheme, _, rest = value.strip().partition(" ")
    if scheme != SCHEME:
        raise AuthError("wrong scheme")
    fields: dict[str, str] = {}
    for part in rest.split(","):
        k, sep, v = part.strip().partition("=")
        if not sep:
            raise AuthError("malformed Authorization")
        fields[k.strip()] = v.strip()
    for need in ("v", "session", "ts", "nonce", "sig"):
        if need not in fields:
            raise AuthError(f"missing {need}")
    if fields["v"] != CRED_VERSION:
        raise AuthError("unsupported credential version")
    return fields


class NonceCache:
    """Nonces seen in the last ``ttl`` seconds (bounded)."""

    def __init__(self, ttl: float = NONCE_TTL_S, max_entries: int = 100_000):
        self.ttl = ttl
        self.max_entries = max_entries
        self._seen: OrderedDict[str, float] = OrderedDict()

    def _expire(self, now: float) -> None:
        while self._seen:
            nonce, t = next(iter(self._seen.items()))
            if now - t <= self.ttl and len(self._seen) <= self.max_entries:
                break
            self._seen.popitem(last=False)

    def check_and_add(self, nonce: str, now: float) -> bool:
        """True if fresh (and records it); False if replayed."""
        self._expire(now)
        if nonce in self._seen:
            return False
        self._seen[nonce] = now
        return True

    def __len__(self) -> int:
        return len(self._seen)


class Verifier:
    def __init__(self, secret: bytes, session: str, max_skew: float = MAX_SKEW_S,
                 nonces: NonceCache | None = None):
        if not isinstance(secret, (bytes, bytearray)) or len(secret) < SECRET_BYTES:
            raise ValueError(f"link secret must be at least {SECRET_BYTES} bytes")
        if not isinstance(session, str) or not _SESSION_RE.fullmatch(session):
            raise ValueError("malformed session id")
        self.secret = bytes(secret)
        self.session = session
        self.max_skew = max_skew
        self.nonces = nonces or NonceCache()

    def verify(self, header: str | None, method: str = "GET", path: str = "/link",
               now: float | None = None) -> str:
        """Return the session id or raise :class:`AuthError`."""
        now = time.time() if now is None else now
        f = parse_header(header)
        session, nonce = f["session"], f["nonce"]
        if not _SESSION_RE.fullmatch(session):
            raise AuthError("malformed session")
        if not _NONCE_RE.fullmatch(nonce):
            raise AuthError("malformed nonce")
        if not _TS_RE.fullmatch(f["ts"]):
            raise AuthError("malformed ts")
        if not _SIG_RE.fullmatch(f["sig"]):
            raise AuthError("malformed sig")      # also keeps compare_digest on ASCII
        ts = int(f["ts"])
        expected = sign(self.secret, session, ts, nonce, method, path)
        if not hmac.compare_digest(expected.encode(), f["sig"].lower().encode()):
            raise AuthError("bad signature")
        if not hmac.compare_digest(session.encode(), self.session.encode()):
            raise AuthError("unknown session")
        if abs(now - ts) > self.max_skew:
            raise AuthError("timestamp skew")
        if not self.nonces.check_and_add(nonce, now):
            raise AuthError("replayed nonce")
        return session
