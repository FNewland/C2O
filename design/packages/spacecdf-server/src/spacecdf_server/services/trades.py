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

Wave 3 (3.D3, SE-06; the v2 trade model of ``trades.yaml``; PI ruling: orbit and launch at MDR,
data architecture at SRR, architecture trades at PDR)::

    level        one of LEVELS (mission, system, architecture, subsystem, equipment); free text of
                 older records is read into it (``level_detail`` keeps "Payload" of "Subsystem: Payload")
    gate         the review the trade serves (mdr, prr, srr, pdr, cdr) or ""
    method       "pugh_weighted" (scores -2..+2 against the datum) or "absolute_scale" (1..5 per
                 criterion against a written scale; the datum is scored like the others)
    option_labels {option: description}
    must         [must-criterion text]; screened {option: reason} = options failing a must (kept
                 for teaching, never ranked)
    criteria_meta {criterion: {source: [MOE-xx | requirement code], scale, rationale}}; a system
                 or mission trade needs a source on every criterion (``issues``)
    weights_locked_at, post_hoc_weights, weight_history: weights lock at the first score; a
                 change after it is kept but flagged
    dissent, acceptance_conditions [..], risks_of_selected [..], recommendation, evidence_by_criterion
    decision     + condition, due, fallback, risks (a conditional decision, open-item register)

``evaluate`` adds, for every method, the ±20 % weight sensitivity (each weight ×0.8 and ×1.2,
renormalised), ``robust_pm20``, ``flips_at``, the break-even multiplier per criterion (the
smallest multiple of one weight that lets the runner-up win), the runner-up, the margin and, for
absolute scales, the Pugh form against the datum (-2..+2), as the v2 baseline computes them.
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
#: trade levels (SE-06); the PI ruling puts mission/system trades at MDR and SRR, architecture at PDR
LEVELS = ("mission", "system", "architecture", "subsystem", "equipment")
METHODS = ("pugh_weighted", "absolute_scale")
ABS_MIN, ABS_MAX = 1, 5
GATES = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")
#: trade deliverable of the protocol per canonical gate (PI ruling): the levels that count
GATE_TRADE_LEVELS = {"mdr": ("mission", "system"), "srr": ("system", "mission"), "pdr": ("architecture",)}
#: ±20 % sensitivity factors and the break-even scan (v2 ``defs_trades.evaluate``)
PM20 = (0.8, 1.2)
BREAK_EVEN_STEPS = [x / 20 for x in range(1, 81)]


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


def norm_level(raw: Any) -> tuple[str, str]:
    """(level enum, detail) from a level as entered: "Mission" → mission, "System architecture"
    → architecture, "Subsystem: Payload" → (subsystem, Payload); unknown text → ("", text)."""
    txt = _text(raw, 120)
    head, _, detail = txt.partition(":")
    h = head.strip().lower()
    if "architecture" in h:
        return "architecture", detail.strip()
    for lv in LEVELS:
        if h == lv or h.startswith(lv):
            return lv, detail.strip()
    return "", txt


def _str_list(raw: Any, limit: int = 30) -> list[str]:
    if isinstance(raw, str):
        raw = [raw] if raw.strip() else []
    return [_text(x, 600) for x in (raw or []) if _text(x, 600)][:limit]


def clean_state(raw: dict[str, Any] | None, tid: str) -> dict[str, Any]:
    """A trade state from client or file data. Tolerates the legacy Pugh record (criteria as
    ``{"id", "name", "weight"}``, the datum as an option name, scores keyed by criterion id)."""
    raw = dict(raw or {})
    method = raw.get("method") if raw.get("method") in METHODS else "pugh_weighted"
    smin, smax = (ABS_MIN, ABS_MAX) if method == "absolute_scale" else (SCORE_MIN, SCORE_MAX)
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
                clean_row[name] = max(smin, min(smax, v))
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
            thresholds[c] = max(smin, min(smax, f))
    links_raw = dict(raw.get("links") or {})
    links = {
        "decision_record": _text(links_raw.get("decision_record") or raw.get("decision_record"), 40),
        "requirements": _names(links_raw.get("requirements"), 200),
        "risks": _names(links_raw.get("risks"), 100),
        "elements": _names(links_raw.get("elements"), 100),
    }
    dec_raw = raw.get("decision") if isinstance(raw.get("decision"), dict) else {}
    decision = {k: _text(dec_raw.get(k), TEXT_LIMIT if k in ("rationale", "condition", "fallback") else 200)
                for k in ("selected", "rationale", "decided_at", "decided_by_seat", "record_id", "condition", "due",
                          "fallback", "blocks_gate") if dec_raw.get(k)}
    if dec_raw.get("risks"):
        decision["risks"] = _names(dec_raw.get("risks"), 50)
    if isinstance(dec_raw.get("condition_met"), dict):
        cm = dec_raw["condition_met"]
        decision["condition_met"] = {k: _text(cm.get(k), 2000) for k in ("condition", "at", "note") if cm.get(k)}
    if decision.get("selected") and decision["selected"] not in options:
        decision.pop("selected")
    status = raw.get("status") if raw.get("status") in STATUSES else ("decided" if decision.get("selected") else "open")
    # wave 3 (3.D3): level enum and gate, must-screen, criterion sources, weight lock, record fields
    lv_in = raw.get("level")
    level, detail = (lv_in, _text(raw.get("level_detail"), 120)) if lv_in in LEVELS else norm_level(lv_in)
    if not level and raw.get("trade_level") in LEVELS:
        level = raw["trade_level"]
    gate = str(raw.get("gate") or "").strip().lower()
    gate = gate if gate in GATES else ""
    labels_raw = raw.get("option_labels") or (raw.get("options") if isinstance(raw.get("options"), dict) else {})
    option_labels = {o: _text(v, 400) for o, v in dict(labels_raw or {}).items() if o in options and _text(v, 400)}
    screened = {o: _text(v, 1000) for o, v in dict(raw.get("screened") or {}).items() if o in options}
    meta_raw = dict(raw.get("criteria_meta") or {})
    for c in crit_raw if isinstance(crit_raw, list) else []:
        if isinstance(c, dict) and _text(c.get("name"), 200) in criteria:
            m = {"source": c.get("source") or c.get("moe"), "scale": c.get("scale"),
                 "rationale": c.get("weight_rationale") or c.get("rationale")}
            meta_raw.setdefault(_text(c.get("name"), 200), {k: v for k, v in m.items() if v})
    criteria_meta = {}
    for c, m in meta_raw.items():
        if c in criteria and isinstance(m, dict):
            criteria_meta[c] = {"source": _names(m.get("source"), 20), "scale": _text(m.get("scale"), 600),
                                "rationale": _text(m.get("rationale"), 600)}
    ev_raw = raw.get("evidence")
    evidence_by = {c: _text(v, 2000) for c, v in dict(raw.get("evidence_by_criterion") or
                                                      (ev_raw if isinstance(ev_raw, dict) else {})).items() if c in criteria}
    history = [h for h in (raw.get("weight_history") or []) if isinstance(h, dict)][-20:]
    locked = _text(raw.get("weights_locked_at"), 40) or (datetime.now(timezone.utc).isoformat()
                                                         if any(scores.values()) else "")
    return {
        "id": tid,
        "title": _text(raw.get("title"), 300),
        "seat": _text(raw.get("seat"), 40),
        "level": level,
        "level_detail": detail,
        "gate": gate,
        "option_labels": option_labels,
        "must": _str_list(raw.get("must")),
        "screened": screened,
        "criteria_meta": criteria_meta,
        "evidence_by_criterion": evidence_by,
        "weights_locked_at": locked,
        "post_hoc_weights": bool(raw.get("post_hoc_weights")),
        "weight_history": history,
        "dissent": _text(raw.get("dissent")),
        "acceptance_conditions": _str_list(raw.get("acceptance_conditions")),
        "risks_of_selected": _str_list(raw.get("risks_of_selected")),
        "recommendation": _text(raw.get("recommendation")),
        "decision_question": _text(raw.get("decision_question") or (raw.get("decision") if isinstance(raw.get("decision"), str) else ""), 600),
        "status": status,
        "method": method,
        "options": options,
        "datum": datum,
        "criteria": criteria,
        "comparisons": comparisons,
        "weights_mode": mode,
        "weights": weights,
        "scores": scores,
        "thresholds": thresholds,
        "evidence": _text(ev_raw) if not isinstance(ev_raw, dict) else "",
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


def _score_row(state: dict[str, Any], i: int, opt: str) -> dict[str, float]:
    row = (state.get("scores") or {}).get(opt) or {}
    crit = state.get("criteria") or []
    if state.get("method") == "absolute_scale":
        return {c: float(row.get(c, 0.0)) for c in crit}
    if i == state.get("datum", 0):
        return {c: 0.0 for c in crit}
    return {c: float(row.get(c, 0.0)) for c in crit}


def _totals(state: dict[str, Any], weights: dict[str, float]) -> list[dict[str, Any]]:
    out = []
    datum = state.get("datum", 0)
    thr = state.get("thresholds") or {}
    screened = state.get("screened") or {}
    absolute = state.get("method") == "absolute_scale"
    for i, opt in enumerate(state.get("options") or []):
        sc = _score_row(state, i, opt)
        weighted = sum(sc[c] * weights.get(c, 0.0) for c in sc)
        below = [c for c, m in thr.items() if sc.get(c, 0.0) < m]
        out.append({"option": opt, "datum": i == datum, "weighted": round(weighted, 3 if absolute else 4),
                    "unweighted": round(sum(sc.values()), 4), "below_threshold": below,
                    "screened": opt in screened, "screen_reason": screened.get(opt, ""),
                    "acceptable": not below and opt not in screened})
    return out


def _winner(totals: list[dict[str, Any]]) -> str | None:
    pool = [t for t in totals if t["acceptable"]] or [t for t in totals if not t.get("screened")] or totals
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


def _scaled(weights: dict[str, float], crit: str, factor: float) -> dict[str, float]:
    """One weight × ``factor``, all renormalised to a sum of 1 (v2 ``defs_trades.evaluate``)."""
    w = dict(weights)
    w[crit] = w.get(crit, 0.0) * factor
    tot = sum(w.values())
    return {c: (v / tot if tot > 0 else 0.0) for c, v in w.items()}


def _eligible(totals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [t for t in totals if t["acceptable"]] or [t for t in totals if not t.get("screened")] or totals


def pm20(state: dict[str, Any], weights: dict[str, float], winner: str | None) -> dict[str, Any]:
    """±20 % sensitivity: each weight ×0.8 and ×1.2 (renormalised); the winner, its total and its
    lead over the next option for each; ``flips_at`` lists the changes that change the winner;
    ``break_even`` the smallest multiplier (0.05 … 4.0) of one weight that lets the runner-up
    overtake the winner."""
    rows, flips = [], []
    base = _eligible(_totals(state, weights))
    ranked = sorted(base, key=lambda t: (-t["weighted"], not t["datum"]))
    runner = ranked[1]["option"] if len(ranked) > 1 else None
    for c in state.get("criteria") or []:
        for f in PM20:
            tt = _eligible(_totals(state, _scaled(weights, c, f)))
            if not tt:
                continue
            best = max(tt, key=lambda t: t["weighted"])
            others = sorted((t["weighted"] for t in tt), reverse=True)
            rows.append({"criterion": c, "factor": f, "winner": best["option"], "winner_total": round(best["weighted"], 3),
                         "margin_to_next": round(others[0] - others[1], 3) if len(others) > 1 else None})
            if best["option"] != winner:
                flips.append(f"{c} x{f}")
    breakeven = []
    if winner and runner:
        for c in state.get("criteria") or []:
            for f in BREAK_EVEN_STEPS:
                tt = {t["option"]: t["weighted"] for t in _totals(state, _scaled(weights, c, f))}
                if tt.get(runner, 0.0) > tt.get(winner, 0.0):
                    breakeven.append({"criterion": c, "multiplier": f})
                    break
    return {"rows": rows, "robust": not flips, "flips_at": flips, "break_even": breakeven, "runner_up": runner}


def pugh_vs_datum(state: dict[str, Any]) -> dict[str, dict[str, float]]:
    """An absolute-scale trade in the Pugh form: each option minus the datum, clipped to ±2."""
    if state.get("method") != "absolute_scale" or not state.get("options"):
        return {}
    opts = state["options"]
    d = opts[state.get("datum", 0)]
    dsc = (state.get("scores") or {}).get(d) or {}
    return {o: {c: max(-2.0, min(2.0, float(((state.get("scores") or {}).get(o) or {}).get(c, 0.0)) - float(dsc.get(c, 0.0))))
                for c in state.get("criteria") or []} for o in opts if o != d}


def issues(state: dict[str, Any]) -> list[str]:
    """What the method asks that the trade lacks (warnings, never blocking)."""
    out = []
    if state.get("level") in ("mission", "system"):
        miss = [c for c in state.get("criteria") or [] if not ((state.get("criteria_meta") or {}).get(c) or {}).get("source")]
        if miss:
            out.append("criteria without a source (MOE or requirement): " + ", ".join(miss))
    if state.get("level") in ("mission", "system", "architecture") and not state.get("gate"):
        out.append("no review gate")
    if state.get("post_hoc_weights"):
        out.append("weights changed after scoring")
    if state.get("method") == "absolute_scale":
        crit = state.get("criteria") or []
        for o in state.get("options") or []:
            row = (state.get("scores") or {}).get(o) or {}
            if any(c not in row for c in crit):
                out.append(f"option {o} not scored on every criterion")
                break
    return out


def evaluate(state: dict[str, Any]) -> dict[str, Any]:
    weights = weights_of(state)
    totals = _totals(state, weights)
    winner = _winner(totals)
    ranking = [t["option"] for t in sorted(totals, key=lambda t: (-t["weighted"], not t["datum"]))]
    sens = sensitivity(state, weights, winner) if len(totals) > 1 else []
    p20 = pm20(state, weights, winner) if len(totals) > 1 else {"rows": [], "robust": True, "flips_at": [],
                                                                 "break_even": [], "runner_up": None}
    tmap = {t["option"]: t["weighted"] for t in totals}
    eligible = [o for o in ranking if not (next(t for t in totals if t["option"] == o).get("screened"))]
    runner = p20["runner_up"]
    return {
        "method": state.get("method") or "pugh_weighted",
        "level": state.get("level") or "",
        "gate": state.get("gate") or "",
        "ranking_eligible": eligible,
        "runner_up": runner,
        "margin": round(tmap[winner] - tmap[runner], 3) if winner in tmap and runner in tmap else None,
        "sensitivity_pm20": p20["rows"],
        "robust_pm20": p20["robust"],
        "flips_at": p20["flips_at"],
        "break_even": p20["break_even"],
        "pugh_vs_datum": pugh_vs_datum(state),
        "issues": issues(state),
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
    opts = t.get("options")
    absolute = t.get("method") == "absolute_scale" or isinstance(opts, dict) or any(
        isinstance(v, (int, float)) and v > SCORE_MAX for row in dict(t.get("scores") or {}).values()
        if isinstance(row, dict) for v in row.values())
    raw = {
        "title": t.get("title"), "seat": t.get("seat"), "level": t.get("trade_level") if t.get("trade_level") in LEVELS
        and not str(t.get("level") or "").strip() else t.get("level"),
        "level_detail": t.get("level_detail"), "gate": t.get("gate"),
        "method": "absolute_scale" if absolute else "pugh_weighted",
        "options": list(opts.keys()) if isinstance(opts, dict) else opts,
        "option_labels": opts if isinstance(opts, dict) else t.get("option_labels"),
        "datum": t.get("datum"), "criteria": t.get("criteria"),
        "scores": t.get("scores"), "comparisons": comps, "thresholds": t.get("thresholds"),
        "weights_mode": "pairwise" if comps else "direct",
        "evidence": t.get("evidence"), "note": t.get("note") or t.get("expected_winner") or t.get("scoring_note"),
        "must": t.get("must"), "screened": t.get("screened"), "dissent": t.get("dissent"),
        "acceptance_conditions": t.get("acceptance_conditions"), "risks_of_selected": t.get("risks_of_selected"),
        "recommendation": t.get("recommendation"),
        "decision_question": t.get("decision") if isinstance(t.get("decision"), str) else t.get("decision_question"),
        "decision": t.get("decision") if isinstance(t.get("decision"), dict) else None,
        "links": {**dict(t.get("links") or {}), "decision_record": t.get("decision_record")
                  or (t.get("links") or {}).get("decision_record")},
    }
    st = clean_state(raw, tid)
    if not st["level"] and t.get("trade_level") in LEVELS:
        st["level"] = t["trade_level"]
    return st


# ─── gate summary and the protocol's trade deliverable (PI ruling) ───────

def gate_summary(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Trades by review gate and level: ``{gate: {total, decided, open, levels: {level: n}, ids}}``
    plus ``by_level``. Subsystem trades without a gate are counted under ``""``."""
    out: dict[str, dict[str, Any]] = {}
    by_level: dict[str, int] = {}
    for tid, rec in records.items():
        st = rec.get("state") or {}
        g = st.get("gate") or ""
        lv = st.get("level") or ""
        b = out.setdefault(g, {"total": 0, "decided": 0, "open": 0, "levels": {}, "ids": [], "undecided": []})
        b["total"] += 1
        b["ids"].append(tid)
        if st.get("status") == "decided":
            b["decided"] += 1
        else:
            b["open"] += 1
            b["undecided"].append(tid)
        b["levels"][lv] = b["levels"].get(lv, 0) + 1
        by_level[lv] = by_level.get(lv, 0) + 1
    return {"by_gate": out, "by_level": by_level}


def trade_deliverable(records: dict[str, dict[str, Any]], canonical: str) -> dict[str, Any] | None:
    """The trade deliverable of the protocol at ``canonical`` (PI ruling: orbit and launch at MDR,
    data architecture at SRR, architecture trades at PDR), in the ``/phase`` deliverable shape:
    ``ok`` when every such trade is decided, ``warn`` when one is still open, ``missing`` when
    there is none. None for a gate that asks no trade."""
    levels = GATE_TRADE_LEVELS.get(canonical)
    if not levels:
        return None
    mine = [(tid, r.get("state") or {}) for tid, r in records.items()
            if (r.get("state") or {}).get("gate") == canonical and (r.get("state") or {}).get("level") in levels]
    decided = [tid for tid, st in mine if st.get("status") == "decided"]
    undecided = [tid for tid, st in mine if st.get("status") != "decided"]
    kind = "architecture" if canonical == "pdr" else "system"
    label = ({"en": "Architecture trade studies", "fr": "Compromis d’architecture"} if kind == "architecture" else
             {"en": "System-level trade study", "fr": "Compromis au niveau système"})
    if not mine:
        state, evidence = "missing", f"No {kind}-level trade recorded for {canonical.upper()}"
    elif undecided:
        state = "warn"
        evidence = (f"{', '.join(decided)} decided; " if decided else "") + f"{', '.join(undecided)} undecided"
    else:
        state, evidence = "ok", f"{', '.join(decided)} decided"
    return {"id": f"trade.{canonical}", "kind": "trade", "label": label, "owner_seat": "systems_engineer",
            "state": state, "evidence": evidence, "fix": {"view": "top", "panel": "decide"},
            "trades": [tid for tid, _ in mine]}


# ─── decision record ─────────────────────────────────────────────────────

def decide(state: dict[str, Any], selected: str, rationale: str, seat: str, *, condition: str = "",
           due: str = "", fallback: str = "", risks: list[str] | None = None, blocks_gate: str = "") -> dict[str, Any]:
    """The trade with its decision recorded (``status`` decided). ``condition`` (with ``due``,
    ``fallback`` and the linked ``risks``) makes it a conditional decision: it stays in the
    open-item register until the condition is met."""
    if selected not in (state.get("options") or []):
        raise ValueError(f"{selected!r} is not an option of {state.get('id')}")
    if (state.get("screened") or {}).get(selected):
        raise ValueError(f"{selected!r} was screened out: {state['screened'][selected]}")
    st = dict(state)
    rec_id = (st.get("links") or {}).get("decision_record") or f"D-{st['id']}"
    st["decision"] = {"selected": selected, "rationale": _text(rationale), "record_id": rec_id,
                      "decided_by_seat": _text(seat, 40),
                      "decided_at": datetime.now(timezone.utc).isoformat()}
    cond = conditional(condition, due, fallback, risks, blocks_gate)
    st["decision"].update(cond)
    st["status"] = "decided"
    st["links"] = {**(st.get("links") or {}), "decision_record": rec_id}
    return st


def conditional(condition: str = "", due: str = "", fallback: str = "", risks: list[str] | None = None,
                blocks_gate: str = "") -> dict[str, Any]:
    """The conditional part of a decision (empty fields left out); ``blocks_gate`` is the review
    the condition must be met by (open-item register)."""
    out: dict[str, Any] = {}
    if str(blocks_gate or "").lower() in GATES:
        out["blocks_gate"] = str(blocks_gate).lower()
    if _text(condition):
        out["condition"] = _text(condition)
    if _text(due, 10):
        out["due"] = _text(due, 10)
    if _text(fallback):
        out["fallback"] = _text(fallback)
    if risks:
        out["risks"] = _names(risks, 50)
    return out


def weights_changed(old: dict[str, Any], new: dict[str, Any]) -> bool:
    """True when the effective weights differ (comparisons, typed weights or mode)."""
    if not old or not old.get("criteria"):
        return False
    a, b = weights_of(old), weights_of(new)
    return set(a) != set(b) or any(abs(a[c] - b.get(c, 0.0)) > 1e-6 for c in a)


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
