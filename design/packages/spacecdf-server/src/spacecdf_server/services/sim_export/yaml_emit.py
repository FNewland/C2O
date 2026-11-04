"""YAML writer with per-key comments (design-to-simulator export, Nov 2026).

PyYAML cannot write comments, and the export contract needs one on every value: where it
came from in the design (``# design: …``) or why it is a default (``# C2O default: …``).
This writer emits block YAML for mappings and lists of mappings, flow style for lists of
scalars and for "small" mappings inside lists, and a trailing or leading comment for any
key path that has one. ``yaml.safe_load(dump(data, comments))`` returns ``data`` exactly
(tested), so the comments never change a value.

Paths are tuples of keys / list indices from the document root, e.g.
``("battery", "capacity_wh")`` or ``("ground_stations", 0)``.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

import yaml

#: keys whose integer values read better in hex (ids, APIDs)
_HEX_KEYS = {"id", "param_id", "func_id", "event_id", "device_id", "spacecraft_apid", "bootloader_apid",
             "action_func_id", "arm_code"}
_HEX_PARENTS = {"param_ids"}

Path = tuple


def _scalar(v: Any, key: Any = None, parent: Any = None) -> str:
    if isinstance(v, bool) or v is None:
        return yaml.safe_dump(v, default_flow_style=True).split("\n")[0]
    if isinstance(v, int):
        if v >= 0x100 and (key in _HEX_KEYS or parent in _HEX_PARENTS):
            return f"0x{v:04X}"
        return str(v)
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return yaml.safe_dump(v, default_flow_style=True).split("\n")[0]
        r = repr(v)
        if "e" in r and "." not in r.split("e")[0]:
            m, e = r.split("e")
            r = f"{m}.0e{e}"          # YAML 1.1 reads 1e-06 as a string, 1.0e-06 as a float
        return r
    s = yaml.safe_dump(v, default_flow_style=True, width=10**9, allow_unicode=True)
    s = s.rstrip("\n")
    if s.endswith("\n..."):
        s = s[:-4].rstrip("\n")
    if s.endswith("..."):
        s = s[:-3].rstrip()
    return s


def _key(k: Any) -> str:
    if isinstance(k, (int, float)) and not isinstance(k, bool):
        return str(k)
    # A key may land inside a flow mapping, where ", [ ] { }" end a plain
    # scalar ("If FAIL, which contingency" split into two keys): quote those.
    if isinstance(k, str) and re.search(r"[,\[\]{}]", k):
        return json.dumps(k, ensure_ascii=False)
    return _scalar(k)


def _is_scalar(v: Any) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def _flowable(v: Any, depth: int = 0) -> bool:
    """Values written on one line: scalars, lists of flowables, small mappings of flowables."""
    if _is_scalar(v):
        return True
    if depth > 3:
        return False
    if isinstance(v, list):
        return all(_flowable(x, depth + 1) for x in v) and len(_flow(v)) <= 160
    if isinstance(v, dict):
        return all(_flowable(x, depth + 1) for x in v.values()) and len(_flow(v)) <= 160
    return False


_PLAIN_FLOW = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-/ ]*$")


def _flow_scalar(v: Any, key: Any = None, parent: Any = None) -> str:
    """A scalar inside a flow collection: plain only when unambiguous, else JSON-quoted."""
    if isinstance(v, str):
        plain = _scalar(v)
        if _PLAIN_FLOW.match(v) and plain == v and not v.endswith(" "):
            return v
        return json.dumps(v, ensure_ascii=False)
    return _scalar(v, key, parent)


def _flow(v: Any, key: Any = None, parent: Any = None) -> str:
    if _is_scalar(v):
        return _flow_scalar(v, key, parent)
    if isinstance(v, list):
        return "[" + ", ".join(_flow(x, key, parent) for x in v) + "]"
    if isinstance(v, dict):
        if not v:
            return "{}"
        return "{" + ", ".join(f"{_key(k)}: {_flow(x, k, key)}" for k, x in v.items()) + "}"
    raise TypeError(f"cannot write {type(v).__name__} to YAML")


def _c(comment: str | None) -> str:
    if not comment:
        return ""
    return "  # " + " ".join(str(comment).split())


def dump(data: Any, comments: dict[Path, str] | None = None, header: list[str] | None = None) -> str:
    """YAML text of ``data`` with ``comments`` keyed by path; ``header`` lines go on top."""
    comments = comments or {}
    out: list[str] = [f"# {h}" if h else "#" for h in (header or [])]
    #: paths with a comment somewhere below them: written in block style so the comment has a line
    inner = {q[:i] for q in comments for i in range(1, len(q))}

    def block(v: Any, path: Path, indent: int, key: Any = None) -> None:
        pad = " " * indent
        if isinstance(v, dict):
            if not v:
                out.append(pad + "{}")
                return
            for k, x in v.items():
                p = path + (k,)
                com = comments.get(p)
                if _flowable(x) and p not in inner:
                    val = _scalar(x, k, key) if _is_scalar(x) else _flow(x, k, key)
                    out.append(f"{pad}{_key(k)}: {val}{_c(com)}")
                else:
                    if com:
                        out.append(f"{pad}{_key(k)}:{_c(com)}")
                    else:
                        out.append(f"{pad}{_key(k)}:")
                    block(x, p, indent + 2, k)
            return
        if isinstance(v, list):
            if not v:
                out.append(pad + "[]")
                return
            for i, x in enumerate(v):
                p = path + (i,)
                com = comments.get(p)
                if _flowable(x) and p not in inner:
                    val = _scalar(x, key, None) if _is_scalar(x) else _flow(x, key, None)
                    out.append(f"{pad}- {val}{_c(com)}")
                elif isinstance(x, dict):
                    # first key on the dash line
                    if com:
                        out.append(f"{pad}-{_c(com)}")
                        block(x, p, indent + 2, key)
                    else:
                        start = len(out)
                        block(x, p, indent + 2, key)
                        out[start] = pad + "- " + out[start][indent + 2:]
                else:
                    out.append(f"{pad}-{_c(com)}")
                    block(x, p, indent + 2, key)
            return
        out.append(pad + _flow(v, key))

    if isinstance(data, (dict, list)):
        block(data, (), 0)
    else:
        out.append(_flow(data))
    return "\n".join(out) + "\n"
