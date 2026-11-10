"""SpaceCDF design -> EOSAT-1-class simulator configuration (design-to-ops export, Nov 2026).

``build(facts, template_dir)`` turns the facts of a study (``facts.gather``) into a
simulator configuration directory with the layout of ``sim/configs/eosat1``. Every value is
either taken from the design model (written with a ``# design: <source>`` comment) or is a
documented default (``# C2O default: <reason>``); the readiness checklist lists, per CDR
area, what still comes from a default and why.

What the simulator can and cannot be told
-----------------------------------------
The simulator runs EOSAT-1-class *models*: a 9-line PCDU, a 4-wheel pyramid, a 16-node
thermal network, a fixed TM point set and S8 function map (the model interface). A design
therefore sets the model's *numbers* (capacities, areas, powers, gains, limits, rates,
thresholds, orbit, stations, tables) and maps its own items onto the model's slots by role
(a design power line by the units it feeds, a design TM point or command by name). What
has no slot is reported as ``unsupported`` instead of being silently dropped.

The defaults are the EOSAT-1 reference configuration (the template directory): a design
that says nothing about a value flies EOSAT-1's.

When the study holds the read-only EOSAT-1 reference CDR database (the import), the TM/TC
database, FDIR, AOCS mode and operations files are written from the CDR rows
(``cdr_sim.export_sim``); a study with its own (designed) CDR database keeps the model
interface catalogue and overlays what maps by name, and writes its full database to
``design_db/`` for reference.
"""
from __future__ import annotations

import copy
import io
import math
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from . import yaml_emit

# ───────────────────────────────────────────────────────────── vocabulary

AREAS: dict[str, dict[str, str]] = {
    "mission": {"en": "Mission and orbit", "fr": "Mission et orbite"},
    "eps": {"en": "Power (EPS)", "fr": "Puissance (EPS)"},
    "aocs": {"en": "Attitude and orbit control (AOCS)", "fr": "Contrôle d’attitude et d’orbite (SCAO)"},
    "tcs": {"en": "Thermal (TCS)", "fr": "Thermique (TCS)"},
    "obdh": {"en": "On-board data handling (OBDH)", "fr": "Gestion bord (OBDH)"},
    "ttc": {"en": "TT&C and RF", "fr": "TT&C et RF"},
    "payload": {"en": "Payload", "fr": "Charge utile"},
    "prop": {"en": "Propulsion", "fr": "Propulsion"},
    "geometry": {"en": "Configuration and geometry", "fr": "Configuration et géométrie"},
    "tmtc": {"en": "TM/TC database", "fr": "Base de données TM/TC"},
    "fdir": {"en": "FDIR", "fr": "FDIR"},
    "ops": {"en": "Operations", "fr": "Exploitation"},
}
STATUSES = ("design", "default", "missing", "unsupported")

#: the simulator's PCDU (eps_basic.POWER_LINE_DEFS): name -> (switchable, index)
SIM_LINES = {"obc": (False, 0), "ttc_rx": (False, 1), "ttc_tx": (True, 2), "payload": (True, 3),
             "fpa_cooler": (True, 4), "htr_bat": (True, 5), "htr_obc": (True, 6), "aocs_wheels": (True, 7),
             "prop": (True, 8)}
#: simulator AOCS mode names (aocs/aocs_mode_codes.yaml)
SIM_AOCS_MODES = ("OFF", "SAFE_BOOT", "DETUMBLE", "COARSE_SUN", "NOMINAL", "FINE_POINT", "SLEW", "DESAT",
                  "ECLIPSE", "INERTIAL")
#: simulator HK SID per subsystem (telemetry/hk_structures.yaml)
SIM_SID_OF_SUBSYSTEM = {"eps": 1, "aocs": 2, "tcs": 3, "obdh": 4, "payload": 5, "ttc": 6, "prop": 9}
#: simulator heater circuits (tcs.yaml heaters) by the unit class they heat
SIM_HEATER_OF_CLASS = {"battery": "battery", "obc": "obc", "propulsion": "thruster"}

#: directories and files of the template that are NOT exported (README in the export says why)
OMIT = ("manual", "procedures", "worksheets", "i18n", "xtce", "smdl")
#: whole files written verbatim from the template (simulator-side content no design decides)
SIM_ONLY_FILES_NOTE = "simulator content with no design counterpart (EOSAT-1 reference file)"

STD_EPOCH = "2026-08-20T12:00:00Z"
RE = 6371.0
MU = 398600.4418


# ───────────────────────────────────────────────────────────── small helpers

def _num(v: Any) -> float | None:
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _r(v: float, n: int = 4) -> float:
    return float(round(float(v), n))


def _get(d: Any, path: tuple) -> Any:
    cur = d
    for k in path:
        if isinstance(cur, dict):
            cur = cur.get(k)
        elif isinstance(cur, list) and isinstance(k, int) and 0 <= k < len(cur):
            cur = cur[k]
        else:
            return None
    return cur


def _set(d: Any, path: tuple, value: Any) -> None:
    cur = d
    for k in path[:-1]:
        if isinstance(cur, dict):
            cur = cur.setdefault(k, {})
        else:
            cur = cur[k]
    cur[path[-1]] = value


def _en(t: Any) -> str:
    return t.get("en", "") if isinstance(t, dict) else str(t or "")


def _slug(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


# ───────────────────────────────────────────────────────────── the export object

@dataclass
class SimConfigExport:
    template_dir: Path
    files: dict[str, Any] = field(default_factory=dict)
    comments: dict[str, dict[tuple, str]] = field(default_factory=dict)
    headers: dict[str, list[str]] = field(default_factory=dict)
    leaf_files: set[str] = field(default_factory=set)
    texts: dict[str, str] = field(default_factory=dict)
    items: list[dict] = field(default_factory=list)
    dataset: str = "empty"
    study_id: str = ""
    study_name: str = ""

    # ── template access ──
    def load(self, rel: str) -> Any:
        if rel not in self.files:
            p = self.template_dir / rel
            self.files[rel] = copy.deepcopy(yaml.safe_load(p.read_text(encoding="utf-8"))) if p.is_file() else {}
            self.comments.setdefault(rel, {})
        return self.files[rel]

    # ── provenance ──
    def design(self, area: str, rel: str, path: tuple, value: Any, src: str, label: str | None = None,
               *, item: bool = True) -> None:
        data = self.load(rel)
        _set(data, path, value)
        self.comments[rel][path] = f"design: {src}"
        if item:
            self.items.append({"area": area, "item": label or ".".join(map(str, path)), "status": "design",
                               "file": rel, "key": ".".join(map(str, path)), "source": src})

    def default(self, area: str, rel: str, path: tuple, reason: str, label: str | None = None,
                status: str = "default", *, item: bool = True, value: Any = ...) -> None:
        data = self.load(rel)
        if value is not ...:
            _set(data, path, value)
        if _get(data, path) is None and value is ...:
            return
        self.comments[rel][path] = f"C2O default: {reason}"
        if item:
            self.items.append({"area": area, "item": label or ".".join(map(str, path)), "status": status,
                               "file": rel, "key": ".".join(map(str, path)), "source": reason})

    def note(self, area: str, label: str, status: str, reason: str, rel: str = "", key: str = "") -> None:
        self.items.append({"area": area, "item": label, "status": status, "file": rel, "key": key, "source": reason})

    def sim_detail(self, rel: str, path: tuple, what: str = "simulator implementation detail (not a design decision)") -> None:
        self.load(rel)
        if _get(self.files[rel], path) is not None:
            self.comments[rel][path] = f"C2O default: {what}"

    # ── output ──
    def readiness(self) -> dict[str, Any]:
        areas = []
        for aid, label in AREAS.items():
            its = [i for i in self.items if i["area"] == aid]
            counts = {s: sum(1 for i in its if i["status"] == s) for s in STATUSES}
            areas.append({"id": aid, "label": label, **counts, "total": len(its),
                          "items": sorted(its, key=lambda i: (STATUSES.index(i["status"]), i["item"]))})
        tot = {s: sum(a[s] for a in areas) for s in STATUSES}
        return {"study_id": self.study_id, "study_name": self.study_name, "dataset": self.dataset,
                "areas": areas, "totals": tot,
                "ready": tot["missing"] == 0 and tot["unsupported"] == 0,
                "files": sorted(list(self.files) + list(self.texts))}

    def render(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for rel, data in self.files.items():
            com = dict(self.comments.get(rel) or {})
            if rel in self.leaf_files:
                _default_leaves(data, com)
            head = self.headers.get(rel) or _header(rel, self)
            if any(SIM_ONLY_FILES_NOTE in h for h in head) and any(str(c).startswith("design:") for c in com.values()):
                head = [head[0], "C2O default: the EOSAT-1 reference file (the simulator model interface); the entries",
                        "marked `# design: ...` come from the design.", ""]
            out[rel] = yaml_emit.dump(data, com, head)
        out.update(self.texts)
        return out

    def write(self, target: Path) -> list[Path]:
        written = []
        for rel, text in self.render().items():
            p = target / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            written.append(p)
        return written

    def zip_bytes(self, root: str = "") -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for rel, text in sorted(self.render().items()):
                z.writestr(f"{root}/{rel}" if root else rel, text)
        return buf.getvalue()


def _header(rel: str, ex: SimConfigExport) -> list[str]:
    return [f"{rel} — simulator configuration exported by SpaceCDF from study {ex.study_name or ex.study_id}",
            "Each value carries its source: `design: ...` (the SpaceCDF design model) or",
            "`C2O default: ...` (a documented default; the EOSAT-1 reference value unless stated).",
            "A key without its own note takes the note of the block above it.", ""]


def _default_leaves(data: Any, com: dict[tuple, str], path: tuple = (), inherited: bool = False) -> None:
    """Mark every top-level key and leaf with no note (and no noted ancestor) as an EOSAT-1 default."""
    if isinstance(data, dict):
        for k, v in data.items():
            p = path + (k,)
            here = p in com
            child_noted = any(len(q) > len(p) and q[:len(p)] == p for q in com)
            if not here and not inherited and not child_noted and (
                    not isinstance(v, (dict, list)) or not v or yaml_emit._flowable(v)):
                com[p] = "C2O default: EOSAT-1 reference value (no design source)"
                here = True
            if isinstance(v, dict) and (not yaml_emit._flowable(v) or child_noted):
                _default_leaves(v, com, p, inherited or here)


# ───────────────────────────────────────────────────────────── design facts views

class Design:
    """Read-only views on the gathered facts (units by class, KB performance, lines …)."""

    def __init__(self, facts: dict[str, Any]):
        from ..mode_model import unit_class
        from ..rule_inputs import kb_component, perf, qty
        self.f = facts
        self.kb_component, self.perf, self.qty = kb_component, perf, qty
        self.els = [e for e in facts.get("elements") or [] if not e.get("deleted_at")]
        self.by_id = {e["id"]: e for e in self.els}
        self.space_units = [e for e in self.els if e.get("element_type") == "component"
                            and (e.get("segment") or "space") == "space" and e.get("in_scope", True) is not False]
        self.cls: dict[str, str] = {}
        for e in self.space_units:
            name = str(e.get("name") or "").lower()
            self.cls[e["id"]] = "sada" if ("sada" in name or "array drive" in name) else unit_class(e)
        self.req = facts.get("requirements") or {}

    def units(self, *classes: str) -> list[dict]:
        return [e for e in self.space_units if self.cls.get(e["id"]) in classes]

    def unit(self, *classes: str) -> dict | None:
        u = self.units(*classes)
        return u[0] if u else None

    def kbp(self, e: dict | None) -> dict:
        if not e:
            return {}
        return {**((self.kb_component(e) or {}).get("performance") or {}), **self.perf(e)}

    def kb(self, e: dict | None) -> dict:
        return (self.kb_component(e) or {}) if e else {}

    def power(self, e: dict | None, peak: bool = False) -> float | None:
        if not e:
            return None
        v = _num(e.get("power_peak_w")) if peak else None
        v = v if v is not None else _num(e.get("power_avg_w"))
        if v is None:
            v = _num(self.kb(e).get("power_w")) or _num(self.kbp(e).get("power_w"))
        return None if v is None else v * self.qty(e)

    def mass(self, els: list[dict]) -> float:
        tot = 0.0
        for e in els:
            m = _num(e.get("mass_kg"))
            if m is None:
                m = _num(self.kb(e).get("mass_kg")) or 0.0
            tot += m * self.qty(e)
        return tot

    def name(self, e: dict | None) -> str:
        return str((e or {}).get("name") or "")

    def mode_power(self, e: dict, kind: str) -> float | None:
        """Unit power in the first mode of ``kind`` (mode × unit matrix)."""
        for m in self.f.get("modes") or []:
            if m.get("kind") != kind:
                continue
            for mem in m.get("members") or []:
                if mem.get("element_id") == e["id"] and mem.get("state") != "off":
                    return _num(mem.get("power_w"))
        return None

    # electrical
    def lines(self) -> list[dict]:
        return [ln for ln in (self.f.get("electrical") or {}).get("lines") or [] if ln.get("status") != "rejected"
                and not ln.get("deleted_at")]

    def rails(self) -> list[dict]:
        return [r for r in (self.f.get("electrical") or {}).get("rails") or [] if r.get("status") != "rejected"]

    def sim_line_of(self, ln: dict) -> str | None:
        """The simulator PCDU line a design power line maps to (by the units it feeds)."""
        loads = [self.by_id.get(i) for i in ln.get("load_element_ids") or []]
        classes = {self.cls.get(e["id"]) for e in loads if e}
        names = " ".join(self.name(e).lower() for e in loads if e) + " " + str(ln.get("name") or "").lower()
        if "obc" in classes or "eps" in classes:
            return "obc"
        if "transmitter" in classes:
            return "ttc_tx"
        if "receiver" in classes:
            return "ttc_rx"
        if "payload" in classes:
            return "payload"
        if "cooler" in names:
            return "fpa_cooler"
        if "heater" in classes:
            if "obc" in names or "computer" in names:
                return "htr_obc"
            if "prop" in names or "thruster" in names or "catbed" in names:
                return "prop"
            return "htr_bat"
        if classes & {"wheel", "star_tracker", "magnetorquer", "adcs_sensor", "gnss"}:
            return "aocs_wheels"
        if "propulsion" in classes:
            return "prop"
        return None


# ───────────────────────────────────────────────────────────── orbit maths

def _sun_ra_deg(t: datetime) -> float:
    """Apparent solar right ascension (Astronomical Almanac low-precision, ~0.01°)."""
    jd = t.timestamp() / 86400.0 + 2440587.5
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360.0
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    return math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))) % 360.0


def raan_from_ltan(ltan: str, epoch: datetime) -> float:
    hh, mm = (ltan.split(":") + ["0"])[:2]
    hours = float(hh) + float(mm) / 60.0
    return (_sun_ra_deg(epoch) + (hours - 12.0) * 15.0) % 360.0


def tle(alt_km: float, inc: float, ecc: float, raan: float, argp: float, ma: float, epoch: datetime) -> tuple[str, str]:
    from spacecdf_agents.exporters.smo.orbit_gen import keplerian_to_tle
    return keplerian_to_tle(altitude_km=alt_km, inclination_deg=inc, eccentricity=ecc, raan_deg=raan,
                            arg_perigee_deg=argp, mean_anomaly_deg=ma, epoch=epoch)


# ───────────────────────────────────────────────────────────── build

def build(facts: dict[str, Any], template_dir: Path) -> SimConfigExport:
    from .. import cdr_model as cm
    ex = SimConfigExport(template_dir=Path(template_dir), study_id=str(facts.get("study_id") or ""),
                         study_name=str(facts.get("study_name") or ""))
    d = Design(facts)
    rows = facts.get("cdr_rows") or []
    ex.dataset = cm.dataset_of(rows)
    _copy_template(ex)
    ctx = {"line_map": _line_map(ex, d)}
    _mission(ex, d, rows)
    _orbit(ex, d)
    _eps(ex, d, rows, ctx)
    _aocs(ex, d, rows)
    _tcs(ex, d)
    _ttc(ex, d, rows, ctx)
    _payload(ex, d)
    _prop(ex, d)
    _obdh(ex, d)
    _geometry(ex, d)
    _consistency(ex, d)
    _database(ex, d, rows, ctx)
    _ops(ex, d, rows)
    _sim_details(ex)
    ex.texts["README.md"] = _readme(ex)
    return ex


def _copy_template(ex: SimConfigExport) -> None:
    """Load every exported YAML of the template (whole-file defaults until a mapper touches them)."""
    root = ex.template_dir
    for p in sorted(root.rglob("*.yaml")):
        rel = p.relative_to(root).as_posix()
        if rel.split("/")[0] in OMIT:
            continue
        ex.load(rel)
    for rel in ("mission.yaml", "orbit.yaml", "simulation.yaml", "rfsim.yaml") + tuple(
            f"subsystems/{n}.yaml" for n in ("eps", "aocs", "tcs", "obdh", "ttc", "payload", "prop", "fdir")):
        ex.leaf_files.add(rel)
    for rel in ex.files:
        if rel not in ex.leaf_files:
            ex.headers[rel] = _header(rel, ex)[:1] + [f"C2O default: {SIM_ONLY_FILES_NOTE}.", ""]


# ── electrical line map ───────────────────────────────────────────────────

def _line_map(ex: SimConfigExport, d: Design) -> dict[str, Any]:
    """design line id -> simulator line name (+ the reverse: the first design line per sim line)."""
    fwd: dict[str, str] = {}
    rev: dict[str, dict] = {}
    for ln in sorted(d.lines(), key=lambda x: x.get("line_no") or 0):
        sim = d.sim_line_of(ln)
        if sim is None:
            ex.note("eps", f"power line {ln.get('name')}", "unsupported",
                    "no simulator PCDU line feeds these units (eps_basic POWER_LINE_DEFS has 9 fixed lines)",
                    "subsystems/eps.yaml", "power_lines")
            continue
        fwd[ln["id"]] = sim
        rev.setdefault(sim, ln)
    return {"fwd": fwd, "rev": rev}


# ── mission.yaml ──────────────────────────────────────────────────────────

def _mission(ex: SimConfigExport, d: Design, rows: list[dict]) -> None:
    from .. import cdr_model as cm
    rel = "mission.yaml"
    req = d.req
    name = req.get("name") if req.get("name") not in (None, "", "New Mission") else ex.study_name
    if name:
        ex.design("mission", rel, ("name",), str(name), "study / MissionRequirements.name", "mission name")
    else:
        ex.default("mission", rel, ("name",), "the study has no mission name", "mission name", "missing")
    mt = str(req.get("mission_type") or "").replace("_", " ")
    ex.design("mission", rel, ("description",),
              f"{mt or 'mission'} — simulator configuration exported from the SpaceCDF study {ex.study_name or ex.study_id}",
              "MissionRequirements.mission_type", "mission description", item=False)
    orb = req.get("orbit") or {}
    ex.design("mission", rel, ("orbit", "type"), str(orb.get("orbit_type") or "").upper() or "LEO",
              "OrbitRequirements.orbit_type", "orbit type (summary)", item=False)
    ex.design("mission", rel, ("orbit", "altitude_km"), _r(orb.get("altitude_km") or 0, 1), "OrbitRequirements.altitude_km", item=False)
    ex.design("mission", rel, ("orbit", "inclination_deg"), _r(orb.get("inclination_deg") or 0, 2), "OrbitRequirements.inclination_deg", item=False)
    pl = d.unit("payload")
    if pl or req.get("payloads"):
        p0 = (req.get("payloads") or [{}])[0]
        ex.design("mission", rel, ("payload", "type"), d.name(pl) or str(p0.get("type") or ""),
                  "payload element" if pl else "PayloadRequirements.type", "payload (summary)", item=False)
    s = cm.singleton(rows, "settings")
    for key, ck, lab in (("spacecraft_apid", "application_apid", "application APID"),
                         ("bootloader_apid", "bootloader_apid", "bootloader APID"),
                         ("pus_version", "pus_version", "PUS version")):
        if s.get(ck) is not None:
            ex.design("tmtc", rel, (key,), int(s[ck]), f"CDR TM/TC settings.{ck}", lab)
        else:
            ex.default("tmtc", rel, (key,), "no CDR TM/TC settings in the study", lab, "missing")
    if "J2000" in str(s.get("time_code") or ""):
        ex.design("tmtc", rel, ("time_epoch",), "2000-01-01T12:00:00", "CDR settings.time_code (CUC, epoch J2000)", "CUC epoch")
    else:
        ex.default("tmtc", rel, ("time_epoch",), "CUC epoch J2000 (no CDR time-code decision)", "CUC epoch")
    ex.default("obdh", rel, ("start_in_bootloader",), "boot concept: power-up in the bootloader (no design decision yet)", "boot into bootloader")
    _hk_apids(ex, d, rows)
    for k in ("network", "time_source", "ui", "ui_lang", "dump_dir", "sim_state_url"):
        ex.sim_detail(rel, (k,))


def _hk_apids(ex: SimConfigExport, d: Design, rows: list[dict]) -> None:
    from .. import cdr_model as cm
    rel = "mission.yaml"
    s = cm.singleton(rows, "settings")
    base = {s.get("application_apid"), s.get("bootloader_apid")}
    hk = cm.live_data(rows, "hk")
    sub_apid = {a.get("subsystem"): a.get("apid") for a in cm.live_data(rows, "apids") if a.get("role") == "subsystem"}
    out: dict[int, int] = {}
    for h in hk:
        apid = h.get("apid")
        sid = h.get("sid") if ex.dataset == "reference" else SIM_SID_OF_SUBSYSTEM.get(h.get("subsystem") or "")
        if sid is None or h.get("beacon"):
            continue
        if apid is not None and apid not in base:
            out[int(sid)] = int(apid)
    if out:
        ex.design("tmtc", rel, ("hk_apids",), dict(sorted(out.items())), "CDR housekeeping.apid (per-subsystem APID plan)",
                  "per-subsystem HK APIDs")
    elif sub_apid:
        ex.note("tmtc", "per-subsystem HK APIDs", "default",
                f"{len(sub_apid)} subsystem APIDs are defined in the CDR APID plan but no housekeeping structure is "
                "assigned to one; every packet stays on the application APID", rel, "hk_apids")
    else:
        ex.note("tmtc", "per-subsystem HK APIDs", "default", "single application APID (no subsystem APID plan)", rel, "hk_apids")


# ── orbit.yaml ────────────────────────────────────────────────────────────

def _orbit(ex: SimConfigExport, d: Design) -> None:
    rel = "orbit.yaml"
    orb = (d.req.get("orbit") or {})
    alt = _num(orb.get("altitude_km")) or _num((d.f.get("orbit") or {}).get("altitude_km"))
    inc = _num(orb.get("inclination_deg")) or _num((d.f.get("orbit") or {}).get("inclination_deg"))
    ecc = _num(orb.get("eccentricity")) or 0.0
    launch = d.req.get("launch_date_target")
    epoch_src = None
    epoch = datetime.fromisoformat(STD_EPOCH.replace("Z", "+00:00"))
    if launch:
        try:
            dt = datetime.fromisoformat(str(launch).replace("Z", "+00:00"))
            epoch = (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).replace(hour=12, minute=0, second=0, microsecond=0)
            epoch_src = "MissionRequirements.launch_date_target (12:00 UTC)"
        except ValueError:
            epoch_src = None
    t0 = epoch.strftime("%Y-%m-%dT%H:%M:%SZ")
    if epoch_src:
        ex.design("mission", rel, ("t0_epoch",), t0, epoch_src, "reference epoch (T-0)")
    else:
        ex.default("mission", rel, ("t0_epoch",), "no launch date in the study: EOSAT-1 reference epoch", "reference epoch (T-0)", value=t0)
    if alt is None or inc is None:
        ex.default("mission", rel, ("tle_line1",), "no orbit in the study", "reference orbit (TLE)", "missing")
        return
    raan_src = None
    if _num(orb.get("raan_deg")) is not None:
        raan, raan_src = float(orb["raan_deg"]) % 360.0, "OrbitRequirements.raan_deg"
    elif orb.get("ltan"):
        raan, raan_src = raan_from_ltan(str(orb["ltan"]), epoch), f"OrbitRequirements.ltan {orb['ltan']} -> RAAN at T-0"
    else:
        raan = raan_from_ltan("10:00", epoch)
    l1, l2 = tle(alt, inc, ecc, raan, 90.0, 270.0, epoch)
    ex.design("mission", rel, ("tle_line1",), l1, "OrbitRequirements (altitude, inclination, eccentricity) at T-0", "reference orbit (TLE)")
    ex.design("mission", rel, ("tle_line2",), l2, "OrbitRequirements (altitude, inclination, eccentricity, RAAN) at T-0", item=False)
    if raan_src:
        ex.note("mission", "RAAN / LTAN", "design", raan_src, rel, "tle_line2")
    else:
        ex.note("mission", "RAAN / LTAN", "default", "no LTAN or RAAN in the study: LTAN 10:00 (EOSAT-1)", rel, "tle_line2")
    ex.note("mission", "argument of perigee / mean anomaly at T-0", "default",
            "90° / 270° (EOSAT-1 injection phase)", rel, "tle_line2")
    ex.design("mission", rel, ("altitude_km",), _r(alt, 1), "OrbitRequirements.altitude_km", item=False)
    ex.design("mission", rel, ("inclination_deg",), _r(inc, 2), "OrbitRequirements.inclination_deg", item=False)
    gs = d.f.get("ground_stations") or []
    if gs:
        out = [{"name": str(g.get("name") or g.get("id")), "lat_deg": _r(g.get("lat") or 0.0, 3),
                "lon_deg": _r(g.get("lon") or 0.0, 3), "alt_km": _r((_num(g.get("alt_m")) or 0.0) / 1000.0, 3),
                "min_elevation_deg": _r(_num(g.get("min_elevation_deg")) or 5.0, 1)} for g in gs]
        ex.design("mission", rel, ("ground_stations",), out, "selected ground stations (KB ground_stations)", "ground stations")
    else:
        ex.default("mission", rel, ("ground_stations",), "no ground station selected: the EOSAT-1 network",
                   "ground stations", "missing")
    ex.sim_detail(rel, ("earth_radius_km",), "propagator constant")


# ── EPS ───────────────────────────────────────────────────────────────────

def _eps(ex: SimConfigExport, d: Design, rows: list[dict], ctx: dict) -> None:
    from .. import cdr_model as cm
    rel, sim = "subsystems/eps.yaml", "simulation.yaml"
    bat = d.unit("battery")
    if bat:
        p = d.kbp(bat)
        cap = _num(p.get("capacity_wh"))
        if cap:
            ex.design("eps", rel, ("battery", "capacity_wh"), _r(cap * d.qty(bat), 2), f"battery {d.name(bat)} (KB capacity_wh)", "battery capacity")
        v = p.get("voltage_v")
        if isinstance(v, dict) and _num(v.get("min")) and _num(v.get("max")):
            lo, hi = float(v["min"]), float(v["max"])
            nom = _num(v.get("nominal")) or (lo + hi) / 2
            ex.design("eps", rel, ("battery", "soc_0_v"), lo, f"battery {d.name(bat)} (KB voltage_v.min)", "battery voltage curve")
            ex.design("eps", rel, ("battery", "soc_100_v"), hi, f"battery {d.name(bat)} (KB voltage_v.max)", item=False)
            ex.design("eps", rel, ("battery", "voltage_nom"), nom, f"battery {d.name(bat)} (KB voltage_v.nominal)", item=False)
        else:
            ex.default("eps", rel, ("battery", "voltage_nom"), "the battery has no voltage range in the KB: EOSAT-1 8S curve",
                       "battery voltage curve", "missing")
        for k in ("internal_r_ohm", "charge_efficiency", "discharge_efficiency", "cv_taper_start_soc_pct"):
            ex.default("eps", rel, ("battery", k), "battery model parameter not in the KB (EOSAT-1 BPX value)", f"battery {k}",
                       item=k == "internal_r_ohm")
    else:
        ex.default("eps", rel, ("battery", "capacity_wh"), "no battery in the design: EOSAT-1 100 Wh", "battery", "missing")
    _solar(ex, d)
    life = _num(d.req.get("design_lifetime_years"))
    if life:
        ex.design("eps", rel, ("array_losses", "design_life_years"), life, "MissionRequirements.design_lifetime_years", "design life (EOL sizing case)")
    for k in ("inherent_degradation", "temp_coeff_per_c", "temp_ref_c", "array_temp_sunlit_c", "harness_efficiency", "annual_degradation"):
        ex.default("eps", rel, ("array_losses", k), "array loss stack not in the design (EOSAT-1 TJ GaAs values)", "array loss stack",
                   item=k == "inherent_degradation")
    # unit powers
    obc, epsb = d.unit("obc"), d.units("eps")
    p_obc = (d.power(obc) or 0.0) + sum(d.power(e) or 0.0 for e in epsb)
    if obc and p_obc > 0:
        ex.design("eps", rel, ("obc_power_w",), _r(p_obc, 2), "OBC + EPS boards (element power, always-on platform line)", "OBC line power")
    else:
        ex.default("eps", rel, ("obc_power_w",), "no OBC power in the design", "OBC line power", "missing")
    pl = d.unit("payload")
    if pl:
        img = d.mode_power(pl, "imaging") or d.power(pl, peak=True)
        stby = d.mode_power(pl, "nominal") or _num((d.kbp(pl).get("power_modes_w") or {}).get("standby")) or d.power(pl)
        if img:
            ex.design("payload", rel, ("payload_power_w",), _r(img, 2), f"{d.name(pl)}: power in the imaging mode", "payload imaging power")
        if stby is not None:
            if img and stby >= img:
                stby = 0.45 * img
                ex.default("payload", rel, ("payload_standby_power_w",), "no standby power below the imaging power: 45 % of it (EOSAT-1 ratio)",
                           "payload standby power", value=_r(stby, 2))
            else:
                ex.design("payload", rel, ("payload_standby_power_w",), _r(stby, 2), f"{d.name(pl)}: power in the nominal mode", "payload standby power")
    else:
        ex.default("payload", rel, ("payload_power_w",), "no payload in the design: EOSAT-1 imager power", "payload power", "missing")
    tx = d.unit("transmitter")
    if tx:
        p_tx = d.power(tx)
        p_hi = d.mode_power(tx, "downlink") or d.power(tx, peak=True)
        if p_tx:
            low = d.mode_power(tx, "nominal") or p_tx
            ex.design("ttc", rel, ("transponder_power_w",), _r(low, 2), f"{d.name(tx)} (nominal mode / element power)", "transmitter power (LOW tier)")
        if p_hi:
            ex.design("ttc", rel, ("transponder_hi_power_w",), _r(max(p_hi, p_tx or 0), 2), f"{d.name(tx)} (downlink mode / peak power)", "transmitter power (HIGH tier)")
        rx = _num((d.kbp(tx).get("power_modes_w") or {}).get("rx")) or _num(d.kbp(tx).get("rx_power_w"))
        if rx:
            ex.design("ttc", rel, ("transponder_rx_power_w",), rx, f"{d.name(tx)} (KB receive power)", "receiver power")
        else:
            ex.default("ttc", rel, ("transponder_rx_power_w",), "receiver power not in the KB (EOSAT-1 1.5 W)", "receiver power")
    else:
        ex.default("ttc", rel, ("transponder_power_w",), "no transmitter in the design", "transmitter power", "missing")
    ex.default("payload", rel, ("fpa_cooler_power_w",), "no FPA cooler element (EOSAT-1 15 W Stirling)", "FPA cooler power")
    # line powers (simulation.yaml)
    for line, cls, lab in (("htr_bat", ("heater",), "battery heater line"), ("aocs_wheels", ("wheel",), "AOCS wheel line"),
                           ("prop", ("propulsion",), "propulsion line")):
        u = None
        if line == "htr_bat":
            u = next((h for h in d.units("heater") if "obc" not in d.name(h).lower()), None)
            hrow = next((h for h in d.f.get("heaters") or [] if d.cls.get(h.get("element_id")) == "battery"), None)
            if hrow and _num(hrow.get("power_w")):
                ex.design("tcs", sim, ("eps", "line_power_w", line), _r(hrow["power_w"], 2), f"heater {hrow.get('name')} (thermal design)", lab)
                continue
        else:
            us = d.units(*cls)
            if us:
                pw = sum(d.power(e) or 0.0 for e in us)
                if pw > 0:
                    ex.design("eps", sim, ("eps", "line_power_w", line), _r(pw, 2), " + ".join(d.name(e) for e in us), lab)
                    continue
        if u and d.power(u):
            ex.design("tcs", sim, ("eps", "line_power_w", line), _r(d.power(u) or 0, 2), f"heater {d.name(u)}", lab)
        else:
            ex.default("eps", sim, ("eps", "line_power_w", line), f"no design unit for the {line} line (EOSAT-1 value)", lab)
    # power lines at power-on, LCL trips
    lm = ctx["line_map"]
    states = {}
    trips = {}
    for sim_line, ln in lm["rev"].items():
        on = bool(ln.get("default_on_boot"))
        sw = SIM_LINES[sim_line][0]
        if not sw and not on:
            ex.note("eps", f"line {ln.get('name')} at power-on", "unsupported",
                    f"design line is off at boot but the simulator's {sim_line} line is non-switchable (always on)",
                    rel, f"power_lines.{sim_line}")
            on = True
        states[sim_line] = on
        if _num(ln.get("lcl_limit_a")):
            trips[sim_line] = _r(ln["lcl_limit_a"], 3)
    for sim_line in SIM_LINES:
        if sim_line in states:
            ex.design("eps", rel, ("power_lines", sim_line), states[sim_line],
                      f"power line {lm['rev'][sim_line].get('name')} (default_on_boot)", f"line {sim_line} at power-on")
        else:
            ex.default("eps", rel, ("power_lines", sim_line), "no design line feeds this simulator line (EOSAT-1 state)",
                       f"line {sim_line} at power-on")
        if sim_line in trips:
            ex.design("eps", sim, ("eps", "overcurrent", "thresholds_a", sim_line), trips[sim_line],
                      f"power line {lm['rev'][sim_line].get('name')} (LCL trip)", f"LCL trip {sim_line}")
        else:
            ex.default("eps", sim, ("eps", "overcurrent", "thresholds_a", sim_line), "no design LCL for this line (EOSAT-1 value)",
                       f"LCL trip {sim_line}")
    # protection ladder and load shed (CDR)
    shed = cm.singleton(rows, "load_shed")
    bp = shed.get("bus_protection") or {}
    for k in ("uv_v", "eps_safe_v", "aocs_safe_v", "cascade_v", "ov_v"):
        v = _num((bp.get(k) or {}).get("value")) if isinstance(bp.get(k), dict) else _num(bp.get(k))
        if v is not None:
            ex.design("fdir", sim, ("eps", "bus_protection", k), v, f"CDR load-shed table, bus protection {k}", f"bus protection {k}")
        elif k == "cascade_v" and _num((bp.get("aocs_safe_v") or {}).get("value")) is not None:
            v = round(float(bp["aocs_safe_v"]["value"]) - 0.2, 2)
            ex.default("fdir", sim, ("eps", "bus_protection", k), "no cascade level in the design: AOCS-safe level - 0.2 V (EOSAT-1 spacing)",
                       f"bus protection {k}", value=v)
        else:
            ex.default("fdir", sim, ("eps", "bus_protection", k), "no CDR load-shed table: EOSAT-1 level", f"bus protection {k}",
                       "missing" if not shed else "default")
    if shed:
        order = []
        for ln_id, nm in zip(_stage_ids(shed), _stage_names(shed)):
            s = lm["fwd"].get(ln_id) or _sim_line_by_name(nm, d, lm)
            if s and SIM_LINES[s][0] and s not in order:
                order.append(s)
            elif not s:
                ex.note("fdir", f"load-shed line {nm}", "unsupported", "no simulator line for this design line",
                        sim, "eps.load_shed.order")
        if ex.dataset == "reference" and shed.get("order"):
            order = [o for o in shed["order"] if o in SIM_LINES]
        if order:
            ex.design("fdir", sim, ("eps", "load_shed", "order"), order, "CDR load-shed table (stages, mapped to simulator lines)", "load-shed order")
        else:
            ex.default("fdir", sim, ("eps", "load_shed", "order"), "load-shed lines do not map to switchable simulator lines", "load-shed order")
        socs = shed.get("soc_stage_thresholds_pct") or [s.get("soc_pct") for s in shed.get("stages") or [] if _num(s.get("soc_pct")) is not None]
        socs = [float(x) for x in socs if _num(x) is not None]
        if len(socs) >= 3:
            ex.design("fdir", sim, ("eps", "load_shed", "soc_stage_thresholds_pct"), sorted(socs[:3], reverse=True), "CDR load-shed stages (SoC)", "load-shed SoC stages")
        elif socs:
            full = sorted(socs, reverse=True)
            tmpl = [float(x) for x in (((ex.load(sim).get("eps") or {}).get("load_shed") or {}).get("soc_stage_thresholds_pct")
                                       or [30.0, 20.0, 10.0])]
            while len(full) < 3:
                nxt = tmpl[len(full)] if len(full) < len(tmpl) else full[-1] / 2.0
                full.append(nxt if nxt < full[-1] else full[-1] / 2.0)
            ex.default("fdir", sim, ("eps", "load_shed", "soc_stage_thresholds_pct"),
                       f"the design has {len(socs)} SoC stage(s); the simulator needs 3: completed from the EOSAT-1 ladder",
                       "load-shed SoC stages", value=full)
        for k in ("restore_hysteresis_v", "auto_restore"):
            if shed.get(k) is not None:
                ex.design("fdir", sim, ("eps", "load_shed", k), shed[k], f"CDR load-shed table {k}", f"load shed {k}")
    else:
        ex.default("fdir", sim, ("eps", "load_shed", "order"), "no CDR load-shed table", "load-shed order", "missing")
    # battery temperature events from the battery's operating range
    if bat:
        rng = d.kbp(bat).get("operating_temp_c")
        if isinstance(rng, (list, tuple)) and len(rng) == 2:
            ex.design("eps", sim, ("eps", "event_thresholds", "bat_overtemp_c"), float(rng[1]) - 5.0,
                      f"{d.name(bat)} operating range max - 5 K", "battery over-temperature event")
            ex.design("eps", sim, ("eps", "event_thresholds", "bat_undertemp_c"), float(rng[0]) + 5.0,
                      f"{d.name(bat)} operating range min + 5 K", "battery under-temperature event")
    for k in ("soc_low_pct", "soc_critical_pct", "soc_charge_complete_pct", "sa_degraded_fraction"):
        ex.default("fdir", sim, ("eps", "event_thresholds", k), "EPS event level (no design monitoring table entry)",
                   f"EPS event {k}", item=k == "soc_low_pct")


def _stage_ids(shed: dict) -> list[str]:
    out = []
    for s in shed.get("stages") or []:
        out.extend(s.get("line_ids") or [None] * len(s.get("lines") or []))
    return out


def _stage_names(shed: dict) -> list[str]:
    out = []
    for s in shed.get("stages") or []:
        out.extend(s.get("lines") or [])
    return out


def _sim_line_by_name(name: str, d: Design, lm: dict) -> str | None:
    if name in SIM_LINES:
        return name
    for ln in d.lines():
        if ln.get("name") == name:
            return lm["fwd"].get(ln["id"])
    return None


def _solar(ex: SimConfigExport, d: Design) -> None:
    rel = "subsystems/eps.yaml"
    geo = d.f.get("geometry")
    sa = d.units("solar_array")
    cell = next((d.kbp(e) for e in sa if d.kbp(e).get("cell_efficiency_percent") or d.kbp(e).get("efficiency")), None)
    if cell:
        eff = _num(cell.get("cell_efficiency_percent"))
        eff = eff / 100.0 if eff else _num(cell.get("efficiency"))
        if eff:
            ex.design("eps", rel, ("cell_efficiency",), _r(eff, 4), "solar array KB cell efficiency", "cell efficiency")
        if cell.get("cell_type"):
            ex.design("eps", rel, ("technology",), str(cell["cell_type"]), "solar array KB cell type", item=False)
    else:
        ex.default("eps", rel, ("cell_efficiency",), "no solar cell data in the design (TJ GaAs 29.5 %)", "cell efficiency",
                   "missing" if not sa else "default")
    faces = ("px", "mx", "py", "my", "pz", "mz")
    if geo and (geo.get("body_panels") or geo.get("wings")):
        for bp in geo.get("body_panels") or []:
            if bp.get("face") in faces:
                ex.design("eps", rel, ("solar_panels", f"{bp['face']}_area_m2"), _r(bp.get("cell_area_m2") or 0.0, 4),
                          "stack builder layout (body-mounted cells per face)", "body-mounted cell areas", item=bp["face"] == "px")
        wings = {w.get("face"): 0.0 for w in geo.get("wings") or []}
        for w in geo.get("wings") or []:
            wings[w.get("face")] = wings.get(w.get("face"), 0.0) + float(w.get("cell_area_m2") or 0.0)
        for f in ("py", "my"):
            ex.design("eps", rel, ("solar_panels", f"wing_{f}_area_m2"), _r(wings.get(f, 0.0), 4),
                      "stack builder layout (deployable wings)", "wing cell areas", item=f == "py")
        other = [f for f in wings if f not in ("py", "my")]
        if other:
            ex.note("eps", "wings off ±Y", "unsupported", f"wings on {other}: the simulator's wings and SADA are on ±Y", rel, "solar_panels")
    elif sa:
        body = {f: 0.0 for f in faces}
        wing = 0.0
        body_src = False
        for e in sa:
            p = d.kbp(e)
            fa = p.get("face_areas_m2")
            area = (_num(p.get("area_m2")) or 0.0) * d.qty(e)
            dep = str(p.get("deployment") or "").lower()
            if isinstance(fa, dict):
                for f, a in fa.items():
                    if f in body and _num(a) is not None:
                        body[f] += float(a)
                body_src = True
            elif "deploy" in dep or "wing" in d.name(e).lower():
                wing += area
            else:
                for f in ("px", "mx", "py", "my"):
                    body[f] += area / 4.0
                body_src = True
        for f in faces:
            ex.design("eps", rel, ("solar_panels", f"{f}_area_m2"), _r(body[f], 4),
                      "solar array elements (performance.face_areas_m2 / area spread over the four long faces)"
                      if body_src else "solar array elements: no body-mounted cells", "body-mounted cell areas", item=f == "px")
        for f in ("py", "my"):
            ex.design("eps", rel, ("solar_panels", f"wing_{f}_area_m2"), _r(wing / 2.0, 4),
                      "deployable solar array elements (area split over the ±Y wings)", "wing cell areas", item=f == "py")
    else:
        ex.default("eps", rel, ("solar_panels",), "no solar array in the design: EOSAT-1 body cells and wings", "solar array layout", "missing")
    sada = d.units("sada")
    if sada:
        ex.design("eps", rel, ("solar_panels", "sada_present"), True, f"{d.name(sada[0])}", "solar array drive (SADA)")
        ex.default("eps", rel, ("solar_panels", "sada_max_rate_deg_s"), "SADA rate not in the design (EOSAT-1 1 °/s)", item=False)
    elif sa or geo:
        ex.design("eps", rel, ("solar_panels", "sada_present"), False, "no solar array drive in the design", "solar array drive (SADA)")
    ex.default("eps", rel, ("solar_panels", "wing_deploy_time_s"), "hinge release time not in the design (EOSAT-1 30 s)", "wing deployment time")


# ── AOCS ──────────────────────────────────────────────────────────────────

def _aocs(ex: SimConfigExport, d: Design, rows: list[dict]) -> None:
    from .. import cdr_model as cm
    rel = "subsystems/aocs.yaml"
    mp = d.f.get("mass_properties")
    if mp and _num(mp.get("total_mass_kg")):
        i = mp["inertia"]
        # SpaceCDF mass_properties: x forward, y starboard, z nadir; simulator body frame: +Z zenith,
        # +Y orbit normal. A 180° rotation about X maps one onto the other: Ixy, Ixz change sign.
        tensor = [[_r(i["ixx"], 5), _r(-i["ixy"], 5), _r(-i["ixz"], 5)],
                  [_r(-i["ixy"], 5), _r(i["iyy"], 5), _r(i["iyz"], 5)],
                  [_r(-i["ixz"], 5), _r(i["iyz"], 5), _r(i["izz"], 5)]]
        ex.design("aocs", rel, ("mass_properties", "mass_kg"), _r(mp["total_mass_kg"], 3), "physics closure: mass properties", "spacecraft mass")
        ex.design("aocs", rel, ("mass_properties", "inertia_kgm2"), tensor,
                  "physics closure: inertia tensor (design z-nadir frame rotated 180° about X into the sim body frame)", "inertia tensor")
        if _num(mp.get("cp_cg_offset_m")):
            ex.design("aocs", rel, ("disturbances", "cp_cg_offset_m"), _r(mp["cp_cg_offset_m"], 4), "physics closure: CP-CG offset", "CP-CG offset")
    else:
        ex.default("aocs", rel, ("mass_properties", "inertia_kgm2"), "no mass properties (run the physics closure)", "inertia tensor", "missing")
    rw = d.units("wheel")
    if rw:
        p = d.kbp(rw[0])
        n = sum(d.qty(e) for e in rw)
        if n != 4:
            ex.note("aocs", "reaction wheel count", "unsupported",
                    f"the design has {n} wheel(s); the simulator models a 4-wheel pyramid (each with the design's wheel)",
                    rel, "reaction_wheels.count")
        sp = _num(p.get("max_speed_rpm"))
        if sp:
            ex.design("aocs", rel, ("reaction_wheels", "max_speed_rpm"), int(sp), f"{d.name(rw[0])} (KB max_speed_rpm)", "wheel max speed")
        tq = _num(p.get("max_torque_nm"))
        if tq:
            ex.design("aocs", rel, ("reaction_wheels", "max_torque_nm"), tq, f"{d.name(rw[0])} (KB max_torque_nm)", "wheel max torque")
        h = _num(p.get("momentum_nms"))
        if h and sp:
            ex.design("aocs", rel, ("reaction_wheels", "rotor_inertia_kgm2"), float(f"{h / (sp * 2 * math.pi / 60):.4g}"),
                      f"{d.name(rw[0])}: momentum / max speed", "wheel rotor inertia")
        for k in ("motor_tau_s", "coulomb_friction_nm", "viscous_friction_nm_per_rads"):
            ex.default("aocs", rel, ("reaction_wheels", k), "wheel friction / motor model not in the KB (EOSAT-1 RW-0.03 values)",
                       "wheel friction model", item=k == "motor_tau_s")
    else:
        ex.default("aocs", rel, ("reaction_wheels", "max_speed_rpm"), "no reaction wheel in the design: EOSAT-1 wheels", "reaction wheels", "missing")
    mtq = d.unit("magnetorquer")
    if mtq:
        p = d.kbp(mtq)
        if _num(p.get("dipole_moment_am2")):
            ex.design("aocs", rel, ("magnetorquers", "max_dipole_am2"), float(p["dipole_moment_am2"]), f"{d.name(mtq)} (KB dipole)", "magnetorquer dipole")
        if _num(p.get("residual_dipole_am2")):
            r = float(p["residual_dipole_am2"]) / math.sqrt(3)
            ex.design("aocs", rel, ("disturbances", "residual_dipole_am2"), [_r(r, 5)] * 3,
                      f"{d.name(mtq)} KB residual dipole (magnitude split equally over the axes)", "residual dipole")
    else:
        ex.default("aocs", rel, ("magnetorquers", "max_dipole_am2"), "no magnetorquer in the design", "magnetorquers", "missing")
    st = d.unit("star_tracker")
    if st and _num(d.kbp(st).get("accuracy_arcsec")):
        a = float(d.kbp(st)["accuracy_arcsec"])
        ex.design("aocs", rel, ("sensors", "star_tracker", "nea_cross_arcsec"), a, f"{d.name(st)} (KB accuracy)", "star tracker noise")
        ex.default("aocs", rel, ("sensors", "star_tracker", "nea_roll_arcsec"), "roll NEA = 6.7 × cross-boresight (EOSAT-1 ratio)",
                   item=False, value=_r(a * 40.0 / 6.0, 1))
    else:
        ex.default("aocs", rel, ("sensors", "star_tracker"), "no star tracker accuracy in the design", "star tracker", "missing" if not st else "default")
    ex.default("aocs", rel, ("sensors", "gyro"), "no gyro / IMU KB category (EOSAT-1 MEMS gyro model)", "gyro model")
    geo = d.f.get("geometry")
    if geo and (geo.get("bus") or {}).get("size_m"):
        sx, sy, sz = (float(x) for x in geo["bus"]["size_m"])
        ex.design("aocs", rel, ("disturbances", "drag_area_m2"), _r(sy * sz, 4), "bus envelope: +X (ram) face area", "drag area")
        wing = sum(float(w.get("cell_area_m2") or 0) for w in geo.get("wings") or []) / 0.85
        ex.design("aocs", rel, ("disturbances", "srp_area_m2"), _r(sx * sy + wing, 4), "bus envelope + wings (sunward area)", "SRP area")
    ctl = cm.singleton(rows, "aocs_control")
    if ctl:
        for key, path, lab in (("bdot_gain_am2_per_tps", ("magnetorquers", "bdot_gain_am2_per_tps"), "B-dot gain"),
                               ("attitude_error_deadband_deg", ("attitude_error_deadband_deg",), "pointing deadband"),
                               ("wheel_bias_rpm", ("reaction_wheels", "nominal_speed_rpm"), "wheel bias speed")):
            if _num(ctl.get(key)) is not None:
                v = int(ctl[key]) if key == "wheel_bias_rpm" else float(ctl[key])
                ex.design("aocs", rel, path, v, f"CDR AOCS control.{key}", lab)
        des = ctl.get("desaturation") or {}
        for k in ("gain_per_s", "deadband_nms", "timeout_s"):
            if _num(des.get(k)) is not None:
                ex.design("aocs", rel, ("magnetorquers", "desaturation", k), float(des[k]), f"CDR AOCS control.desaturation.{k}",
                          "desaturation law", item=k == "gain_per_s")
        if _num(ctl.get("detumble_exit_rate_dps")) is not None:
            ex.design("aocs", rel, ("control", "transitions", "detumble_exit_rate_dps"), float(ctl["detumble_exit_rate_dps"]),
                      "CDR AOCS control.detumble_exit_rate_dps", "DETUMBLE exit rate")
    else:
        ex.default("aocs", rel, ("magnetorquers", "bdot_gain_am2_per_tps"), "no CDR AOCS control parameters", "AOCS control parameters", "missing")
    modes = {m.get("name"): m for m in cm.live_data(rows, "aocs_modes")}
    if modes:
        for name, m in modes.items():
            if name not in SIM_AOCS_MODES:
                ex.note("aocs", f"AOCS mode {name}", "unsupported", "the simulator's AOCS mode set is fixed (aocs_mode_codes.yaml)",
                        rel, "control.modes")
                continue
            g = m.get("gains") or {}
            for src, key in (("omega_n", "omega_n_rad_s"), ("zeta", "zeta")):
                if _num(g.get(src)) is not None:
                    ex.design("aocs", rel, ("control", "modes", name, key), float(g[src]), f"CDR AOCS mode {name} gains", item=False)
            for src, key in (("min_dwell_s", "min_dwell_s"), ("power_w", "power_w"), ("pointing_sigma_deg", "pointing_sigma_deg")):
                if _num(m.get(src)) is not None:
                    ex.design("aocs", rel, ("control", "modes", name, key), float(m[src]), f"CDR AOCS mode {name}.{src}", item=False)
            ex.note("aocs", f"AOCS mode {name} (gains, dwell, power, pointing)", "design", "CDR AOCS modes", rel, f"control.modes.{name}")
        for name in SIM_AOCS_MODES:
            if name not in modes:
                ex.note("aocs", f"AOCS mode {name}", "default", "not in the design's mode set: simulator default values",
                        rel, f"control.modes.{name}")
                ex.comments[rel][("control", "modes", name)] = "C2O default: not in the design's AOCS mode set (EOSAT-1 values)"
    else:
        ex.default("aocs", rel, ("control", "modes"), "no CDR AOCS mode table: EOSAT-1 gains, dwells and powers", "AOCS mode table", "missing")
    tr = cm.live_data(rows, "aocs_transitions")
    if tr:
        ex.note("aocs", "AOCS transition table", "design" if ex.dataset != "reference" else "default",
                f"{len(tr)} CDR transitions; the simulator's transition logic is fixed, its guards are control.transitions",
                rel, "control.transitions")
    for k in ("safe_boot_init_s", "detumble_exit_hold_s", "coarse_sun_error_deg", "coarse_sun_hold_s",
              "eclipse_entry_debounce_s", "desat_exit_hold_s"):
        ex.default("aocs", rel, ("control", "transitions", k), "transition guard not in the design (EOSAT-1 value)",
                   "transition guards", item=k == "coarse_sun_error_deg")
    for k in ("integration",):
        ex.sim_detail(rel, (k,), "integrator setting (simulator implementation detail)")


# ── TCS ───────────────────────────────────────────────────────────────────

def _tcs(ex: SimConfigExport, d: Design) -> None:
    rel = "subsystems/tcs.yaml"
    data = ex.load(rel)
    heaters = data.get("heaters") or []
    done = set()
    for h in d.f.get("heaters") or []:
        cls = d.cls.get(h.get("element_id")) or ""
        sim_h = SIM_HEATER_OF_CLASS.get(cls)
        if not sim_h:
            ex.note("tcs", f"heater {h.get('name')}", "unsupported",
                    f"heats a {cls or 'unit'}: the simulator has battery, OBC and thruster heater circuits only", rel, "heaters")
            continue
        idx = next((i for i, x in enumerate(heaters) if x.get("name") == sim_h), None)
        if idx is None:
            continue
        for key, k2 in (("power_w", "power_w"), ("on_c", "on_temp_c"), ("off_c", "off_temp_c")):
            if _num(h.get(key)) is not None:
                ex.design("tcs", rel, ("heaters", idx, k2), float(h[key]), f"heater {h.get('name')} (thermal design)", item=False)
        ex.note("tcs", f"{sim_h} heater (power, set-points)", "design", f"heater {h.get('name')}", rel, f"heaters.{idx}")
        done.add(sim_h)
    if "battery" not in done:
        u = next((x for x in d.units("heater") if "obc" not in d.name(x).lower()), None)
        idx = next((i for i, x in enumerate(heaters) if x.get("name") == "battery"), None)
        if u and d.power(u) and idx is not None:
            ex.design("tcs", rel, ("heaters", idx, "power_w"), _r(d.power(u) or 0, 2), f"heater element {d.name(u)} (power)", "battery heater power")
            ex.note("tcs", "battery heater set-points", "default", "no thermostat set-points in the design (EOSAT-1 5 / 10 °C)", rel, f"heaters.{idx}")
        else:
            ex.note("tcs", "battery heater", "default" if d.units("battery") else "missing",
                    "no battery heater in the design (EOSAT-1 8 W, 5 / 10 °C)", rel, "heaters")
    for name in ("obc", "thruster"):
        if name not in done:
            ex.note("tcs", f"{name} heater", "default", f"no {name} heater in the design (EOSAT-1 circuit)", rel, "heaters")
    # temperature event limits from the units' operating ranges
    for unit_cls, key in (("battery", "battery"), ("obc", "obc")):
        u = d.unit(unit_cls)
        rng = None
        if u:
            for src in (d.perf(u), d.kbp(u)):
                r = src.get("operating_temp_c")
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    rng = [float(r[0]), float(r[1])]
                    break
        if rng:
            ex.design("tcs", rel, ("event_thresholds", "temperature_warning", key), rng, f"{d.name(u)} operating range", f"{key} temperature warning")
            ex.design("tcs", rel, ("event_thresholds", "temperature_alarm", key), [rng[0] - 10.0, rng[1] + 10.0],
                      f"{d.name(u)} operating range ± 10 K (C2O alarm margin)", f"{key} temperature alarm")
        else:
            ex.default("tcs", rel, ("event_thresholds", "temperature_warning", key), "no operating range in the design (EOSAT-1 limits)",
                       f"{key} temperature limits")
    # network node masses from the units
    nodes = (data.get("network") or {}).get("nodes") or []
    groups = {"structure": d.units("structure"), "obc": d.units("obc"), "payload": d.units("payload"),
              "ttc": d.units("transmitter", "receiver", "antenna"),
              "aocs": d.units("wheel", "star_tracker", "magnetorquer", "adcs_sensor", "gnss")}
    for i, n in enumerate(nodes):
        nm = n.get("name")
        if nm in groups and groups[nm] and "mass_kg" in n:
            m = d.mass(groups[nm])
            if m > 0:
                ex.design("tcs", rel, ("network", "nodes", i, "mass_kg"), _r(m, 3), " + ".join(d.name(e) for e in groups[nm]) + " (mass)",
                          f"thermal node {nm}", item=True)
        elif nm == "battery" and d.units("battery"):
            m = d.mass(d.units("battery"))
            if m > 0:
                ex.design("tcs", rel, ("network", "nodes", i, "capacitance_j_per_k"), _r(m * 1000.0, 1),
                          "battery mass × 1000 J/(kg K) (Li-ion cells + bracket)", "thermal node battery")
    ex.note("tcs", "thermal network couplings, surfaces and coatings", "default",
            "the 16-node EOSAT-1 network (no per-face coating map or internal radiative couplings in the design)", rel, "network")
    ex.comments[rel].setdefault(("network",), "C2O default: EOSAT-1 16-node network; node masses from the design where noted")
    ex.default("tcs", rel, ("fpa_envelope",), "no FPA cooler / detector thermal ICD in the design (EOSAT-1 envelope)", "FPA thermal envelope")


# ── TT&C ──────────────────────────────────────────────────────────────────

def _ttc(ex: SimConfigExport, d: Design, rows: list[dict], ctx: dict) -> None:
    from .. import cdr_model as cm
    rel = "subsystems/ttc.yaml"
    tx = d.unit("transmitter")
    p = d.kbp(tx)
    f = _num(p.get("frequency_mhz")) or _num(p.get("dl_frequency_mhz"))
    if f:
        ex.design("ttc", rel, ("dl_freq_mhz",), f, f"{d.name(tx)} (KB frequency_mhz)", "downlink frequency")
        if not (2200.0 <= f <= 2290.0):
            ex.note("ttc", "downlink band", "unsupported",
                    f"{f:.0f} MHz is outside the simulator's S-band downlink allocation (2200–2290 MHz)", rel, "dl_freq_mhz")
        ul = _num(p.get("ul_frequency_mhz"))
        if ul:
            ex.design("ttc", rel, ("ul_freq_mhz",), ul, f"{d.name(tx)} (KB ul_frequency_mhz)", "uplink frequency")
        else:
            ex.default("ttc", rel, ("ul_freq_mhz",), "no uplink frequency in the KB (EOSAT-1 2025 MHz)", "uplink frequency")
    else:
        ex.default("ttc", rel, ("dl_freq_mhz",), "no transmitter frequency in the design", "downlink frequency", "missing")
    pw = _num(p.get("tx_power_w"))
    if pw is None and _num(p.get("tx_power_dbm")) is not None:
        pw = 10 ** ((float(p["tx_power_dbm"]) - 30.0) / 10.0)
    ant = d.unit("antenna")
    gain = _num(d.kbp(ant).get("gain_dbi"))
    if gain is not None:
        ex.design("ttc", rel, ("sc_gain_dbi",), gain, f"{d.name(ant)} (KB gain)", "antenna gain")
    else:
        ex.default("ttc", rel, ("sc_gain_dbi",), "no antenna gain in the design (EOSAT-1 3 dBi)", "antenna gain")
    if pw:
        g = gain if gain is not None else float(ex.load(rel).get("sc_gain_dbi") or 0.0)
        ex.design("ttc", rel, ("eirp_dbw",), _r(10 * math.log10(pw) + g, 2), f"{d.name(tx)} RF power + antenna gain", "EIRP")
        ex.design("ttc", rel, ("pa_ref_power_w",), _r(pw, 3), f"{d.name(tx)} RF power", item=False)
        ex.design("ttc", rel, ("pa_nominal_power_w",), _r(pw, 3), f"{d.name(tx)} RF power", "PA levels")
        ex.default("ttc", rel, ("pa_low_power_w",), "half the nominal RF power (EOSAT-1 ladder)", item=False, value=_r(pw / 2, 3))
        ex.default("ttc", rel, ("pa_max_power_w",), "2.5 × the nominal RF power (EOSAT-1 ladder)", item=False, value=_r(pw * 2.5, 3))
    else:
        ex.default("ttc", rel, ("eirp_dbw",), "no transmitter RF power in the design", "EIRP", "missing")
    gt = [_num(g.get("g_over_t_db_k")) for g in d.f.get("ground_stations") or []]
    gt = [x for x in gt if x is not None]
    if gt:
        ex.design("ttc", rel, ("gs_g_t_db",), min(gt), "selected ground stations: lowest G/T", "ground station G/T")
    else:
        ex.default("ttc", rel, ("gs_g_t_db",), "no ground station G/T in the design (EOSAT-1 Iqaluit 20 dB/K)", "ground station G/T")
    tiers = cm.live_data(rows, "rate_tiers")
    if tiers:
        out = []
        for t in tiers:
            out.append({k: t.get(k) for k in ("name", "bps", "command_code", "modulation", "coding", "coding_gain_db",
                                               "bootloader_only", "requires_antenna", "requires_downlink_mode", "min_elevation_deg")
                        if t.get(k) is not None})
        # the command code of TTC_SET_DATA_RATE: LOW = 0, HIGH = 1 in the simulator; keep the design's or set it
        for i, t in enumerate(out):
            t.setdefault("command_code", {"LOW": 0, "HIGH": 1}.get(t["name"], 0xFF if t.get("bootloader_only") else i))
        ex.design("ttc", rel, ("tm_rate_tiers",), out, "CDR TT&C rate ladder", "TM rate ladder")
        by = {t["name"]: t for t in out}
        if "LOW" in by:
            ex.design("ttc", rel, ("tm_rate_lo_bps",), int(by["LOW"]["bps"]), "CDR rate ladder LOW tier", item=False)
        if "HIGH" in by:
            ex.design("ttc", rel, ("tm_rate_hi_bps",), int(by["HIGH"]["bps"]), "CDR rate ladder HIGH tier", item=False)
        if not ({"LOW", "HIGH"} <= set(by)):
            ex.note("ttc", "rate tier names", "unsupported", "the simulator's TTC_SET_DATA_RATE selects tiers named LOW and HIGH",
                    rel, "tm_rate_tiers")
        coding = by.get("HIGH", {}).get("coding_gain_db")
        if coding is not None:
            ex.design("ttc", rel, ("coding_gain_db",), float(coding), "CDR rate ladder (HIGH tier coding gain)", item=False)
    else:
        ex.default("ttc", rel, ("tm_rate_tiers",), "no CDR rate ladder: EOSAT-1 SAFE / LOW / HIGH", "TM rate ladder", "missing")
    t = cm.singleton(rows, "ttc")
    for k, lab in (("default_tier", "default tier"), ("beacon_tier", "beacon / bootloader tier"), ("safe_tier", "safe-mode tier"),
                   ("tc_uplink_rate_bps", "TC uplink rate"), ("cmd_loss_switch_timeout_s", "command-loss timer"),
                   ("cmd_loss_rssi_threshold_dbm", "command-loss RSSI threshold")):
        if t.get(k) is not None:
            ex.design("ttc", rel, (k,), t[k], f"CDR TT&C settings.{k}", lab)
        else:
            ex.default("ttc", rel, (k,), "no CDR TT&C settings (EOSAT-1 value)", lab, "missing" if not t else "default")
    b = t.get("beacon") or {}
    for k in ("enabled", "bps", "rf_power_w", "hk_sid", "dl_freq_mhz", "sc_gain_dbi", "dc_power_w"):
        if b.get(k) is not None:
            ex.design("ttc", rel, ("beacon", k), b[k], f"CDR TT&C beacon.{k}", "beacon" if k == "enabled" else None, item=k == "enabled")
    if b.get("eps_line") is not None:
        line = b["eps_line"] if b["eps_line"] in SIM_LINES else _sim_line_by_name(str(b["eps_line"]), d, ctx["line_map"])
        if line == "ttc_tx":
            line = "ttc_rx"          # a beacon is keyed with the receiver, independent of the main TX line
        if line in SIM_LINES:
            ex.design("ttc", rel, ("beacon", "eps_line"), line, f"CDR beacon.eps_line {b['eps_line']} (mapped)", item=False)
    if not b:
        ex.default("ttc", rel, ("beacon",), "no CDR beacon definition (EOSAT-1 UHF beacon)", "beacon")
    for k in ("atmospheric_loss_db", "polarization_loss_db", "implementation_loss_db"):
        ex.default("ttc", rel, (k,), "link-budget loss (EOSAT-1 value)", "link-budget losses", item=k == "implementation_loss_db")
    ex.default("ttc", rel, ("sband_antennas",), "S-band antenna pair (EOSAT-1 +Z / -Z patches)", "S-band antenna accommodation")


# ── payload ───────────────────────────────────────────────────────────────

def _payload(ex: SimConfigExport, d: Design) -> None:
    rel = "subsystems/payload.yaml"
    pl = d.unit("payload")
    if not pl:
        ex.default("payload", rel, ("pixels_across_track",), "no payload in the design: EOSAT-1 imager", "imager", "missing")
        return
    p = d.kbp(pl)
    m = re.search(r"(\d+)\s*px\s*[x×]\s*([\d.]+)\s*(?:um|µm)", str(p.get("sensor") or ""))
    px = _num(p.get("pixels_across_track")) or (float(m.group(1)) if m else None)
    pitch = _num(p.get("pixel_pitch_um")) or (float(m.group(2)) if m else None)
    if px:
        ex.design("payload", rel, ("pixels_across_track",), int(px), f"{d.name(pl)} (detector)", "detector pixels")
    else:
        ex.default("payload", rel, ("pixels_across_track",), "no detector size in the design", "detector pixels", "missing")
    if pitch:
        ex.design("payload", rel, ("pixel_pitch_um",), pitch, f"{d.name(pl)} (detector pitch)", "pixel pitch")
    f = _num(p.get("focal_length_mm"))
    if f:
        ex.design("payload", rel, ("focal_length_mm",), f, f"{d.name(pl)} (focal length)", "focal length")
    else:
        ex.default("payload", rel, ("focal_length_mm",), "no focal length in the design", "focal length", "missing")
    dr = _num(p.get("data_rate_mbps"))
    bits = _num(p.get("bits_per_pixel"))
    if bits:
        ex.design("payload", rel, ("bits_per_pixel",), int(bits), f"{d.name(pl)} (ADC depth)", "bits per pixel")
    else:
        ex.default("payload", rel, ("bits_per_pixel",), "no ADC depth in the design (12 bit)", "bits per pixel")
    if dr:
        ex.design("payload", rel, ("data_rate_mbps",), dr, f"{d.name(pl)} (data rate)", "imager data rate")
        n_px = px or float(ex.load(rel).get("pixels_across_track") or 8192)
        b = bits or float(ex.load(rel).get("bits_per_pixel") or 12)
        bands = 4
        ex.design("payload", rel, ("line_rate_hz",), _r(dr * 1e6 / (n_px * b * bands), 1),
                  f"{d.name(pl)}: data rate / (pixels × bits × 4 bands)", "line rate")
    else:
        ex.default("payload", rel, ("data_rate_mbps",), "no imager data rate in the design", "imager data rate", "missing")
    ex.note("payload", "spectral bands", "default", "the simulator's 4-band table (443/560/665/865 nm) is in the payload model", rel, "")
    st = sum(_num(d.kbp(e).get("storage_gb")) or 0.0 for e in d.units("payload", "obc"))
    if st > 0:
        ex.design("payload", rel, ("total_storage_mb",), _r(st * 1000.0, 1), "payload / OBC storage_gb", "mass memory")
    else:
        ex.default("payload", rel, ("total_storage_mb",), "no mass-memory size in the design (EOSAT-1 20 GB)", "mass memory")
    for k in ("fpa_cooler_target_c", "fpa_ambient_c", "fpa_tau_cooling_s", "fpa_tau_warming_s", "image_size_mb", "num_memory_segments"):
        ex.default("payload", rel, (k,), "imager thermal / storage model value (EOSAT-1)", "FPA and storage model", item=k == "fpa_cooler_target_c")


# ── propulsion ────────────────────────────────────────────────────────────

def _prop(ex: SimConfigExport, d: Design) -> None:
    rel = "subsystems/prop.yaml"
    th = d.units("propulsion")
    mp = d.f.get("mass_properties") or {}
    if not th:
        ex.note("prop", "propulsion", "unsupported",
                "the design has no propulsion; the simulator's propulsion model stays (EOSAT-1 ADN thruster), its line off", rel, "")
        ex.headers[rel] = _header(rel, ex)[:1] + ["C2O default: the design has no propulsion; EOSAT-1 model kept, its power line stays off.", ""]
        return
    p = d.kbp(th[0])
    for k, src, lab in (("thrust_bol_n", "thrust_n", "thrust"), ("isp_bol_s", "isp_s", "specific impulse")):
        if _num(p.get(src)):
            ex.design("prop", rel, (k,), float(p[src]), f"{d.name(th[0])} (KB {src})", lab)
        else:
            ex.default("prop", rel, (k,), f"no {src} in the KB", lab, "missing")
    pm = _num(d.f.get("flat", {}).get("propulsion.propellant_mass_kg")) or _num(p.get("propellant_mass_kg"))
    if pm:
        ex.design("prop", rel, ("propellant_mass_kg",), pm, "propulsion.propellant_mass_kg", "propellant mass")
    else:
        ex.default("prop", rel, ("propellant_mass_kg",), "no propellant budget in the design (EOSAT-1 0.4 kg)", "propellant mass", "missing")
    if _num(mp.get("total_mass_kg")):
        ex.design("prop", rel, ("sc_dry_mass_kg",), _r(mp["total_mass_kg"], 3), "physics closure: spacecraft mass", "dry mass")
    for k in ("arm_code", "arm_window_s", "interlocks", "abort"):
        ex.default("prop", rel, (k,), "propulsion safety table not in the design (EOSAT-1 inhibits / interlocks)", "propulsion inhibits and interlocks",
                   item=k == "interlocks")


def _obdh(ex: SimConfigExport, d: Design) -> None:
    rel = "subsystems/obdh.yaml"
    obc = d.units("obc")
    n = sum(d.qty(e) for e in obc)
    if n >= 2 or any(str(e.get("redundancy_type") or "") for e in obc):
        ex.note("obdh", "OBC redundancy", "design", f"{n} OBC units (the simulator models a cold-redundant A/B pair)", rel, "")
    elif obc:
        ex.note("obdh", "OBC redundancy", "unsupported", "single OBC in the design; the simulator always models OBC A/B", rel, "")
    else:
        ex.note("obdh", "OBC", "missing", "no OBC in the design", rel, "")
    for k in ("modes", "watchdog_period_ticks", "cpu_baseline_pct", "clock_drift_ppm_nominal", "clock_drift_sigma_ppm",
              "clock_gps_discipline", "clock_jump_event_threshold_s"):
        ex.default("obdh", rel, (k,), "FSW / onboard-clock parameter not in the design (EOSAT-1 value)",
                   {"modes": "OBC modes", "watchdog_period_ticks": "watchdog period", "cpu_baseline_pct": "CPU budget",
                    "clock_drift_ppm_nominal": "onboard clock stability"}.get(k), item=k in ("modes", "watchdog_period_ticks",
                                                                                         "cpu_baseline_pct", "clock_drift_ppm_nominal"))
    ex.sim_detail(rel, ("clock_drift_failure_ppm",), "failure-injection magnitude (instructor tool)")
    buses = [b for b in (d.f.get("electrical") or {}).get("buses") or [] if b.get("status") != "rejected"]
    if buses:
        segs = sorted({str(b.get("segment") or "") for b in buses})
        ex.note("obdh", "data buses", "design" if {"A", "B"} <= set(segs) else "unsupported",
                f"design buses {[b.get('name') for b in buses]}; the simulator models CAN A (EPS/TCS/AOCS) and B (TTC/payload)",
                rel, "")


def _geometry(ex: SimConfigExport, d: Design) -> None:
    rel = "geometry.yaml"
    geo = d.f.get("geometry")
    if geo:
        ex.files[rel] = copy.deepcopy(geo)
        ex.comments[rel] = {}
        ex.headers[rel] = [f"{rel} — c2o.geometry/1 from the approved SpaceCDF stack layout of study {ex.study_name or ex.study_id}",
                           "design: stack builder (design/docs/STACK_BUILDER.md); display only, the simulator physics never reads it", ""]
        ex.note("geometry", "spacecraft geometry (faces, wings, sensors, antennas)", "design", "approved stack layout", rel, "")
    else:
        ex.note("geometry", "spacecraft geometry", "missing", "no approved stack layout: EOSAT-1 geometry (display only)", rel, "")


_FACE_OF = {(1, 0, 0): "px", (-1, 0, 0): "mx", (0, 1, 0): "py", (0, -1, 0): "my", (0, 0, 1): "pz", (0, 0, -1): "mz"}


def _consistency(ex: SimConfigExport, d: Design) -> None:
    """The copies geometry.yaml carries must equal their owners (smo_common.config.geometry
    cross-check): cell areas = eps.yaml, S-band patches = ttc.yaml, payload FOV = planner.yaml."""
    geo = ex.load("geometry.yaml")
    eps = ex.load("subsystems/eps.yaml").get("solar_panels") or {}
    designed = bool(d.f.get("geometry"))
    for bp in geo.get("body_panels") or []:
        v = eps.get(f"{bp.get('face')}_area_m2")
        if v is not None:
            bp["cell_area_m2"] = float(v)
    by_face: dict[str, list[dict]] = {}
    for w in geo.get("wings") or []:
        by_face.setdefault(w.get("face"), []).append(w)
    for face, ws in by_face.items():
        v = eps.get(f"wing_{face}_area_m2")
        if v is not None:
            for w in ws:
                w["cell_area_m2"] = _r(float(v) / len(ws), 5)
    if not designed:
        ex.headers["geometry.yaml"] = ["geometry.yaml — C2O default: EOSAT-1 geometry (no approved stack layout); cell areas copied",
                                       "from subsystems/eps.yaml so the display matches the power model. Display only.", ""]
    # S-band patches drawn by the stack builder -> ttc.yaml
    patches = [a for a in geo.get("antennas") or [] if a.get("kind") == "patch"]
    if designed and patches:
        gain = ex.load("subsystems/ttc.yaml").get("sc_gain_dbi") or 3.0
        out = []
        for a in patches:
            b = [round(float(x)) for x in a.get("boresight") or [0, 0, -1]]
            out.append({"id": a["id"], "face": _FACE_OF.get(tuple(b), "mz"), "boresight": [float(x) for x in a["boresight"]],
                        "gain_dbi": float(gain)})
        ex.design("ttc", "subsystems/ttc.yaml", ("sband_antennas",), out, "stack builder layout (S-band patches)", "S-band antenna accommodation")
    elif designed:
        ex.default("ttc", "subsystems/ttc.yaml", ("sband_antennas",), "the stack layout places no S-band patch", "S-band antenna accommodation",
                   "missing", value=[])
    # payload FOV -> planner
    fov = _num((geo.get("payload") or {}).get("fov_deg"))
    pl = d.unit("payload")
    pfov = _num(d.kbp(pl).get("fov_deg")) if pl else None
    if pfov and not designed:
        geo.setdefault("payload", {})["fov_deg"] = pfov
        fov = pfov
    if fov:
        plan = ex.load("planning/planner.yaml")
        if (plan.get("imaging") or {}).get("fov_deg") is not None:
            plan["imaging"]["fov_deg"] = fov
            ex.comments["planning/planner.yaml"][("imaging", "fov_deg")] = (
                "design: payload FOV" if (pfov or designed) else "C2O default: EOSAT-1 imager FOV")
            if pfov or designed:
                ex.note("payload", "imager field of view", "design", "payload element / stack builder FOV", "planning/planner.yaml", "imaging.fov_deg")


# ── TM/TC database, FDIR tables ───────────────────────────────────────────

def _database(ex: SimConfigExport, d: Design, rows: list[dict], ctx: dict) -> None:
    from ..cdr_sim import export_sim
    if ex.dataset == "empty":
        for area, lab in (("tmtc", "TM/TC database (parameters, HK, commands, events)"), ("fdir", "FDIR tables (S12, S19, rules)"),
                          ("ops", "positions, GO/NO-GO, MCS limits")):
            ex.note(area, lab, "missing", "no CDR database in the study: the simulator model interface catalogue (EOSAT-1)")
        return
    files = export_sim(rows)
    if ex.dataset == "reference":
        _from_reference(ex, files)
        return
    # designed database: the model interface stays; overlay by name; full design DB as documentation
    for name, data in files.items():
        rel = "design_db/" + name.replace("#", "_")
        ex.files[rel] = data
        ex.comments[rel] = {}
        ex.headers[rel] = [f"{rel} — the study's own CDR database in the simulator's shapes (design: CDR model).",
                           "Not read by the simulator: its models implement the EOSAT-1-class TM/TC interface. Items that map",
                           "by name onto that interface are applied to the files one level up (see README.md).", ""]
    _overlay_design_db(ex, d, rows, ctx)


def _from_reference(ex: SimConfigExport, files: dict[str, Any]) -> None:
    """EOSAT-1 reference import: the CDR rows are the database (the round trip)."""
    src = "CDR database (EOSAT-1 reference import)"
    whole = {"telemetry/parameters.yaml": ("tmtc", "TM parameters"), "telemetry/hk_structures.yaml": ("tmtc", "housekeeping structures"),
             "commands/tc_catalog.yaml": ("tmtc", "TC catalogue"), "events/event_catalog.yaml": ("tmtc", "event catalogue"),
             "monitoring/s12_definitions.yaml": ("fdir", "S12 monitoring table"), "monitoring/s19_rules.yaml": ("fdir", "S19 event-action table"),
             "mcs/gonogo_matrix.yaml": ("ops", "GO/NO-GO matrix"), "mcs/limits.yaml": ("ops", "MCS limits")}
    for rel, (area, lab) in whole.items():
        new = files.get(rel)
        if not new:
            continue
        old = ex.load(rel)
        for k, v in new.items():
            if k == "commands":
                # keep template keys the CDR row does not carry (quick-command metadata …), by name
                byname = {c.get("name"): c for c in (old.get("commands") or [])}
                v = [{**byname.get(c["name"], {}), **c} for c in v]
            if k == "events":
                byid = {e.get("id"): e for e in (old.get("events") or [])}
                v = [{**byid.get(e["id"], {}), **e} for e in v]
            old[k] = v
        ex.headers[rel] = [f"{rel} — design: {src}", ""]
        ex.note(area, lab, "design", src, rel, "")
    rules = files.get("subsystems/fdir.yaml#rules")
    if rules and rules.get("rules"):
        ex.design("fdir", "subsystems/fdir.yaml", ("rules",), rules["rules"], src, "FDIR rule table")
    hk = files.get("simulation.yaml#housekeeping") or {}
    if hk.get("default_enabled_sids"):
        ex.design("tmtc", "simulation.yaml", ("housekeeping", "default_enabled_sids"), hk["default_enabled_sids"], src + " (enabled at boot)",
                  "HK enabled at boot")
    modes = files.get("aocs/aocs_mode_codes.yaml")
    if modes and modes.get("modes"):
        old = ex.load("aocs/aocs_mode_codes.yaml")
        for code, m in modes["modes"].items():
            old.setdefault("modes", {}).setdefault(code, {}).update({k: v for k, v in m.items() if v})
        ex.headers["aocs/aocs_mode_codes.yaml"] = ["aocs/aocs_mode_codes.yaml — design: " + src, ""]
        ex.note("aocs", "AOCS mode codes", "design", src, "aocs/aocs_mode_codes.yaml", "")
    pos = (files.get("mcs/positions.yaml") or {}).get("positions") or {}
    if pos:
        old = ex.load("mcs/positions.yaml")
        for pid, p in pos.items():
            entry = old.setdefault("positions", {}).setdefault(pid, {})
            entry.update({k: v for k, v in p.items() if v is not None})
        ex.headers["mcs/positions.yaml"] = ["mcs/positions.yaml — design: " + src + " (tabs and command lists the CDR does not hold: EOSAT-1)", ""]
        ex.note("ops", "operator positions", "design", src, "mcs/positions.yaml", "")


def _overlay_design_db(ex: SimConfigExport, d: Design, rows: list[dict], ctx: dict) -> None:
    from .. import cdr_model as cm
    src = "CDR database (designed)"
    params = ex.load("telemetry/parameters.yaml").get("parameters") or []
    pid_of = {p["name"]: p["id"] for p in params}
    # HK periods per subsystem + enabled at boot
    hk = cm.live_data(rows, "hk")
    sims = ex.load("telemetry/hk_structures.yaml").get("structures") or []
    enabled = set()
    applied = 0
    own = [h for h in hk if h.get("store_sid") is not None or isinstance(h.get("rt_period_by_mode"), dict) or h.get("params")]
    if own:
        # W4.05: a study-specific SID layout (stored copies, per-mode intervals, own parameter lists)
        # is kept whole in design_db/telemetry/ — never merged into the EOSAT-1 structures by subsystem.
        ex.note("tmtc", "housekeeping structures", "unsupported",
                f"{src}: {len(own)} study-specific SIDs (stored copies, intervals per mode) kept whole in "
                "design_db/telemetry/hk_structures.yaml and hk_mode_intervals.yaml; the simulator's EOSAT-1 structures are not changed",
                "telemetry/hk_structures.yaml", "")
        hk = [h for h in hk if h not in own]
    for h in hk:
        sub = h.get("subsystem") or ""
        if sub in ("sys", "fdir", "str") and not h.get("beacon"):
            ex.note("tmtc", f"HK structure {h.get('name')}", "default",
                    "system / FDIR parameters are in the simulator's Platform SID 4 (its period follows the OBDH SID)",
                    "telemetry/hk_structures.yaml", "")
            if h.get("enabled_at_boot"):
                enabled.add(4)
            continue
        sid = 11 if h.get("beacon") else SIM_SID_OF_SUBSYSTEM.get(sub)
        idx = next((i for i, s in enumerate(sims) if s.get("sid") == sid), None)
        if idx is None:
            ex.note("tmtc", f"HK structure {h.get('name')}", "unsupported", "no simulator HK structure for this subsystem",
                    "telemetry/hk_structures.yaml", "")
            continue
        if _num(h.get("period_s")):
            ex.design("tmtc", "telemetry/hk_structures.yaml", ("structures", idx, "interval_s"), float(h["period_s"]),
                      f"{src}: SID {h.get('sid')} {h.get('name')} period", item=False)
            applied += 1
        if h.get("enabled_at_boot"):
            enabled.add(sid)
    if applied:
        ex.note("tmtc", "housekeeping rates", "design", f"{src}: {applied} SID periods mapped by subsystem", "telemetry/hk_structures.yaml", "")
    if enabled:
        ex.design("tmtc", "simulation.yaml", ("housekeeping", "default_enabled_sids"), sorted(enabled | {11}),
                  f"{src}: HK enabled at boot (by subsystem)", "HK enabled at boot")
    # parameters and commands: count what maps
    dparams = cm.live_data(rows, "parameters")
    hit = [p for p in dparams if p.get("name") in pid_of]
    ex.note("tmtc", "TM parameters", "default",
            f"model interface catalogue kept; {len(hit)} of {len(dparams)} design parameters exist in it by name "
            "(the rest are in design_db/telemetry/parameters.yaml only)", "telemetry/parameters.yaml", "")
    cmds = ex.load("commands/tc_catalog.yaml").get("commands") or []
    ci = {c.get("name"): i for i, c in enumerate(cmds)}
    nm = 0
    for c in cm.live_data(rows, "commands"):
        i = ci.get(c.get("name"))
        if i is None:
            continue
        nm += 1
        if c.get("arm_execute") is not None:
            ex.design("tmtc", "commands/tc_catalog.yaml", ("commands", i, "arm_execute"), bool(c["arm_execute"]),
                      f"{src}: {c['name']} arm_execute", item=False)
        if c.get("criticality") and c["criticality"] != "normal":
            ex.design("tmtc", "commands/tc_catalog.yaml", ("commands", i, "criticality"), c["criticality"],
                      f"{src}: {c['name']} criticality", item=False)
    ex.note("tmtc", "TC catalogue", "design" if nm else "default",
            f"model interface catalogue; arm-execute and criticality of {nm} design commands applied by name", "commands/tc_catalog.yaml", "")
    ex.note("tmtc", "event catalogue", "default", "model interface catalogue (events are raised by the simulator models)",
            "events/event_catalog.yaml", "")
    # MCS limits and S12 monitors by parameter name
    lims = ex.load("mcs/limits.yaml").get("limits") or []
    li = {x.get("param_id"): i for i, x in enumerate(lims)}
    nl = 0
    for lim in cm.live_data(rows, "limits"):
        pid = pid_of.get(lim.get("parameter") or "")
        if pid is None or pid == 0x0105:
            continue                      # the bus-voltage limits follow the named bus-protection levels below
        entry = {"param_id": pid, **{k: lim[k] for k in ("yellow_low", "yellow_high", "red_low", "red_high", "check_interval_s")
                                     if lim.get(k) is not None}}
        if pid in li:
            lims[li[pid]].update(entry)
        else:
            lims.append(entry)
            li[pid] = len(lims) - 1
        ex.comments["mcs/limits.yaml"][("limits", li[pid])] = f"design: {src} limit on {lim.get('parameter')}"
        nl += 1
    ex.note("ops", "MCS limits", "design" if nl else "default", f"{nl} design limits applied by parameter name; the others: EOSAT-1",
            "mcs/limits.yaml", "")
    mons = ex.load("monitoring/s12_definitions.yaml").get("s12_definitions") or []
    nmn = 0
    for m in cm.live_data(rows, "monitors"):
        pid = pid_of.get(m.get("parameter") or "")
        if pid is None or pid == 0x0105:
            continue
        idx = next((i for i, x in enumerate(mons) if x.get("param_id") == pid), None)
        if idx is None:
            continue
        for k_from, k_to in (("low", "low_limit"), ("high", "high_limit")):
            if _num(m.get(k_from)) is not None:
                mons[idx][k_to] = float(m[k_from])
        ex.comments["monitoring/s12_definitions.yaml"][("s12_definitions", idx)] = f"design: {src} monitor {m.get('pmon_id')}"
        nmn += 1
    ex.note("fdir", "S12 monitoring table", "design" if nmn else "default",
            f"{nmn} design monitors applied to the simulator's definitions by parameter name; the others: EOSAT-1",
            "monitoring/s12_definitions.yaml", "")
    ex.note("fdir", "S19 event-action table", "default",
            "model interface table kept (actions are simulator S8 functions); the design's table is in design_db/",
            "monitoring/s19_rules.yaml", "")
    ex.note("fdir", "FDIR rule table", "default", "EOSAT-1 rules; their bus-voltage levels follow the design's named levels (threshold_ref)",
            "subsystems/fdir.yaml", "rules")
    # positions: labels and services of the ids the simulator has
    pos = ex.load("mcs/positions.yaml").get("positions") or {}
    npz = 0
    for p in cm.live_data(rows, "positions"):
        if p.get("id") in pos:
            pos[p["id"]]["display_name"] = _en(p.get("label")) or pos[p["id"]].get("display_name")
            npz += 1
    if npz:
        ex.note("ops", "operator positions", "design", f"{npz} positions: names from the design (command lists: the model interface)",
                "mcs/positions.yaml", "")


def _bus_ladder_copies(ex: SimConfigExport) -> None:
    """Keep the S12 / MCS-limit copies of the bus levels, and the fault-propagation copies of the
    load-shed SoC stages, equal to their single source in simulation.yaml (engine start-up checks)."""
    socs = ((ex.load("simulation.yaml").get("eps") or {}).get("load_shed") or {}).get("soc_stage_thresholds_pct") or []
    fp = ex.load("fdir/fault_propagation.yaml")
    stages = next((v for v in fp.values() if isinstance(v, dict) and "stage_1" in v), None) if isinstance(fp, dict) else None
    if stages:
        for i, v in enumerate(socs[:3]):
            st = stages.get(f"stage_{i + 1}")
            if isinstance(st, dict) and "soc_threshold" in st:
                st["soc_threshold"] = float(v)
    bp = (ex.load("simulation.yaml").get("eps") or {}).get("bus_protection") or {}

    def named(node: Any) -> None:
        """Literal copies next to a ``threshold_ref`` follow the named level (the engine uses the
        named value anyway and logs the drift)."""
        if isinstance(node, dict):
            ref = node.get("threshold_ref")
            if isinstance(ref, str) and ref.startswith("eps.bus_protection.") and "threshold" in node:
                v = _num(bp.get(ref.rsplit(".", 1)[1]))
                if v is not None:
                    node["threshold"] = v
            for x in node.values():
                named(x)
        elif isinstance(node, list):
            for x in node:
                named(x)
    named(ex.load("subsystems/fdir.yaml"))
    named(ex.load("fdir/fault_propagation.yaml"))
    s12 = ex.load("monitoring/s12_definitions.yaml").get("s12_definitions") or []
    for i, m in enumerate(s12):
        if m.get("param_id") == 0x0105:
            key = {"EPS Bus Voltage Low": "uv_v", "EPS Bus Voltage Critical": "eps_safe_v"}.get(m.get("name"))
            if key and _num(bp.get(key)) is not None:
                m["low_limit"] = float(bp[key])
                ex.comments["monitoring/s12_definitions.yaml"][("s12_definitions", i)] = f"from simulation.yaml eps.bus_protection.{key}"
    for i, lim in enumerate(ex.load("mcs/limits.yaml").get("limits") or []):
        if lim.get("param_id") == 0x0105:
            for k, n in (("yellow_low", "uv_v"), ("red_low", "eps_safe_v"), ("yellow_high", "ov_v")):
                if _num(bp.get(n)) is not None:
                    lim[k] = float(bp[n])
            if _num(bp.get("ov_v")) is not None and _num(lim.get("red_high")) is not None and lim["red_high"] < bp["ov_v"]:
                lim["red_high"] = float(bp["ov_v"]) + 0.6
            ex.comments["mcs/limits.yaml"][("limits", i)] = "bus voltage: from simulation.yaml eps.bus_protection (uv_v / eps_safe_v / ov_v)"


# ── operations ────────────────────────────────────────────────────────────

def _ops(ex: SimConfigExport, d: Design, rows: list[dict]) -> None:
    from .. import cdr_model as cm
    _bus_ladder_copies(ex)
    fr = cm.live_data(rows, "flight_rules")
    rel = "ops/flight_rules.yaml"
    if fr:
        ex.files[rel] = {"flight_rules": [{"id": r.get("rule_id"), "text": _en(r.get("text")),
                                           "text_fr": (r.get("text") or {}).get("fr") if isinstance(r.get("text"), dict) else None,
                                           "ref": r.get("ref")} for r in fr]}
        ex.comments[rel] = {}
        ex.headers[rel] = [f"{rel} — design: CDR flight rules (study {ex.study_name or ex.study_id})",
                           "Read by nothing in the simulator yet: the operations document of record for the procedures and the FD.", ""]
        ex.note("ops", "flight rules", "design", "CDR flight rules (exported as a document, not consumed by the simulator)", rel, "")
    else:
        ex.note("ops", "flight rules", "missing", "no CDR flight rules", rel, "")
    gng = cm.live_data(rows, "gonogo")
    if gng and ex.dataset == "design":
        ex.files["mcs/gonogo_matrix.yaml"] = {"gonogo_matrix": [{"situation": _en(g.get("situation")), "who_calls": g.get("who_calls"),
                                                                 "who_responds": g.get("who_responds") or [],
                                                                 "fd_decision": _en(g.get("decision")), "critical": bool(g.get("critical"))}
                                                                for g in gng]}
        ex.headers["mcs/gonogo_matrix.yaml"] = ["mcs/gonogo_matrix.yaml — design: CDR GO/NO-GO matrix", ""]
        ex.note("ops", "GO/NO-GO matrix", "design", "CDR GO/NO-GO matrix", "mcs/gonogo_matrix.yaml", "")
    elif not gng:
        ex.note("ops", "GO/NO-GO matrix", "missing" if ex.dataset != "reference" else "default", "no CDR GO/NO-GO matrix (EOSAT-1)",
                "mcs/gonogo_matrix.yaml", "")
    ex.note("ops", "flight operations procedures", "default", "not exported: write them for the design (README.md)", "procedures/", "")
    # rfsim SCID
    s = cm.singleton(rows, "settings")
    if s.get("spacecraft_id") is not None:
        ex.design("tmtc", "rfsim.yaml", ("ccsds", "scid"), int(s["spacecraft_id"]), "CDR TM/TC settings.spacecraft_id", "spacecraft id (SCID)")
    else:
        ex.default("tmtc", "rfsim.yaml", ("ccsds", "scid"), "no spacecraft id decided (EOSAT-1 SCID 1)", "spacecraft id (SCID)")


def _sim_details(ex: SimConfigExport) -> None:
    rel = "simulation.yaml"
    for k in ("tick_hz", "seed", "tick", "speed", "epoch", "failures", "scenario_defaults", "auto_snapshots"):
        ex.sim_detail(rel, (k,))
    for k in ("rt_tm_pacing", "rt_tm_backlog_max"):
        ex.sim_detail(rel, ("ttc", k))
    ex.sim_detail(rel, ("eps", "initial"), "initial conditions (simulation set-up, not a design decision)")
    ex.sim_detail(rel, ("eps", "heater_duty_from_tcs"))
    ex.default("tcs", rel, ("tcs", "environment"), "orbital thermal environment (EOSAT-1 constants: 1361 W/m², albedo 0.30, OLR 237 W/m²)",
               "thermal environment")
    ex.default("obdh", rel, ("phases", "separation_timer_s"), "separation inhibit timer (CDS 30 min, EOSAT-1)", "separation timer")
    ex.default("ttc", rel, ("ttc", "auto_tx_hold_s"), "auto TX-off hold after contact (EOSAT-1 300 s)", "auto TX hold")
    ex.default("prop", rel, ("prop",), "propulsion scenario switches (simulation set-up)", item=False)
    ex.sim_detail("rfsim.yaml", ("network",))
    ex.sim_detail("rfsim.yaml", ("channel",), "RF channel simulation (simulator implementation detail)")
    ex.sim_detail("rfsim.yaml", ("pipeline",), "modulator pipeline (simulator implementation detail)")


def _readme(ex: SimConfigExport) -> str:
    r = ex.readiness()
    lines = [f"# Simulator configuration — {ex.study_name or ex.study_id}", "",
             "Exported by SpaceCDF (design-to-simulator export, see `docs/plan_2026-11/design_sim/SIM_EXPORT.md`).",
             f"CDR database: **{ex.dataset}**. Run it with the EOSAT-1-class simulator:", "",
             "```", "cd sim && ./start.sh --config=/path/to/this/directory", "```", "",
             "Every value in the YAML files carries its source: `# design: ...` (the SpaceCDF design model) or",
             "`# C2O default: ...` (a documented default, the EOSAT-1 reference value unless stated).", "",
             "## Readiness", "", "| Area | design | default | missing | unsupported |", "|---|---|---|---|---|"]
    for a in r["areas"]:
        lines.append(f"| {a['label']['en']} | {a['design']} | {a['default']} | {a['missing']} | {a['unsupported']} |")
    lines += ["", "### Still default, missing or unsupported", ""]
    for a in r["areas"]:
        for i in a["items"]:
            if i["status"] != "design":
                lines.append(f"- **{a['label']['en']}** — {i['item']} ({i['status']}): {i['source']}")
    lines += ["", "## Not exported", "",
              "- `procedures/`, `manual/`, `worksheets/`: the flight operations procedures, the operations manual and the",
              "  course worksheets are written for a spacecraft, not generated. The MCS and planner run without them.",
              "- `i18n/`, `xtce/`, `smdl/`: translations and generated artefacts; regenerate XTCE / SMDL with",
              "  `sim/tools/generate_xtce.py` and `generate_smdl.py` pointed at this directory if needed.", "",
              "## Files read by nothing yet", "",
              "- `ops/flight_rules.yaml` (CDR flight rules), and `design_db/` (a designed CDR database in the simulator's",
              "  shapes; the simulator runs the EOSAT-1-class TM/TC interface, onto which the design maps by name).", ""]
    return "\n".join(lines)
