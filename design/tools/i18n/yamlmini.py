"""Tiny YAML reader/writer so the tool runs without PyYAML.

load(text): uses PyYAML when installed, else a block-YAML subset parser that is
enough for i18n.yaml and the db.yaml overlay this tool writes (nested block
maps/lists, single-line flow maps/lists, quoted and plain scalars, comments).
"""
from __future__ import annotations

import json
import re

try:  # optional
    import yaml as _pyyaml  # type: ignore
except Exception:  # pragma: no cover - exercised only without PyYAML
    _pyyaml = None

HAVE_PYYAML = _pyyaml is not None


class YamlError(ValueError):
    pass


def load(text: str, force_mini: bool = False):
    if _pyyaml is not None and not force_mini:
        return _pyyaml.safe_load(text)
    return MiniParser(text).parse()


def require_pyyaml(what: str):
    if _pyyaml is None:
        raise SystemExit(
            f"i18n: PyYAML is required to {what}. Install it (pip install pyyaml) "
            "or run inside the project venv. Docs and catalogs work without it.")
    return _pyyaml


# ---------------------------------------------------------------- mini parser
def _strip_comment(line: str) -> str:
    out, q = [], None
    for i, ch in enumerate(line):
        if q:
            out.append(ch)
            if ch == q:
                if q == "'" and i + 1 < len(line) and line[i + 1] == "'":
                    continue
                if q == '"' and i > 0 and line[i - 1] == "\\":
                    continue
                q = None
            continue
        if ch in "'\"" and (not out or out[-1] in " \t:[{,-") :
            q = ch
        elif ch == "#" and (not out or out[-1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _split_flow(s: str) -> list[str]:
    parts, depth, q, cur = [], 0, None, []
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "'\"":
            q = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def _find_colon(s: str) -> int:
    q = None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
            continue
        if ch in "'\"" and i == 0:
            q = ch
        elif ch == ":" and (i + 1 == len(s) or s[i + 1] in " \t"):
            return i
    return -1


def scalar(s: str):
    s = s.strip()
    if s == "":
        return None
    if s.startswith('"'):
        return json.loads(s)
    if s.startswith("'"):
        return s[1:-1].replace("''", "'")
    if s.startswith("[") and s.endswith("]"):
        return [scalar(p) for p in _split_flow(s[1:-1])]
    if s.startswith("{") and s.endswith("}"):
        d = {}
        for p in _split_flow(s[1:-1]):
            c = _find_colon(p)
            if c < 0:
                raise YamlError(f"bad flow mapping item: {p!r}")
            d[str(scalar(p[:c]))] = scalar(p[c + 1:])
        return d
    if s in ("null", "~", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+)([eE][-+]?\d+)?", s):
        return float(s)
    return s


class MiniParser:
    def __init__(self, text: str):
        self.lines = []
        for raw in text.splitlines():
            if raw.strip() in ("---", "..."):
                continue
            ln = _strip_comment(raw)
            if ln.strip():
                self.lines.append((len(ln) - len(ln.lstrip(" ")), ln.strip()))
        self.i = 0

    def parse(self):
        if not self.lines:
            return None
        return self._block(self.lines[0][0])

    def _block(self, indent):
        if self.lines[self.i][1].startswith("- ") or self.lines[self.i][1] == "-":
            return self._list(indent)
        return self._map(indent)

    def _value_after(self, rest: str, indent: int):
        if rest.strip():
            return scalar(rest)
        if self.i < len(self.lines) and self.lines[self.i][0] > indent:
            return self._block(self.lines[self.i][0])
        if (self.i < len(self.lines) and self.lines[self.i][0] == indent
                and self.lines[self.i][1].startswith("-")):
            return self._list(indent)  # "key:\n- a" (list at same indent)
        return None

    def _map(self, indent):
        d = {}
        while self.i < len(self.lines):
            ind, txt = self.lines[self.i]
            if ind < indent or txt.startswith("-"):
                break
            if ind > indent:
                raise YamlError(f"unexpected indent at: {txt!r}")
            c = _find_colon(txt)
            if c < 0:
                raise YamlError(f"expected 'key: value' at: {txt!r}")
            key = scalar(txt[:c])
            self.i += 1
            d[str(key) if not isinstance(key, str) else key] = self._value_after(txt[c + 1:], indent)
        return d

    def _list(self, indent):
        out = []
        while self.i < len(self.lines):
            ind, txt = self.lines[self.i]
            if ind != indent or not (txt.startswith("- ") or txt == "-"):
                break
            body = txt[1:].strip()
            if not body:
                self.i += 1
                out.append(self._value_after("", indent))
                continue
            c = _find_colon(body)
            if c >= 0 and not body.startswith(("{", "[", '"', "'")):
                # "- key: v" starts an inline mapping; continuation lines are deeper
                sub_indent = indent + (len(txt) - len(body))
                self.lines[self.i] = (sub_indent, body)
                out.append(self._map(sub_indent))
            else:
                self.i += 1
                out.append(scalar(body))
        return out


# ---------------------------------------------------------------- writer
def q(s) -> str:
    """Emit a YAML double-quoted scalar (JSON string syntax is valid YAML)."""
    if s is None:
        return "null"
    if isinstance(s, bool):
        return "true" if s else "false"
    if isinstance(s, (int, float)):
        return str(s)
    return json.dumps(str(s), ensure_ascii=False)
