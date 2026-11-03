"""Who is writing (LOGBOOK_SPEC §1).

Behind Google IAP the load balancer sets ``X-Goog-Authenticated-User-Email``
(``accounts.google.com:alice@example.org``); the person is that address,
lower-cased. Anywhere else (a laptop, the local demo) the person is "this
browser": a random 128-bit id in the ``c2o_lb`` cookie. Cookies ignore the
port, so every tool on one host shares it.

The id never leaves the ground segment: smo-link never forwards
``/api/logbook`` (its route allowlist does not contain it, and the GSG
strips IAP headers anyway).
"""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import Mapping

__all__ = ["COOKIE", "COOKIE_MAX_AGE", "IAP_HEADER", "Identity", "identify", "cookie_header"]

IAP_HEADER = "X-Goog-Authenticated-User-Email"
COOKIE = "c2o_lb"
COOKIE_MAX_AGE = 30 * 24 * 3600
_LOCAL_RE = re.compile(r"^local:[0-9a-f]{32}$")
_EMAIL_RE = re.compile(r"^[^@\s]{1,200}@[^@\s]{1,200}$")


@dataclass(frozen=True)
class Identity:
    person_id: str
    local: bool
    #: a fresh cookie value to send back (None: nothing to set)
    new_cookie: str | None = None

    @property
    def label(self) -> str:
        return "this browser" if self.local else self.person_id


def identify(headers: Mapping[str, str], cookies: Mapping[str, str]) -> Identity:
    raw = (headers.get(IAP_HEADER) or "").strip()
    if raw:
        email = raw.split(":", 1)[1] if raw.startswith("accounts.google.com:") else raw
        email = email.strip().lower()
        if _EMAIL_RE.match(email):
            return Identity(email, False)
    c = (cookies.get(COOKIE) or "").strip()
    if _LOCAL_RE.match(c):
        return Identity(c, True)
    fresh = "local:" + secrets.token_hex(16)
    return Identity(fresh, True, new_cookie=fresh)


def cookie_header(value: str, secure: bool = False) -> str:
    """The ``Set-Cookie`` value for a fresh local id."""
    return (f"{COOKIE}={value}; Path=/; Max-Age={COOKIE_MAX_AGE}; SameSite=Lax; HttpOnly"
            + ("; Secure" if secure else ""))
