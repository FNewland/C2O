"""smo-link v2 channel security (LINK_DESIGN §3.3, §7).

1. **Mutual challenge-response** inside the WebSocket, right after the
   (still header-authenticated) upgrade::

       GSG   -> agent  CHALLENGE {nonce_g: 32 B hex, gsg_id}
       agent -> GSG    AUTH      {nonce_a: 32 B hex,
                                  mac_a = HMAC(secret, "smo-link/v2/agent" | session | nonce_g | nonce_a)}
       GSG   -> agent  AUTH_OK   {mac_g = HMAC(secret, "smo-link/v2/gsg"   | session | nonce_a | nonce_g)}

   Each side verifies the other's MAC (constant time) or aborts. Fresh nonces
   from both ends make every login unique, so a captured exchange cannot be
   replayed (closes M6) and a GSG without the secret cannot complete it (a
   rogue GSG never receives HELLO, a TC or a proxy response).

2. **Per-direction keys**: ``K_a2g = HMAC(secret, "smo-link/v2/k_a2g" | nonce_a | nonce_g)``
   and ``K_g2a`` likewise.

3. **Every later frame carries a tag**: the first 16 bytes of
   ``HMAC-SHA256(K_dir, dir_label | counter u64 BE | frame)``, appended to the
   frame. The counter is implicit: both ends count frames per direction from 0,
   so a forged, replayed, dropped or reordered frame fails its tag and the
   receiver closes the link (and the GSG resets its TC clients).

The tags give integrity and authenticity end to end, including the plaintext
LB -> GSG hop inside the VPC. They give **no confidentiality**: that comes only
from TLS between the agent and the load balancer.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import logging
import os
import secrets
from urllib.parse import urlsplit

from . import protocol as P

logger = logging.getLogger("smo_link.channel")

TAG_SIZE = 16
NONCE_BYTES = 32
LABEL_AGENT = b"smo-link/v2/agent"
LABEL_GSG = b"smo-link/v2/gsg"
LABEL_K_A2G = b"smo-link/v2/k_a2g"
LABEL_K_G2A = b"smo-link/v2/k_g2a"
DIR_A2G = b"a2g"
DIR_G2A = b"g2a"


class IntegrityError(Exception):
    """A frame failed its tag, or a handshake MAC did not verify."""


def new_nonce() -> bytes:
    return secrets.token_bytes(NONCE_BYTES)


def parse_nonce(value: object) -> bytes:
    if not isinstance(value, str) or len(value) != 2 * NONCE_BYTES:
        raise IntegrityError("malformed nonce")
    try:
        raw = bytes.fromhex(value)
    except ValueError as e:
        raise IntegrityError("malformed nonce") from e
    if len(raw) != NONCE_BYTES:
        raise IntegrityError("malformed nonce")
    return raw


def parse_mac(value: object) -> bytes:
    if not isinstance(value, str) or len(value) != 64:
        raise IntegrityError("malformed mac")
    try:
        return bytes.fromhex(value)
    except ValueError as e:
        raise IntegrityError("malformed mac") from e


def _session_bytes(session: str) -> bytes:
    s = session.encode("utf-8")
    return len(s).to_bytes(2, "big") + s       # length-prefixed: unambiguous


def mac_agent(secret: bytes, session: str, nonce_g: bytes, nonce_a: bytes) -> bytes:
    return hmac.new(secret, LABEL_AGENT + _session_bytes(session) + nonce_g + nonce_a,
                    hashlib.sha256).digest()


def mac_gsg(secret: bytes, session: str, nonce_a: bytes, nonce_g: bytes) -> bytes:
    return hmac.new(secret, LABEL_GSG + _session_bytes(session) + nonce_a + nonce_g,
                    hashlib.sha256).digest()


def derive_keys(secret: bytes, nonce_a: bytes, nonce_g: bytes) -> tuple[bytes, bytes]:
    """``(K_a2g, K_g2a)``."""
    return (hmac.new(secret, LABEL_K_A2G + nonce_a + nonce_g, hashlib.sha256).digest(),
            hmac.new(secret, LABEL_K_G2A + nonce_a + nonce_g, hashlib.sha256).digest())


def verify_mac(expected: bytes, got: bytes) -> None:
    if not hmac.compare_digest(expected, got):
        raise IntegrityError("handshake MAC mismatch")


class SecureChannel:
    """Seals outgoing and opens incoming frames for one link connection.

    Only the connection's single writer may call :meth:`seal` and only its
    single reader may call :meth:`open`; the implicit counters depend on it.
    """

    def __init__(self, k_tx: bytes, k_rx: bytes, tx_label: bytes, rx_label: bytes):
        self._tx = hmac.new(k_tx, tx_label, hashlib.sha256)
        self._rx = hmac.new(k_rx, rx_label, hashlib.sha256)
        self.tx_counter = 0
        self.rx_counter = 0

    @classmethod
    def for_agent(cls, secret: bytes, nonce_a: bytes, nonce_g: bytes) -> "SecureChannel":
        k_a2g, k_g2a = derive_keys(secret, nonce_a, nonce_g)
        return cls(k_a2g, k_g2a, DIR_A2G, DIR_G2A)

    @classmethod
    def for_gsg(cls, secret: bytes, nonce_a: bytes, nonce_g: bytes) -> "SecureChannel":
        k_a2g, k_g2a = derive_keys(secret, nonce_a, nonce_g)
        return cls(k_g2a, k_a2g, DIR_G2A, DIR_A2G)

    @staticmethod
    def _tag(base: "hmac.HMAC", counter: int, frame: bytes) -> bytes:
        h = base.copy()
        h.update(counter.to_bytes(8, "big"))
        h.update(frame)
        return h.digest()[:TAG_SIZE]

    def seal(self, frame: bytes) -> bytes:
        tag = self._tag(self._tx, self.tx_counter, frame)
        self.tx_counter += 1
        return frame + tag

    def open(self, message: bytes) -> bytes:
        """Return the frame bytes, or raise :class:`IntegrityError`."""
        if len(message) < P.HEADER_SIZE + TAG_SIZE:
            raise IntegrityError("message too short for a sealed frame")
        frame, tag = bytes(message[:-TAG_SIZE]), bytes(message[-TAG_SIZE:])
        if not hmac.compare_digest(self._tag(self._rx, self.rx_counter, frame), tag):
            raise IntegrityError(f"bad tag on frame {self.rx_counter}")
        self.rx_counter += 1
        return frame


# --- transport policy (agent) --------------------------------------------------

LOOPBACK_NAMES = frozenset({"localhost", "localhost.localdomain"})


def host_is_private(host: str) -> bool:
    """Loopback, RFC 1918 or IPv6 ULA/link-local literal (or ``localhost``)."""
    h = (host or "").strip("[]").lower()
    if h in LOOPBACK_NAMES:
        return True
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if ip.is_loopback:
        return True
    if isinstance(ip, ipaddress.IPv4Address):
        return any(ip in ipaddress.ip_network(n) for n in
                   ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
    return ip in ipaddress.ip_network("fc00::/7") or ip.is_link_local


def env_allow_insecure(env: dict | None = None) -> bool:
    env = os.environ if env is None else env
    return str(env.get("SMO_LINK_ALLOW_INSECURE", "")).strip() == "1"


def check_link_url(url: str, allow_insecure: bool = False) -> None:
    """Raise ``ValueError`` unless the agent may dial ``url``.

    ``wss://`` is always allowed. ``ws://`` only to a loopback / RFC 1918 /
    ULA literal (or ``localhost``), or with an explicit
    ``SMO_LINK_ALLOW_INSECURE=1`` (logged as a warning on every start).
    """
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
    except ValueError as e:
        raise ValueError(f"malformed link URL: {e}") from e
    scheme = parts.scheme.lower()
    if scheme == "wss":
        return
    if scheme != "ws":
        raise ValueError(f"link URL must be wss:// (or ws:// on a private network), got {scheme!r}")
    if host_is_private(host):
        return
    if allow_insecure:
        logger.warning(P.kv(
            "INSECURE_TRANSPORT", url_host=host,
            message="SMO_LINK_ALLOW_INSECURE=1: plaintext ws:// to a non-private host. "
                    "Frames are still authenticated, but TM, TC and proxied pages "
                    "are readable by anyone on the path"))
        return
    raise ValueError(
        f"refusing plaintext ws:// to {host!r}: use wss://, a loopback/private address, "
        "or set SMO_LINK_ALLOW_INSECURE=1 deliberately")
