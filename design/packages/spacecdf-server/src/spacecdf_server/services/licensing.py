"""SpaceCDF — licensing model: record, frequency assignments, disposal and filings (W5.01-W5.03, W5.06).

What the design already knows is *derived* here at export time; what it cannot know is kept in the
study's licensing record (``db/models_licensing.py``), edited in the Licensing tab:

* ``record``      — applicant, contacts, system participants and affiliates, the command and data
                    protection plan (facilities, encryption and key management, personnel and physical
                    security), data policy and EULA, launch provider and site, assignment overrides,
                    disposal-device figures, imported DRAMA/DAS results, and the filing tracker;
* ``assignments`` — one frequency assignment per transmitter and receiver, space and ground
                    (W5.01): centre frequency, bandwidth, emission designator, power, antenna gain,
                    polarisation, EIRP and the PFD at 5 deg elevation, with the band's service;
* ``disposal``    — the drag-sail disposal analysis against the ISED conditions (W5.02);
* ``filings``     — the six filings and their status (W5.06).

``collect(ctx)`` is the body of the export-context section ``licensing``; every regulatory document
(``services/licensing_docs.py``) takes its data from it. Nothing in this module writes, except
``save_record``.
"""
from __future__ import annotations

import copy
import math
import re
from typing import Any

from . import spectrum

# ───────────────────────────────────────────────────────────────── record

FILING_STATUSES = ("not_started", "in_preparation", "submitted", "received", "granted",
                   "granted_with_conditions", "refused", "not_applicable")

#: the filings a Canadian remote-sensing CubeSat with its own UHF ground network needs, in the order
#: of the research checklist (start dates relative to launch L, in months)
DEFAULT_FILINGS: tuple[dict, ...] = (
    {"id": "ised_preconsultation", "authority": "ISED", "start_months": -42,
     "title": {"en": "ISED pre-consultation on frequencies (401 MHz downlink, 450 MHz uplink, VHF fallback)",
               "fr": "Pré-consultation d’ISDE sur les fréquences (liaison descendante 401 MHz, montante 450 MHz, repli VHF)"}},
    {"id": "itu_api", "authority": "ISED / ITU BR", "start_months": -30,
     "title": {"en": "ITU advance publication (API) and RR No. 9.21 agreement for 449.75-450.25 MHz",
               "fr": "Publication anticipée UIT (API) et accord au titre du n° 9.21 du RR pour 449,75-450,25 MHz"}},
    {"id": "ised_space_station", "authority": "ISED", "start_months": -24,
     "title": {"en": "ISED space station licence (CPC-2-6-02) with the space debris mitigation plan",
               "fr": "Licence de station spatiale d’ISDE (CPC-2-6-02) avec le plan de réduction des débris spatiaux"}},
    {"id": "rsssa_licence", "authority": "Global Affairs Canada", "start_months": -24,
     "title": {"en": "RSSSA operating licence (Remote Sensing Space Systems Act)",
               "fr": "Licence d’exploitation LSTS (Loi sur les systèmes de télédétection spatiale)"}},
    {"id": "ised_earth_stations", "authority": "ISED", "start_months": -12,
     "title": {"en": "ISED earth station licences (one per site)",
               "fr": "Licences de station terrienne d’ISDE (une par site)"}},
    {"id": "un_registration", "authority": "Canada (UN Registration Convention)", "start_months": 2,
     "title": {"en": "UN registration of the space object (after launch)",
               "fr": "Immatriculation de l’objet spatial auprès de l’ONU (après le lancement)"}},
)

EMPTY_RECORD: dict[str, Any] = {
    "applicant": {"legal_name": "", "address": "", "country": "Canada", "canadian_entity": None,
                  "contact_name": "", "contact_email": "", "contact_phone": "", "security_officer": ""},
    "contacts": [],                # [{role, name, email, phone}]
    "participants": [],            # system participants: [{name, role, country}]
    "affiliates": [],              # [{name, relationship, country}]
    "itu_network_name": "",
    "cdpp": {                      # command and data protection plan (RSSSA §14-30)
        "command_facility": "", "data_facility": "", "backup_facility": "",
        "command_encryption": "", "command_authentication": "", "downlink_encryption": "",
        "key_management": "", "key_custody": "", "command_process": "",
        "personnel_security": "", "physical_security": "", "network_security": "",
    },
    "data_policy": {"distribution": "", "eula": "", "retention": "", "disposal": "", "sensed_state_access": "",
                    "priority_access": ""},
    "launch": {"provider": "", "vehicle": "", "site": "", "deployer": "", "date": ""},
    "assignment_overrides": {},    # assignment id -> {field: value}
    "disposal": {"mechanism_reliability": None, "circuit_reliability": None, "independent_circuits": None,
                 "independent_timer_days": None, "trigger": [], "deployment_time_s": None,
                 "mass_basis": "allocation"},
    "evidence": [],                # imported DRAMA/DAS results: [{tool, version, date, lifetime_years, ...}]
    "filings": [],                 # tracker rows (merged with DEFAULT_FILINGS)
    "notes": "",
}


def _merge(base: Any, over: Any) -> Any:
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = _merge(base.get(k), v) if k in base else v
        return out
    return copy.deepcopy(over) if over is not None else copy.deepcopy(base)


def filings_with_defaults(rows: list[dict] | None, lang: str = "en") -> list[dict]:
    """The tracker: every default filing (in order) merged with the stored rows; extra rows kept."""
    stored = {r.get("id"): r for r in (rows or []) if isinstance(r, dict) and r.get("id")}
    out = []
    for d in DEFAULT_FILINGS:
        r = stored.pop(d["id"], {})
        out.append({"id": d["id"], "authority": d["authority"], "title": d["title"].get(lang) or d["title"]["en"],
                    "start_months": d["start_months"], "status": r.get("status") or "not_started",
                    "submitted": r.get("submitted") or "", "received": r.get("received") or "",
                    "granted": r.get("granted") or "", "reference": r.get("reference") or "",
                    "conditions": r.get("conditions") or "", "notes": r.get("notes") or ""})
    for r in stored.values():
        out.append({"id": r["id"], "authority": r.get("authority", ""), "title": r.get("title", r["id"]),
                    "start_months": r.get("start_months"), "status": r.get("status") or "not_started",
                    "submitted": r.get("submitted") or "", "received": r.get("received") or "",
                    "granted": r.get("granted") or "", "reference": r.get("reference") or "",
                    "conditions": r.get("conditions") or "", "notes": r.get("notes") or ""})
    return out


def validate_record(data: dict) -> list[str]:
    """Problems in a record patch (empty = valid)."""
    errs = []
    if not isinstance(data, dict):
        return ["the licensing record must be an object"]
    for f in data.get("filings") or []:
        if not isinstance(f, dict) or not f.get("id"):
            errs.append("every filing needs an id")
        elif f.get("status") and f["status"] not in FILING_STATUSES:
            errs.append(f"filing {f['id']}: status must be one of {', '.join(FILING_STATUSES)}")
    disp = data.get("disposal") or {}
    for k in ("mechanism_reliability", "circuit_reliability"):
        v = disp.get(k)
        if v is not None and not (isinstance(v, (int, float)) and 0 < float(v) <= 1):
            errs.append(f"disposal.{k} must be a probability in (0, 1]")
    n = disp.get("independent_circuits")
    if n is not None and not (isinstance(n, int) and 1 <= n <= 4):
        errs.append("disposal.independent_circuits must be 1-4")
    ov = data.get("assignment_overrides")
    if ov is not None:
        if not isinstance(ov, dict):
            errs.append("assignment_overrides must map an assignment id to its fields")
        else:
            for aid, fields in ov.items():
                if not isinstance(fields, dict):
                    errs.append(f"assignment_overrides.{aid} must be an object")
                    continue
                for k, v in fields.items():
                    if k == "link_case":          # provenance tag written by the link-budget sync
                        continue
                    if k not in OVERRIDABLE:
                        errs.append(f"assignment_overrides.{aid}.{k} cannot be overridden "
                                    f"(allowed: {', '.join(OVERRIDABLE)})")
                    elif k in _NUMERIC_OVERRIDES and v not in (None, "") and _num(v) is None:
                        errs.append(f"assignment_overrides.{aid}.{k} must be a number")
    for ev in data.get("evidence") or []:
        if not isinstance(ev, dict) or not ev.get("tool"):
            errs.append("every evidence row needs a tool (DRAMA, DAS, ...)")
    return errs


async def load_record(study_id: str) -> tuple[dict, int]:
    """(record merged with the empty shape, version); version 0 when nothing is stored."""
    from ..db.engine import get_session_factory
    from ..db.models_licensing import LicensingRow
    try:
        async with get_session_factory()() as s:
            row = await s.get(LicensingRow, study_id)
            if row is None:
                return copy.deepcopy(EMPTY_RECORD), 0
            return _merge(EMPTY_RECORD, row.data_json or {}), int(row.version or 1)
    except Exception:  # noqa: BLE001 — a missing table (old DB) reads as an empty record
        return copy.deepcopy(EMPTY_RECORD), 0


class VersionConflict(Exception):
    def __init__(self, current: int):
        super().__init__(f"version conflict (current {current})")
        self.current = current


async def save_record(study_id: str, patch: dict, *, version: int | None = None, actor: str = "") -> tuple[dict, int]:
    """Merge ``patch`` into the stored record. ``version`` (when given) must match the stored one.

    Lists (contacts, participants, filings, evidence ...) are replaced as a whole."""
    from ..db.engine import get_session_factory
    from ..db.models_licensing import LicensingRow
    async with get_session_factory()() as s:
        row = await s.get(LicensingRow, study_id)
        current = int(row.version or 1) if row is not None else 0
        if version is not None and int(version) != current:
            raise VersionConflict(current)
        data = _merge(row.data_json or {}, patch) if row is not None else _merge({}, patch)
        if row is None:
            row = LicensingRow(study_id=study_id, data_json=data, version=1, updated_by=actor[:64])
            s.add(row)
        else:
            row.data_json = data
            row.version = current + 1
            row.updated_by = actor[:64]
        await s.commit()
        return _merge(EMPTY_RECORD, data), int(row.version)


# ───────────────────────────────────────────────────────────────── helpers

def _perf(e: dict) -> dict:
    p = e.get("performance")
    return p if isinstance(p, dict) else {}


def _kb(e: dict) -> dict:
    try:
        from .rule_inputs import kb_component
        return kb_component(e) or {}
    except Exception:  # noqa: BLE001
        return {}


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:\.\d+)?", str(v))
    return float(m.group(0)) if m else None


def _space(elements: list[dict]) -> list[dict]:
    return [e for e in elements if (e.get("segment") or "space") == "space" and not e.get("deleted_at")]


def stations(elements: list[dict]) -> list[dict]:
    """Ground stations of the study (ground-segment elements with coordinates)."""
    out = []
    for e in elements:
        p = _perf(e)
        lat = p.get("lat", p.get("latitude"))
        lon = p.get("lon", p.get("longitude"))
        if e.get("segment") == "ground" and lat is not None and lon is not None:
            out.append({"id": e.get("id"), "name": e.get("name"), "lat": float(lat), "lon": float(lon),
                        "alt_m": p.get("alt_m"), "min_elevation_deg": p.get("min_elevation_deg", 10.0),
                        "bands": p.get("bands") or [], "antenna_m": p.get("antenna_m")})
    return sorted(out, key=lambda s: str(s["name"]))


def node_times(ltan: str | None, orbit_type: str = "sso") -> dict:
    """LTAN and LTDN from the stored local time of the ascending node (P4: show both)."""
    if not ltan or not re.match(r"^\d{1,2}:\d{2}$", str(ltan).strip()):
        return {"ltan": None, "ltdn": None, "daylight_node": None}
    h, m = (int(x) for x in str(ltan).strip().split(":"))
    dn = ((h + 12) % 24, m)
    ltdn = f"{dn[0]:02d}:{dn[1]:02d}"
    asc = f"{h:02d}:{m:02d}"
    daylight = "descending" if 6 <= dn[0] < 18 else "ascending"
    return {"ltan": asc, "ltdn": ltdn, "daylight_node": daylight,
            "equator_crossing": f"{ltdn} LTDN (daylight, descending)" if daylight == "descending"
            else f"{asc} LTAN (daylight, ascending)"}


def _payload_info(study: Any, elements: list[dict], altitude_km: float) -> dict:
    """Sensor performance for the RSSSA (EG D7: the GSD comes from the payload, never from the
    pointing accuracy). ``gsd_m`` is the payload's stated product GSD (payload subsystem or mission
    payload ``gsd_m``); ``instruments`` lists each camera's native GSD from its optics (pixel pitch
    and focal length of the element or its KB entry), so the finest native resolution is visible."""
    stated, swath, bands, fov, names = [], [], [], [], []
    for p in (getattr(getattr(study, "requirements", None), "payloads", None) or []):
        if getattr(p, "gsd_m", None):
            stated.append(float(p.gsd_m))
        if getattr(p, "swath_km", None):
            swath.append(float(p.swath_km))
        if getattr(p, "type", "") in ("imager", "optical_imager", "camera") and getattr(p, "fov_deg", None):
            fov.append(float(p.fov_deg))
            names.append(getattr(p, "name", ""))
    instruments = []
    for e in elements:
        if (e.get("subsystem_domain") or "") != "payload" or e.get("deleted_at"):
            continue
        p = _perf(e)
        if _num(p.get("gsd_m")):
            stated.append(_num(p.get("gsd_m")))
        if _num(p.get("swath_km")):
            swath.append(_num(p.get("swath_km")))
        if p.get("spectral_bands"):
            sb = p["spectral_bands"]
            bands.extend(sb if isinstance(sb, list) else [str(sb)])
        if p.get("fov_deg") and _num(p["fov_deg"]):
            fov.append(_num(p["fov_deg"]))
        kb = _kb(e).get("performance") or {}
        pitch = _num(p.get("pixel_pitch_um") or kb.get("pixel_pitch_um") or kb.get("pixel_size_um"))
        focal = _num(p.get("focal_length_mm") or kb.get("focal_length_mm"))
        if not focal:
            m = re.search(r"(\d+(?:\.\d+)?)\s*mm\b", str(e.get("name") or ""))
            focal = float(m.group(1)) if m else None
        if pitch and focal and e.get("element_type") == "component":
            instruments.append({"name": e.get("name"), "pixel_pitch_um": pitch, "focal_length_mm": focal,
                                "native_gsd_m": round(altitude_km * 1e3 * pitch * 1e-6 / (focal * 1e-3), 1)})
    native = [i["native_gsd_m"] for i in instruments]
    gsd = min(stated) if stated else (min(native) if native else None)
    sw = max(swath) if swath else (2 * altitude_km * math.tan(math.radians(max(fov) / 2)) if fov else None)
    return {"gsd_m": round(gsd, 1) if gsd else None,
            "gsd_source": "payload gsd_m" if stated else ("optics" if native else None),
            "finest_native_gsd_m": min(native) if native else None, "instruments": instruments,
            "swath_km": round(sw, 1) if sw else None, "spectral_bands": bands,
            "fov_deg": max(fov) if fov else None, "instrument_names": [n for n in names if n]}


# ───────────────────────────────────────────────────────── frequency assignments (W5.01)

def necessary_bandwidth_hz(rate_bps: float, modulation: str = "GMSK") -> float:
    """Necessary bandwidth for a narrow-band digital link: 1.3 x the channel rate for GMSK/BPSK
    (99 % power of GMSK BT 0.5 is about 1.04 Rb; 1.3 leaves room for Doppler pre-compensation
    residuals), rounded up to 0.5 kHz."""
    k = 1.3 if modulation.upper() in ("GMSK", "BPSK", "GFSK", "FSK") else 1.0
    bw = k * float(rate_bps)
    return math.ceil(bw / 500.0) * 500.0


def _slant_km(alt_km: float, el_deg: float) -> float:
    re_ = 6371.0
    s = math.sin(math.radians(el_deg))
    return -re_ * s + math.sqrt((re_ * s) ** 2 + (re_ + alt_km) ** 2 - re_ ** 2)


def _ttc(elements: list[dict]) -> tuple[dict, dict, dict]:
    """(TT&C subsystem performance, radio element, radio KB performance)."""
    sub, radio = {}, {}
    for e in _space(elements):
        if (e.get("subsystem_domain") or "") in ("ttc", "comms", "communications"):
            if e.get("element_type") == "subsystem":
                sub = _perf(e)
            elif e.get("element_type") == "component" and not radio and (
                    _kb(e).get("category") in ("transponder", "transceiver", "radio") or
                    re.search(r"radio|transceiver|transmitter|transponder", str(e.get("name")), re.I)):
                radio = e
    return sub, radio, (_kb(radio).get("performance") or {}) if radio else {}


def _station_key(name: Any) -> str:
    """Comparable station name: case-folded, without a "GS" / "ground station" prefix or suffix."""
    s = re.sub(r"\b(gs|ground station|earth station|station)\b", " ", str(name or "").lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def _case_for(cases: list[dict], direction: str, station: str) -> dict | None:
    """The link case (W4.04) that applies to ``station`` in ``direction``: a case named for that
    station first, else a case for every station (no station, or "all four sites", "all", "any");
    in each group the design case wins, then the display order. A case for another station is
    never used."""
    key = _station_key(station)
    own, shared = [], []
    for c in cases or []:
        if c.get("direction") != direction:
            continue
        ck = _station_key(c.get("station"))
        if ck and key and (ck == key or ck in key or key in ck):
            own.append(c)
        elif not ck or re.search(r"\b(all|any|every|each)\b", str(c.get("station") or ""), re.I):
            shared.append(c)
    for group in (own, shared):
        if group:
            return sorted(group, key=lambda c: (not c.get("is_design_case"), c.get("order") or 0))[0]
    return None


def _case_ref(c: dict | None) -> dict | None:
    """What a licensing document quotes from a link case."""
    if not c:
        return None
    r = c.get("results") or {}
    return {"id": c.get("id"), "name": c.get("name"), "station": c.get("station"),
            "is_design_case": bool(c.get("is_design_case")), "elevation_deg": c.get("elevation_deg"),
            "data_rate_bps": c.get("data_rate_bps"), "coding": c.get("coding"),
            "tx_power_w": c.get("tx_power_w"), "system_noise_temp_k": c.get("system_noise_temp_k"),
            "g_over_t_dbk": r.get("g_over_t_dbk"), "ebn0_db": r.get("ebn0_db"),
            "margin_db": c.get("margin_db") if c.get("margin_db") is not None else r.get("margin_db"),
            "slant_range_km": r.get("slant_range_km"), "eirp_dbw": r.get("eirp_dbw")}


#: assignment fields the licensing record may override per assignment id (``assignment_overrides``)
OVERRIDABLE = ("centre_frequency_mhz", "tx_power_w", "antenna_gain_dbi", "line_loss_db", "eirp_dbw", "polarisation",
               "antenna", "note", "emission_designator", "necessary_bandwidth_khz", "antenna_height_m")
_NUMERIC_OVERRIDES = ("centre_frequency_mhz", "tx_power_w", "antenna_gain_dbi", "line_loss_db", "eirp_dbw",
                      "necessary_bandwidth_khz", "antenna_height_m")


def _in_band(f: float | None, band: list[float]) -> bool:
    return f is not None and band[0] <= f <= band[1]


def frequency_assignments(study: Any, elements: list[dict], overrides: dict | None = None,
                          link_cases: list[dict] | None = None) -> list[dict]:
    """One assignment per transmitter / receiver, space and ground (W5.01, W5.04).

    Each earth station takes its transmit power, antenna gain and line loss from the named link
    case (W4.04, export section ``links.items``) for that station and direction (``_case_for``),
    else the band defaults; the space station takes the study's design link, else the downlink
    design case. The licensing record's ``assignment_overrides`` (by assignment id) win over both,
    and EIRP and PFD are recomputed from the overridden values (unless ``eirp_dbw`` itself is
    overridden)."""
    req = getattr(study, "requirements", None)
    link = getattr(req, "link", None)
    cons = getattr(req, "constraints", None) or {}
    alt = float(getattr(getattr(req, "orbit", None), "altitude_km", 500.0) or 500.0)
    sub, radio, kbp = _ttc(elements)
    p_radio = _perf(radio) if radio else {}
    cases = [c for c in (link_cases or []) if isinstance(c, dict)]
    dl_design = next((c for c in cases if c.get("direction") == "downlink" and c.get("is_design_case")), None) or {}
    ul_design = next((c for c in cases if c.get("direction") == "uplink" and c.get("is_design_case")), None) or {}

    def first(*vals):
        for v in vals:
            n = _num(v)
            if n is not None and n > 0:
                return n
        return None

    def any_num(*vals):
        for v in vals:
            n = _num(v)
            if n is not None:
                return n
        return None

    dl_band = cons.get("downlink_band_mhz") or [401.0, 402.0]
    ul_band = cons.get("uplink_band_mhz") or [449.75, 450.25]
    dl_f = first(getattr(link, "downlink_frequency_mhz", None), p_radio.get("downlink_frequency_mhz"),
                 sub.get("downlink_frequency_mhz"), dl_design.get("frequency_mhz"),
                 kbp.get("frequency_mhz")) or round(sum(dl_band) / 2, 3)
    if not _in_band(dl_f, dl_band):
        dl_f = 401.5 if dl_band == [401.0, 402.0] else round(sum(dl_band) / 2, 3)
    ul_f = first(getattr(link, "uplink_frequency_mhz", None), p_radio.get("uplink_frequency_mhz"),
                 sub.get("uplink_frequency_mhz"), ul_design.get("frequency_mhz"))
    if not _in_band(ul_f, ul_band):
        ul_f = round(sum(ul_band) / 2, 3)
    dl_rate = first(getattr(link, "downlink_rate_bps", None), _num(p_radio.get("data_rate_bps")),
                    (_num(sub.get("data_rate_kbps")) or 0) * 1e3, dl_design.get("data_rate_bps"),
                    kbp.get("data_rate_bps")) or 9600.0
    ul_rate = first(getattr(link, "uplink_rate_bps", None), p_radio.get("uplink_rate_bps"),
                    ul_design.get("data_rate_bps")) or 9600.0
    tx_w = first(getattr(link, "tx_power_w", None), p_radio.get("tx_power_w"), sub.get("tx_power_w"),
                 dl_design.get("tx_power_w"), (10 ** ((kbp.get("tx_power_dbm") or 30) / 10)) / 1000.0) or 1.0
    # a gain may be negative (a near-omni UHF antenna at -3 dBi): any number, not only positive ones
    sc_gain = any_num(getattr(link, "tx_antenna_gain_dbi", None), p_radio.get("antenna_gain_dbi"),
                      sub.get("antenna_gain_dbi"), dl_design.get("tx_antenna_gain_dbi"))
    sc_gain = 0.0 if sc_gain is None else sc_gain
    line_loss = first(getattr(link, "tx_losses_db", None), dl_design.get("tx_losses_db")) or 1.0
    gs_gain = first(getattr(link, "rx_antenna_gain_dbi", None)) or 15.0
    mod = "GMSK"
    m = str(sub.get("modulation") or p_radio.get("modulation") or "").upper()
    if "BPSK" in m and "GMSK" not in m:
        mod = "BPSK"

    def entry(aid: str, *, station: str, side: str, direction: str, freq: float, band: list[float],
              rate: float, power_w: float | None, gain_dbi: float, loss_db: float, pol: str, ant: str,
              note: str = "") -> dict:
        svc = spectrum.service_for(freq, "space-to-Earth" if direction == "downlink" else "Earth-to-space")
        bw = necessary_bandwidth_hz(rate, mod)
        return {"id": aid, "station": station, "side": side, "direction": direction,
                "transmits": (side == "space") == (direction == "downlink"),
                "centre_frequency_mhz": round(freq, 4), "band_mhz": list(band),
                "necessary_bandwidth_khz": round(bw / 1e3, 1),
                "emission_designator": _designator(bw, mod), "modulation": mod, "rate_bps": rate,
                "tx_power_w": power_w, "antenna": ant, "antenna_gain_dbi": gain_dbi, "polarisation": pol,
                "line_loss_db": loss_db, "service": svc["service"], "allocation": svc["allocation"],
                "footnotes": svc["footnotes"], "coordination": svc["coordination"], "note": note,
                "basis": "design"}

    out = [
        entry("SS-TX-DL", station="space station", side="space", direction="downlink", freq=dl_f, band=dl_band,
              rate=dl_rate, power_w=tx_w, gain_dbi=sc_gain, loss_db=line_loss, pol="linear",
              ant="UHF deployable dipole/monopole (near-omnidirectional)",
              note="Avoid 401.4-401.7 MHz (NGSO data-collection systems, ITU-R SA.2045)."),
        entry("SS-RX-UL", station="space station", side="space", direction="uplink", freq=ul_f, band=ul_band,
              rate=ul_rate, power_w=None, gain_dbi=sc_gain, loss_db=line_loss, pol="linear",
              ant="UHF deployable dipole/monopole (near-omnidirectional)",
              note="Radio receive edge at 450.25 MHz to be confirmed with the supplier."),
    ]
    if dl_design:
        out[0]["link_case"] = _case_ref(dl_design)
    if ul_design:
        out[1]["link_case"] = _case_ref(ul_design)
    for st in stations(elements):
        key = re.sub(r"[^A-Z0-9]+", "", str(st["name"]).upper().replace("GS ", ""))[:6] or "GS"
        ulc = _case_for(cases, "uplink", st["name"]) or {}
        dlc = _case_for(cases, "downlink", st["name"]) or {}
        uf, df = first(ulc.get("frequency_mhz")), first(dlc.get("frequency_mhz"))
        tx = entry(f"ES-{key}-TX-UL", station=st["name"], side="earth", direction="uplink",
                   freq=uf if _in_band(uf, ul_band) else ul_f, band=ul_band,
                   rate=first(ulc.get("data_rate_bps")) or ul_rate, power_w=first(ulc.get("tx_power_w")) or 25.0,
                   gain_dbi=any_num(ulc.get("tx_antenna_gain_dbi"), gs_gain),
                   loss_db=any_num(ulc.get("tx_losses_db"), 0.3),
                   pol="circular (RHCP)", ant="450 MHz circularly polarised Yagi on az/el rotator",
                   note="Protect land-mobile users in 450-470 MHz (Canadian footnote C23).")
        rx = entry(f"ES-{key}-RX-DL", station=st["name"], side="earth", direction="downlink",
                   freq=df if _in_band(df, dl_band) else dl_f, band=dl_band,
                   rate=first(dlc.get("data_rate_bps")) or dl_rate, power_w=None,
                   gain_dbi=any_num(dlc.get("rx_antenna_gain_dbi"), gs_gain),
                   loss_db=any_num(dlc.get("rx_losses_db"), 0.3),
                   pol="circular (RHCP)", ant="401 MHz circularly polarised Yagi on az/el rotator")
        for row, c in ((tx, ulc), (rx, dlc)):
            row["station_lat"], row["station_lon"] = st["lat"], st["lon"]
            row["min_elevation_deg"] = st.get("min_elevation_deg")
            if c:
                row["link_case"] = _case_ref(c)
                row["basis"] = "link case"
                if row["direction"] == "downlink" and c.get("system_noise_temp_k"):
                    row["system_noise_temp_k"] = c["system_noise_temp_k"]
        out += [tx, rx]
    # VHF fallback uplink, listed but not filed unless selected
    vhf = spectrum.band_by_name("VHF space operation uplink (fallback)")
    if vhf is not None:
        fb = entry("SS-RX-UL-VHF", station="space station", side="space", direction="uplink",
                   freq=149.0, band=[vhf.freq_min_mhz, vhf.freq_max_mhz], rate=ul_rate, power_w=None,
                   gain_dbi=0.0, loss_db=line_loss, pol="linear", ant="VHF monopole (if fitted)",
                   note="Fallback only: filed if the 450 MHz agreement under RR No. 9.21 cannot be obtained.")
        fb["fallback"] = True
        out.append(fb)
    for row in out:
        ov = (overrides or {}).get(row["id"]) or {}
        for k, v in ov.items():
            if k in OVERRIDABLE and v is not None and v != "":
                val = _num(v) if k in _NUMERIC_OVERRIDES else v
                cur = row.get(k)
                same = (val == cur) if k not in _NUMERIC_OVERRIDES else (
                    val is not None and _num(cur) is not None and abs(val - _num(cur)) < 1e-9)
                row[k] = val
                row.setdefault("overridden", []).append(k)       # the record carries the field
                if not same or k == "eirp_dbw":
                    row.setdefault("changed", []).append(k)
        # a value the link-budget tool synced from this station's case (equal to the derived one)
        # is recorded but does not change the basis: only a differing value makes it the record's
        if row.get("changed"):
            row["basis"] = "licensing record"
        _radiated(row, alt)
    return out


def _radiated(row: dict, alt_km: float) -> None:
    """EIRP of a transmitting assignment (and, for the space station, the PFD at 5 deg elevation)
    from its power, antenna gain and line loss, or the overridden EIRP."""
    if not row["transmits"]:
        return
    p, g = _num(row.get("tx_power_w")), _num(row.get("antenna_gain_dbi"))
    loss = _num(row.get("line_loss_db")) or 0.0
    if "eirp_dbw" in (row.get("overridden") or []):
        eirp = _num(row["eirp_dbw"])
    elif p and p > 0 and g is not None:
        eirp = round(10 * math.log10(p) + g - loss, 1)
    else:
        return
    if eirp is None:
        return
    row["eirp_dbw"] = eirp
    if row["side"] == "space":
        from .regulatory import compute_pfd_dbw_m2
        bw = (_num(row.get("necessary_bandwidth_khz")) or 4.0) * 1e3
        pfd = compute_pfd_dbw_m2(eirp, alt_km, 5.0)
        row["pfd_5deg_dbw_m2"] = pfd
        row["pfd_5deg_dbw_m2_4khz"] = round(pfd - 10 * math.log10(max(bw, 4000.0) / 4000.0), 1)
        row["slant_range_5deg_km"] = round(_slant_km(alt_km, 5.0), 0)


def _designator(bw_hz: float, mod: str) -> str:
    from .regulatory import compute_emission_designator
    return compute_emission_designator(bw_hz, mod)


# ───────────────────────────────────────────────────────────────── disposal (W5.02)

def disposal_device(elements: list[dict], record_disposal: dict | None = None):
    """The drag sail of the study as a ``DragDevice`` (None when the study has none)."""
    from spacecdf_common.physics.disposal import DragDevice
    sail = None
    timer = None
    for e in _space(elements):
        kb = _kb(e)
        cat = (kb.get("category") or "").lower()
        name = str(e.get("name") or "")
        if cat in ("deorbit_device", "drag_sail") or re.search(r"drag sail|deorbit sail|deorbiting sail", name, re.I):
            if sail is None and e.get("element_type") != "subsystem":
                sail = e
        if re.search(r"timer", name, re.I) and re.search(r"deorbit|sail|disposal", name, re.I):
            timer = e
    if sail is None:
        return None
    p, kbp = _perf(sail), (_kb(sail).get("performance") or {})
    area = _num(p.get("deployed_area_m2") or p.get("area_m2") or kbp.get("deployed_area_m2") or kbp.get("area_m2"))
    if area is None:
        m = re.search(r"(\d+(?:\.\d+)?)\s*m2|(\d+(?:\.\d+)?)\s*m²", str(sail.get("name")))
        area = float(m.group(1) or m.group(2)) if m else 0.0
    eff = _num(p.get("effective_area_m2") or kbp.get("effective_area_m2"))
    rd = record_disposal or {}
    circuits = rd.get("independent_circuits")
    if circuits is None and timer is not None:
        m = re.search(r"(\d)\s*release circuits?", str(timer.get("name")), re.I)
        circuits = int(m.group(1)) if m else 2
    trig = list(rd.get("trigger") or [])
    if not trig:
        trig = ["ground command"] + (["independent timer (OBC-independent)", "battery under-voltage"] if timer else [])
    life = None
    if "config_a" in str(kbp.get("independent_power", "")).lower() or "config A" in str(sail.get("name")):
        life = 2.0
    return DragDevice(
        name=str(sail.get("name")), deployed_area_m2=float(area or 0.0), effective_area_m2=eff,
        mass_kg=float(sail.get("mass_kg") or 0.0) * int(sail.get("quantity") or 1), trigger=trig,
        deployment_time_s=rd.get("deployment_time_s"),
        mechanism_reliability=float(rd.get("mechanism_reliability") or 0.97),
        circuit_reliability=float(rd.get("circuit_reliability") or 0.90),
        independent_circuits=int(circuits or 1),
        independent_timer_days=rd.get("independent_timer_days") or (90 if timer else None),
        stowed_life_years=life, source=str(sail.get("kb_component_id") or "element"))


def _smallest_dimension_cm(form_factor: str | None) -> float | None:
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*U", str(form_factor or ""))
    if not m:
        return None
    return 10.0     # every CubeSat form factor has a 10 cm side (1U face)


def disposal_analysis(study: Any, elements: list[dict], rollup: dict, record: dict | None = None) -> dict:
    """The W5.02 disposal analysis as a JSON-ready dict (with the stored DRAMA/DAS evidence)."""
    from spacecdf_common.physics.disposal import assess_disposal, year_of
    req = getattr(study, "requirements", None)
    orb = getattr(req, "orbit", None)
    alt = float(getattr(orb, "altitude_km", 500.0) or 500.0)
    ecc = float(getattr(orb, "eccentricity", 0.0) or 0.0)
    rec = record or {}
    rd = rec.get("disposal") or {}
    mass = rollup.get("mass") or {}
    basis = rd.get("mass_basis") or "allocation"
    alloc = _num(getattr(req, "target_mass_kg", None)) or _num(mass.get("limit_kg"))
    cands = {"cbe": _num(mass.get("cbe_kg")), "with_margin": _num(mass.get("with_system_margin_kg")),
             "allocation": alloc}
    m = cands.get(basis) or max([v for v in cands.values() if v] or [4.0])
    if basis == "allocation" and not cands.get("allocation"):
        basis = "with_margin" if cands.get("with_margin") else "cbe"
    labels = {"cbe": "current best estimate", "with_margin": "with maturity and system margins",
              "allocation": "mass allocation (conservative: a heavier satellite decays more slowly)"}
    dev = disposal_device(elements, rd)
    has_prop = any((e.get("subsystem_domain") == "propulsion" and e.get("element_type") == "component" and
                    re.search(r"thruster|propulsion|engine", str(e.get("name")), re.I)) for e in _space(elements))
    launch = rec.get("launch", {}).get("date") or getattr(req, "launch_date_target", None)
    ops = float(getattr(orb, "mission_duration_years", None) or getattr(req, "design_lifetime_years", 3.0) or 3.0)
    a = assess_disposal(altitude_km=alt, eccentricity=ecc, mass_kg=m, mass_basis=labels.get(basis, basis),
                        launch_year=year_of(launch), operations_years=ops, device=dev, has_propulsion=has_prop,
                        smallest_dimension_cm=_smallest_dimension_cm(rollup.get("form_factor")))
    out = a.as_dict()
    # the CBE case alongside (teaching: how much the mass basis matters)
    if basis != "cbe" and cands.get("cbe") and dev is not None:
        b = assess_disposal(altitude_km=alt, eccentricity=ecc, mass_kg=cands["cbe"], mass_basis=labels["cbe"],
                            launch_year=year_of(launch), operations_years=ops, device=dev,
                            has_propulsion=has_prop, smallest_dimension_cm=10.0)
        out["cbe_case"] = {"mass_kg": b.mass_kg, "lifetime_with_sail_y": b.lifetime_with_sail_y,
                           "lifetime_without_sail_y": b.lifetime_without_sail_y}
    out["launch_date"] = launch or None
    out["operations_years"] = ops
    out["evidence"] = list(rec.get("evidence") or [])
    if out["evidence"]:
        ev = out["evidence"][-1]
        out["evidence_summary"] = (f"{ev.get('tool')} {ev.get('version') or ''}".strip() +
                                   (f": lifetime {ev['lifetime_years']} y" if ev.get("lifetime_years") else "") +
                                   (f", Pc {ev['collision_probability']}" if ev.get("collision_probability") else ""))
    return out


# ───────────────────────────────────────────────────────────────── collector (W5.06)

def _filing_dates(filings: list[dict], launch: str | None) -> list[dict]:
    from spacecdf_common.physics.disposal import year_of
    ly = year_of(launch, default=0.0) if launch else 0.0
    for f in filings:
        if ly and f.get("start_months") is not None:
            t = ly + f["start_months"] / 12.0
            y = int(t)
            mth = min(12, max(1, int(round((t - y) * 12 + 0.5))))
            f["start_by"] = f"{y:04d}-{mth:02d}"
        else:
            f["start_by"] = ""
    return filings


async def collect(ctx) -> dict:
    """Body of the export-context section ``licensing`` (W5.01, W5.03, W5.06)."""
    rec, version = await load_record(ctx.study_id)
    study, els = ctx.study, ctx.elements
    rollup = ctx.sections.get("rollup") or {}
    if not rollup:
        try:
            from . import rollup as _ru
            rollup = (await _ru.compute(ctx.study_id, gate=ctx.gate)).as_dict()
        except Exception:  # noqa: BLE001
            rollup = {}
    req = getattr(study, "requirements", None)
    orb = getattr(req, "orbit", None)
    alt = float(getattr(orb, "altitude_km", 500.0) or 500.0)
    launch = (rec.get("launch") or {}).get("date") or getattr(req, "launch_date_target", None)
    filings = _filing_dates(filings_with_defaults(rec.get("filings"), ctx.lang), launch)
    counts: dict[str, int] = {}
    for f in filings:
        counts[f["status"]] = counts.get(f["status"], 0) + 1
    links = ctx.sections.get("links") or {}
    link_items = links.get("items")
    if link_items is None:
        try:
            from ..routers.link_budgets import list_cases
            link_items = await list_cases(ctx.study_id)
        except Exception:  # noqa: BLE001 — no link cases: band defaults
            link_items = []
    try:
        disposal = disposal_analysis(study, els, rollup, rec) if study is not None else {}
    except Exception as exc:  # noqa: BLE001
        disposal = {"error": f"{type(exc).__name__}: {exc}"}
    return {
        "status": "ok", "owner": "L", "work_package": "W5.01/W5.03/W5.06", "version": version,
        "applicant": rec.get("applicant") or {}, "contacts": rec.get("contacts") or [],
        "participants": rec.get("participants") or [], "affiliates": rec.get("affiliates") or [],
        "itu_network_name": rec.get("itu_network_name") or "",
        "cdpp": rec.get("cdpp") or {}, "data_policy": rec.get("data_policy") or {},
        "launch": {**(rec.get("launch") or {}), "date": launch or "",
                   "vehicle": (rec.get("launch") or {}).get("vehicle") or getattr(req, "launch_vehicle", None) or ""},
        "orbit": {"altitude_km": alt, "inclination_deg": getattr(orb, "inclination_deg", None),
                  "eccentricity": getattr(orb, "eccentricity", 0.0),
                  **node_times(getattr(orb, "ltan", None))},
        "sensor": _payload_info(study, els, alt),
        "stations": stations(els),
        "assignments": frequency_assignments(study, els, rec.get("assignment_overrides"), link_items)
        if study is not None else [],
        "disposal": disposal,
        "evidence": rec.get("evidence") or [],
        "filings": filings, "filing_counts": counts,
        "notes": rec.get("notes") or "",
        "to_be_confirmed": TO_BE_CONFIRMED,
    }


#: statements the generated documents must not assert as fact (research flags them unverified)
TO_BE_CONFIRMED: list[dict] = [
    {"id": "TBC-01", "text": "Number of the ISED decision on space debris mitigation (April 2026): SMSE-009-26 "
                             "(ISED page) or SMSE-005-26 (secondary source)."},
    {"id": "TBC-02", "text": "Canadian Table of Frequency Allocations: rows for 401-402, 438-450 and 450-455 MHz "
                             "re-checked in the 2026 edition (research parsed the 2018 edition)."},
    {"id": "TBC-03", "text": "Radio receive edge 450.25 MHz with the transceiver supplier."},
    {"id": "TBC-04", "text": "ECCN / ECL entry of the SWIR (InGaAs) camera from the vendor (likely 6A003.b.4.b)."},
    {"id": "TBC-05", "text": "Whether a ~58 m SWIR / ~32 m NIR system qualifies for the RSSSA multi-stage (Annex D) "
                             "process: ask Global Affairs Canada."},
    {"id": "TBC-06", "text": "RSSSA guide section numbering against the guide in force (structure follows the "
                             "research summary of the guide)."},
    {"id": "TBC-07", "text": "Earth-station licensing procedure (CPC-2-6-01) and the antenna-siting exemption "
                             "(CPC-2-0-03) for each site."},
]
