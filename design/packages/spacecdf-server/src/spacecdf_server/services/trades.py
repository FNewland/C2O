"""SpaceCDF — trade studies (W6.01, Nov 2026).

A study holds any number of trade studies, keyed by a trade id (``T-01``, ``T-02`` ...), in
``study.trade_records``::

    {"T-01": {"state": <trade>, "version": 3}, "T-02": {...}}

Until Nov 2026 the study held ONE Pugh record under the key ``pugh``; it is read as ``T-01``
(``normalise_records``) and the old ``/trades/pugh`` route still answers with it.

A trade (``state``)::

    id, title, seat, level, status ("open" | "decided"), method ("pugh_weighted")
    options      [option name, ...]            the datum is one of them (index ``datum``)
    criteria     [criterion name, ...]
    comparisons  {"A|B": 1 | 0.5 | 0}         pairwise: 1 = A more important, 0.5 equal, 0 = B
    weights      {criterion: w}               typed weights; used only when ``weights_mode`` is
                                              "direct" (otherwise derived from ``comparisons``)
    scores       {option: {criterion: -2..+2}} against the datum (the datum scores 0)
    thresholds   {criterion: minimum score}   an option scoring below it is not acceptable
    evidence, note
    decision     {selected, rationale, decided_at, decided_by_seat, record_id}
    links        {decision_record, requirements: [codes], risks: [ids], elements: [ids]}

``evaluate(state)`` gives the weights, the weighted and unweighted totals, the threshold
violations, the ranking and winner (the datum counts as 0), and a weight sensitivity: for each
criterion the smallest change of its weight (the others rescaled to keep the sum at 1) that
changes the winner. Pure functions; the routes are in routers/trades.py.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

LEGACY_KEY = "pugh"
FIRST_ID = "T-01"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,23}$")
SCORE_MIN, SCORE_MAX = -2, 2
#: weight change (fraction of the total) inside which a winner that does not change is "robust"
ROBUST_DELTA = 0.10
MAX_OPTIONS = 12
MAX_CRITERIA = 15
TEXT_LIMIT = 4000
STATUSES = ("open", "decided")


# ─── records ─────────────────────────────────────────────────────────────

def normalise_records(recs: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """The study's trade records with the legacy single Pugh record read as ``T-01``."""
    out: dict[str, dict[str, Any]] = {}
    for k, v in dict(recs or {}).items():
        if not isinstance(v, dict):
            continue
        out[k] = v
    if LEGACY_KEY in out:
        legacy = out.pop(LEGACY_KEY)
        if FIRST_ID not in out:
            st = clean_state({**(legacy.get("state") or {}), "id": FIRST_ID}, FIRST_ID)
            out[FIRST_ID] = {"state": st, "version": int(legacy.get("version") or 0)}
    return dict(sorted(out.items(), key=lambda kv: _id_key(kv[0])))


def _id_key(tid: str) -> tuple:
    m = re.match(r"^([A-Za-z-]*?)(\d+)$", tid)
    return (m.group(1), int(m.group(2)), tid) if m else (tid, 0, tid)


def resolve_id(tid: str) -> str:
    """``pugh`` (the old single record) is ``T-01``."""
    return FIRST_ID if tid == LEGACY_KEY else tid


def next_id(recs: dict[str, Any]) -> str:
    n = 0
    for k in recs:
        m = re.match(r"^T-(\d+)$", k)
        if m:
            n = max(n, int(m.group(1)))
    return f"T-{n + 1:02d}"


# ─── cleaning ────────────────────────────────────────────────────────────

def _text(v: Any, limit: int = TEXT_LIMIT) -> str:
    return str(v if v is not None else "").strip()[:limit]


def _names(raw: Any, limit: int) -> list[str]:
    out: list[str] = []
    for x in raw or []:
        name = x.get("name") if isinstance(x, dict) else x
        name = _text(name, 200)
        if name and name not in out:
            out.append(name)
    return out[:limit]


def _num(v: Any, default: float | None = None) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    return f if f == f else default   # NaN → default


def clean_state(raw: dict[str, Any] | None, tid: str) -> dict[str, Any]:
    """A trade state from client or file data. Tolerates the legacy Pugh record (criteria as
    ``{"id", "name", "weight"}``, the datum as an option name, scores keyed by criterion id)."""
    raw = dict(raw or {})
    crit_raw = raw.get("criteria") or []
    criteria = _names(crit_raw, MAX_CRITERIA)
    by_cid = {str(c.get("id")): _text(c.get("name"), 200) for c in crit_raw if isinstance(c, dict) and c.get("id")}
    typed_w = {_text(c.get("name"), 200): _num(c.get("weight"), 0.0) for c in crit_raw
               if isinstance(c, dict) and c.get("weight") is not None}
    if isinstance(crit_raw, dict):     # {name: weight} (trades.yaml)
        criteria = _names(list(crit_raw.keys()), MAX_CRITERIA)
        typed_w = {k: _num(v, 0.0) for k, v in crit_raw.items()}
    options = _names(raw.get("options"), MAX_OPTIONS)
    datum = raw.get("datum", 0)
    if isinstance(datum, str):
        datum = options.index(datum) if datum in options else 0
    try:
        datum = int(datum)
    except (TypeError, ValueError):
        datum = 0
    if not 0 <= datum < max(len(options), 1):
        datum = 0
    scores: dict[str, dict[str, float]] = {}
    for opt, row in dict(raw.get("scores") or {}).items():
        if opt not in options or not isinstance(row, dict):
            continue
        clean_row = {}
        for c, s in row.items():
            name = c if c in criteria else by_cid.get(str(c))
            v = _num(s)
            if name in criteria and v is not None:
                clean_row[name] = max(SCORE_MIN, min(SCORE_MAX, v))
        scores[opt] = clean_row
    comparisons: dict[str, float] = {}
    for k, v in dict(raw.get("comparisons") or {}).items():
        a, _, b = str(k).partition("|")
        f = _num(v)
        if a in criteria and b in criteria and a != b and f is not None:
            comparisons[f"{a}|{b}"] = max(0.0, min(1.0, f))
    weights = {c: max(0.0, _num(w, 0.0) or 0.0) for c, w in dict(raw.get("weights") or typed_w or {}).items()
               if c in criteria}
    mode = raw.get("weights_mode")
    if mode not in ("pairwise", "direct"):
        mode = "pairwise" if comparisons or not weights else "direct"
    thresholds = {}
    for c, v in dict(raw.get("thresholds") or {}).items():
        f = _num(v)
        if c in criteria and f is not None:
            thresholds[c] = max(SCORE_MIN, min(SCORE_MAX, f))
    links_raw = dict(raw.get("links") or {})
    links = {
        "decision_record": _text(links_raw.get("decision_record") or raw.get("decision_record"), 40),
        "requirements": _names(links_raw.get("requirements"), 200),
        "risks": _names(links_raw.get("risks"), 100),
        "elements": _names(links_raw.get("elements"), 100),
    }
    dec_raw = raw.get("decision") if isinstance(raw.get("decision"), dict) else {}
    decision = {k: _text(dec_raw.get(k), TEXT_LIMIT if k == "rationale" else 200)
                for k in ("selected", "rationale", "decided_at", "decided_by_seat", "record_id") if dec_raw.get(k)}
    if decision.get("selected") and decision["selected"] not in options:
        decision.pop("selected")
    status = raw.get("status") if raw.get("status") in STATUSES else ("decided" if decision.get("selected") else "open")
    return {
        "id": tid,
        "title": _text(raw.get("title"), 300),
        "seat": _text(raw.get("seat"), 40),
        "level": _text(raw.get("level"), 120),
        "status": status,
        "method": "pugh_weighted",
        "options": options,
        "datum": datum,
        "criteria": criteria,
        "comparisons": comparisons,
        "weights_mode": mode,
        "weights": weights,
        "scores": scores,
        "thresholds": thresholds,
        "evidence": _text(raw.get("evidence")),
        "note": _text(raw.get("note")),
        "decision": decision,
        "links": links,
    }


# ─── evaluation ──────────────────────────────────────────────────────────

def pairwise_weights(criteria: list[str], comparisons: dict[str, float]) -> dict[str, float]:
    """Row sums of the pairwise matrix, normalised (frontend ``workbench/pairwise.ts``): an
    untouched pair counts as equal (0.5)."""
    raw: dict[str, float] = {}
    for c in criteria:
        s = 0.0
        for o in criteria:
            if o == c:
                continue
            v = comparisons.get(f"{c}|{o}")
            r = comparisons.get(f"{o}|{c}")
            s += v if v is not None else (1 - r) if r is not None else 0.5
        raw[c] = max(s, 0.0)
    total = sum(raw.values())
    n = len(criteria)
    return {c: (raw[c] / total if total > 0 else (1 / n if n else 0.0)) for c in criteria}


def weights_of(state: dict[str, Any]) -> dict[str, float]:
    criteria = state.get("criteria") or []
    if state.get("weights_mode") == "direct" and state.get("weights"):
        w = {c: float((state.get("weights") or {}).get(c, 0.0)) for c in criteria}
        total = sum(w.values())
        if total > 0:
            return {c: v / total for c, v in w.items()}
    return pairwise_weights(criteria, state.get("comparisons") or {})


def _totals(state: dict[str, Any], weights: dict[str, float]) -> list[dict[str, Any]]:
    out = []
    datum = state.get("datum", 0)
    thr = state.get("thresholds") or {}
    for i, opt in enumerate(state.get("options") or []):
        row = (state.get("scores") or {}).get(opt) or {}
        if i == datum:
            sc = {c: 0.0 for c in state.get("criteria") or []}
        else:
            sc = {c: float(row.get(c, 0.0)) for c in state.get("criteria") or []}
        weighted = sum(sc[c] * weights.get(c, 0.0) for c in sc)
        below = [c for c, m in thr.items() if sc.get(c, 0.0) < m]
        out.append({"option": opt, "datum": i == datum, "weighted": round(weighted, 4),
                    "unweighted": round(sum(sc.values()), 4), "below_threshold": below,
                    "acceptable": not below})
    return out


def _winner(totals: list[dict[str, Any]]) -> str | None:
    pool = [t for t in totals if t["acceptable"]] or totals
    if not pool:
        return None
    best = max(t["weighted"] for t in pool)
    # ties: the datum first (no change without a reason), then the option order
    tied = [t for t in pool if abs(t["weighted"] - best) < 1e-9]
    return next((t["option"] for t in tied if t["datum"]), tied[0]["option"])


def _shifted(weights: dict[str, float], crit: str, delta: float) -> dict[str, float] | None:
    w0 = weights.get(crit, 0.0)
    w1 = w0 + delta
    if w1 < 0 or w1 > 1:
        return None
    rest = 1 - w0
    out = {}
    for c, w in weights.items():
        if c == crit:
            out[c] = w1
        else:
            out[c] = (w / rest * (1 - w1)) if rest > 0 else (1 - w1) / max(len(weights) - 1, 1)
    return out


def sensitivity(state: dict[str, Any], weights: dict[str, float], winner: str | None) -> list[dict[str, Any]]:
    """Per criterion: the smallest weight change (in points of the total, either sign) that
    changes the winner, and the new winner; ``None`` when no change within [0, 1] does."""
    out = []
    steps = [i / 100 for i in range(1, 101)]
    for c in state.get("criteria") or []:
        found = None
        for d in steps:
            for sign in (1, -1):
                w = _shifted(weights, c, sign * d)
                if w is None:
                    continue
                win = _winner(_totals(state, w))
                if win != winner:
                    found = {"delta": round(sign * d, 2), "new_weight": round(w[c], 3), "new_winner": win}
                    break
            if found:
                break
        out.append({"criterion": c, "weight": round(weights.get(c, 0.0), 4),
                    "flip": found, "robust": found is None or abs(found["delta"]) > ROBUST_DELTA + 1e-9})
    return out


def evaluate(state: dict[str, Any]) -> dict[str, Any]:
    weights = weights_of(state)
    totals = _totals(state, weights)
    winner = _winner(totals)
    ranking = [t["option"] for t in sorted(totals, key=lambda t: (-t["weighted"], not t["datum"]))]
    sens = sensitivity(state, weights, winner) if len(totals) > 1 else []
    return {
        "weights": {c: round(w, 4) for c, w in weights.items()},
        "weights_source": "direct" if state.get("weights_mode") == "direct" and state.get("weights") else "pairwise",
        "totals": totals,
        "ranking": ranking,
        "winner": winner,
        "datum": (state.get("options") or [None])[state.get("datum", 0)] if state.get("options") else None,
        "sensitivity": sens,
        "robust": all(s["robust"] for s in sens),
        "decided": (state.get("decision") or {}).get("selected"),
        "decision_differs_from_winner": bool((state.get("decision") or {}).get("selected"))
                                         and (state.get("decision") or {}).get("selected") != winner,
    }


# ─── import (trades.yaml format) ─────────────────────────────────────────

def from_file_trade(t: dict[str, Any], pairwise: dict[str, Any] | None = None) -> dict[str, Any]:
    """A trade in the teaching-baseline file format (``trades.yaml``: ``criteria`` as
    ``{name: weight}``, ``datum`` as an option name, ``pairwise_inputs[id].pairwise`` as
    ``{"A vs B": value}``) as a trade state."""
    tid = _text(t.get("id"), 24)
    comps: dict[str, float] = {}
    for k, v in dict((pairwise or {}).get("pairwise") or {}).items():
        a, sep, b = str(k).partition(" vs ")
        if sep:
            comps[f"{a.strip()}|{b.strip()}"] = v
    raw = {
        "title": t.get("title"), "seat": t.get("seat"), "level": t.get("level"),
        "options": t.get("options"), "datum": t.get("datum"), "criteria": t.get("criteria"),
        "scores": t.get("scores"), "comparisons": comps, "thresholds": t.get("thresholds"),
        "weights_mode": "pairwise" if comps else "direct",
        "evidence": t.get("evidence"), "note": t.get("note") or t.get("expected_winner"),
        "links": {**dict(t.get("links") or {}), "decision_record": t.get("decision_record")
                  or (t.get("links") or {}).get("decision_record")},
    }
    return clean_state(raw, tid)


# ─── decision record ─────────────────────────────────────────────────────

def decide(state: dict[str, Any], selected: str, rationale: str, seat: str) -> dict[str, Any]:
    """The trade with its decision recorded (``status`` decided)."""
    if selected not in (state.get("options") or []):
        raise ValueError(f"{selected!r} is not an option of {state.get('id')}")
    st = dict(state)
    rec_id = (st.get("links") or {}).get("decision_record") or f"D-{st['id']}"
    st["decision"] = {"selected": selected, "rationale": _text(rationale), "record_id": rec_id,
                      "decided_by_seat": _text(seat, 40),
                      "decided_at": datetime.now(timezone.utc).isoformat()}
    st["status"] = "decided"
    st["links"] = {**(st.get("links") or {}), "decision_record": rec_id}
    return st


def decision_record(state: dict[str, Any]) -> dict[str, Any]:
    """The study decision record (``spacecdf_common.models.conflicts.DecisionRecord`` fields) of
    a decided trade."""
    ev = evaluate(state)
    dec = state.get("decision") or {}
    totals = {t["option"]: t for t in ev["totals"]}
    sel = dec.get("selected")
    return {
        "id": dec.get("record_id") or (state.get("links") or {}).get("decision_record") or f"D-{state['id']}",
        "title": state.get("title") or state["id"],
        "decision_statement": f"{state['id']} {state.get('title') or ''}: {sel}".strip(),
        "level": state.get("level") or "architecture",
        "criteria": [{"name": c, "weight": ev["weights"].get(c, 0.0), "unit": ""} for c in state.get("criteria") or []],
        "alternatives": [{"id": o, "name": o,
                          "description": "datum" if totals.get(o, {}).get("datum") else "",
                          "scores": {c: float(((state.get("scores") or {}).get(o) or {}).get(c, 0.0))
                                     for c in state.get("criteria") or []},
                          "weighted_total": totals.get(o, {}).get("weighted", 0.0),
                          "pros": [], "cons": [f"below threshold: {', '.join(totals[o]['below_threshold'])}"]
                          if totals.get(o, {}).get("below_threshold") else []}
                         for o in state.get("options") or []],
        "selected_alternative_id": sel,
        "rationale": dec.get("rationale") or "",
        "decision_authority": dec.get("decided_by_seat") or state.get("seat") or "",
        "related_objective_ids": [],
        "related_requirement_ids": list((state.get("links") or {}).get("requirements") or []),
        "affected_parameters": [],
        "status": "decided",
    }


def upsert_decision_record(study: Any, state: dict[str, Any]) -> dict[str, Any]:
    """Write (or replace) the decision record of a decided trade on ``study.decision_records``."""
    from spacecdf_common.models.conflicts import DecisionRecord
    rec = DecisionRecord(**decision_record(state))
    recs = [r for r in list(study.decision_records or []) if getattr(r, "id", None) != rec.id]
    study.decision_records = [*recs, rec]
    return rec.model_dump(mode="json")
