"""Diagram model primitives (design rules §3: one diagram model per diagram).

A diagram model is plain JSON that the React view (``frontend/src/diagrams``) and the
document exporters (``render.py`` → SVG / PNG → docx) draw the same way. Geometry is
computed here, on the server, so the screen and the document show the same picture.

    {
      "kind", "title", "subtitle", "view", "width", "height",
      "groups":  [{id, label, x, y, w, h, style, ref?, prov?}],
      "nodes":   [{id, label, sub?, x, y, w, h, shape, style, badges[], group?, ref?, prov}],
      "edges":   [{id, from, to, type?, label?, points[[x,y]…], curve?, dash?, width?, color?,
                   arrow: end|both|none, faded?, prov}],
      "labels":  [{x, y, text, anchor, size, weight, style, rotate?}],
      "cells":   [{x, y, w, h, text?, style, title?}],          (matrices, timelines)
      "legend":  [{kind: line|box, label, style?, type?, dash?}],
      "gaps":    [{code, message, count, severity, fix?}],
      "completeness": {expected, filled, score},
      "table":   {columns: [...], rows: [[...]]},             (accessible alternative)
      "sources": [...],
    }

Translatable text is ``{"t": <English text with {{x}}>, "p": {"x": …}}`` (the English text is the
i18n key, as in the UI catalogs); a plain string is data (an element name, a code) and is
never translated. Every key passed to :func:`T` must be listed in
``frontend/src/diagrams/vocab.ts`` (``// i18n-keys``) so the FR catalog check knows it;
``tests/test_api/test_diagrams_api.py`` keeps the two in step.
"""
from __future__ import annotations

import math
from typing import Any

Text = dict | str


def T(text: str, **params: Any) -> dict:
    """A translatable string (English text = key; ``{{name}}`` placeholders)."""
    return {"t": text, "p": params} if params else {"t": text}


def plain(v: Any) -> str:
    """English rendering of a Text (for widths, tables in logs and the English export)."""
    if isinstance(v, dict) and "t" in v:
        s = str(v["t"])
        for k, val in (v.get("p") or {}).items():
            s = s.replace("{{" + k + "}}", str(val))
        return s
    return "" if v is None else str(v)


#: average glyph advance of IBM Plex Sans as a fraction of the font size
_ADV = 0.56
_ADV_BOLD = 0.6


def text_w(v: Any, size: float = 12.0, bold: bool = False) -> float:
    s = plain(v)
    wide = sum(1 for c in s if c in "MWmw@%") * 0.3
    return (len(s) + wide) * size * (_ADV_BOLD if bold else _ADV)


def clip(s: Any, n: int) -> str:
    s = plain(s)
    return s if len(s) <= n else s[: max(1, n - 1)] + "…"


def prov(source: str, ref: str | None = None, *, origin: str | None = None, status: str | None = None,
         note: str | None = None) -> dict:
    """Where an item comes from: ``source`` = element | interface | rail | line | bus | node |
    mode | transition | member | function | allocation | requirement | verification | risk |
    thermal_closure | stack | kb | conops | template | derived | parameter."""
    p: dict[str, Any] = {"source": source}
    if ref:
        p["ref"] = ref
    if origin:
        p["origin"] = origin
    if status:
        p["status"] = status
    if note:
        p["note"] = note
    return p


def gap(code: str, message: dict, count: int = 1, *, severity: str = "warn", fix: str | None = None) -> dict:
    g = {"code": code, "message": message, "count": int(count), "severity": severity}
    if fix:
        g["fix"] = fix
    return g


#: interface type → line pattern and width (colour comes from the renderer palette); the
#: pattern keeps the type readable in greyscale (C2O principle P6: never colour alone).
TYPE_LINE: dict[str, dict[str, Any]] = {
    "power": {"dash": "", "width": 2.4},
    "data": {"dash": "", "width": 1.4},
    "rf": {"dash": "7 3", "width": 1.6},
    "mechanical": {"dash": "1.5 3", "width": 1.6},
    "thermal": {"dash": "5 2 1.5 2", "width": 1.4},
    "timing": {"dash": "9 2 2 2", "width": 1.2},
    "optical": {"dash": "2 2", "width": 1.2},
    "fluid": {"dash": "11 3", "width": 2.0},
    "electrical_signal": {"dash": "3 2", "width": 1.2},
}
TYPE_CODE = {"power": "P", "data": "D", "rf": "RF", "mechanical": "M", "thermal": "Th", "timing": "Ti",
             "optical": "O", "fluid": "F", "electrical_signal": "S"}
# English text is the key (vocab.ts lists it)
TYPE_LABEL = {"power": "Power", "data": "Data", "rf": "RF", "mechanical": "Mechanical", "thermal": "Thermal",
              "timing": "Timing", "optical": "Optical", "fluid": "Fluid", "electrical_signal": "Discrete signal"}

#: subsystem domain → category colour (node accent bar)
DOMAIN_STYLE = {"payload": "cat6", "power": "cat4", "aocs": "cat1", "ttc": "cat2", "obc": "cat3",
                "thermal": "cat5", "structure": "cat8", "propulsion": "cat7", "ground": "cat5"}
DOMAIN_LABEL = {"payload": "Payload", "power": "EPS", "aocs": "AOCS", "ttc": "TT&C", "obc": "OBDH",
                "thermal": "Thermal", "structure": "Structure", "propulsion": "Propulsion", "ground": "Ground"}


def type_legend(types: list[str]) -> list[dict]:
    out = []
    for t in sorted(set(types), key=lambda x: list(TYPE_LINE).index(x) if x in TYPE_LINE else 99):
        out.append({"kind": "line", "type": t, "label": T(TYPE_LABEL.get(t, "Data")), "code": TYPE_CODE.get(t, "?"),
                    **TYPE_LINE.get(t, TYPE_LINE["data"])})
    return out


def edge_style(itype: str | None) -> dict:
    t = itype if itype in TYPE_LINE else "data"
    return {"type": t, **TYPE_LINE[t]}


class Diagram:
    """Accumulates one diagram model."""

    def __init__(self, kind: str, title: dict, view: str = "graph", subtitle: Any = None):
        self.m: dict[str, Any] = {
            "kind": kind, "title": title, "subtitle": subtitle, "view": view, "width": 0, "height": 0,
            "groups": [], "nodes": [], "edges": [], "labels": [], "cells": [], "legend": [], "gaps": [],
            "completeness": {"expected": 0, "filled": 0, "score": 1.0}, "table": {"columns": [], "rows": []},
            "sources": [], "notes": [], "empty": None,
        }

    # ---- items
    def node(self, nid: str, label: Any, x: float, y: float, w: float, h: float, *, shape: str = "rect",
             style: str = "default", sub: Any = None, badges: list | None = None, group: str | None = None,
             ref: dict | None = None, p: dict | None = None, **extra: Any) -> dict:
        n = {"id": nid, "label": label, "x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1),
             "shape": shape, "style": style, "badges": badges or [], "prov": p or prov("derived")}
        if sub not in (None, ""):
            n["sub"] = sub
        if group:
            n["group"] = group
        if ref:
            n["ref"] = ref
        n.update(extra)
        self.m["nodes"].append(n)
        return n

    def edge(self, eid: str, a: str, b: str, points: list, *, label: Any = None, itype: str | None = None,
             arrow: str = "end", curve: bool = False, faded: bool = False, p: dict | None = None,
             style: dict | None = None, **extra: Any) -> dict:
        e = {"id": eid, "from": a, "to": b, "points": [[round(x, 1), round(y, 1)] for x, y in points],
             "arrow": arrow, "prov": p or prov("derived")}
        e.update(style or edge_style(itype))
        if label not in (None, ""):
            e["label"] = label
        if curve:
            e["curve"] = True
        if faded:
            e["faded"] = True
        e.update(extra)
        self.m["edges"].append(e)
        return e

    def group(self, gid: str, label: Any, x: float, y: float, w: float, h: float, *, style: str = "group",
              ref: dict | None = None, p: dict | None = None, **extra: Any) -> dict:
        g = {"id": gid, "label": label, "x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1),
             "style": style, "prov": p or prov("derived")}
        if ref:
            g["ref"] = ref
        g.update(extra)
        self.m["groups"].append(g)
        return g

    def label(self, x: float, y: float, text: Any, *, anchor: str = "start", size: float = 12, weight: int = 400,
              style: str = "text2", rotate: float | None = None) -> None:
        lab = {"x": round(x, 1), "y": round(y, 1), "text": text, "anchor": anchor, "size": size, "weight": weight,
               "style": style}
        if rotate is not None:
            lab["rotate"] = rotate
        self.m["labels"].append(lab)

    def cell(self, x: float, y: float, w: float, h: float, *, text: Any = None, style: str = "cell",
             title: Any = None, **extra: Any) -> None:
        c = {"x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1), "style": style}
        if text not in (None, ""):
            c["text"] = text
        if title not in (None, ""):
            c["title"] = title
        c.update(extra)
        self.m["cells"].append(c)

    def gap(self, *a: Any, **k: Any) -> None:
        self.m["gaps"].append(gap(*a, **k))

    def legend(self, items: list[dict]) -> None:
        self.m["legend"].extend(items)

    def table(self, columns: list, rows: list[list]) -> None:
        self.m["table"] = {"columns": columns, "rows": rows}

    def source(self, *s: str) -> None:
        for x in s:
            if x not in self.m["sources"]:
                self.m["sources"].append(x)

    def completeness(self, expected: int, filled: int) -> None:
        self.m["completeness"] = {"expected": int(expected), "filled": int(filled),
                                  "score": round(filled / expected, 3) if expected else 1.0}

    def empty(self, message: dict) -> None:
        self.m["empty"] = message

    def finish(self, pad: float = 16.0) -> dict:
        """Fit width / height to the content (adds ``pad`` on the right and bottom)."""
        xs, ys = [0.0], [0.0]
        for coll in ("nodes", "groups", "cells"):
            for it in self.m[coll]:
                xs.append(it["x"] + it["w"])
                ys.append(it["y"] + it["h"])
        for e in self.m["edges"]:
            for x, y in e["points"]:
                xs.append(x)
                ys.append(y)
        for lab in self.m["labels"]:
            w = text_w(lab["text"], lab["size"], lab["weight"] >= 600)
            if lab.get("rotate"):
                ys.append(lab["y"] + w)
                xs.append(lab["x"] + lab["size"])
            else:
                xs.append(lab["x"] + (w if lab["anchor"] == "start" else w / 2 if lab["anchor"] == "middle" else 0))
                ys.append(lab["y"] + 4)
        self.m["width"] = math.ceil(max(xs) + pad)
        self.m["height"] = math.ceil(max(ys) + pad)
        if self.m["empty"] is not None:
            self.m["width"] = max(self.m["width"], 480)
            self.m["height"] = max(self.m["height"], 120)
        return self.m
