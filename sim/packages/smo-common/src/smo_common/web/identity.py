"""Who is looking: the IAP account and whether it is an instructor.

Behind Google IAP every request carries ``X-Goog-Authenticated-User-Email``
(``accounts.google.com:prof@c2o.live``). The app cannot read the
``c2o-instructors`` group, so the instructor accounts are listed in
``SMO_INSTRUCTORS`` (space/comma separated), which deploy/gcp/vm-bootstrap.sh
writes into the ground env file from c2o.env ``VOICE_INSTRUCTORS``. The voice
loops' older ``SMO_VOICE_INSTRUCTORS`` is read as a fallback so one list
serves both.

Laptop / ``start.sh`` mode (no IAP header and no list configured): the person
at the keyboard runs the whole suite, instructor included, so they count as
an instructor. Behind IAP (the header present) with no list configured,
nobody does: closed by default.
"""
from __future__ import annotations

import os
import re
from typing import Mapping, Optional

__all__ = ["IAP_USER_HEADER", "iap_user", "instructor_emails",
           "is_instructor", "cloud_deployment"]

IAP_USER_HEADER = "X-Goog-Authenticated-User-Email"


def iap_user(headers) -> Optional[str]:
    """The IAP-asserted account, lower case, without the
    ``accounts.google.com:`` prefix. Only the load balancer sets the
    header; locally it is absent."""
    raw = (headers.get(IAP_USER_HEADER) or "").strip()
    if not raw:
        return None
    user = raw.split(":", 1)[1] if ":" in raw else raw
    return user[:254].lower() or None


def instructor_emails(env: Optional[Mapping[str, str]] = None) -> frozenset:
    env = os.environ if env is None else env
    raw = env.get("SMO_INSTRUCTORS") or env.get("SMO_VOICE_INSTRUCTORS") or ""
    return frozenset(x.strip().lower() for x in re.split(r"[\s,;]+", raw)
                     if "@" in x)


def cloud_deployment(env: Optional[Mapping[str, str]] = None) -> bool:
    """True for a cloud deployment: ``SMO_REQUIRE_IAP`` (or the voice
    loops' ``SMO_VOICE_REQUIRE_IAP``) is set, or a portal domain is
    configured (``SMO_PORTAL_DOMAIN`` in ground.env)."""
    env = os.environ if env is None else env

    def _t(k: str) -> bool:
        return str(env.get(k, "")).strip().lower() in ("1", "true", "yes", "on")
    dom = str(env.get("SMO_PORTAL_DOMAIN", "")).strip()
    return _t("SMO_REQUIRE_IAP") or _t("SMO_VOICE_REQUIRE_IAP") or (
        bool(dom) and not dom.startswith("@"))


def is_instructor(headers, env: Optional[Mapping[str, str]] = None, *,
                  behind_iap: Optional[bool] = None) -> bool:
    """True for an instructor account (see the module docstring).

    ``behind_iap`` forces the cloud rule even when the header is missing
    (a cloud deployment where IAP was bypassed must not fall open)."""
    if behind_iap is None:
        behind_iap = cloud_deployment(env)
    user = iap_user(headers)
    listed = instructor_emails(env)
    if user is None and not listed and not behind_iap:
        return True            # laptop / start.sh: the operator is the instructor
    return user is not None and user in listed
