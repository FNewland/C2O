"""Draw a diagram model as SVG or PNG, and put diagrams into Word documents.

The model → *scene* step (rectangles, polylines, text in model coordinates, colours from
the C2O light theme) is shared by the SVG writer and the matplotlib PNG writer, so the
download, the document figure and the React view (frontend/src/diagrams/DiagramCanvas.tsx,
same rules, same coordinates) show the same picture.

Labels are English keys (``{"t": …, "p": …}``); ``lang="fr"`` translates them with the UI's
own French catalogs (frontend/src/i18n/locales/fr*.json), the single catalog for EN/FR.
"""
from __future__ import annotations

import io
import json
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .base import plain, text_w

# C2O light theme (frontend/src/theme/tokens.css) — documents are printed light.
C = {
    "surface0": "#F4F5F7", "surface1": "#FFFFFF", "surface2": "#EEF0F3", "surface3": "#E3E6EA",
    "line": "#D5D9DE", "lineStrong": "#B8BEC6", "text": "#141619", "text2": "#383C42", "text3": "#4A4F56",
    "interactive": "#0B5577", "interactiveWash": "#E7EEF1", "caution": "#6E4300", "cautionWash": "#FBF1DE",
    "alarm": "#8F1D12", "alarmWash": "#FBE7E4", "ok": "#0B5A42", "okWash": "#E0F1EA",
    "cat1": "#3F6A8F", "cat2": "#5E5596", "cat3": "#2F6E64", "cat4": "#6A5F45", "cat5": "#4F6276",
    "cat6": "#85506A", "cat7": "#4A6B57", "cat8": "#5B5F66", "riskHigh": "#F6DEC4",
}
TYPE_COLOR = {"power": "cat4", "data": "cat2", "rf": "cat6", "mechanical": "cat8", "thermal": "cat5", "timing": "cat1",
              "optical": "cat1", "fluid": "cat7", "electrical_signal": "cat3"}
FONT = "'IBM Plex Sans', 'Liberation Sans', Arial, sans-serif"


# ───────────────────────────────────────────────────────────── i18n

@lru_cache(maxsize=1)
def _fr_catalog() -> dict[str, str]:
    """fr.json + fr.*.json merged in file-name order (as frontend/src/i18n/index.ts does)."""
    cands = []
    env = os.environ.get("SPACECDF_FR_CATALOG_DIR")
    if env:
        cands.append(Path(env))
    here = Path(__file__).resolve()
    for up in here.parents:
        cands.append(up / "frontend" / "src" / "i18n" / "locales")
        cands.append(up / "design" / "frontend" / "src" / "i18n" / "locales")
    cands.append(Path.cwd() / "frontend" / "src" / "i18n" / "locales")
    for d in cands:
        if (d / "fr.json").is_file():
            out: dict[str, str] = {}
            files = [d / "fr.json"] + sorted(p for p in d.glob("fr.*.json"))
            for f in files:
                try:
                    data = json.loads(f.read_text("utf8"))
                except (OSError, ValueError):
                    continue
                out.update({k: v for k, v in data.items() if isinstance(v, str) and v})
            return out
    return {}


def tx(v: Any, lang: str = "en") -> str:
    """Text of a model string in ``lang``: {"t","p"} keys, {"en","fr"} pairs, or plain data."""
    if isinstance(v, dict):
        if "t" in v:
            s = str(v["t"])
            if lang == "fr":
                s = _fr_catalog().get(s, s)
            for k, val in (v.get("p") or {}).items():
                s = s.replace("{{" + k + "}}", str(val))
            return s
        if "en" in v:
            return str(v.get(lang) or v.get("en") or "")
    return "" if v is None else str(v)


# ───────────────────────────────────────────────────────────── styles

def _col(key: str | None, default: str = "text2") -> str:
    if not key:
        return C[default]
    if key.startswith("#"):
        return key
    if key.startswith("type:"):
        return C[TYPE_COLOR.get(key[5:], "cat2")]
    return C.get(key, C[default])


def mix(hex_: str, a: float) -> str:
    """``hex_`` at ``a`` over white (a wash of a category colour)."""
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % tuple(round(255 - (255 - v) * a) for v in (r, g, b))


def edge_color(e: dict) -> str:
    c = e.get("color")
    if c == "line":
        return C["lineStrong"]
    if c:
        return _col(c)
    return C[TYPE_COLOR[e["type"]]] if e.get("type") in TYPE_COLOR else C["text3"]


def node_style(style: str) -> dict[str, Any]:
    s = {"fill": C["surface1"], "stroke": C["lineStrong"], "bar": None, "text": C["text"], "dash": "", "bold": True}
    if style == "emph":
        s.update(fill=C["surface2"], stroke=C["text3"])
    elif style == "accent":
        s.update(fill=C["interactiveWash"], stroke=C["interactive"])
    elif style in ("ok", "caution", "alarm"):
        s.update(fill=C[style + "Wash"], stroke=C[style], bar=C[style])
    elif style == "muted":
        s.update(fill=C["surface0"], stroke=C["lineStrong"], dash="4 3", text=C["text3"])
    elif style.startswith("cat"):
        s.update(bar=C.get(style, C["cat8"]))
    elif style.startswith("type-"):
        s.update(fill=C[TYPE_COLOR.get(style[5:], "cat2")], stroke=C[TYPE_COLOR.get(style[5:], "cat2")])
    elif style == "cogbox":
        s.update(fill="none", stroke=C["interactive"], dash="4 3")
    return s


def cell_style(style: str) -> dict[str, Any]:
    base = {"fill": C["surface1"], "stroke": C["line"], "text": C["text"], "bold": False, "dash": ""}
    m = {
        "cell": {}, "band": {"fill": C["surface0"]},
        "on": {"fill": C["interactiveWash"], "text": C["interactive"], "bold": True},
        "off": {"fill": C["surface0"], "text": C["text3"]},
        "alarm": {"fill": C["alarmWash"], "text": C["alarm"], "bold": True},
        "ok": {"fill": C["okWash"], "text": C["ok"]}, "caution": {"fill": C["cautionWash"], "text": C["caution"]},
        "muted": {"fill": C["surface2"], "text": C["text3"]},
        "unknown": {"fill": C["surface2"], "text": C["text3"], "dash": "2 2"},
        "total": {"fill": C["surface2"], "bold": True},
        "n2": {"fill": C["surface1"]},
        "grid": {"fill": C["line"], "stroke": "none"}, "divider": {"fill": C["lineStrong"], "stroke": "none"},
        "cogbox": {"fill": "none", "stroke": C["interactive"], "dash": "4 3"},
        "risk-low": {"fill": C["okWash"]}, "risk-med": {"fill": C["cautionWash"]},
        "risk-high": {"fill": C["riskHigh"]}, "risk-vhigh": {"fill": C["alarmWash"], "text": C["alarm"], "bold": True},
    }
    if style.startswith("diag-"):
        return {**base, "fill": C["surface3"], "bold": True}
    return {**base, **m.get(style, {})}


def group_style(style: str) -> dict[str, Any]:
    if style == "lane":
        return {"fill": C["surface0"], "stroke": C["line"], "bar": None, "dash": ""}
    if style == "envelope":
        return {"fill": C["surface0"], "stroke": C["text3"], "bar": None, "dash": ""}
    if style.startswith("group-cat"):
        return {"fill": C["surface0"], "stroke": C["line"], "bar": C.get(style[6:], C["cat8"]), "dash": ""}
    return {"fill": C["surface0"], "stroke": C["line"], "bar": None, "dash": ""}


# ───────────────────────────────────────────────────────────── scene

def scene(m: dict, lang: str = "en", *, legend: bool = True, header: bool = False) -> tuple[list[dict], float, float]:
    """Primitives (model coordinates, y down) and the scene size."""
    P: list[dict] = []
    dy = 0.0
    W, H = float(m["width"]), float(m["height"])
    if header:
        P.append({"k": "text", "x": 16, "y": 24, "s": tx(m["title"], lang), "size": 16, "w": 600, "fill": C["text"]})
        if m.get("subtitle"):
            P.append({"k": "text", "x": 16, "y": 44, "s": tx(m["subtitle"], lang), "size": 12, "w": 400, "fill": C["text2"]})
        dy = 56.0
    P.append({"k": "rect", "x": 0, "y": 0, "w": W, "h": H + dy, "fill": C["surface1"], "stroke": "none"})
    P.insert(0, P.pop())   # background first

    def Y(y: float) -> float:
        return y + dy
    if m.get("empty") is not None:
        P.append({"k": "text", "x": W / 2, "y": Y(H / 2), "s": tx(m["empty"], lang), "size": 13, "w": 400,
                  "fill": C["text3"], "anchor": "middle", "italic": True})
    for g in m["groups"]:
        st = group_style(g.get("style") or "group")
        P.append({"k": "rect", "x": g["x"], "y": Y(g["y"]), "w": g["w"], "h": g["h"], "fill": st["fill"],
                  "stroke": st["stroke"], "r": 3, "dash": st["dash"], "sw": 1})
        if st["bar"]:
            P.append({"k": "rect", "x": g["x"], "y": Y(g["y"]), "w": g["w"], "h": 4, "fill": st["bar"], "stroke": "none"})
        if g.get("label") not in (None, ""):
            P.append({"k": "text", "x": g["x"] + 8, "y": Y(g["y"]) + 16, "s": tx(g["label"], lang), "size": 12, "w": 600,
                      "fill": C["text2"]})
    for c in m["cells"]:
        st = cell_style(c.get("style") or "cell")
        P.append({"k": "rect", "x": c["x"], "y": Y(c["y"]), "w": c["w"], "h": c["h"], "fill": st["fill"],
                  "stroke": st["stroke"], "sw": 1 if st["stroke"] != "none" else 0, "dash": st["dash"]})
        cy = Y(c["y"]) + c["h"] / 2
        if c.get("codes"):
            codes = c["codes"]
            lines = [codes[i:i + 2] for i in range(0, len(codes), 2)]
            for li, line in enumerate(lines):
                total = sum(text_w(x["c"], 12, True) for x in line) + 3 * (len(line) - 1)
                x = c["x"] + (c["w"] - total) / 2
                ly = cy + 4 + (li - (len(lines) - 1) / 2) * 13
                for code in line:
                    P.append({"k": "text", "x": x, "y": ly, "s": code["c"], "size": 12, "w": 600,
                              "fill": C[TYPE_COLOR.get(code["type"], "cat2")]})
                    x += text_w(code["c"], 12, True) + 3
        elif c.get("text") not in (None, ""):
            sub = c.get("sub")
            P.append({"k": "text", "x": c["x"] + c["w"] / 2, "y": cy + (4 if not sub else -4), "s": tx(c["text"], lang),
                      "size": 12 if not sub else 15, "w": 600 if st["bold"] or sub else 400, "fill": st["text"], "anchor": "middle"})
            if sub:
                P.append({"k": "text", "x": c["x"] + c["w"] / 2, "y": cy + 14, "s": tx(sub, lang), "size": 12, "w": 400,
                          "fill": C["text2"], "anchor": "middle"})
    # edges under nodes
    for e in m["edges"]:
        col = edge_color(e)
        pts = [(x, Y(y)) for x, y in e["points"]]
        op = 0.45 if e.get("faded") else 1.0
        P.append({"k": "path", "pts": pts, "curve": bool(e.get("curve")), "stroke": col, "sw": e.get("width", 1.4),
                  "dash": e.get("dash") or "", "op": op})
        arrow = e.get("arrow") or "none"
        if arrow in ("end", "both"):
            P.append(_arrow(pts[-2] if not e.get("curve") else pts[1], pts[-1], col, op))
        if arrow in ("start", "both"):
            P.append(_arrow(pts[1] if not e.get("curve") else pts[1], pts[0], col, op))
    for n in m["nodes"]:
        P.extend(_node(n, Y, lang))
    # edge labels on top
    for e in m["edges"]:
        if e.get("label") in (None, ""):
            continue
        pts = [(x, Y(y)) for x, y in e["points"]]
        if e.get("curve") and len(pts) == 3:
            lx = 0.25 * pts[0][0] + 0.5 * pts[1][0] + 0.25 * pts[2][0]
            ly = 0.25 * pts[0][1] + 0.5 * pts[1][1] + 0.25 * pts[2][1]
        else:
            seg = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
            lx, ly = (pts[seg][0] + pts[seg + 1][0]) / 2, (pts[seg][1] + pts[seg + 1][1]) / 2
        s = tx(e["label"], lang)
        w = text_w(s, 12) + 8
        P.append({"k": "rect", "x": lx - w / 2, "y": ly - 9, "w": w, "h": 17, "fill": C["surface1"], "stroke": "none", "op": 0.92})
        P.append({"k": "text", "x": lx, "y": ly + 4, "s": s, "size": 12, "w": 400, "fill": C["text2"], "anchor": "middle"})
    for lab in m["labels"]:
        P.append({"k": "text", "x": lab["x"], "y": Y(lab["y"]), "s": tx(lab["text"], lang), "size": lab.get("size", 12),
                  "w": lab.get("weight", 400), "fill": _col(lab.get("style"), "text2") if lab.get("style") != "caution" else C["caution"],
                  "anchor": lab.get("anchor", "start"), "rot": lab.get("rotate")})
    H2 = H + dy
    if legend and m.get("legend"):
        P2, h = _legend(m["legend"], W, H2, lang)
        P.extend(P2)
        H2 += h
        W = max(W, max((p["x"] + p.get("w", 0) for p in P2 if p["k"] == "rect"), default=W) + 16)
    P[0]["w"], P[0]["h"] = W, H2
    return P, W, H2


def _arrow(a: tuple, b: tuple, col: str, op: float) -> dict:
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    L_, Wd = 8.0, 3.6
    bx, by = b
    p1 = (bx - L_ * math.cos(ang) + Wd * math.sin(ang), by - L_ * math.sin(ang) - Wd * math.cos(ang))
    p2 = (bx - L_ * math.cos(ang) - Wd * math.sin(ang), by - L_ * math.sin(ang) + Wd * math.cos(ang))
    return {"k": "poly", "pts": [b, p1, p2], "fill": col, "op": op}


def _badges(n: dict) -> list[str]:
    return [plain(b) if not isinstance(b, str) else b for b in (n.get("badges") or []) if b not in (None, "")]


def _node(n: dict, Y, lang: str) -> list[dict]:
    out: list[dict] = []
    st = node_style(n.get("style") or "default")
    x, y, w, h = n["x"], Y(n["y"]), n["w"], n["h"]
    shape = n.get("shape") or "rect"
    r = {"round": 10, "state": 12, "pill": h / 2, "chip": h / 2, "band": 2, "part": 1, "row": 2, "trunk": 2}.get(shape, 3)
    if shape == "dot":
        out.append({"k": "circle", "cx": x + w / 2, "cy": y + h / 2, "r": w / 2, "fill": C["text"], "stroke": C["text"], "sw": 1})
        return out
    if shape == "cog":
        cx, cy = x + w / 2, y + h / 2
        out.append({"k": "circle", "cx": cx, "cy": cy, "r": w / 2, "fill": C["surface1"], "stroke": C["interactive"], "sw": 1.5})
        out.append({"k": "path", "pts": [(cx - w / 2, cy), (cx + w / 2, cy)], "stroke": C["interactive"], "sw": 1.2, "dash": "", "op": 1})
        out.append({"k": "path", "pts": [(cx, cy - h / 2), (cx, cy + h / 2)], "stroke": C["interactive"], "sw": 1.2, "dash": "", "op": 1})
        return out
    if shape == "part" and st["bar"]:
        st = {**st, "fill": mix(st["bar"], 0.22), "stroke": st["bar"]}
    out.append({"k": "rect", "x": x, "y": y, "w": w, "h": h, "fill": st["fill"], "stroke": st["stroke"], "r": r,
                "dash": st["dash"], "sw": 1.6 if shape == "state" else 1})
    if shape == "trunk":
        return out
    pad = 10.0
    if st["bar"] and shape == "state":
        out[-1]["stroke"] = st["bar"]
    elif st["bar"] and shape not in ("part", "chip", "pill"):
        out.append({"k": "rect", "x": x, "y": y, "w": 4, "h": h, "fill": st["bar"], "stroke": "none", "r": 1})
        pad = 12.0
    label = tx(n.get("label"), lang)
    sub = tx(n.get("sub"), lang) if n.get("sub") not in (None, "") else ""
    badges = [tx(b, lang) for b in (n.get("badges") or []) if b not in (None, "")]
    if shape in ("chip", "pill", "part"):
        if label:
            out.append({"k": "text", "x": x + w / 2 if shape != "pill" else x + 10, "y": y + h / 2 + 4, "s": label, "size": 12,
                        "w": 600 if shape == "pill" else 400, "fill": st["text"], "anchor": "middle" if shape != "pill" else "start"})
        return out
    if shape == "row":
        out.append({"k": "text", "x": x + 8, "y": y + h / 2 + 4, "s": label, "size": 12, "w": 400, "fill": st["text"]})
        bx = x + w + 6
        for b in badges:
            bw = text_w(b, 12) + 10
            out.append({"k": "rect", "x": bx, "y": y + 2, "w": bw, "h": h - 4, "fill": C["surface2"], "stroke": C["line"], "r": 8})
            out.append({"k": "text", "x": bx + bw / 2, "y": y + h / 2 + 4, "s": b, "size": 12, "w": 400, "fill": C["text2"], "anchor": "middle"})
            bx += bw + 4
        return out
    content = 16 + (15 if sub else 0) + (17 if badges else 0)
    ty = y + (h - content) / 2
    centre = shape in ("state", "round", "step")
    tx_ = x + w / 2 if centre else x + pad
    anchor = "middle" if centre else "start"
    out.append({"k": "text", "x": tx_, "y": ty + 12.5, "s": label, "size": 13 if shape != "step" else 12,
                "w": 600 if shape != "step" else 400, "fill": st["text"], "anchor": anchor})
    if sub:
        out.append({"k": "text", "x": tx_, "y": ty + 16 + 11.5, "s": sub, "size": 12, "w": 400, "fill": C["text2"], "anchor": anchor})
    if badges:
        widths = [text_w(b, 12) + 10 for b in badges]
        total = sum(widths) + 4 * (len(badges) - 1)
        bx = x + (w - total) / 2 if centre else x + pad
        by = ty + 16 + (15 if sub else 0) + 1
        for b, bw in zip(badges, widths):
            out.append({"k": "rect", "x": bx, "y": by, "w": bw, "h": 15, "fill": C["surface2"], "stroke": C["line"], "r": 7.5})
            out.append({"k": "text", "x": bx + bw / 2, "y": by + 11.5, "s": b, "size": 12, "w": 400, "fill": C["text2"], "anchor": "middle"})
            bx += bw + 4
    return out


def _legend(items: list[dict], W: float, y0: float, lang: str) -> tuple[list[dict], float]:
    P: list[dict] = []
    x, y = 16.0, y0 + 8
    maxw = max(W, 520.0) - 16
    for it in items:
        lab = tx(it.get("label"), lang)
        if it.get("code") and it["code"] != lab:
            lab = f"{it['code']}  {lab}"
        iw = 34 + text_w(lab, 12) + 18
        if x + iw > maxw and x > 16:
            x, y = 16.0, y + 22
        if it.get("kind") == "dot":
            P.append({"k": "circle", "cx": x + 13, "cy": y + 8, "r": 6, "fill": C["text"], "stroke": C["text"], "sw": 1})
        elif it.get("kind") == "line":
            col = C[TYPE_COLOR[it["type"]]] if it.get("type") in TYPE_COLOR and not it.get("color") else _col(it.get("color"), "text2")
            P.append({"k": "path", "pts": [(x, y + 8), (x + 26, y + 8)], "stroke": col, "sw": it.get("width", 1.4),
                      "dash": it.get("dash") or "", "op": 0.45 if it.get("faded") else 1})
        else:
            st = node_style(it.get("style") or "default") if not str(it.get("style", "")).startswith(("risk", "on", "off", "unknown", "cogbox")) \
                else {**cell_style(it["style"]), "bar": None}
            P.append({"k": "rect", "x": x + 4, "y": y + 1, "w": 18, "h": 14, "fill": st["fill"] if st["fill"] != "none" else C["surface1"],
                      "stroke": st.get("stroke", C["line"]) if st.get("stroke") != "none" else C["line"], "r": 2, "dash": st.get("dash", "")})
            if st.get("bar"):
                P.append({"k": "rect", "x": x + 4, "y": y + 1, "w": 4, "h": 14, "fill": st["bar"], "stroke": "none"})
        P.append({"k": "text", "x": x + 34, "y": y + 12, "s": lab, "size": 12, "w": 400, "fill": C["text2"]})
        x += iw
    return P, (y - y0) + 30


# ───────────────────────────────────────────────────────────── writers

def to_svg(m: dict, lang: str = "en", *, legend: bool = True, header: bool = True) -> str:
    P, W, H = scene(m, lang, legend=legend, header=header)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" '
           f'font-family="{escape(FONT)}" role="img" aria-label="{escape(tx(m["title"], lang))}">',
           f"<title>{escape(tx(m['title'], lang))}</title>"]
    for p in P:
        k = p["k"]
        op = f' opacity="{p["op"]}"' if p.get("op", 1) != 1 else ""
        if k == "rect":
            dash = f' stroke-dasharray="{p["dash"]}"' if p.get("dash") else ""
            sw = p.get("sw", 1)
            out.append(f'<rect x="{p["x"]:.1f}" y="{p["y"]:.1f}" width="{max(p["w"], 0):.1f}" height="{max(p["h"], 0):.1f}" '
                       f'rx="{p.get("r", 0)}" fill="{p["fill"]}" stroke="{p["stroke"]}" stroke-width="{sw}"{dash}{op}/>')
        elif k == "circle":
            out.append(f'<circle cx="{p["cx"]:.1f}" cy="{p["cy"]:.1f}" r="{p["r"]:.1f}" fill="{p["fill"]}" stroke="{p["stroke"]}" '
                       f'stroke-width="{p["sw"]}"/>')
        elif k == "path":
            pts = p["pts"]
            if p.get("curve") and len(pts) == 3:
                d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f} Q{pts[1][0]:.1f},{pts[1][1]:.1f} {pts[2][0]:.1f},{pts[2][1]:.1f}"
            else:
                d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            dash = f' stroke-dasharray="{p["dash"]}"' if p.get("dash") else ""
            out.append(f'<path d="{d}" fill="none" stroke="{p["stroke"]}" stroke-width="{p["sw"]}" stroke-linejoin="round"{dash}{op}/>')
        elif k == "poly":
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in p["pts"])
            out.append(f'<polygon points="{pts}" fill="{p["fill"]}"{op}/>')
        elif k == "text":
            anchor = {"middle": "middle", "end": "end"}.get(p.get("anchor", "start"), "start")
            rot = f' transform="rotate({p["rot"]} {p["x"]:.1f} {p["y"]:.1f})"' if p.get("rot") else ""
            style = ' font-style="italic"' if p.get("italic") else ""
            out.append(f'<text x="{p["x"]:.1f}" y="{p["y"]:.1f}" font-size="{p["size"]}" font-weight="{p["w"]}" fill="{p["fill"]}" '
                       f'text-anchor="{anchor}"{rot}{style}>{escape(p["s"])}</text>')
    out.append("</svg>")
    return "\n".join(out)


def to_png(m: dict, lang: str = "en", *, legend: bool = True, header: bool = False, dpi: int = 200) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, PathPatch, Polygon, Rectangle, Circle
    from matplotlib.path import Path as MPath

    P, W, H = scene(m, lang, legend=legend, header=header)
    K = 0.72   # model px → points (100 px per inch)
    with matplotlib.rc_context({"font.family": "sans-serif",
                                "font.sans-serif": ["IBM Plex Sans", "Liberation Sans", "Arial", "DejaVu Sans"],
                                "lines.scale_dashes": False, "svg.fonttype": "none"}):
        fig = plt.figure(figsize=(W / 100, H / 100), dpi=dpi)
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)
        ax.axis("off")

        def dashes(s: str, lw: float):
            if not s:
                return "solid"
            return (0, tuple(float(v) * K for v in s.split()))
        for p in P:
            k = p["k"]
            op = p.get("op", 1)
            if k == "rect":
                fill = None if p["fill"] == "none" else p["fill"]
                ec = None if p["stroke"] == "none" else p["stroke"]
                lw = p.get("sw", 1) * K if ec else 0
                if p.get("r"):
                    r = min(p["r"], p["w"] / 2, p["h"] / 2)
                    patch = FancyBboxPatch((p["x"] + r, p["y"] + r), max(p["w"] - 2 * r, 0.01), max(p["h"] - 2 * r, 0.01),
                                           boxstyle=f"round,pad={r}", fc=fill or "none", ec=ec or "none", lw=lw,
                                           ls=dashes(p.get("dash", ""), lw), alpha=op)
                else:
                    patch = Rectangle((p["x"], p["y"]), p["w"], p["h"], fc=fill or "none", ec=ec or "none", lw=lw,
                                      ls=dashes(p.get("dash", ""), lw), alpha=op)
                ax.add_patch(patch)
            elif k == "circle":
                ax.add_patch(Circle((p["cx"], p["cy"]), p["r"], fc=p["fill"], ec=p["stroke"], lw=p["sw"] * K))
            elif k == "path":
                pts = p["pts"]
                if p.get("curve") and len(pts) == 3:
                    path = MPath(pts, [MPath.MOVETO, MPath.CURVE3, MPath.CURVE3])
                else:
                    path = MPath(pts, [MPath.MOVETO] + [MPath.LINETO] * (len(pts) - 1))
                ax.add_patch(PathPatch(path, fc="none", ec=p["stroke"], lw=p["sw"] * K, ls=dashes(p.get("dash", ""), p["sw"]),
                                       alpha=op, joinstyle="round", capstyle="butt"))
            elif k == "poly":
                ax.add_patch(Polygon(p["pts"], closed=True, fc=p["fill"], ec="none", alpha=op))
            elif k == "text":
                ha = {"middle": "center", "end": "right"}.get(p.get("anchor", "start"), "left")
                ax.text(p["x"], p["y"], p["s"], fontsize=p["size"] * K, fontweight="bold" if p["w"] >= 600 else "normal",
                        color=p["fill"], ha=ha, va="baseline", rotation=-(p.get("rot") or 0),
                        rotation_mode="anchor", fontstyle="italic" if p.get("italic") else "normal")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
        plt.close(fig)
    return buf.getvalue()


# ───────────────────────────────────────────────────────────── Word

def add_diagram(doc: Any, m: dict, *, lang: str = "en", heading_level: int | None = 2, gaps: bool = True,
                table: bool = False, width_cm: float = 16.0) -> None:
    """A diagram as a figure (same model as the screen), with its gaps and optional data table."""
    from spacecdf_agents.exporters.docs import theme
    if heading_level:
        doc.add_heading(tx(m["title"], lang), level=heading_level)
    if m.get("subtitle"):
        p = doc.add_paragraph(tx(m["subtitle"], lang))
        p.runs[0].italic = True
    w = float(m["width"])
    width = min(width_cm, max(8.0, w / 50.0))
    theme.add_figure(doc, to_png(m, lang), caption=tx(m["title"], lang) + _gate_note(m, lang), width_cm=width)
    if gaps and m.get("gaps"):
        doc.add_paragraph(tx({"t": "Gaps"}, lang) + ":").runs[0].bold = True
        for g in m["gaps"]:
            doc.add_paragraph(tx(g["message"], lang), style="List Bullet")
    if table and m.get("table", {}).get("rows"):
        rows = [[tx(c, lang) for c in r] for r in m["table"]["rows"][:80]]
        theme.styled_table(doc, headers=[tx(c, lang) for c in m["table"]["columns"]], rows=rows)
    if m.get("sources"):
        doc.add_paragraph(tx({"t": "Sources: {{s}}", "p": {"s": ", ".join(m["sources"])}}, lang)).runs[0].italic = True


def _gate_note(m: dict, lang: str) -> str:
    gs = m.get("gates") or []
    if not gs:
        return ""
    return " (" + ", ".join(f"{g['gate'].upper()} {g['maturity']}" for g in gs) + ")"


def diagrams_docx(d: Any, kinds: list[str], *, study_name: str, lang: str = "en") -> bytes:
    from docx import Document

    from spacecdf_agents.exporters.docs import theme

    from . import build
    doc = Document()
    try:
        theme.apply_document_styles(doc)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    doc.add_heading(tx({"t": "SEMP / ECSS diagram set"}, lang), level=0)
    doc.add_paragraph(f"{study_name}")
    doc.add_paragraph(tx({"t": "Each figure is drawn from the design model; the gaps list what the model still lacks for it."}, lang))
    doc.add_paragraph(tx({"t": "Maturity per gate: D draft, B baselined, U updated."}, lang))
    from . import expand
    for kind, opts in expand(kinds, d):
        m = build(kind, d, **opts)
        add_diagram(doc, m, lang=lang, heading_level=1, gaps=True, table=True)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
