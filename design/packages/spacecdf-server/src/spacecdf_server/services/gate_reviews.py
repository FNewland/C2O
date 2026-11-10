"""SpaceCDF — review gate state machine (WP6, Nov 2026).

States of one profile gate::

    not_ready ──(all must-pass items pass)──▶ ready ──start──▶ under_review ──pass──▶ passed
        ▲                                      ▲                  │                    │
        └──────────────(derived)───────────────┴────cancel────────┘                 reopen
                                                                                       ▼
                                                                    reopened ──start──▶ under_review

``not_ready`` / ``ready`` are derived from the server evaluation every time; the others are
stored in ``Study.gate_states[gate_id]`` with a history. Passing saves a baseline snapshot
(routers/gates.py). Pure functions: no I/O.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

STATES = ("not_ready", "ready", "under_review", "passed", "reopened")
ACTIONS = ("start", "cancel", "pass", "reopen")


class GateTransitionError(ValueError):
    """An action that the gate's state does not allow. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def stored_state(entry: dict[str, Any] | None) -> str | None:
    st = (entry or {}).get("state")
    return st if st in ("under_review", "passed", "reopened") else None


def display_state(entry: dict[str, Any] | None, ready: bool) -> str:
    """The state shown for a gate: the stored one, else derived from readiness."""
    st = stored_state(entry)
    if st in ("under_review", "passed", "reopened"):
        return st
    return "ready" if ready else "not_ready"


def transition(entry: dict[str, Any] | None, action: str, *, ready: bool, by: str = "",
               note: str = "", now: datetime | None = None) -> dict[str, Any]:
    """The gate's new stored entry after ``action``; raises GateTransitionError if not allowed.

    ``ready``: the server evaluation says every must-pass item passes (checked again on
    ``pass``, so a design that broke during the review cannot be passed).
    """
    if action not in ACTIONS:
        raise GateTransitionError("bad_action", f"Unknown action {action!r}")
    entry = {"state": None, "history": [], "baselines": [], **(entry or {})}
    current = display_state(entry, ready)
    new: str | None
    if action == "start":
        if current not in ("ready", "reopened"):
            raise GateTransitionError("not_ready" if current == "not_ready" else "bad_state",
                                      f"Cannot start a review from {current}")
        if not ready:
            raise GateTransitionError("not_ready", "Every must-pass item must pass before the review starts")
        new = "under_review"
    elif action == "cancel":
        if current != "under_review":
            raise GateTransitionError("bad_state", f"No review in progress ({current})")
        new = None
    elif action == "pass":
        if current != "under_review":
            raise GateTransitionError("bad_state", f"Only a gate under review can pass ({current})")
        if not ready:
            raise GateTransitionError("not_ready", "A must-pass item failed during the review")
        new = "passed"
    else:  # reopen
        if current != "passed":
            raise GateTransitionError("bad_state", f"Only a passed gate can be reopened ({current})")
        new = "reopened"
    at = (now or datetime.now(timezone.utc)).isoformat()
    entry["history"] = [*entry.get("history", []),
                        {"action": action, "from": current, "to": new or ("ready" if ready else "not_ready"),
                         "at": at, "by": by, "note": note[:500]}]
    entry["state"] = new
    entry["updated_at"] = at
    return entry


# ─── review record (W4.08): RIDs and actions, chair note, go / no-go, baseline diff ─────────

RID_KINDS = ("rid", "action")
RID_STATUSES = ("open", "in_work", "closed", "rejected")
RID_SEVERITIES = ("major", "minor")
RID_OPEN = ("open", "in_work")
DECISIONS = ("go", "go_with_actions", "no_go")


def rid_number(kind: str, gate_short: str, n: int) -> str:
    """``RID-MDR-01`` / ``ACT-MDR-01``."""
    prefix = "ACT" if kind == "action" else "RID"
    tag = "".join(ch for ch in (gate_short or "").upper() if ch.isalnum())[:8] or "GATE"
    return f"{prefix}-{tag}-{n:02d}"


def clean_review(raw: dict[str, Any] | None, by: str = "", now: datetime | None = None) -> dict[str, Any]:
    """The review record stored with a gate (``gate_states[gate]["review"]``)."""
    raw = dict(raw or {})
    dec = raw.get("decision") if raw.get("decision") in DECISIONS else None
    return {"chair_note": str(raw.get("chair_note") or "")[:4000], "decision": dec,
            "board": str(raw.get("board") or "")[:1000],
            "decided_at": (now or datetime.now(timezone.utc)).isoformat() if dec else None,
            "by": str(by or "")[:160]}


#: Review-record criteria of the gates after CDR (QR, AR, FRR): gate_exit_criteria.yaml has no
#: phases for them yet (W4.09). ``auto`` items are evaluated here from the RID log; ``manual``
#: items are board evidence the instructor signs off (they stay "manual" until then, so an
#: unsigned FRR is not ready and names what is missing).
POST_CDR_CRITERIA: dict[str, list[dict[str, Any]]] = {
    "qr": [
        {"id": "QR-RR-01", "auto": "rids_closed", "owner_seat": "systems_engineer", "category": "review",
         "question": "Are the RIDs and actions of the earlier reviews closed?"},
        {"id": "QR-RR-02", "owner_seat": "systems_engineer", "category": "verification",
         "question": "Have the qualification test results been reviewed and accepted by the board?",
         "evidence": "Qualification test reports and the verification control document at qualification"},
        {"id": "QR-RR-03", "owner_seat": "systems_engineer", "category": "verification",
         "question": "Are the non-conformances of the qualification campaign closed or waived?",
         "evidence": "NCR log with closure or waiver for every item"},
    ],
    "ar": [
        {"id": "AR-RR-01", "auto": "rids_closed", "owner_seat": "systems_engineer", "category": "review",
         "question": "Are the RIDs and actions of the earlier reviews closed?"},
        {"id": "AR-RR-02", "owner_seat": "systems_engineer", "category": "verification",
         "question": "Has the flight model passed its acceptance tests?",
         "evidence": "Acceptance test reports of the flight (protoflight) model"},
        {"id": "AR-RR-03", "owner_seat": "team_leader", "category": "programmatic",
         "question": "Is the acceptance data package complete (as-built configuration, logbook, waivers)?",
         "evidence": "Acceptance data package"},
    ],
    "frr": [
        {"id": "FRR-RR-01", "auto": "rids_closed", "owner_seat": "systems_engineer", "category": "review",
         "question": "Are the RIDs and actions of the earlier reviews closed?"},
        {"id": "FRR-RR-02", "owner_seat": "systems_engineer", "category": "verification",
         "question": "Is every verification item closed, or waived with a recorded justification?",
         "evidence": "Verification control document with every item closed or waived"},
        {"id": "FRR-RR-03", "owner_seat": "team_leader", "category": "regulatory",
         "question": "Are the licences granted (spectrum, space station, earth stations, remote sensing)?",
         "evidence": "Licences and their conditions"},
        {"id": "FRR-RR-04", "owner_seat": "mission_analyst", "category": "operations",
         "question": "Are operations ready (procedures validated, team trained, ground segment tested end to end)?",
         "evidence": "Operations readiness: validated procedures, training records, end-to-end test report"},
        {"id": "FRR-RR-05", "owner_seat": "structures_engineer", "category": "launch",
         "question": "Are the as-built mass properties within the launch interface limits?",
         "evidence": "Measured mass, centre of mass and the launch ICD limits"},
    ],
}


def post_cdr_criteria(canonical: str, rids: list[dict[str, Any]], earlier: set[str]) -> list[dict[str, Any]]:
    """The review-record criteria of a canonical gate after CDR, evaluated. ``rids``: every RID
    and action of the study; ``earlier``: the profile gate ids before the gate under review."""
    out = []
    for spec in POST_CDR_CRITERIA.get(canonical, []):
        c = {"id": spec["id"], "question": spec["question"], "category": spec.get("category", "review"),
             "priority": "must_pass", "advisory": False, "owner_seat": spec.get("owner_seat"),
             "evidence_required": spec.get("evidence", ""), "evidence_key": "", "evidence_params": {},
             "step": None, "mode": "auto" if spec.get("auto") else "manual"}
        if spec.get("auto") == "rids_closed":
            still = [r for r in rids if r.get("gate") in earlier and r.get("status") in RID_OPEN]
            ok = not still
            c.update(status="pass" if ok else "fail", verdict="pass" if ok else "fail",
                     evidence_required="Every RID and action of the earlier reviews closed or rejected",
                     evidence_found=("All earlier RIDs and actions are closed" if ok else
                                     "Open: " + ", ".join(r.get("number") or r.get("id", "") for r in still[:12])))
        else:
            c.update(status="manual", verdict="manual",
                     evidence_found=f"Missing evidence: {spec.get('evidence', '')} (board sign-off)")
        out.append(c)
    return out


def _index(items: list[dict[str, Any]] | None, key: str) -> dict[str, dict[str, Any]]:
    return {str(x.get(key)): x for x in items or [] if isinstance(x, dict) and x.get(key)}


def diff_snapshots(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """What changed from baseline snapshot ``a`` to baseline snapshot ``b`` (routers/gates.py
    ``_save_baseline``): requirements, elements, risks by id, the mission need fields and the
    criteria results."""
    def by_key(items, key="id"):
        return _index(items, key)

    def req_key(r):
        return str(r.get("code") or r.get("id"))

    ra = {req_key(r): r for r in a.get("requirements") or [] if isinstance(r, dict)}
    rb = {req_key(r): r for r in b.get("requirements") or [] if isinstance(r, dict)}
    req_fields = ("text", "level", "status", "threshold_op", "threshold_value", "verification_method", "parent_id")
    ea, eb = by_key(a.get("elements")), by_key(b.get("elements"))
    el_fields = ("name", "mass_kg", "power_avg_w", "quantity", "trl", "kb_component_id", "parent_id")
    ka, kb = by_key(a.get("risk_register")), by_key(b.get("risk_register"))
    risk_fields = ("description", "likelihood", "consequence", "status", "mitigation")

    def changed(x, y, fields):
        return [f for f in fields if (x or {}).get(f) != (y or {}).get(f)]

    na, nb = a.get("mission_need") or {}, b.get("mission_need") or {}
    ca = {c.get("id"): c.get("status") for c in a.get("criteria") or []}
    cb = {c.get("id"): c.get("status") for c in b.get("criteria") or []}
    return {
        "requirements": {
            "added": sorted(set(rb) - set(ra)), "removed": sorted(set(ra) - set(rb)),
            "changed": sorted(k for k in set(ra) & set(rb) if changed(ra[k], rb[k], req_fields)),
        },
        "elements": {
            "added": sorted(eb[k].get("name") or k for k in set(eb) - set(ea)),
            "removed": sorted(ea[k].get("name") or k for k in set(ea) - set(eb)),
            "changed": sorted(eb[k].get("name") or k for k in set(ea) & set(eb) if changed(ea[k], eb[k], el_fields)),
        },
        "risks": {
            "added": sorted(set(kb) - set(ka)), "removed": sorted(set(ka) - set(kb)),
            "changed": sorted(k for k in set(ka) & set(kb) if changed(ka[k], kb[k], risk_fields)),
        },
        "mission_need": sorted(k for k in set(na) | set(nb) if k != "created" and na.get(k) != nb.get(k)),
        "criteria": sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k) and k in ca and k in cb),
        "counts": {"requirements": [len(ra), len(rb)], "elements": [len(ea), len(eb)], "risks": [len(ka), len(kb)]},
    }


# ─── wave 3 (3.D1): protocol enforcement at review start, baseline kinds ──────────────────

#: how the systems-engineering protocol is enforced when a review starts (PI ruling: ``warn`` by
#: default, the instructor can set ``block``; ``off`` = the behaviour before wave 3)
ENFORCEMENT_MODES = ("off", "warn", "block")
DEFAULT_ENFORCEMENT = "warn"
#: the study's own setting lives in ``Study.gate_states[SETTINGS_KEY]`` (not a gate id)
SETTINGS_KEY = "_settings"
#: configuration baseline a passed canonical gate sets (``gate_profiles.yaml`` ``baseline_kinds``)
BASELINE_KINDS = {"mdr": "mission", "prr": "mission", "srr": "functional", "pdr": "allocated",
                  "cdr": "product", "qr": "product", "ar": "product", "frr": "product"}


def enforcement_mode(profile: dict[str, Any] | None, gate_states: dict[str, Any] | None,
                     config: dict[str, Any] | None = None) -> dict[str, Any]:
    """The study's enforcement mode and where it comes from: the study's setting (the instructor
    chose it), else the profile's ``se_enforcement``, else the file default, else ``warn``."""
    cfg = config or {}
    study = ((gate_states or {}).get(SETTINGS_KEY) or {}).get("se_enforcement")
    if study in ENFORCEMENT_MODES:
        return {"mode": study, "source": "study", "set_by": ((gate_states or {}).get(SETTINGS_KEY) or {}).get("set_by", "")}
    prof = (profile or {}).get("se_enforcement")
    if prof in ENFORCEMENT_MODES:
        return {"mode": prof, "source": "profile"}
    dflt = cfg.get("default_se_enforcement")
    return {"mode": dflt if dflt in ENFORCEMENT_MODES else DEFAULT_ENFORCEMENT, "source": "default"}


def baseline_kind(pg: dict[str, Any], config: dict[str, Any] | None = None) -> str:
    """The baseline a pass of profile gate ``pg`` sets: that of the last canonical gate it covers."""
    kinds = {**BASELINE_KINDS, **dict((config or {}).get("baseline_kinds") or {})}
    covers = list(pg.get("covers") or [])
    return kinds.get(covers[-1], "mission") if covers else "mission"


def protocol_checks(gate_id: str, order: list[str], gate_states: dict[str, Any] | None,
                    entry: list[dict[str, Any]] | None, deliverables: list[dict[str, Any]] | None,
                    ) -> list[dict[str, Any]]:
    """What the protocol says before a review of ``gate_id`` starts, as a list of findings
    ``{code, kind, id, label, owner_seat, state, evidence}``:

    * ``out_of_order``: an earlier gate of the profile has not passed;
    * ``entry_missing``: a "Before you start" item of the phase is not ``ok``;
    * ``deliverables_missing``: a deliverable of the phase is ``missing`` (``warn`` items, which
      exist but are incomplete, are listed with code ``deliverable_partial``).

    Pure: ``entry`` and ``deliverables`` come from ``se_protocol.phase`` (agent S)."""
    out: list[dict[str, Any]] = []
    states = gate_states or {}
    if gate_id in order:
        for g in order[: order.index(gate_id)]:
            if (states.get(g) or {}).get("state") != "passed":
                out.append({"code": "out_of_order", "kind": "gate", "id": g, "label": {"en": g.upper(), "fr": g.upper()},
                            "state": "missing", "evidence": f"{g.upper()} has not passed"})
    for e in entry or []:
        if e.get("state") not in ("ok", "pass", None):
            out.append({"code": "entry_missing", "kind": "entry", "id": e.get("id"), "label": e.get("label") or {},
                        "owner_seat": e.get("owner_seat", ""), "state": e.get("state"), "evidence": e.get("evidence", "")})
    for d in deliverables or []:
        st = d.get("state")
        if st in ("missing", "warn"):
            out.append({"code": "deliverables_missing" if st == "missing" else "deliverable_partial",
                        "kind": d.get("kind", "deliverable"), "id": d.get("id"), "label": d.get("label") or {},
                        "owner_seat": d.get("owner_seat", ""), "state": st, "evidence": d.get("evidence", ""),
                        "fix": d.get("fix")})
    return out


def blocking_code(findings: list[dict[str, Any]]) -> str | None:
    """The 409 code a ``block`` start answers with (out of order first), or None."""
    codes = {f["code"] for f in findings}
    if "out_of_order" in codes:
        return "out_of_order"
    if "deliverables_missing" in codes or "entry_missing" in codes:
        return "deliverables_missing"
    return None


def finding_text(f: dict[str, Any], lang: str = "en") -> str:
    lab = f.get("label") or {}
    name = (lab.get(lang) or lab.get("en") or f.get("id") or "") if isinstance(lab, dict) else str(lab)
    if f["code"] == "out_of_order":
        return (f"{name} n’a pas été franchi" if lang == "fr" else f"{name} has not passed")
    if f["code"] == "entry_missing":
        return (f"Avant de commencer : {name}" if lang == "fr" else f"Before you start: {name}")
    if f["code"] == "deliverable_partial":
        return (f"Livrable incomplet : {name}" if lang == "fr" else f"Deliverable incomplete: {name}")
    return (f"Livrable manquant : {name}" if lang == "fr" else f"Deliverable missing: {name}")


# ─── wave 3 (PI addendum): the review-readiness evidence of SRR and PDR ───────────────────
#
# v2 REVIEW_READINESS says SRR and PDR are "not ready" until the team has produced the SEMP, the
# debris assessment, the ICDs at Issue A signed by both owners, the reliability analysis and the
# FMEA, the thermal model (hot and cold cases) and the change decisions due at the gate. These
# criteria read the records the other agents' tools write (``services/gate_evidence.py``), so the
# gates pass legitimately once the work is done in the tool and not before.

READINESS_CRITERIA: dict[str, list[dict[str, Any]]] = {
    "srr": [
        {"id": "SRR-RD-01", "probe": "semp", "mode": "hybrid", "owner_seat": "systems_engineer", "category": "management",
         "question": "Is the systems engineering management plan (SEMP) issued for the review?",
         "evidence": "SEMP generated from the study (organisation, life cycle and gates, technical processes, "
                     "model philosophy, risk and configuration management, tailoring) and issued"},
        {"id": "SRR-RD-02", "probe": "debris", "owner_seat": "mission_analyst", "category": "sustainability",
         "question": "Is the debris assessment completed and accepted (lifetime, casualty risk, collision probability)?",
         "evidence": "Debris assessment run in the tool and accepted"},
        {"id": "SRR-RD-03", "probe": "changes", "owner_seat": "team_leader", "category": "configuration",
         "question": "Are the change proposals due at this review decided?",
         "evidence": "Every change proposal whose decision gate is this review or an earlier one approved or rejected"},
    ],
    "pdr": [
        {"id": "PDR-RD-01", "probe": "icds", "owner_seat": "systems_engineer", "category": "interfaces",
         "question": "Are the interface control documents at Issue A and signed by both owning seats?",
         "evidence": "Every ICD at Issue A (or later) with the provider and consumer sign-off"},
        {"id": "PDR-RD-02", "probe": "reliability", "owner_seat": "cost_engineer", "category": "dependability",
         "question": "Is the reliability analysis run and the FMEA worksheet filled for the space segment?",
         "evidence": "Reliability block diagram computed over the mission-success horizon and FMEA lines per subsystem"},
        {"id": "PDR-RD-03", "probe": "thermal", "owner_seat": "thermal_engineer", "category": "thermal",
         "question": "Is the thermal model solved for the hot and cold cases with positive design margins?",
         "evidence": "Nodal thermal model (at least 6 nodes) solved for a hot and a cold case; no negative design margin"},
        {"id": "PDR-RD-04", "probe": "changes", "owner_seat": "team_leader", "category": "configuration",
         "question": "Are the change proposals due at this review decided?",
         "evidence": "Every change proposal whose decision gate is this review or an earlier one approved or rejected"},
    ],
}

#: change-proposal statuses that count as decided (L's ``change_proposals.status``)
CHANGE_DECIDED = ("accepted", "approved", "rejected", "closed", "implemented", "withdrawn")
CANON_ORDER = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")


def _due_by(gate: str, canonical: str) -> bool:
    g = str(gate or "").lower()
    if g not in CANON_ORDER or canonical not in CANON_ORDER:
        return False
    return CANON_ORDER.index(g) <= CANON_ORDER.index(canonical)


def _probe(kind: str, canonical: str, ev: dict[str, Any]) -> tuple[str, str]:
    """(status, evidence found) of one readiness probe; status pass | fail | manual."""
    if kind == "semp":
        s = ev.get("semp") or {}
        if s.get("issue"):
            return "pass", f"SEMP issue {s['issue']}" + (f" ({s.get('issued_at')})" if s.get("issued_at") else "")
        if s.get("ready"):
            return "manual", (f"SEMP content ready ({s.get('parts', 0)}/{s.get('of', 0)} parts): export it, review it "
                              "and record the issue (instructor sign-off)")
        return "fail", ("Missing evidence: the SEMP generator has no content yet"
                        + (f" ({s.get('parts', 0)}/{s.get('of', 0)} parts)" if s.get("of") else ""))
    if kind == "debris":
        d = ev.get("debris")
        if not d:
            return "fail", "Missing evidence: no debris assessment run"
        if d.get("status") == "accepted":
            life = d.get("lifetime_y")
            return "pass", ("Debris assessment accepted" + (f" at {str(d.get('accepted_gate')).upper()}" if d.get("accepted_gate") else "")
                            + (f": orbital lifetime {life:.1f} y" if isinstance(life, (int, float)) else ""))
        return "fail", f"Debris assessment is {d.get('status') or 'draft'}, not accepted"
    if kind == "changes":
        due = [c for c in ev.get("changes") or [] if _due_by(c.get("decision_gate"), canonical)]
        open_ = [c for c in due if str(c.get("status") or "").lower() not in CHANGE_DECIDED]
        if not due:
            return "pass", "No change proposal is due at this review"
        if open_:
            return "fail", "Not decided: " + ", ".join(c.get("code") or c.get("id", "") for c in open_[:12])
        return "pass", "Decided: " + ", ".join(f"{c.get('code')} ({c.get('status')})" for c in due[:12])
    if kind == "icds":
        icds = ev.get("icds") or []
        if not icds:
            return "fail", "Missing evidence: no ICD issued yet"
        low = [i for i in icds if i.get("state") not in ("issue_a", "issue_b", "baselined")]
        unsigned = [i for i in icds if i not in low and not i.get("signed_by_both")]
        if low or unsigned:
            parts = []
            if low:
                parts.append("below Issue A: " + ", ".join(i.get("icd_ref", "") for i in low[:10]))
            if unsigned:
                parts.append("not signed by both owners: " + ", ".join(i.get("icd_ref", "") for i in unsigned[:10]))
            return "fail", f"{len(icds) - len(low) - len(unsigned)}/{len(icds)} ICDs at Issue A and signed; " + "; ".join(parts)
        return "pass", f"{len(icds)}/{len(icds)} ICDs at Issue A or later, signed by both owners"
    if kind == "reliability":
        r, f = ev.get("reliability") or {}, ev.get("fmea") or {}
        miss = []
        if not r.get("computed"):
            miss.append("reliability block diagram not computed")
        if not f.get("rows"):
            miss.append("FMEA worksheet empty")
        if miss:
            return "fail", "Missing evidence: " + "; ".join(miss)
        val = r.get("system")
        return "pass", ((f"Mission reliability {val:.3f}" if isinstance(val, (int, float)) else "Reliability computed")
                        + (f" over {r['horizon_months']:g} months" if isinstance(r.get("horizon_months"), (int, float)) else "")
                        + f"; FMEA {f['rows']} lines over {len(f.get('subsystems') or [])} subsystems")
    if kind == "thermal":
        t = ev.get("thermal") or {}
        nodes = int(t.get("nodes") or 0)
        cases = t.get("cases") or []
        solved = {c.get("kind") for c in cases if c.get("solved")}
        miss = []
        if nodes < 6:
            miss.append(f"{nodes} node(s), at least 6 needed")
        for k in ("hot", "cold"):
            if k not in solved:
                miss.append(f"no solved {k} case")
        neg = [c for c in cases if isinstance(c.get("min_margin_c"), (int, float)) and c["min_margin_c"] < 0]
        if neg:
            miss.append("negative design margin: " + ", ".join(f"{c.get('code')} {c['min_margin_c']:.1f} °C" for c in neg))
        if miss:
            return "fail", "Missing evidence: " + "; ".join(miss)
        mm = [c["min_margin_c"] for c in cases if isinstance(c.get("min_margin_c"), (int, float))]
        return "pass", f"{nodes} nodes; hot and cold cases solved" + (f"; smallest design margin {min(mm):.1f} °C" if mm else "")
    return "not_evaluated", ""


def readiness_criteria(canonical: str, evidence: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The review-readiness criteria of canonical gate ``canonical`` (SRR, PDR), evaluated on the
    evidence ``services/gate_evidence.collect`` gathered. Must-pass: the gate is not ready until
    the work is done in the tool. Shapes as ``gate_evaluator`` criteria."""
    ev = evidence or {}
    out = []
    for spec in READINESS_CRITERIA.get(canonical, []):
        status, found = _probe(spec["probe"], canonical, ev)
        out.append({"id": spec["id"], "question": spec["question"], "category": spec["category"],
                    "priority": "must_pass", "advisory": False, "owner_seat": spec["owner_seat"],
                    "evidence_required": spec["evidence"], "evidence_key": f"readiness.{spec['probe']}",
                    "evidence_params": {}, "step": None, "mode": spec.get("mode", "auto"),
                    "status": status, "verdict": status, "evidence_found": found, "source": "review_readiness"})
    return out
