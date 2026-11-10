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
