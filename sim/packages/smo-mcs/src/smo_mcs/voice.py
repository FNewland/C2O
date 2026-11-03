"""Voice loops: the LiveKit token service and the keyset panel (WP-4 prototype).

Why the MCS and not the portal
------------------------------
* ``/voice`` must know the operator's console position. With console seats
  on (``SMO_SEATS=iap|local``, WP10) the position comes from the seat
  registry: a token is minted only for a desk the caller holds (or, for an
  instructor, the instructor/SIM roles). With seats off it is the one chosen
  in the MCS header (``localStorage["mcs.position"]`` on the MCS origin),
  self-asserted as before. Served from the MCS (``ops.<domain>``), the
  voice panel reads it directly and follows changes.
* The docked panel is an ``<iframe>`` inside the MCS page. Same origin means
  no cross-origin microphone/autoplay delegation and one IAP cookie.
* Decision 6 (REDESIGN_DECISIONS.md): seat authority lives in the MCS on the
  ground; the token endpoint takes the position from the seat registry
  (``smo_mcs.seats_http``), and the identity from it too (the IAP JWT is
  verified there).

What it serves (all behind IAP in the cloud)
--------------------------------------------
``GET  /voice``             the keyset panel (static/modern/voice.html)
``GET  /api/voice/config``  who you are, which positions you may take, labels
``POST /api/voice/token``   ``{"position": ..., "name": ...}`` -> one LiveKit
                            JWT per loop the position may hear (a loop with
                            access OFF is never sent), ``canPublish`` only on
                            TALK loops, TTL <= 10 min; the page refreshes at
                            75 % of the TTL.

Identity
--------
* Cloud: the IAP header ``X-Goog-Authenticated-User-Email`` (verified). With
  ``SMO_VOICE_REQUIRE_IAP=1`` (set on the ground VM) a request without it is
  refused. The VMs have no public IP and admit only the load balancer, so the
  header cannot be forged from outside. Verifying the IAP-signed JWT
  (``X-Goog-IAP-JWT-Assertion``) is WP-3 work and is not done here yet.
* Local (laptop, no IAP): the typed display name, marked unverified.
* Instructor role (positions ``instructor`` and ``sim``, and every
  ``instructor_only`` loop): a verified email listed in
  ``SMO_VOICE_INSTRUCTORS`` (the IAP group cannot be read from inside the
  app; the list mirrors the c2o-instructors group, deploy/gcp c2o.env
  ``VOICE_INSTRUCTORS``), or, locally, ``SMO_VOICE_LOCAL_INSTRUCTOR=1``.

Settings (environment)
----------------------
``LIVEKIT_URL``          browser-facing wss:// URL of the LiveKit server
``LIVEKIT_API_KEY``      API key / secret (Secret Manager on GCP, written to
``LIVEKIT_API_SECRET``   sim/docker/voice.env by vm-bootstrap.sh; never committed)
``SMO_VOICE=dev``        laptop mode: the compose ``livekit`` service (profile
                         ``voice``) on ws://<this host>:7880 with its dev key
``SMO_VOICE_REQUIRE_IAP``  1 = refuse requests without the IAP identity
``SMO_VOICE_INSTRUCTORS``  emails with the instructor role (space/comma list)
``SMO_VOICE_LOCAL_INSTRUCTOR``  1 = unverified (local) users may be instructor
``SMO_VOICE_ROOM_PREFIX``  room name prefix, one per team/session (default c2o)
``SMO_VOICE_TOKEN_TTL_S``  token lifetime, 60..600 s (default 600)

Recordings: ``recordings: false`` in voice_loops.yaml. Egress recording
(instructor-only toggle, UTC + sim time stamps, indexed in the console log)
is out of scope for the prototype: :func:`start_recording` is the stub.
"""
from __future__ import annotations

import logging
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Mapping

from aiohttp import web

logger = logging.getLogger(__name__)

STATES = ("OFF", "MON", "TALK")
_RANK = {s: i for i, s in enumerate(STATES)}
#: Positions that are not MCS consoles and need the instructor role.
ROLE_POSITIONS = ("instructor", "sim")
COLOURS = frozenset([f"cat-{i}" for i in range(1, 9)] + ["neutral"])
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_PREFIX_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
IAP_USER_HEADER = "X-Goog-Authenticated-User-Email"
MIN_TTL_S, MAX_TTL_S = 60, 600
#: The compose `livekit` service (profile voice) runs with this key pair.
#: Loopback only, never a production credential.
DEV_API_KEY = "c2odev"
DEV_API_SECRET = "c2o-local-development-secret-not-for-production"
DEV_PORT = 7880
LOOPS_FILE = Path("voice") / "voice_loops.yaml"


class VoiceConfigError(ValueError):
    """voice_loops.yaml is missing or inconsistent (all problems listed)."""


# ── Loop configuration ────────────────────────────────────────────────

@dataclass(frozen=True)
class Loop:
    id: str
    label: dict
    colour: str
    instructor_only: bool
    access: dict
    start: dict

    def access_for(self, position: str) -> str:
        return self.access.get(position, self.access.get("default", "OFF"))

    def start_for(self, position: str) -> str:
        """Initial key state, never above the access right."""
        want = self.start.get(position, self.start.get("default", "OFF"))
        have = self.access_for(position)
        return want if _RANK[want] <= _RANK[have] else have


@dataclass(frozen=True)
class VoiceLoops:
    loops: tuple
    recordings: bool
    positions: tuple                 # MCS positions (positions.yaml order)
    role_labels: dict                # instructor / sim -> {en, fr}
    position_labels: dict = field(default_factory=dict)   # MCS id -> {en, fr}

    @property
    def all_positions(self) -> tuple:
        return tuple(self.positions) + ROLE_POSITIONS

    def label_for(self, position: str) -> dict:
        if position in self.role_labels:
            return dict(self.role_labels[position])
        return dict(self.position_labels.get(position) or {"en": position})


def _fr_position_names(config_dir: Path) -> dict:
    """{position id: French display name} from the translation overlay
    (``pos:<id>:display_name``); {} when the overlay is absent."""
    import yaml
    p = Path(config_dir) / "i18n" / "fr" / "db.yaml"
    try:
        rows = yaml.safe_load(p.read_text(encoding="utf-8")) or []
    except (OSError, yaml.YAMLError):
        return {}
    out = {}
    for e in rows if isinstance(rows, list) else []:
        key = str((e or {}).get("key", ""))
        if key.startswith("pos:") and key.endswith(":display_name") and e.get("fr"):
            out[key.split(":")[1]] = str(e["fr"])
    return out


def _mcs_positions(config_dir: Path) -> dict:
    """{position id: display name} from mcs/positions.yaml, in file order."""
    import yaml
    p = Path(config_dir) / "mcs" / "positions.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out = {}
    for k, v in (data.get("positions") or {}).items():
        v = v if isinstance(v, dict) else {}
        out[str(k)] = str(v.get("display_name") or v.get("label") or k)
    return out


def validate(data, mcs_positions) -> list[str]:
    """Every problem with a parsed voice_loops.yaml, as readable strings.

    ``mcs_positions`` is the list of MCS position ids (positions.yaml)."""
    errs: list[str] = []
    if not isinstance(data, dict):
        return ["voice_loops.yaml: top level must be a mapping"]
    known = set(mcs_positions) | set(ROLE_POSITIONS)
    if not isinstance(data.get("recordings"), bool):
        errs.append("recordings: must be true or false")
    roles = data.get("role_positions")
    if not isinstance(roles, dict) or set(roles) != set(ROLE_POSITIONS):
        errs.append(f"role_positions: must define exactly {list(ROLE_POSITIONS)}")
    else:
        for r, v in roles.items():
            lab = (v or {}).get("label") if isinstance(v, dict) else None
            if not (isinstance(lab, dict) and str(lab.get("en") or "").strip()
                    and str(lab.get("fr") or "").strip()):
                errs.append(f"role_positions.{r}.label: needs en and fr")
    clash = set(ROLE_POSITIONS) & set(mcs_positions)
    if clash:
        errs.append(f"positions.yaml already defines {sorted(clash)}: rename the voice roles")
    loops = data.get("loops")
    if not isinstance(loops, list) or not loops:
        return errs + ["loops: must be a non-empty list"]
    seen: set[str] = set()
    talk_at_start: dict[str, list[str]] = {}
    for i, lp in enumerate(loops):
        where = f"loops[{i}]"
        if not isinstance(lp, dict):
            errs.append(f"{where}: must be a mapping"); continue
        lid = lp.get("id")
        if not isinstance(lid, str) or not _ID_RE.match(lid):
            errs.append(f"{where}.id: {lid!r} is not an identifier ([a-z][a-z0-9_]*, <= 32)")
            lid = f"#{i}"
        elif lid in seen:
            errs.append(f"{where}.id: duplicate {lid!r}")
        seen.add(lid)
        where = f"loop {lid}"
        extra = set(lp) - {"id", "label", "colour", "instructor_only", "access", "start"}
        if extra:
            errs.append(f"{where}: unknown keys {sorted(extra)}")
        lab = lp.get("label")
        if not (isinstance(lab, dict) and str(lab.get("en") or "").strip()
                and str(lab.get("fr") or "").strip()):
            errs.append(f"{where}.label: needs non-empty en and fr")
        if lp.get("colour") not in COLOURS:
            errs.append(f"{where}.colour: {lp.get('colour')!r} (use cat-1..cat-8 or neutral)")
        io = lp.get("instructor_only")
        if not isinstance(io, bool):
            errs.append(f"{where}.instructor_only: must be true or false")
        maps = {}
        for key in ("access", "start"):
            m = lp.get(key, {} if key == "start" else None)
            if not isinstance(m, dict) or (key == "access" and not m):
                errs.append(f"{where}.{key}: must be a mapping of position -> OFF|MON|TALK")
                m = {}
            for pos, st in m.items():
                if pos != "default" and pos not in known:
                    errs.append(f"{where}.{key}.{pos}: unknown position "
                                f"(positions.yaml or {list(ROLE_POSITIONS)})")
                if st is False:
                    errs.append(f"{where}.{key}.{pos}: write \"OFF\" in quotes "
                                f"(YAML reads a bare OFF as false)")
                elif st not in STATES:
                    errs.append(f"{where}.{key}.{pos}: {st!r} (OFF, MON or TALK)")
            maps[key] = {k: v for k, v in m.items() if v in STATES}
        acc = maps["access"]
        default_acc = acc.get("default", "OFF")
        for pos, st in maps["start"].items():
            if pos == "default":
                continue
            have = acc.get(pos, default_acc)
            if _RANK[st] > _RANK[have]:
                errs.append(f"{where}.start.{pos}: {st} is above its access {have}")
        if io is True:
            if default_acc != "OFF":
                errs.append(f"{where}: instructor_only loop must have access.default OFF")
            for pos in mcs_positions:
                if acc.get(pos, default_acc) != "OFF":
                    errs.append(f"{where}: instructor_only loop gives student position "
                                f"{pos} {acc.get(pos, default_acc)}")
        for pos in known:
            st = maps["start"].get(pos, maps["start"].get("default", "OFF"))
            have = acc.get(pos, default_acc)
            if st == "TALK" and have == "TALK":
                talk_at_start.setdefault(pos, []).append(lid)
    for pos, lids in sorted(talk_at_start.items()):
        if len(lids) > 1:
            errs.append(f"position {pos} starts in TALK on {lids}: one talk loop at a time")
    for pos in sorted(known):
        if not any(isinstance(lp, dict) and isinstance(lp.get("access"), dict)
                   and lp["access"].get(pos, lp["access"].get("default", "OFF")) != "OFF"
                   for lp in loops):
            errs.append(f"position {pos} hears no loop at all")
    return errs


def load_voice_loops(config_dir: str | os.PathLike) -> VoiceLoops:
    import yaml
    config_dir = Path(config_dir)
    path = config_dir / LOOPS_FILE
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise VoiceConfigError(f"{path}: {e}") from e
    except yaml.YAMLError as e:
        raise VoiceConfigError(f"{path} does not parse: {e}") from e
    mcs = _mcs_positions(config_dir)
    fr = _fr_position_names(config_dir)
    errs = validate(data, list(mcs))
    if errs:
        raise VoiceConfigError(f"{path}:\n  " + "\n  ".join(errs))
    loops = tuple(
        Loop(id=lp["id"], label={"en": str(lp["label"]["en"]), "fr": str(lp["label"]["fr"])},
             colour=lp["colour"], instructor_only=bool(lp["instructor_only"]),
             access=dict(lp["access"]), start=dict(lp.get("start") or {}))
        for lp in data["loops"])
    roles = {r: {"en": str(v["label"]["en"]), "fr": str(v["label"]["fr"])}
             for r, v in data["role_positions"].items()}
    return VoiceLoops(loops=loops, recordings=bool(data["recordings"]),
                      positions=tuple(mcs), role_labels=roles,
                      position_labels={k: ({"en": v, "fr": fr[k]} if k in fr else {"en": v})
                                       for k, v in mcs.items()})


# ── Settings and identity ─────────────────────────────────────────────

def _truthy(v) -> bool:
    return str(v or "").strip().lower() in ("1", "yes", "true", "on")


@dataclass(frozen=True)
class Settings:
    url: str = ""                    # "" + dev = ws://<request host>:7880
    api_key: str = ""
    api_secret: str = ""
    dev: bool = False
    require_iap: bool = False
    instructors: frozenset = frozenset()
    local_instructor: bool = False
    room_prefix: str = "c2o"
    ttl_s: int = MAX_TTL_S

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = dict(os.environ if env is None else env)
        dev = str(env.get("SMO_VOICE", "")).strip().lower() == "dev"
        key = env.get("LIVEKIT_API_KEY", "").strip() or (DEV_API_KEY if dev else "")
        secret = env.get("LIVEKIT_API_SECRET", "").strip() or (DEV_API_SECRET if dev else "")
        url = env.get("LIVEKIT_URL", "").strip()
        instr = frozenset(x.strip().lower() for x in
                          re.split(r"[\s,;]+", env.get("SMO_VOICE_INSTRUCTORS", "")
                                   or env.get("SMO_INSTRUCTORS", "")) if "@" in x)
        prefix = env.get("SMO_VOICE_ROOM_PREFIX", "").strip().lower() or "c2o"
        if not _PREFIX_RE.match(prefix):
            logger.warning("SMO_VOICE_ROOM_PREFIX %r is not [a-z0-9-]{1,32}: using c2o", prefix)
            prefix = "c2o"
        try:
            ttl = int(env.get("SMO_VOICE_TOKEN_TTL_S") or MAX_TTL_S)
        except ValueError:
            ttl = MAX_TTL_S
        local_default = "1" if dev else "0"
        return cls(url=url, api_key=key, api_secret=secret, dev=dev,
                   require_iap=_truthy(env.get("SMO_VOICE_REQUIRE_IAP")),
                   instructors=instr,
                   local_instructor=_truthy(env.get("SMO_VOICE_LOCAL_INSTRUCTOR", local_default)),
                   room_prefix=prefix, ttl_s=max(MIN_TTL_S, min(MAX_TTL_S, ttl)))

    def problem(self) -> str | None:
        """Why tokens cannot be minted, or None."""
        if not (self.api_key and self.api_secret):
            return "not-configured"
        if not self.url and not self.dev:
            return "not-configured"
        if len(self.api_secret) < 32:
            return "weak-secret"
        try:
            import livekit.api  # noqa: F401
        except ImportError:
            return "no-library"
        return None

    def server_url(self, request_host: str | None) -> str:
        if self.url:
            return self.url
        host = (request_host or "localhost").strip()
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"ws://{host}:{DEV_PORT}"


@dataclass(frozen=True)
class Caller:
    who: str            # stable account key: an email, or "local:<name>"
    name: str           # shown on the talker indicator
    verified: bool
    instructor: bool


def iap_email(headers) -> str | None:
    raw = (headers.get(IAP_USER_HEADER) or "").strip()
    if not raw:
        return None
    email = (raw.split(":", 1)[1] if ":" in raw else raw).strip().lower()
    return email[:254] if "@" in email else None


def clean_name(raw) -> str:
    """A typed display name: printable, single-spaced, <= 40 characters."""
    s = unicodedata.normalize("NFC", str(raw or ""))
    s = "".join(ch for ch in s if unicodedata.category(ch)[0] not in ("C",))
    s = " ".join(s.split())
    return s[:40].strip()


def caller_for(headers, typed_name, settings: Settings) -> Caller | None:
    """The caller, or None when a name must be typed first (local mode).
    Raises HTTPUnauthorized when IAP is required and absent."""
    email = iap_email(headers)
    if email:
        return Caller(who=email, name=email, verified=True,
                      instructor=email in settings.instructors)
    if settings.require_iap:
        raise web.HTTPUnauthorized(
            text='{"error": "sign-in required (IAP identity missing)"}',
            content_type="application/json")
    name = clean_name(typed_name)
    if not name:
        return None
    return Caller(who="local:" + name.lower(), name=name, verified=False,
                  instructor=settings.local_instructor)


def positions_for(cfg: VoiceLoops, caller: Caller | None) -> list[str]:
    """Positions this caller may take (roles only with the instructor role)."""
    out = list(cfg.positions)
    if caller is not None and caller.instructor:
        out += list(ROLE_POSITIONS)
    return out


def room_name(settings: Settings, loop: Loop) -> str:
    return f"{settings.room_prefix}-{loop.id}"


def mint(cfg: VoiceLoops, settings: Settings, caller: Caller, position: str, *,
         request_host: str | None = None) -> dict:
    """One token per loop the position may hear; canPublish only on TALK."""
    from livekit import api as lk
    ttl = int(settings.ttl_s)
    attrs = {"position": position, "verified": "1" if caller.verified else "0",
             "role": "instructor" if caller.instructor else "operator"}
    identity = f"{caller.who}|{position}"
    out = []
    for loop in cfg.loops:
        access = loop.access_for(position)
        if access == "OFF":
            continue                      # never tell a browser about it
        if loop.instructor_only and not caller.instructor:
            continue                      # belt and braces: validate() already forbids it
        talk = access == "TALK"
        grant = lk.VideoGrants(
            room_join=True, room=room_name(settings, loop),
            can_subscribe=True, can_publish=talk,
            can_publish_sources=["microphone"] if talk else [],
            can_publish_data=False, can_update_own_metadata=False)
        tok = (lk.AccessToken(settings.api_key, settings.api_secret)
               .with_identity(identity).with_name(caller.name)
               .with_attributes(attrs).with_grants(grant)
               .with_ttl(timedelta(seconds=ttl)))
        out.append({"id": loop.id, "label": dict(loop.label), "colour": loop.colour,
                    "instructor_only": loop.instructor_only, "access": access,
                    "start": loop.start_for(position), "room": room_name(settings, loop),
                    "token": tok.to_jwt()})
    now = int(time.time())
    return {"url": settings.server_url(request_host), "position": position,
            "identity": {"name": caller.name, "verified": caller.verified,
                         "instructor": caller.instructor},
            "issued_at": now, "expires_at": now + ttl, "ttl_s": ttl,
            "refresh_in_s": max(30, int(ttl * 0.75)),
            "recordings": cfg.recordings, "loops": out}


def start_recording(*_args, **_kwargs):
    """STUB (out of scope for the prototype). Recording will be an
    instructor-only toggle that starts LiveKit egress (room composite, audio
    only) per loop into a Cloud Storage bucket in Toronto, stamped with UTC
    and sim time and indexed in the MCS console log. `recordings: false` in
    voice_loops.yaml keeps it off; nothing calls this yet."""
    raise NotImplementedError("voice recordings are not implemented (WP-4 prototype)")


# ── HTTP ──────────────────────────────────────────────────────────────

_NO_STORE = {"Cache-Control": "no-store"}


def register_voice_routes(app: web.Application, config_dir, *,
                          env: Mapping[str, str] | None = None,
                          static_dir: str | os.PathLike | None = None,
                          default_lang: str = "en", seats=None) -> None:
    """Mount /voice, /api/voice/config and /api/voice/token on *app*.

    An invalid voice_loops.yaml is logged and the endpoints answer 503 with
    the reason; the rest of the MCS is unaffected."""
    settings = Settings.from_env(env)
    try:
        cfg: VoiceLoops | None = load_voice_loops(config_dir)
        cfg_error = None
    except VoiceConfigError as e:
        cfg, cfg_error = None, str(e)
        logger.error("Voice loops disabled: %s", e)
    static_dir = Path(static_dir) if static_dir else Path(__file__).parent / "static" / "modern"
    page = static_dir / "voice.html"
    if cfg is not None:
        prob = settings.problem()
        logger.info("Voice loops: %d loops, %s", len(cfg.loops),
                    f"tokens for {settings.url or 'ws://<host>:7880 (dev)'}" if not prob
                    else f"token service off ({prob})")

    def _err(status: int, code: str, msg: str) -> web.Response:
        return web.json_response({"error": msg, "code": code}, status=status, headers=_NO_STORE)

    async def voice_page(request):
        if not page.is_file():
            raise web.HTTPNotFound(text="voice panel not installed")
        from smo_common.web.http import stamp_asset_versions
        html = page.read_text(encoding="utf-8")
        if default_lang and default_lang != "en":
            from smo_common.i18n import inject_default_lang
            html = inject_default_lang(html, default_lang)
        return web.Response(text=stamp_asset_versions(html, app), content_type="text/html",
                            headers={"Cache-Control": "no-cache"})

    async def seat_caller(request, typed_name):
        """(caller, desks) from the seat registry, or (None, None) when
        seats are off. Raises SeatHttpError for 401."""
        if seats is None or not seats.enforced:
            return None, None
        ident = await seats.person(request, typed_name=typed_name or "", require=False)
        if ident is None or not ident.name:
            return None, []
        desks = seats.registry.command_positions(ident.person_id)
        return Caller(who=ident.person_id, name=ident.name, verified=ident.verified,
                      instructor=ident.instructor), desks

    async def voice_config(request):
        if cfg is None:
            return _err(503, "bad-config", cfg_error or "voice_loops.yaml invalid")
        from smo_mcs.seats_http import SeatHttpError
        try:
            caller, desks = await seat_caller(request, request.query.get("name"))
            if desks is None:
                caller = caller_for(request.headers, request.query.get("name"), settings)
        except (web.HTTPUnauthorized, SeatHttpError):
            return _err(401, "sign-in", "sign-in required")
        if desks is not None:
            labels = {p: cfg.label_for(p) for p in cfg.all_positions}
            ident = None if caller is None else {"name": caller.name, "verified": caller.verified,
                                                 "instructor": caller.instructor}
            return web.json_response({
                "available": settings.problem() is None, "reason": settings.problem(),
                "recordings": cfg.recordings, "identity": ident,
                "needs_name": caller is None, "seats": True,
                "local_instructor": False,
                "positions": [p for p in cfg.positions if p in desks] +
                (list(ROLE_POSITIONS) if caller is not None and caller.instructor else []),
                "role_positions": list(ROLE_POSITIONS),
                "position_labels": labels, "ttl_s": settings.ttl_s,
            }, headers=_NO_STORE)
        labels = {p: cfg.label_for(p) for p in cfg.all_positions}
        ident = None
        if caller is not None:
            ident = {"name": caller.name, "verified": caller.verified,
                     "instructor": caller.instructor}
        return web.json_response({
            "available": settings.problem() is None, "reason": settings.problem(),
            "recordings": cfg.recordings, "identity": ident,
            "needs_name": caller is None,
            "local_instructor": (not settings.require_iap) and settings.local_instructor,
            "positions": positions_for(cfg, caller) if caller is not None
            else list(cfg.positions) + (list(ROLE_POSITIONS) if settings.local_instructor else []),
            "role_positions": list(ROLE_POSITIONS),
            "position_labels": labels, "ttl_s": settings.ttl_s,
        }, headers=_NO_STORE)

    async def voice_token(request):
        if cfg is None:
            return _err(503, "bad-config", cfg_error or "voice_loops.yaml invalid")
        prob = settings.problem()
        if prob:
            return _err(503, prob, {
                "not-configured": "voice server not configured (LIVEKIT_URL/API_KEY/API_SECRET)",
                "weak-secret": "LIVEKIT_API_SECRET must be at least 32 characters",
                "no-library": "the livekit-api package is not installed",
            }.get(prob, prob))
        # JSON only: a cross-site form post cannot send it without a CORS
        # preflight, which this endpoint never answers.
        if request.content_type != "application/json":
            return _err(415, "json", "send application/json")
        if (request.content_length or 0) > 4096:
            return _err(413, "too-large", "request too large")
        try:
            body = await request.json()
        except ValueError:
            return _err(400, "json", "body is not JSON")
        if not isinstance(body, dict):
            return _err(400, "json", "body must be an object")
        from smo_mcs.seats_http import SeatHttpError
        try:
            caller, desks = await seat_caller(request, body.get("name"))
            if desks is None:
                caller = caller_for(request.headers, body.get("name"), settings)
        except (web.HTTPUnauthorized, SeatHttpError):
            return _err(401, "sign-in", "sign-in required")
        if caller is None:
            return _err(400, "name", "type your name first")
        position = str(body.get("position") or "").strip()
        if position not in cfg.all_positions:
            return _err(400, "position", f"unknown position {position[:40]!r}")
        if position in ROLE_POSITIONS and not caller.instructor:
            return _err(403, "instructor", "this position needs the instructor role")
        if desks is not None and position not in ROLE_POSITIONS and position not in desks:
            # Seats on: the loops follow the desk the caller HOLDS, never a
            # position typed into the request (WP10).
            return _err(403, "not-holder", f"you do not hold the {position[:40]} desk")
        result = mint(cfg, settings, caller, position, request_host=request.url.host)
        logger.info("voice token: %s as %s, %d loops", caller.who, position, len(result["loops"]))
        return web.json_response(result, headers=_NO_STORE)

    app.router.add_get("/voice", voice_page)
    app.router.add_get("/api/voice/config", voice_config)
    app.router.add_post("/api/voice/token", voice_token)
