"""Who is behind a request (COMET "Person") and whether they are an instructor.

* Behind Google IAP the load balancer sends ``X-Goog-Authenticated-User-Email``
  (``accounts.google.com:name@c2o.live``) → ``iap:<email>``, *verified*.
* Laptop mode (no IAP): the browser sends ``X-C2O-Client`` (a random id kept in
  localStorage) and ``X-C2O-Name`` (the typed name, URI-encoded) → ``local:<id>``,
  *unverified*. Two people who type the same name stay two people.
* Nothing → ``anon`` (may read; may not hold a seat).

Instructors: ``SPACECDF_INSTRUCTORS`` and ``SMO_INSTRUCTORS`` (the ops tools' variable), both
comma- or space-separated e-mail lists, merged. With a list configured only a *verified*
listed e-mail is an instructor. With no list (laptop mode) the first person who presses
"Become instructor" is the instructor (stored server-side; the board can hand it over);
until someone does, nobody has instructor powers except deleting studies, which stays open
so a single-user laptop keeps working.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import unquote

from fastapi import Request

IAP_HEADER = "x-goog-authenticated-user-email"
CLIENT_HEADER = "x-c2o-client"
NAME_HEADER = "x-c2o-name"
SEAT_HEADER = "x-c2o-seat"
CONFIRM_HEADER = "x-c2o-confirm-review"


@dataclass(frozen=True)
class Person:
    id: str
    name: str
    verified: bool
    email: str = ""

    @property
    def anonymous(self) -> bool:
        return self.id == "anon"

    def public(self) -> dict:
        return {"id": self.id, "name": self.name, "verified": self.verified,
                "email": self.email or None}


def _clean_name(raw: str) -> str:
    try:
        name = unquote(raw or "")
    except Exception:  # noqa: BLE001
        name = raw or ""
    name = re.sub(r"[\x00-\x1f]", "", name).strip()
    return name[:80]


def _name_from_email(email: str) -> str:
    return email.split("@", 1)[0].replace(".", " ").replace("_", " ").title()


def person_from_headers(headers) -> Person:
    raw = (headers.get(IAP_HEADER) or "").strip()
    email = raw.split(":", 1)[-1].strip().lower() if raw else ""
    typed = _clean_name(headers.get(NAME_HEADER) or "")
    if email:
        return Person(id=f"iap:{email}", name=typed or _name_from_email(email), verified=True, email=email)
    cid = "".join(ch for ch in (headers.get(CLIENT_HEADER) or "") if ch.isalnum() or ch in "-_")[:64]
    if cid:
        return Person(id=f"local:{cid}", name=typed or "Guest", verified=False)
    return Person(id="anon", name=typed or "", verified=False)


def person(request: Request) -> Person:
    return person_from_headers(request.headers)


def requested_seat(request: Request) -> str:
    return "".join(ch for ch in (request.headers.get(SEAT_HEADER) or "") if ch.isalnum() or ch == "_")[:40]


def confirmed_review(request: Request) -> bool:
    return (request.headers.get(CONFIRM_HEADER) or "").strip().lower() in ("1", "true", "yes")


def instructor_emails() -> set[str]:
    out: set[str] = set()
    for var in ("SPACECDF_INSTRUCTORS", "SMO_INSTRUCTORS"):
        for part in re.split(r"[\s,;]+", os.environ.get(var, "") or ""):
            part = part.strip().lower()
            if part:
                out.add(part.split(":", 1)[-1])
    return out


def instructor_mode() -> str:
    """``list`` when an instructor list is configured, else ``laptop``.

    A list variable that is *set but empty* (the hosted deployment with no
    instructors listed yet) is still ``list`` mode: nobody is instructor,
    and nobody can self-promote with "Become instructor"."""
    if instructor_emails():
        return "list"
    if any(v in os.environ for v in ("SPACECDF_INSTRUCTORS", "SMO_INSTRUCTORS")):
        return "list"
    return "laptop"
