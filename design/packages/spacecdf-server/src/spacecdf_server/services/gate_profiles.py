"""SpaceCDF — gate profiles (configs/gate_profiles.yaml).

A study holds the review gates of its *profile*: full ECSS (MDR → PRR → SRR → PDR → CDR, the
default, ruling 1 carried on to CDR in Nov 2026), ESA IOD CubeSat (concept review → PDR → CDR),
C2O three gates (MDR → PRR+SRR → PDR) or the NASA vocabulary skin (MCR → SRR → MDR/SDR → PDR → CDR).
A profile covers the canonical gates in order from MDR to at least PDR; CDR, the qualification
and acceptance reviews (QR, AR) and the flight readiness review (FRR) are optional (Nov 2026: the
PI's profile is full ECSS plus FRR).

Each profile gate ``covers`` canonical gates (the phases of gate_exit_criteria.yaml):
its checklist is the union of their criteria, the decisions due by it are those of every
canonical gate up to the last one it covers, and its budgets use the margin-ladder step of
``margin_gate`` (default: the last canonical gate covered).

Pure functions over the cached YAML; no I/O beyond reading the file.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

CANONICAL = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")
#: the canonical gates every profile must cover (CDR and later are optional: the C2O spine stops at PDR)
REQUIRED = ("mdr", "prr", "srr", "pdr")
#: canonical gates after CDR: no step of the margin ladder of their own (they use the CDR step)
POST_CDR = ("qr", "ar", "frr")


def _file() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "configs" / "gate_profiles.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("configs/gate_profiles.yaml not found")


@lru_cache(maxsize=4)
def _load(path: str, stamp: int) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def load() -> dict[str, Any]:
    try:
        p = _file()
        return _load(str(p), p.stat().st_mtime_ns)
    except (FileNotFoundError, OSError, yaml.YAMLError) as exc:
        logger.warning("gate_profiles.yaml failed to load: %s", exc)
        return {"profiles": {}, "steps": {}, "products": []}


def validate(data: dict[str, Any] | None = None) -> list[str]:
    """Structural checks: every profile covers the canonical gates once, in order, from MDR to
    at least PDR (CDR, QR, AR and FRR optional, in that order)."""
    data = data if data is not None else load()
    errs: list[str] = []
    profiles = data.get("profiles") or {}
    if data.get("default_profile") not in profiles:
        errs.append("default_profile must name a profile")
    steps = data.get("steps") or {}
    for pid, p in profiles.items():
        for lang in ("en", "fr"):
            if not ((p.get("label") or {}).get(lang)):
                errs.append(f"profiles.{pid}.label.{lang} missing")
        covered: list[str] = []
        ids: set[str] = set()
        for g in p.get("gates") or []:
            if g.get("id") in ids:
                errs.append(f"profiles.{pid}: duplicate gate id {g.get('id')}")
            ids.add(g.get("id"))
            for lang in ("en", "fr"):
                if not ((g.get("name") or {}).get(lang)):
                    errs.append(f"profiles.{pid}.{g.get('id')}.name.{lang} missing")
            for c in g.get("covers") or []:
                if c not in CANONICAL:
                    errs.append(f"profiles.{pid}.{g.get('id')}: unknown canonical gate {c}")
                covered.append(c)
            mg = g.get("margin_gate")
            if mg is not None and mg not in (*CANONICAL, "cdr"):
                errs.append(f"profiles.{pid}.{g.get('id')}: bad margin_gate {mg}")
        if covered != list(CANONICAL[: len(covered)]) or len(covered) < len(REQUIRED):
            errs.append(f"profiles.{pid}: gates must cover {list(REQUIRED)} (then optionally cdr, qr, ar, frr) "
                        f"once, in order (got {covered})")
    for step, label in steps.items():
        if not (isinstance(label, dict) and label.get("en") and label.get("fr")):
            errs.append(f"steps.{step}: needs en and fr")
    return errs


# ─── lookups ──────────────────────────────────────────────────────────────

def default_profile_id() -> str:
    return load().get("default_profile") or "full_ecss"


def profile_ids() -> list[str]:
    return list((load().get("profiles") or {}).keys())


def get_profile(profile_id: str | None) -> dict[str, Any]:
    """The profile (with its id), falling back to the default for unknown ids."""
    profiles = load().get("profiles") or {}
    pid = profile_id if profile_id in profiles else default_profile_id()
    return {"id": pid, **(profiles.get(pid) or {"gates": []})}


def legacy_gate_id(gate_id: str | None) -> str:
    g = (gate_id or "").strip().lower()
    return (load().get("legacy_gate_ids") or {}).get(g, g)


def gate_of(profile: dict[str, Any], gate_id: str | None) -> dict[str, Any] | None:
    """A profile gate by id, short label (case-insensitive), legacy id (mcr) or covered canonical id."""
    if not gate_id:
        return None
    raw = gate_id.strip().lower()
    g = legacy_gate_id(raw)
    gates = profile.get("gates") or []
    for cand in (raw, g):
        for x in gates:
            if x.get("id") == cand or str(x.get("short", "")).lower() == cand:
                return x
    for x in gates:   # a canonical gate merged into a profile gate (IOD: mdr → cr)
        if g in (x.get("covers") or []):
            return x
    return None


def covering_gate(profile: dict[str, Any], canonical: str) -> dict[str, Any] | None:
    for x in profile.get("gates") or []:
        if canonical in (x.get("covers") or []):
            return x
    return None


def margin_gate(gate: dict[str, Any]) -> str:
    covers = gate.get("covers") or []
    mg = gate.get("margin_gate") or (covers[-1] if covers else "mdr")
    return "cdr" if mg in POST_CDR else mg


def due_canonical(gate: dict[str, Any]) -> list[str]:
    """Canonical gates whose decisions must be recorded by ``gate`` (cumulative)."""
    covers = gate.get("covers") or []
    if not covers:
        return []
    last = max(CANONICAL.index(c) for c in covers if c in CANONICAL)
    return list(CANONICAL[: last + 1])


def gate_index(profile: dict[str, Any], gate_id: str) -> int:
    for i, x in enumerate(profile.get("gates") or []):
        if x.get("id") == gate_id:
            return i
    return -1


def step_label(step: str | None) -> dict[str, str] | None:
    if not step:
        return None
    lab = (load().get("steps") or {}).get(step)
    return dict(lab) if isinstance(lab, dict) else None


def products_baselined(gate: dict[str, Any]) -> list[dict[str, Any]]:
    """Products that reach B (baselined) at one of the canonical gates ``gate`` covers."""
    covers = set(gate.get("covers") or [])
    out = []
    for p in load().get("products") or []:
        mat = p.get("maturity") or {}
        if any(mat.get(c) == "B" for c in covers):
            out.append({"id": p["id"], "label": p.get("label"), "owner_seat": p.get("owner_seat")})
    return out


def public_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """The profile as the API returns it (labels in both languages)."""
    return {
        "id": profile["id"],
        "label": profile.get("label"),
        "description": profile.get("description"),
        "source": profile.get("source"),
        "skin": bool(profile.get("skin")),
        "default": profile["id"] == default_profile_id(),
        "gates": [{"id": g["id"], "short": g.get("short", g["id"].upper()), "name": g.get("name"),
                   "covers": list(g.get("covers") or []), "margin_gate": margin_gate(g)}
                  for g in profile.get("gates") or []],
    }


def list_profiles() -> list[dict[str, Any]]:
    return [public_profile(get_profile(pid)) for pid in profile_ids()]
