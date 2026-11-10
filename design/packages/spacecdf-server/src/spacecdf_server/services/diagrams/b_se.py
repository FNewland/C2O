"""Systems-engineering diagrams of the V, drawn from the model (wave 3, 3.X1).

``context``            system of interest (segments, stations), the stakeholders and the launch
                       segment around it, with what they exchange
``stakeholder_map``    stakeholders grouped by category, with their authority (engagement), the
                       needs they hold and the objectives the needs serve
``ffbd``               top functions in ConOps-phase lanes, with the functional exchanges
``n2_functions``       N² of the top functions (``n2?view=functions``): the exchange items
``v_model``            the V: specification levels on the left (counts from the store), the
                       verification stages and validation activities on the right, the reviews
                       and the documents each review baselines
``trade_matrix``       one trade (``?focus=<trade id>``): criteria × options with weights, the
                       weighted totals and the ±20 % weight sensitivity
``budget_flowdown``    the allocation ledger: limit → system margin → allocation per element
                       (mass, orbit-average power, data), with the CBE behind each line
``verification_flow``  requirement level → verification method → model → closing stage

Every figure reads the stored model and the export sections (``DiagramData.se``: the same data
the review packs print), never the baseline files. What is missing becomes a gap.

Section items read here (owners fill them in wave 3; keys tolerated with or without ``_json``):

* ``stakeholders.items``  {id|code, name, category, role, authority, engagement, needs[]}
  (falls back to ``need.stakeholders``); ``stakeholders.needs`` {id|code, need|text,
  stakeholder(s)}; ``stakeholders.moes`` {code|id, name, objectives[], needs[], placeholder}
* ``validation.items``    {code, title, stage, needs[], moes[], status}
* ``allocations.items``   {element_code, budget_type, line_kind, value, unit, cbe, margined,
  requirement_code, owner_seat, status}; ``allocations.closure`` {budget_type: {limit, …}}
* ``trades.items``        {id, state{title, options, criteria, scores, level, …}, evaluation}
"""
from __future__ import annotations

import re
from typing import Any

from . import layout as L
from .base import Diagram, T, clip, plain, prov, text_w
from .data import DiagramData

# ───────────────────────────────────────────────────────────── helpers


def g(obj: Any, *keys: str, default: Any = None) -> Any:
    """First non-empty value among ``keys`` (each also tried with ``_json``)."""
    if obj is None:
        return default
    for k in keys:
        for kk in (k, k + "_json"):
            v = obj.get(kk) if isinstance(obj, dict) else getattr(obj, kk, None)
            if v not in (None, "", [], {}):
                return v
    return default


def as_list(v: Any) -> list:
    if v is None or v == "":
        return []
    if isinstance(v, (list, tuple, set)):
        return [x for x in v if x not in (None, "")]
    if isinstance(v, str):
        return [s.strip() for s in re.split(r"[,;]", v) if s.strip()]
    return [v]


def sec(d: DiagramData, name: str) -> dict:
    s = (d.se or {}).get(name) or {}
    return s if isinstance(s, dict) else {}


def is_stub(s: dict | None) -> bool:
    return isinstance(s, dict) and s.get("status") == "not_implemented"


def _num(v: Any) -> float | None:
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _fmt(v: Any, nd: int = 3) -> str:
    x = _num(v)
    if x is None:
        return "—"
    s = f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return s or "0"


def size_of(label: Any, sub: Any = None, *, minw: float = 110, maxw: float = 260, lines: int = 1) -> tuple[float, float]:
    w = max(text_w(label, 13, True), text_w(sub, 12) if sub else 0) + 24
    return max(minw, min(maxw, w)), 30 + (16 * lines if sub else 0)


def stakeholders(d: DiagramData) -> list[dict]:
    """Stakeholder register: the stakeholders section, else the mission need's list."""
    st = sec(d, "stakeholders")
    items = list(st.get("items") or []) if not is_stub(st) else []
    if not items:
        items = list(sec(d, "need").get("stakeholders") or [])
        if not items and d.study is not None and getattr(d.study, "mission_need", None) is not None:
            from ..export_context.sections._util import dump
            items = dump(list(getattr(d.study.mission_need, "stakeholders", None) or [])) or []
    out = []
    for i, s in enumerate(items):
        if not isinstance(s, dict):
            continue
        out.append({"id": str(g(s, "code", "id", default=f"STK-{i + 1:02d}")), "name": str(g(s, "name", default="?")),
                    "category": str(g(s, "category", default="") or "").replace("_", " ").strip(),
                    "role": str(g(s, "role", default="") or ""), "authority": str(g(s, "authority", default="") or ""),
                    "engagement": str(g(s, "engagement", default="") or ""),
                    "needs": [str(x) for x in as_list(g(s, "needs", "need_codes", default=[]))]})
    return out


def need_rows(d: DiagramData) -> list[dict]:
    """Stakeholder needs {id, text}: the stakeholders section, else the SN-* requirement rows."""
    st = sec(d, "stakeholders")
    out = []
    for n in (st.get("needs") or []) if not is_stub(st) else []:
        if isinstance(n, dict):
            out.append({"id": str(g(n, "code", "id", default="")), "text": str(g(n, "need", "text", "statement", default=""))})
    if not out:
        for r in d.requirements:
            if r.get("level") == "stakeholder" or str(r.get("code") or "").startswith("SN-"):
                out.append({"id": r.get("code") or r["id"], "text": r.get("text") or ""})
    return sorted(out, key=lambda n: n["id"])


def moe_rows(d: DiagramData) -> list[dict]:
    st = sec(d, "stakeholders")
    out = []
    for m in (st.get("moes") or []) if not is_stub(st) else []:
        if isinstance(m, dict):
            out.append({"id": str(g(m, "code", "id", default="")), "name": str(g(m, "name", "measure", default="")),
                        "objectives": [str(x) for x in as_list(g(m, "objectives", "objective_codes", default=[]))],
                        "needs": [str(x) for x in as_list(g(m, "needs", "need_codes", default=[]))],
                        "placeholder": bool(g(m, "placeholder", default=False))})
    return out


def objectives(d: DiagramData) -> list[dict]:
    return [o for o in (sec(d, "need").get("objectives") or []) if isinstance(o, dict) and o.get("id")]


_FCODE = re.compile(r"^(F\d+(?:\.\d+)*)\b\s*[:.\-–]?\s*(.*)$")


def fcode(f: dict) -> str:
    """The function code (F1, F1.3.2): ``code``, an F-style external id, or the name prefix."""
    for k in ("code", "external_id"):
        v = str(f.get(k) or "")
        if re.match(r"^F\d+(\.\d+)*$", v):
            return v
    m = _FCODE.match(str(f.get("name") or ""))
    return m.group(1) if m else ""


def fname(f: dict) -> str:
    m = _FCODE.match(str(f.get("name") or ""))
    return (m.group(2) or f.get("name") or "") if m else str(f.get("name") or "")


def _code_key(c: str) -> tuple:
    return tuple(int(x) if x.isdigit() else 0 for x in re.findall(r"\d+", c or "")) or (999,)


def top_functions(d: DiagramData) -> tuple[list[dict], dict[str, str]]:
    """(top functions in code order, {function id: top ancestor id})."""
    ids = {f["id"]: f for f in d.functions}
    top: dict[str, str] = {}
    for f in d.functions:
        cur, n = f, 0
        while cur.get("parent_id") in ids and n < 20:
            cur = ids[cur["parent_id"]]
            n += 1
        top[f["id"]] = cur["id"]
    roots = [f for f in d.functions if f.get("parent_id") not in ids]
    # a single root above the top functions (the mission function) is skipped
    if len(roots) == 1:
        kids = [f for f in d.functions if f.get("parent_id") == roots[0]["id"]]
        if len(kids) > 1:
            root = roots[0]["id"]
            for fid in list(top):
                cur, n = ids[fid], 0
                while cur.get("parent_id") not in (root, None) and cur.get("parent_id") in ids and n < 20:
                    cur = ids[cur["parent_id"]]
                    n += 1
                top[fid] = cur["id"] if cur["id"] != root else root
            roots = kids
    roots.sort(key=lambda f: (_code_key(fcode(f)), f.get("name") or ""))
    return roots, top


def user_requirements(d: DiagramData) -> list[dict]:
    """Requirements the V counts: the team's rows, without stakeholder needs (SN-*), objective
    rows (OBJ-*) or interface requirements generated from links (IR-*)."""
    return [r for r in d.requirements if not r.get("generated_interface") and r.get("level") != "stakeholder"
            and not str(r.get("code") or "").startswith(("OBJ-", "SN-", "IR-"))]


def _seat(s: Any) -> str:
    return str(s or "").replace("_", " ")


# ───────────────────────────────────────────────────────────── context diagram

#: which part of the system of interest a stakeholder deals with (keywords on role, category, name)
_CTX_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("launch", ("launch",)),
    ("space", ("orbit", "space operator", "non-human", "debris population")),
    ("user", ("science", "user", "data", "communit", "beneficiar", "public", "researcher")),
    ("ground", ("regulator", "operator", "operations", "licens", "spectrum", "station", "host site", "land-use")),
    ("mission", ("sponsor", "fund", "agency", "student", "partner", "team")),
)


def context_target(s: dict) -> str:
    blob = " ".join((s.get("role") or "", s.get("category") or "", s.get("name") or "")).lower()
    role = (s.get("role") or "").lower()
    if role == "regulator":
        return "ground"
    if role == "operator":
        return "ground"
    if role in ("sponsor",):
        return "mission"
    for target, keys in _CTX_RULES:
        if any(k in blob for k in keys):
            return target
    return "mission"


def _segments(d: DiagramData) -> dict[str, dict]:
    """{segment kind: element} for the segments of the product tree (space, ground, user, launch …)."""
    out: dict[str, dict] = {}
    for e in d.elements:
        if e.get("element_type") != "segment":
            continue
        seg = (e.get("segment") or "").lower() or (e.get("name") or "").split()[0].lower()
        if "science" in (e.get("name") or "").lower() or seg in ("user", "science"):
            seg = "user"
        out.setdefault(seg, e)
    return out


def _stations(d: DiagramData) -> list[dict]:
    out = []
    for e in d.elements:
        p = e.get("performance") if isinstance(e.get("performance"), dict) else {}
        if (p.get("lat") is not None or p.get("latitude") is not None) and d.segment(e) == "ground":
            out.append(e)
    return sorted(out, key=lambda e: e.get("name") or "")


def _under(d: DiagramData, root_id: str | None) -> set[str]:
    if not root_id:
        return set()
    kids: dict[str, list[str]] = {}
    for e in d.elements:
        kids.setdefault(e.get("parent_id") or "", []).append(e["id"])
    out, stack = set(), [root_id]
    while stack:
        x = stack.pop()
        if x in out:
            continue
        out.add(x)
        stack.extend(kids.get(x, []))
    return out


def context(d: DiagramData, **_: Any) -> dict:
    D = Diagram("context", T("Context diagram"), "graph",
                T("System of interest (segments and stations) and the external entities it exchanges with"))
    D.source("elements", "stakeholders", "link cases", "interfaces")
    segs = _segments(d)
    sh = stakeholders(d)
    if not segs:
        D.empty(T("No segments yet: add the space and ground segments in Blocks."))
        D.gap("no_segments", T("missing: segments of the system of interest"), severity="alarm", fix="blocks")
        return D.finish()
    stations = _stations(d)
    links = sec(d, "links")
    cases = [c for c in (links.get("items") or []) if isinstance(c, dict)]
    soi_order = [k for k in ("space", "ground", "operations", "user") if k in segs] + \
        [k for k in segs if k not in ("space", "ground", "operations", "user", "launch")]
    # segment boxes (centre column)
    seg_sub: dict[str, Any] = {}
    for k in soi_order:
        e = segs[k]
        kids = [c for c in d.elements if c.get("parent_id") == e["id"]]
        if k == "ground" and stations:
            seg_sub[k] = T("{{n}} stations: {{names}}", n=len(stations),
                           names=", ".join(clip(re.sub(r"^GS\s+", "", s.get("name") or ""), 14) for s in stations))
        elif k == "space":
            sc = next((c for c in kids if c.get("element_type") == "system"), None)
            seg_sub[k] = clip(sc.get("name"), 44) if sc else None
        else:
            seg_sub[k] = clip(", ".join(c.get("name") or "" for c in kids), 44) if kids else None
    SW = max([size_of(segs[k].get("name"), seg_sub.get(k), maxw=340)[0] for k in soi_order] + [260])
    # externals: the stakeholders, the launch segment
    ext: list[dict] = []
    if "launch" in segs:
        ls = segs["launch"]
        kids = [c.get("name") for c in d.elements if c.get("parent_id") == ls["id"]]
        ext.append({"id": ls["id"], "label": ls.get("name"), "sub": clip(", ".join(kids), 34) if kids else T("Launch segment"),
                    "target": "space", "style": "muted", "kind": "launch", "ref": {"kind": "element", "id": ls["id"]},
                    "prov": prov("element", ls["id"]), "edge": T("deployer interface, launch environment")})
    for s in sh:
        tgt = context_target(s)
        cat = s["category"] or ""
        style = "accent" if "authority" in cat or "rights" in cat else ("muted" if "affected" in cat else "default")
        ext.append({"id": "sh:" + s["id"], "label": clip(s["name"], 34), "sub": f"{s['id']} · {clip(cat or s['role'] or '—', 24)}",
                    "target": tgt if tgt in segs or tgt == "mission" else ("ground" if "ground" in segs else soi_order[0]),
                    "style": style, "kind": "stakeholder", "ref": {"kind": "stakeholder", "id": s["id"]},
                    "prov": prov("stakeholder", s["id"]), "edge": None,
                    "s": s})
    # two balanced columns: externals in the order of the segment they deal with (launch and
    # space first, the ground and user segments last), first half on the left
    seg_rank = {k: i for i, k in enumerate(["launch", "mission", "space", *soi_order])}
    ext = [x for _, x in sorted(enumerate(ext), key=lambda ix: (seg_rank.get(ix[1]["target"], 99), ix[0]))]
    half = (len(ext) + 1) // 2
    left, right = ext[:half], ext[half:]
    def esize(x): return size_of(x["label"], x["sub"], minw=170, maxw=250)
    LW = max([esize(x)[0] for x in left] + [170])
    lane_l = 26 + 7 * max(1, len(left))
    lane_r = 26 + 7 * max(1, len(right))
    xs = 16 + LW + lane_l + 40
    y_top = 40.0
    # SOI group with the segments stacked
    seg_pos: dict[str, dict] = {}
    y = y_top + 34
    for k in soi_order:
        w, h = size_of(segs[k].get("name"), seg_sub.get(k), minw=SW, maxw=SW)
        seg_pos[k] = {"x": xs + 20, "y": y, "w": SW, "h": h + 6}
        y += h + 6 + 46
    soi_h = y - 46 + 20 - y_top
    mission = next((e for e in d.elements if e.get("element_type") == "mission"), None)
    D.group("soi", T("System of interest: {{name}}", name=clip((mission or {}).get("name") or getattr(d.study, "name", "") or "", 40)),
            xs, y_top, SW + 40, soi_h, style="envelope", p=prov("element", (mission or {}).get("id")))
    for k in soi_order:
        b = seg_pos[k]
        e = segs[k]
        D.node(e["id"], clip(e.get("name"), 36), b["x"], b["y"], b["w"], b["h"], sub=seg_sub.get(k), style="emph",
               ref={"kind": "element", "id": e["id"]}, p=prov("element", e["id"]))
    # links between the segments (stacked: straight vertical)
    ids_of = {k: _under(d, segs[k]["id"]) for k in soi_order}
    rows: list[list] = []

    def between(a: str, b: str) -> list[dict]:
        A, B = ids_of.get(a, set()), ids_of.get(b, set())
        return [i for i in d.interfaces if (i.get("from_element_id") in A and i.get("to_element_id") in B)
                or (i.get("from_element_id") in B and i.get("to_element_id") in A)]

    for a, b in zip(soi_order, soi_order[1:]):
        pa, pb = seg_pos[a], seg_pos[b]
        ifs = between(a, b)
        if a == "space" and b == "ground":
            bands = sorted({str(c.get("band") or "") for c in cases if c.get("band")})
            lab = T("{{bands}} link: {{n}} link cases", bands="/".join(bands) or "RF", n=len(cases)) if cases else \
                (T("{{n}} interfaces", n=len(ifs)) if ifs else None)
        else:
            lab = T("{{n}} interfaces", n=len(ifs)) if ifs else None
        cx = pa["x"] + pa["w"] / 2
        D.edge(f"seg-{a}-{b}", segs[a]["id"], segs[b]["id"], [(cx, pa["y"] + pa["h"]), (cx, pb["y"])], arrow="both",
               label=lab, style={"type": "rf" if a == "space" and b == "ground" else "data", "dash": "", "width": 1.6},
               p=prov("derived", note="interfaces and link cases between the segments"))
        rows.append([segs[a].get("name"), T("Segment"), "", segs[b].get("name"), plain(lab) if lab else "—"])
    # externals in two columns and their edges
    y_l, y_r = y_top + 10, y_top + 10
    k_l = k_r = 0
    for x in ext:
        w, h = esize(x)
        side = "l" if x in left else "r"
        if side == "l":
            bx, by = 16.0 + (LW - w), y_l
            y_l += h + 12
        else:
            bx, by = xs + SW + 40 + lane_r + 40, y_r
            y_r += h + 12
        D.node(x["id"], x["label"], bx, by, w, h, sub=x["sub"], style=x["style"], ref=x["ref"], p=x["prov"])
        tgt = x["target"]
        cy = by + h / 2
        if tgt == "mission" or tgt not in seg_pos:
            ty = y_top + 14
            tx_ = xs if side == "l" else xs + SW + 40
            tid = "soi"
        else:
            tb = seg_pos[tgt]
            ty = tb["y"] + tb["h"] / 2 + (((k_l if side == "l" else k_r) % 5) - 2) * 5
            tx_ = tb["x"] if side == "l" else tb["x"] + tb["w"]
            tid = segs[tgt]["id"]
        if side == "l":
            mx = 16 + LW + 20 + k_l * 7
            k_l += 1
            pts = [(bx + w, cy), (mx, cy), (mx, ty), (tx_, ty)]
        else:
            mx = xs + SW + 40 + 20 + k_r * 7
            k_r += 1
            pts = [(bx, cy), (mx, cy), (mx, ty), (tx_, ty)]
        D.edge(f"ext-{x['id']}", x["id"], tid, pts, arrow="both" if x["kind"] == "launch" else "none",
               style={"type": "data", "dash": "" if x["kind"] == "launch" else "5 3", "width": 1.2, "color": "line"},
               p=x["prov"])
        rows.append([x["label"] if isinstance(x["label"], str) else plain(x["label"]),
                     T("Launch segment") if x["kind"] == "launch" else T("Stakeholder"),
                     (x.get("s") or {}).get("category") or "", segs[tgt].get("name") if tgt in segs else T("System of interest"),
                     plain(x.get("edge")) if x.get("edge") else ((x.get("s") or {}).get("engagement") or "—")])
    D.legend([{"kind": "box", "style": "emph", "label": T("Segment of the system of interest")},
              {"kind": "box", "style": "accent", "label": T("Decision authority or rights-holder")},
              {"kind": "box", "style": "default", "label": T("Beneficiary")},
              {"kind": "box", "style": "muted", "label": T("Affected party or launch segment")}])
    # gaps
    expected, filled = 4, 0
    if not sh:
        D.gap("no_stakeholders", T("missing: stakeholder register"), severity="alarm", fix="mission")
    else:
        filled += 1
    if not stations:
        D.gap("no_stations", T("missing: ground stations"), fix="blocks")
    else:
        filled += 1
    if "launch" not in segs:
        D.gap("no_launch", T("missing: launch segment"), fix="blocks")
    else:
        filled += 1
    if sh and not any(s["role"] == "regulator" or "regulator" in s["name"].lower() for s in sh):
        D.gap("no_regulator", T("missing: the regulator among the stakeholders"), fix="mission")
    else:
        filled += int(bool(sh))
    no_cat = [s for s in sh if not s["category"]]
    if no_cat:
        D.gap("no_category", T("missing: category for {{n}} stakeholders", n=len(no_cat)), len(no_cat), fix="mission")
    D.completeness(expected, filled)
    D.m["counts"] = {"stakeholders": len(sh), "stations": len(stations), "segments": len(soi_order),
                     "launch": int("launch" in segs), "regulators": sum(1 for s in sh if s["role"] == "regulator"
                                                                       or "regulator" in s["name"].lower())}
    D.table([T("Entity"), T("Kind"), T("Category"), T("Connects to"), T("Exchange")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── stakeholder map

def stakeholder_map(d: DiagramData, **_: Any) -> dict:
    D = Diagram("stakeholder_map", T("Stakeholder map"), "graph",
                T("Stakeholders by category with their engagement; the needs they hold and the objectives the needs serve"))
    D.source("stakeholders", "needs", "MOEs", "objectives")
    sh = stakeholders(d)
    if not sh:
        D.empty(T("No stakeholders yet: fill the stakeholder register of the mission need."))
        D.gap("no_stakeholders", T("missing: stakeholder register"), severity="alarm", fix="mission")
        return D.finish()
    needs = need_rows(d)
    objs = objectives(d)
    moes = moe_rows(d)
    need_ids = {n["id"] for n in needs}
    # need -> objectives: from the MOEs (needs × objectives), else from the objective's stakeholders
    n2o: dict[str, set[str]] = {}
    for m in moes:
        for n in m["needs"]:
            n2o.setdefault(n, set()).update(m["objectives"])
    obj_ids = [o["id"] for o in objs]
    # groups by category (order of first appearance)
    cats: list[str] = []
    for s in sh:
        c = s["category"] or "—"
        if c not in cats:
            cats.append(c)
    W1 = max(size_of(s["name"], s["engagement"], minw=200, maxw=300)[0] for s in sh)
    x1, y = 24.0, 40.0
    pos: dict[str, dict] = {}
    for c in cats:
        members = [s for s in sh if (s["category"] or "—") == c]
        gy = y
        y += 26
        for s in members:
            w, h = size_of(clip(s["name"], 44), s["engagement"] or "—", minw=W1, maxw=W1)
            pos["sh:" + s["id"]] = {"x": x1, "y": y, "w": W1, "h": h}
            y += h + 8
        D.group("cat:" + c, c, x1 - 10, gy, W1 + 20, y - gy + 2, style="lane", p=prov("stakeholder", note="category"))
        y += 14
    total_h = y
    # needs column
    NW = 92.0
    xn = x1 + W1 + 110
    nh = 26.0
    step = max(nh + 6, (total_h - 60) / max(1, len(needs)))
    for i, n in enumerate(needs):
        pos["need:" + n["id"]] = {"x": xn, "y": 50 + i * step, "w": NW, "h": nh}
    # objectives column
    xo = xn + NW + 110
    ostep = max(40.0, (total_h - 60) / max(1, len(obj_ids)))
    for i, o in enumerate(objs):
        pos["obj:" + o["id"]] = {"x": xo, "y": 50 + i * ostep, "w": 120, "h": 34}
    for s in sh:
        b = pos["sh:" + s["id"]]
        badges = []
        if "authority" in (s["category"] or "") or "rights" in (s["category"] or ""):
            badges.append(T("decides"))
        D.node("sh:" + s["id"], clip(s["name"], 44), b["x"], b["y"], b["w"], b["h"], sub=clip(s["engagement"] or "—", 44),
               style="accent" if badges else "default", badges=badges, ref={"kind": "stakeholder", "id": s["id"]},
               p=prov("stakeholder", s["id"]), tip=s["authority"] or None)
    for n in needs:
        b = pos["need:" + n["id"]]
        D.node("need:" + n["id"], n["id"], b["x"], b["y"], b["w"], b["h"], style="emph", p=prov("requirement", n["id"]),
               tip=clip(n["text"], 160))
    for o in objs:
        b = pos["obj:" + o["id"]]
        D.node("obj:" + o["id"], o["id"], b["x"], b["y"], b["w"], b["h"], sub=str(o.get("priority") or ""),
               style="ok" if str(o.get("priority")) == "primary" else "default", p=prov("derived", o["id"], note="objective"))
    k = 0
    unlinked = []
    rows = []
    for s in sh:
        own = [n for n in s["needs"] if n in need_ids]
        if not own:
            unlinked.append(s)
        for n in own:
            a, b = pos["sh:" + s["id"]], pos["need:" + n]
            mx = xn - 40 - (k % 6) * 6
            D.edge(f"sn-{k}", "sh:" + s["id"], "need:" + n, [(a["x"] + a["w"], a["y"] + a["h"] / 2), (mx, a["y"] + a["h"] / 2),
                                                           (mx, b["y"] + b["h"] / 2), (b["x"], b["y"] + b["h"] / 2)],
                   style={"type": "data", "dash": "", "width": 1.0, "color": "line"}, p=prov("stakeholder", s["id"]))
            k += 1
        rows.append([s["id"], s["name"], s["category"] or "—", s["engagement"] or "—", s["authority"] or "—",
                     ", ".join(s["needs"]) or "—"])
    j = 0
    for n in needs:
        for o in sorted(n2o.get(n["id"], set())):
            if "obj:" + o not in pos:
                continue
            a, b = pos["need:" + n["id"]], pos["obj:" + o]
            mx = xo - 40 - (j % 6) * 6
            D.edge(f"no-{j}", "need:" + n["id"], "obj:" + o, [(a["x"] + a["w"], a["y"] + a["h"] / 2), (mx, a["y"] + a["h"] / 2),
                                                          (mx, b["y"] + b["h"] / 2), (b["x"], b["y"] + b["h"] / 2)],
                   style={"type": "data", "dash": "4 3", "width": 1.0, "color": "line"}, p=prov("derived", note="MOE"))
            j += 1
    D.label(xn, 36, T("Needs"), size=12, weight=600, style="text3")
    D.label(xo, 36, T("Objectives"), size=12, weight=600, style="text3")
    if unlinked:
        D.gap("no_needs", T("missing: needs for {{n}} stakeholders", n=len(unlinked)), len(unlinked), fix="mission")
    if not needs:
        D.gap("no_need_rows", T("missing: stakeholder needs (SN-…)"), fix="mission")
    if needs and not n2o:
        D.gap("no_moes", T("missing: measures of effectiveness linking needs to objectives"), fix="mission")
    placeholders = [m["id"] for m in moes if m["placeholder"]]
    if placeholders:
        D.gap("moe_placeholder", T("to co-define: {{ids}}", ids=", ".join(placeholders)), len(placeholders), severity="info",
              fix="mission")
    D.legend([{"kind": "box", "style": "accent", "label": T("Decision authority or rights-holder")},
              {"kind": "line", "type": "data", "dash": "4 3", "label": T("Need serves objective (through an MOE)")}])
    D.completeness(len(sh) + 1, len(sh) - len(unlinked) + int(bool(n2o)))
    D.m["counts"] = {"stakeholders": len(sh), "categories": len(cats), "needs": len(needs), "moes": len(moes),
                     "placeholders": len(placeholders)}
    D.table([T("Id"), T("Stakeholder"), T("Category"), T("Engagement"), T("Authority"), T("Needs")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── FFBD

#: ConOps phases, in order (English text = key)
PHASES = ("Launch and early orbit", "Commissioning", "Nominal operations", "Continuous (every phase)",
          "Contingency", "End of life")
_PHASE_KEYS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (5, ("dispos", "end of life", "passivat", "de-orbit", "deorbit")),
    (0, ("launch", "separat", "deploy")),
    (1, ("commission", "calibrat", "first light")),
    (4, ("protect", "safe", "fault", "anomal", "contingen")),
    (3, ("power", "temperat", "thermal", "attitude", "time and position", "manage the spacecraft", "manage", "structure")),
    (2, ("acquire", "image", "process", "store", "communicat", "ground", "product", "deliver", "operate", "observe")),
)


def phase_of(f: dict) -> int:
    """ConOps phase of a top function: its own field (``conops_phase``/``phase``), else by keyword."""
    for k in ("conops_phase", "phase"):
        v = str(f.get(k) or (f.get("external_ids_json") or {}).get(k) or "").lower()
        if v:
            for i, p in enumerate(PHASES):
                if v[:6] in p.lower():
                    return i
    name = fname(f).lower()
    for i, keys in _PHASE_KEYS:
        if any(k in name for k in keys):
            return i
    return 2


def _top_exchanges(d: DiagramData, top: dict[str, str]) -> dict[tuple[str, str], list[str]]:
    pairs: dict[tuple[str, str], list[str]] = {}
    for x in d.exchanges:
        a, b = top.get(x["from_fn"]), top.get(x["to_fn"])
        if not a or not b or a == b:
            continue
        pairs.setdefault((a, b), []).append(x.get("name") or "")
    return pairs


def ffbd(d: DiagramData, **_: Any) -> dict:
    D = Diagram("ffbd", T("Functional flow block diagram"), "graph",
                T("Top functions in ConOps-phase lanes (left to right) with the functional exchanges between them; the items are in the table and the functional N²"))
    D.source("functions", "functional exchanges")
    roots, top = top_functions(d)
    if not roots:
        D.empty(T("No functions yet: build the function tree in Functions."))
        D.gap("no_functions", T("missing: function tree"), severity="alarm", fix="functions")
        return D.finish()
    pairs = _top_exchanges(d, top)
    ids = [f["id"] for f in roots]
    rank = {f["id"]: phase_of(f) for f in roots}
    # compact the ranks to the phases present
    used = sorted(set(rank.values()))
    rmap = {r: i for i, r in enumerate(used)}
    ranks = {k: rmap[v] for k, v in rank.items()}
    lab = {f["id"]: (fcode(f) + " " if fcode(f) else "") + fname(f) for f in roots}

    def size(n: str) -> tuple[float, float]:
        return size_of(clip(lab[n], 34), None, minw=150, maxw=240)
    edges = list(pairs)
    pos, routed = L.layered(ids, edges, size, ranks=ranks, rank_gap=150, node_gap=40, x0=26, y0=70, lane=5)
    # lanes
    for r in range(len(used)):
        col = [pos[n] for n in ids if ranks[n] == r]
        if not col:
            continue
        x0 = min(b["x"] for b in col) - 10
        x1 = max(b["x"] + b["w"] for b in col) + 10
        y1 = max(b["y"] + b["h"] for b in col) + 14
        D.group(f"phase{r}", T(PHASES[used[r]]), x0, 40, x1 - x0, y1 - 40, style="lane", p=prov("derived", note="ConOps phase"))
    by = {f["id"]: f for f in roots}
    for n in ids:
        b = pos[n]
        f = by[n]
        D.node(n, clip(lab[n], 34), b["x"], b["y"], b["w"], b["h"], style="default",
               ref={"kind": "function", "id": n}, p=prov("function", n), tip=f.get("description") or None)
    rows = []
    for i, e in enumerate(routed):
        items = pairs.get((e["from"], e["to"])) or []
        D.edge(f"x{i}", e["from"], e["to"], e["points"], title="; ".join(items),
               style={"type": "data", "dash": "", "width": 1.0 + min(1.5, 0.3 * len(items))},
               p=prov("function", note="functional exchange"))
        rows.append([lab[e["from"]], lab[e["to"]], "; ".join(items)])
    isolated = [lab[n] for n in ids if not any(n in p for p in pairs)]
    if not d.exchanges:
        D.gap("no_exchanges", T("missing: functional exchanges between the functions"), fix="functions")
    elif isolated:
        D.gap("isolated", T("missing: exchanges for {{n}} top functions", n=len(isolated)), len(isolated), fix="functions")
    D.legend([{"kind": "line", "type": "data", "label": T("Functional exchange (item)")}])
    D.completeness(len(ids), len(ids) - len(isolated) if d.exchanges else 0)
    D.m["counts"] = {"functions": len(ids), "exchange_pairs": len(pairs), "exchanges": sum(len(v) for v in pairs.values())}
    D.table([T("From"), T("To"), T("Items")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── functional N²

def n2_functions(d: DiagramData, **_: Any) -> dict:
    D = Diagram("n2", T("N² chart — functions"), "matrix",
                T("Row function sends to column function; the cells name the exchanged items"))
    D.source("functions", "functional exchanges")
    roots, top = top_functions(d)
    if len(roots) < 2:
        D.empty(T("An N² chart needs at least two functions."))
        D.gap("no_functions", T("missing: function tree"), severity="alarm", fix="functions")
        D.m["options"] = {"view": "functions"}
        return D.finish()
    pairs = _top_exchanges(d, top)
    idx = {f["id"]: k for k, f in enumerate(roots)}
    n = len(roots)
    cw, ch = 104.0, 44.0
    lab = [(fcode(f) + " " if fcode(f) else "") + fname(f) for f in roots]
    label_w = min(260.0, max(text_w(clip(x, 32), 12) for x in lab) + 18)
    x0, y0 = 16 + label_w, 40.0
    rows = []
    for k, f in enumerate(roots):
        D.label(16 + label_w - 8, y0 + k * ch + ch / 2 + 4, clip(lab[k], 32), anchor="end", size=12)
        D.label(x0 + k * cw + cw / 2, y0 - 8, fcode(f) or str(k + 1), anchor="middle", size=12, weight=600)
        for j in range(n):
            x, y = x0 + j * cw, y0 + k * ch
            if j == k:
                D.cell(x, y, cw, ch, text=clip(fcode(f) or fname(f), 12), style="diag-default", title=lab[k])
                continue
            items = pairs.get((f["id"], roots[j]["id"]))
            if items:
                D.cell(x, y, cw, ch, text=clip("; ".join(items), 16), style="n2",
                       title=f"{lab[k]} → {lab[j]}: " + "; ".join(items))
                rows.append([lab[k], lab[j], "; ".join(items)])
            else:
                D.cell(x, y, cw, ch, style="band" if (k + j) % 2 else "cell")
    linked = {idx[a] for a, _ in pairs} | {idx[b] for _, b in pairs}
    lonely = [lab[k] for k in range(n) if k not in linked]
    if lonely:
        D.gap("isolated", T("missing: exchanges for {{n}} top functions", n=len(lonely)), len(lonely), fix="functions")
    D.completeness(n, n - len(lonely))
    D.table([T("From"), T("To"), T("Items")], rows)
    D.m["options"] = {"view": "functions"}
    D.m["counts"] = {"functions": n, "cells": len(pairs)}
    return D.finish()


# ───────────────────────────────────────────────────────────── V diagram

#: left arm: (requirement levels counted, title, gates that baseline it)
V_LEFT = (
    ("needs", "Stakeholder needs and MOEs", ("MDR", "PRR")),
    (("mission",), "Mission requirements", ("PRR",)),
    (("segment",), "Segment requirements", ("SRR",)),
    (("system",), "System requirements", ("SRR", "PDR")),
    (("subsystem", "interface"), "Subsystem and interface requirements", ("PDR",)),
)
#: right arm, top to bottom: (stages counted, title)
V_RIGHT = (
    ("validation", "Validation"),
    (("IOV",), "Mission verification in orbit"),
    (("AR",), "Acceptance (flight model)"),
    (("QR",), "Qualification (system)"),
    (("CDR",), "Subsystem and unit verification"),
    (("PRR", "SRR", "PDR"), "Design verification by review and analysis"),
)
GATE_SEQ = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")


def stage_of(r: dict) -> str:
    return str(r.get("verification_stage") or r.get("verification_phase") or "").upper()


def _gate_documents() -> dict[str, list[str]]:
    """{gate: [titles of the documents its review data pack holds]} (pack catalogue, full ECSS)."""
    out: dict[str, list[str]] = {}
    try:
        from spacecdf_agents.exporters.docs.pack_catalog import plan_pack
        from .. import gate_profiles as gp
        prods = list(gp.load().get("products") or [])
        for gate in GATE_SEQ:
            plan = plan_pack(gate, profile=None, profile_products=prods)
            out[gate] = [dd.title.get("en") or dd.id for dd in plan.documents if not dd.file.startswith("data/")]
    except Exception:  # noqa: BLE001 — the V still draws without the document strip
        import logging
        logging.getLogger(__name__).info("pack catalogue for the V diagram failed", exc_info=True)
    return out


def v_model(d: DiagramData, **_: Any) -> dict:
    D = Diagram("v_model", T("V diagram"), "graph",
                T("Specification levels on the left, verification stages and validation on the right; counts from the store"))
    D.source("requirements", "stakeholders", "validation activities", "gate profile", "pack catalogue")
    reqs = user_requirements(d)
    if not reqs and not stakeholders(d):
        D.empty(T("No requirements yet: write or generate them in Requirements."))
        D.gap("no_requirements", T("missing: requirements"), severity="alarm", fix="requirements")
        return D.finish()
    needs = need_rows(d)
    moes = moe_rows(d)
    val = sec(d, "validation")
    acts = [a for a in (val.get("items") or []) if isinstance(a, dict)] if not is_stub(val) else []
    by_level: dict[str, int] = {}
    by_stage: dict[str, int] = {}
    for r in reqs:
        by_level[r.get("level") or "—"] = by_level.get(r.get("level") or "—", 0) + 1
        st = stage_of(r)
        if st:
            by_stage[st] = by_stage.get(st, 0) + 1
    W, H, dx, dy = 250.0, 58.0, 64.0, 82.0
    x_l0, y0 = 16.0, 50.0
    n_right = len(V_RIGHT)
    x_r0 = x_l0 + (n_right - 1) * dx + W + 120 + (n_right - 1) * dx
    left_ids, right_ids = [], []
    rows = []
    for i, (lv, title, gates) in enumerate(V_LEFT):
        if lv == "needs":
            n = len(needs)
            sub = T("{{n}} needs, {{m}} MOEs", n=n, m=len(moes))
        else:
            n = sum(by_level.get(x, 0) for x in lv)
            sub = T("{{n}} requirements", n=n)
        nid = f"L{i}"
        D.node(nid, T(title), x_l0 + i * dx, y0 + i * dy, W, H, sub=sub, style="accent", badges=list(gates),
               p=prov("requirement", note="count from the store"))
        left_ids.append(nid)
        rows.append([T(title), plain(sub), ", ".join(gates)])
    bi = len(V_LEFT)
    bx = (x_l0 + x_r0) / 2 + (bi - (n_right - 1)) * 0  # centred below
    bx = (x_l0 + bi * dx + x_r0 - (n_right - 1) * dx) / 2
    yb = y0 + (len(V_RIGHT) - 1) * dy + dy
    D.node("B", T("Detailed design and build"), bx, yb, W, H, sub=T("product baseline"), style="emph",
           badges=["CDR"], p=prov("derived"))
    for i, (st, title) in enumerate(V_RIGHT):
        if st == "validation":
            n = len(acts)
            codes = ", ".join(str(g(a, "code", "id", default="")) for a in acts[:8])
            sub = T("{{n}} validation activities: {{codes}}", n=n, codes=clip(codes, 16)) if n else T("no validation activity")
            badges = []
        else:
            n = sum(by_stage.get(x, 0) for x in st)
            sub = T("{{n}} requirements closed at {{stages}}", n=n,
                    stages=", ".join(f"{x} {by_stage.get(x, 0)}" for x in st) if len(st) > 1 else st[0])
            badges = list(st)
        nid = f"R{i}"
        D.node(nid, T(title), x_r0 - i * dx, y0 + i * dy, W, H, sub=sub, style="caution" if st != "validation" else "ok",
               badges=badges, p=prov("verification" if st != "validation" else "derived", note="count from the store"))
        right_ids.append(nid)
        rows.append([T(title), plain(sub), ", ".join(badges)])
    # arms
    for i in range(len(left_ids) - 1):
        a = (x_l0 + i * dx + W / 2, y0 + i * dy + H)
        b = (x_l0 + (i + 1) * dx + W / 2, y0 + (i + 1) * dy)
        D.edge(f"l{i}", left_ids[i], left_ids[i + 1], [a, (a[0], (a[1] + b[1]) / 2), (b[0], (a[1] + b[1]) / 2), b],
               style={"type": "tree", "dash": "", "width": 1.6, "color": "interactive"})
    a = (x_l0 + (bi - 1) * dx + W / 2, y0 + (bi - 1) * dy + H)
    D.edge("lb", left_ids[-1], "B", [a, (a[0], yb + H / 2), (bx, yb + H / 2)],
           style={"type": "tree", "dash": "", "width": 1.6, "color": "interactive"})
    last = n_right - 1
    b = (x_r0 - last * dx + W / 2, y0 + last * dy + H)
    D.edge("br", "B", right_ids[-1], [(bx + W, yb + H / 2), (b[0], yb + H / 2), b],
           style={"type": "tree", "dash": "", "width": 1.6, "color": "caution"})
    for i in range(last, 0, -1):
        a = (x_r0 - i * dx + W / 2, y0 + i * dy)
        b = (x_r0 - (i - 1) * dx + W / 2, y0 + (i - 1) * dy + H)
        D.edge(f"r{i}", right_ids[i], right_ids[i - 1], [a, (a[0], (a[1] + b[1]) / 2), (b[0], (a[1] + b[1]) / 2), b],
               style={"type": "tree", "dash": "", "width": 1.6, "color": "caution"})
    # verified-by links across the V (needs ↔ validation, levels ↔ stages)
    for i in range(len(left_ids)):
        y = y0 + i * dy + H / 2
        D.edge(f"v{i}", left_ids[i], right_ids[i], [(x_l0 + i * dx + W, y), (x_r0 - i * dx, y)], arrow="end",
               style={"type": "data", "dash": "4 4", "width": 1.0, "color": "line"}, faded=True)
    # reviews and documents strip
    docs = _gate_documents()
    ys = yb + H + 46
    D.label(x_l0, ys - 10, T("Reviews and the documents in each review data pack"), size=12, weight=600, style="text3")
    cwid = (x_r0 + W - x_l0) / len(GATE_SEQ)
    for k, gate in enumerate(GATE_SEQ):
        dl = docs.get(gate) or []
        D.cell(x_l0 + k * cwid, ys, cwid - 4, 44, text=gate.upper(), sub=T("{{n}} documents", n=len(dl)),
               style="on" if gate in ("mdr", "prr", "srr", "pdr") else "cell", title="; ".join(dl))
        rows.append([gate.upper(), T("{{n}} documents", n=len(dl)), "; ".join(dl)])
    D.legend([{"kind": "box", "style": "accent", "label": T("Specification (left of the V)")},
              {"kind": "box", "style": "caution", "label": T("Verification stage (right of the V)")},
              {"kind": "box", "style": "ok", "label": T("Validation")},
              {"kind": "line", "type": "data", "dash": "4 4", "label": T("Verified or validated by")}])
    missing_stage = [r for r in reqs if not stage_of(r)]
    if missing_stage:
        D.gap("no_stage", T("missing: verification stage for {{n}} requirements", n=len(missing_stage)), len(missing_stage),
              fix="requirements")
    if not acts:
        D.gap("no_validation", T("missing: validation activities (V1 …)"), fix="vv")
    if not needs:
        D.gap("no_needs", T("missing: stakeholder needs (SN-…)"), fix="mission")
    D.completeness(len(reqs) + 2, len(reqs) - len(missing_stage) + int(bool(acts)) + int(bool(needs)))
    D.m["counts"] = {"by_level": by_level, "by_stage": by_stage, "validation": len(acts), "needs": len(needs),
                     "moes": len(moes), "documents": {k: len(v) for k, v in docs.items()}}
    D.table([T("Level or stage"), T("Count"), T("Gates")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── trade matrix

def trade_items(d: DiagramData) -> list[dict]:
    t = sec(d, "trades")
    return [i for i in (t.get("items") or []) if isinstance(i, dict) and i.get("id")] if not is_stub(t) else []


def trade_ids(d: DiagramData) -> list[str]:
    return [i["id"] for i in trade_items(d)]


def _sens_20(state: dict, weights: dict[str, float], winner: str | None) -> dict[str, tuple[str | None, str | None]]:
    """Winner with each criterion's weight at −20 % and +20 % (the others rescaled to keep the sum)."""
    from ..trades import _shifted, _totals, _winner
    out: dict[str, tuple[str | None, str | None]] = {}
    for c in state.get("criteria") or []:
        w = weights.get(c, 0.0)
        res = []
        for f in (-0.2, 0.2):
            ww = _shifted(weights, c, f * w)
            res.append(_winner(_totals(state, ww)) if ww is not None else winner)
        out[c] = (res[0], res[1])
    return out


def trade_matrix(d: DiagramData, focus: str | None = None, **_: Any) -> dict:
    items = trade_items(d)
    D = Diagram("trade_matrix", T("Trade matrix"), "matrix",
                T("Criteria × options: weights, scores, weighted totals and the winner with each weight ±20 %"))
    D.source("trade studies")
    if not items:
        D.empty(T("No trade studies yet: record them in Decide."))
        D.gap("no_trades", T("missing: trade studies"), severity="warn", fix="decide")
        D.m["options"] = {"trades": [], "focus": None}
        return D.finish()
    it = next((i for i in items if i["id"] == focus), items[0])
    st = it.get("state") or {}
    ev = it.get("evaluation") or {}
    if not ev:
        from ..trades import evaluate
        ev = evaluate(st)
    D.m["title"] = T("Trade matrix — {{id}}", id=it["id"])
    D.m["subtitle"] = clip(st.get("title") or "", 90)
    opts = list(st.get("options") or [])
    crit = list(st.get("criteria") or [])
    weights = {c: float(w) for c, w in (ev.get("weights") or {}).items()}
    totals = {t["option"]: t for t in ev.get("totals") or []}
    winner = ev.get("winner")
    decided = (st.get("decision") or {}).get("selected")
    screened = set((st.get("screened") or {}).keys()) if isinstance(st.get("screened"), dict) else set(as_list(st.get("screened")))
    sens = _sens_20(st, weights, winner) if len(opts) > 1 else {}
    cw, rh = 84.0, 26.0
    datum = ev.get("datum")
    label_w = min(330.0, max([text_w(clip(c, 46), 12) for c in crit] + [120]) + 16)
    x0, y0 = 16 + label_w, 44.0
    xw = x0                                   # weight column
    xo = x0 + 60                              # option columns
    xs = xo + len(opts) * cw + 10             # sensitivity columns
    D.label(xw + 30, y0 - 10, T("Weight"), anchor="middle", size=12, weight=600)
    for j, o in enumerate(opts):
        D.label(xo + j * cw + cw / 2, y0 - 10, clip(o, 12), anchor="middle", size=12, weight=600,
                style="text3" if o in screened else "text2")
    D.label(xs + 40, y0 - 10, "−20 %", anchor="middle", size=12, weight=600)
    D.label(xs + 120, y0 - 10, "+20 %", anchor="middle", size=12, weight=600)
    rows = []
    flips = 0
    for i, c in enumerate(crit):
        y = y0 + i * rh
        D.label(x0 - 8, y + rh / 2 + 4, clip(c, 46), anchor="end", size=12)
        D.cell(xw, y, 56, rh, text=f"{weights.get(c, 0.0):.2f}", style="total")
        for j, o in enumerate(opts):
            v = ((st.get("scores") or {}).get(o) or {}).get(c)
            if v is None and o == datum:
                v = 0
            D.cell(xo + j * cw, y, cw, rh, text=_fmt(v, 2) if v is not None else "—",
                   style="muted" if o in screened else ("on" if o == winner else ("band" if i % 2 else "cell")))
        lo, hi = sens.get(c, (winner, winner))
        for k, wv in enumerate((lo, hi)):
            flip = wv != winner
            flips += int(flip)
            D.cell(xs + k * 80, y, 76, rh, text=clip(wv or "—", 10), style="caution" if flip else "ok")
        rows.append([c, f"{weights.get(c, 0.0):.3f}"] + [_fmt(((st.get("scores") or {}).get(o) or {}).get(c), 2) for o in opts]
                    + [lo or "—", hi or "—"])
    yt = y0 + len(crit) * rh + 6
    D.label(x0 - 8, yt + rh / 2 + 4, T("Weighted total"), anchor="end", size=12, weight=600)
    for j, o in enumerate(opts):
        tw = (totals.get(o) or {}).get("weighted")
        D.cell(xo + j * cw, yt, cw, rh, text=_fmt(tw, 2), style="on" if o == winner else "total")
    rows.append([plain(T("Weighted total")), "1.000"] + [_fmt((totals.get(o) or {}).get("weighted"), 2) for o in opts] + ["", ""])
    note = T("Winner {{w}}; decided {{d}}", w=winner or "—", d=decided or "—")
    D.label(16, yt + rh + 24, note, size=12, weight=600)
    D.legend([{"kind": "box", "style": "on", "label": T("Winner (highest weighted total)")},
              {"kind": "box", "style": "muted", "label": T("Screened out (fails a must criterion)")},
              {"kind": "box", "style": "caution", "label": T("The winner changes with this weight ±20 %")}])
    if not crit or not opts:
        D.gap("incomplete", T("missing: options or criteria"), severity="alarm", fix="decide")
    unscored = sum(1 for o in opts if o != datum for c in crit if ((st.get("scores") or {}).get(o) or {}).get(c) is None)
    if unscored:
        D.gap("unscored", T("missing: {{n}} scores", n=unscored), unscored, fix="decide")
    if not decided:
        D.gap("undecided", T("trade not decided"), severity="info", fix="decide")
    elif decided != winner:
        D.gap("decision_differs", T("decision {{d}} differs from the winner {{w}}: record the rationale", d=decided, w=winner or "—"),
              severity="info", fix="decide")
    if flips:
        D.gap("sensitive", T("{{n}} weight changes of ±20 % change the winner", n=flips), flips, severity="info", fix="decide")
    D.completeness(max(1, len(opts) * len(crit)), len(opts) * len(crit) - unscored)
    D.m["options"] = {"trades": [{"id": i["id"], "title": (i.get("state") or {}).get("title") or ""} for i in items],
                      "focus": it["id"]}
    D.m["counts"] = {"options": len(opts), "criteria": len(crit), "flips": flips, "winner": winner, "decided": decided}
    D.table([T("Criterion"), T("Weight")] + opts + ["−20 %", "+20 %"], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── budget flow-down

BUDGETS = (("mass", "Mass", "kg"), ("power_avg", "Orbit-average power", "W"), ("data", "Downlink data", "MB/day"))


def ledger_lines(d: DiagramData) -> list[dict]:
    a = sec(d, "allocations")
    return [x for x in (a.get("items") or []) if isinstance(x, dict)] if not is_stub(a) else []


def _is_reserve(x: dict) -> bool:
    return str(g(x, "line_kind", default="")) == "reserve" or str(g(x, "element_code", default="")).upper() == "SYS"


def budget_flowdown(d: DiagramData, **_: Any) -> dict:
    D = Diagram("budget_flowdown", T("Budget flow-down"), "graph",
                T("Limit → system margin held by Systems → allocation per element, with the current best estimate behind each line"))
    D.source("allocation ledger", "roll-up", "data budget")
    lines = ledger_lines(d)
    if not lines:
        D.empty(T("No allocation ledger yet: propose the allocations in Budget."))
        D.gap("no_ledger", T("missing: allocation ledger"), severity="alarm", fix="budget")
        return D.finish()
    alloc = sec(d, "allocations")
    closure = alloc.get("closure") if isinstance(alloc.get("closure"), dict) else {}
    ru = sec(d, "rollup")
    daily = (sec(d, "data_budget").get("daily") or {}) if isinstance(sec(d, "data_budget").get("daily"), dict) else {}
    margin_pct = _num((ru.get("mass") or {}).get("system_margin_percent"))
    y = 40.0
    rows = []
    sums: dict[str, float] = {}
    over = []
    for bt, title, unit in BUDGETS:
        mine = [x for x in lines if str(g(x, "budget_type", default="")) == bt]
        alloc_lines = [x for x in mine if not _is_reserve(x)]
        if not alloc_lines:
            continue
        cl = closure.get(bt) if isinstance(closure.get(bt), dict) else {}
        total = sum(_num(g(x, "value")) or 0.0 for x in alloc_lines)
        sums[bt] = round(total, 4)
        if bt == "mass":
            limit = _num(cl.get("limit")) or _num((ru.get("mass") or {}).get("limit_kg"))
            mp = _num(cl.get("margin_percent")) if cl.get("margin_percent") is not None else margin_pct
        elif bt == "power_avg":
            limit = _num(cl.get("limit"))
            mp = _num(cl.get("margin_percent")) if cl.get("margin_percent") is not None else \
                _num((ru.get("power") or {}).get("system_margin_percent"))
        else:
            limit = _num(cl.get("limit")) or _num(daily.get("capacity_mb_per_day"))
            mp = _num(cl.get("margin_percent"))
        res = [x for x in mine if _is_reserve(x)]
        with_m = total * (1 + (mp or 0) / 100.0) if mp is not None else None
        gy = y
        y += 28
        # root (limit) and system node
        limit_req = cl.get("requirement_code") or next((g(x, "requirement_code") for x in res if g(x, "requirement_code")), "")
        rlab = T("Limit {{v}} {{u}}", v=_fmt(limit), u=unit) if limit is not None else T("Limit not set")
        D.node(f"{bt}:limit", rlab, 30, y, 190, 44, sub=limit_req or None, style="emph" if limit is not None else "caution",
               p=prov("requirement", limit_req or None, note="limit"))
        if mp is not None:
            slab = T("System margin {{p}} % held by Systems", p=_fmt(mp, 1))
            ssub = T("Σ allocations {{s}} × {{f}} = {{t}} {{u}}", s=_fmt(total), f=_fmt(1 + mp / 100.0, 3), t=_fmt(with_m), u=unit)
        else:
            slab = T("Σ allocations {{s}} {{u}}", s=_fmt(total), u=unit)
            ssub = T("{{n}} lines", n=len(alloc_lines))
        left = (limit - (with_m if with_m is not None else total)) if limit is not None else None
        bad = left is not None and left < 0
        D.node(f"{bt}:sys", slab, 260, y, 280, 58, sub=ssub, style="alarm" if bad else "accent",
               badges=[T("left {{v}} {{u}}", v=_fmt(left), u=unit)] if left is not None else [],
               p=prov("allocation", note="system margin and reserve"))
        D.edge(f"{bt}:e0", f"{bt}:limit", f"{bt}:sys", [(220, y + 22), (260, y + 22)],
               style={"type": "tree", "dash": "", "width": 1.6, "color": "line"})
        cy = y
        for k, x in enumerate(sorted(alloc_lines, key=lambda x: -(_num(g(x, "value")) or 0))):
            code = str(g(x, "element_code", default="") or "?")
            v, cbe, mg = _num(g(x, "value")), _num(g(x, "cbe")), _num(g(x, "margined"))
            req = str(g(x, "requirement_code", default="") or "")
            status = str(g(x, "status", default="") or "")
            exceeds = mg is not None and v is not None and mg > v + 1e-9
            if exceeds:
                over.append(f"{code} {bt}")
            sub = T("CBE {{c}} / margined {{m}}", c=_fmt(cbe), m=_fmt(mg)) if (cbe is not None or mg is not None) else req or None
            nid = f"{bt}:{k}"
            D.node(nid, T("{{code}} alloc {{v}} {{u}}", code=code, v=_fmt(v), u=unit), 600, cy, 250, 44, sub=sub,
                   style="alarm" if exceeds else ("caution" if status == "disputed" else ("default" if status == "agreed" else "muted")),
                   badges=[x for x in (req, status) if x], p=prov("allocation", str(g(x, "id", default="")) or None, status=status))
            D.edge(f"{bt}:e{k + 1}", f"{bt}:sys", nid, [(540, y + 29), (570, y + 29), (570, cy + 22), (600, cy + 22)],
                   style={"type": "tree", "dash": "", "width": 1.2, "color": "line"})
            rows.append([T(title), code, _fmt(v), _fmt(cbe), _fmt(mg), unit, req, status or "—"])
            cy += 52
        for x in res:
            D.node(f"{bt}:res", T("Reserve {{v}} {{u}}", v=_fmt(g(x, "value")), u=unit), 600, cy, 250, 34, style="ok",
                   p=prov("allocation", str(g(x, "id", default="")) or None, note="reserve"))
            D.edge(f"{bt}:er", f"{bt}:sys", f"{bt}:res", [(540, y + 29), (570, y + 29), (570, cy + 17), (600, cy + 17)],
                   style={"type": "tree", "dash": "4 3", "width": 1.2, "color": "line"})
            rows.append([T(title), "SYS", _fmt(g(x, "value")), "", "", unit, str(g(x, "requirement_code", default="") or ""),
                         T("reserve")])
            cy += 42
        y = max(cy, y + 70) + 10
        D.group(f"g:{bt}", T(title), 16, gy, 860, y - gy, style="lane", p=prov("allocation"))
        y += 20
        if bad:
            D.gap(f"{bt}_over", T("Allocations with margin exceed the limit by {{v}} {{u}} ({{b}})", b=bt, v=_fmt(-left), u=unit),
                  severity="alarm", fix="budget")
        if limit is None:
            D.gap(f"{bt}_limit", T("missing: limit for the {{b}} budget", b=bt), fix="budget")
    if over:
        D.gap("cbe_over", T("{{n}} lines whose margined estimate exceeds the allocation: {{l}}", n=len(over), l=", ".join(over[:4])),
              len(over), fix="budget")
    if not sums:
        D.empty(T("No mass, power or data allocation in the ledger."))
    D.legend([{"kind": "box", "style": "default", "label": T("Agreed allocation")},
              {"kind": "box", "style": "muted", "label": T("Proposed allocation")},
              {"kind": "box", "style": "caution", "label": T("Disputed allocation")},
              {"kind": "box", "style": "alarm", "label": T("Estimate exceeds the allocation")}])
    D.completeness(max(1, len(rows)), len(rows) - len(over))
    D.m["counts"] = {"sums": sums, "lines": len(lines)}
    D.table([T("Budget"), T("Element"), T("Allocation"), T("CBE"), T("Margined"), T("Unit"), T("Requirement"), T("Status")], rows)
    return D.finish()


# ───────────────────────────────────────────────────────────── verification flow

METHOD_NAMES = {"T": "Test", "A": "Analysis", "I": "Inspection", "R": "Review of design", "D": "Demonstration"}
STAGE_ORDER = ("PRR", "SRR", "PDR", "CDR", "QR", "AR", "FRR", "IOV")
LEVEL_ORDER = ("mission", "segment", "system", "subsystem", "interface")


def _method(r: dict) -> str:
    m = str(r.get("verification_method") or "").strip()
    if not m:
        return "—"
    m0 = m[:1].upper()
    return m0 if m0 in METHOD_NAMES else m


def verification_flow(d: DiagramData, **_: Any) -> dict:
    D = Diagram("verification_flow", T("Verification flow"), "graph",
                T("Requirement level → verification method → model → stage that closes it; line width grows with the number of requirements (counts in the table)"))
    D.source("requirements")
    reqs = user_requirements(d)
    if not reqs:
        D.empty(T("No requirements yet: write or generate them in Requirements."))
        D.gap("no_requirements", T("missing: requirements"), severity="alarm", fix="requirements")
        return D.finish()
    cols: list[dict[str, int]] = [{}, {}, {}, {}]
    edges: dict[tuple[str, str], int] = {}
    for r in reqs:
        lv = "L:" + (r.get("level") or "—")
        me = "M:" + _method(r)
        mo = "D:" + str(r.get("verification_model") or "—")
        sg = "S:" + (stage_of(r) or "—")
        for k, n in enumerate((lv, me, mo, sg)):
            cols[k][n] = cols[k].get(n, 0) + 1
        for a, b in ((lv, me), (me, mo), (mo, sg)):
            edges[(a, b)] = edges.get((a, b), 0) + 1

    def order(k: int, n: str) -> tuple:
        v = n[2:]
        if k == 0:
            return (LEVEL_ORDER.index(v) if v in LEVEL_ORDER else 99, v)
        if k == 1:
            return (list(METHOD_NAMES).index(v) if v in METHOD_NAMES else 99, v)
        if k == 3:
            return (STAGE_ORDER.index(v) if v in STAGE_ORDER else 99, v)
        return (v == "—", v)

    def label(n: str) -> Any:
        k, v = n[:1], n[2:]
        c = next(cc[n] for cc in cols if n in cc)
        if k == "L":
            return T("{{level}} ({{n}})", level=v, n=c)
        if k == "M":
            return T(METHOD_NAMES[v] + " ({{n}})", n=c) if v in METHOD_NAMES else T("{{m}} ({{n}})", m=v, n=c)
        if k == "D":
            return T("model: {{m}} ({{n}})", m=v, n=c)
        return T("closed at {{s}} ({{n}})", s=v, n=c)
    nodes = [n for k in range(4) for n in sorted(cols[k], key=lambda x, k=k: order(k, x))]
    ranks = {n: k for k in range(4) for n in cols[k]}
    pos, routed = L.layered(nodes, list(edges), lambda n: size_of(label(n), None, minw=150, maxw=230), ranks=ranks,
                            rank_gap=170, node_gap=14, x0=16, y0=40, lane=6)
    style = {"L": "accent", "M": "default", "D": "emph", "S": "caution"}
    for n in nodes:
        b = pos[n]
        D.node(n, label(n), b["x"], b["y"], b["w"], b["h"], style="caution" if n.endswith("—") else style[n[:1]],
               p=prov("requirement", note="count"))
    rows = []
    for i, e in enumerate(routed):
        c = edges[(e["from"], e["to"])]
        D.edge(f"f{i}", e["from"], e["to"], e["points"], title=str(c),
               style={"type": "data", "dash": "", "width": min(4.0, 0.8 + c / 25.0)}, p=prov("requirement", note="count"))
        rows.append([plain(label(e["from"])), plain(label(e["to"])), str(c)])
    for k, title in enumerate(("Level", "Method", "Model", "Stage")):
        col = [pos[n] for n in nodes if ranks[n] == k]
        if col:
            D.label(min(b["x"] for b in col), 30, T(title), size=12, weight=600, style="text3")
    gaps = {k: [r for r in reqs if not v(r)] for k, v in
            (("method", lambda r: r.get("verification_method")), ("model", lambda r: r.get("verification_model")),
             ("stage", stage_of))}
    msg = {"method": "missing: verification method for {{n}} requirements",
           "model": "missing: verification model for {{n}} requirements",
           "stage": "missing: verification stage for {{n}} requirements"}
    for k, miss in gaps.items():
        if miss:
            D.gap(f"no_{k}", T(msg[k], n=len(miss)), len(miss), fix="requirements")
    D.completeness(len(reqs) * 3, len(reqs) * 3 - sum(len(v) for v in gaps.values()))
    D.m["counts"] = {"requirements": len(reqs), "by_stage": {n[2:]: c for n, c in cols[3].items()},
                     "by_method": {n[2:]: c for n, c in cols[1].items()}, "by_level": {n[2:]: c for n, c in cols[0].items()}}
    D.table([T("From"), T("To"), T("Requirements")], rows)
    return D.finish()


__all__ = ["context", "stakeholder_map", "ffbd", "n2_functions", "v_model", "trade_matrix", "budget_flowdown",
           "verification_flow", "trade_ids", "stakeholders", "need_rows", "moe_rows", "user_requirements", "stage_of",
           "context_target", "fcode", "fname", "top_functions", "ledger_lines"]
