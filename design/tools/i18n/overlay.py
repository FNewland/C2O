"""YAML label overlay: spacecraft-database prose → configs/<mission>/i18n/fr/db.yaml.

Each overlay entry:  {key: "kind:id:field", en: "...", en_hash: "...", fr: "..." | null}
  * en       — current English (refreshed by `extract`)
  * en_hash  — hash of the English the French was made from (stale when it differs
               from hash(en)); for untranslated entries it tracks en
  * en_prev  — previous English, kept when it changes under a translation
  * orphan   — true when the source no longer has the key (kept only if fr is set)

Extraction rules (i18n.yaml → yaml_overlay.rules):
  - kind: tc                     # key prefix
    files: commands/tc_catalog.yaml   # glob(s) relative to yaml_overlay.base
    items: commands.*            # dotted path; '*' iterates a list or mapping
    id: "{name}"                 # template: {field} of the item, {^field} of the
                                 #   enclosing '*' item, {$key} list index / map key,
                                 #   {^$key}, {$file} file stem, {a|b} first non-empty
    fields: [description, position_roles.*]   # dotted; trailing .* = each sub-key
"""
from __future__ import annotations

import json
import os
import re
from collections import OrderedDict

from . import yamlmini
from .config import iglob
from .textutil import text_hash, word_count

HEADER = """# EN→FR overlay of the spacecraft-database prose (labels, descriptions…).
# Generated and refreshed by `python3 -m tools.i18n extract`; translators fill `fr`.
# en_hash = hash of the English the French was written from; when it differs from
# the current `en` the entry is STALE.  fr: null = untranslated (client shows EN).
# Keys are kind:id:field and never change with the English text.
"""


class _Frame:
    __slots__ = ("item", "key")

    def __init__(self, item, key):
        self.item, self.key = item, key


def _walk(obj, segs, frames):
    if not segs:
        yield obj, frames
        return
    s, rest = segs[0], segs[1:]
    if s == "*":
        if isinstance(obj, dict):
            it = obj.items()
        elif isinstance(obj, list):
            it = enumerate(obj)
        else:
            return
        for k, v in it:
            yield from _walk(v, rest, frames + [_Frame(v, k)])
    else:
        if isinstance(obj, dict) and s in obj:
            yield from _walk(obj[s], rest, frames)


def _get(obj, path: str):
    for p in path.split("."):
        if isinstance(obj, dict) and p in obj:
            obj = obj[p]
        elif isinstance(obj, list) and p.isdigit() and int(p) < len(obj):
            obj = obj[int(p)]
        else:
            return None
    return obj


def _render_id(tpl: str, frames: list, item, file_stem: str) -> str:
    def one(expr: str) -> str:
        up = len(expr) - len(expr.lstrip("^"))
        expr = expr.lstrip("^")
        if expr == "$file":
            return file_stem
        fr_i = len(frames) - 1 - up
        if fr_i < 0:
            return ""
        fr = frames[fr_i]
        if expr == "$key":
            return str(fr.key)
        v = _get(item if up == 0 else fr.item, expr)
        return "" if v is None or isinstance(v, (dict, list)) else str(v)

    def sub(m):
        for alt in m.group(1).split("|"):
            v = one(alt.strip())
            if v != "":
                return v
        return ""
    return re.sub(r"\{([^{}]+)\}", sub, tpl)


def _fields(item, spec: str):
    if spec.endswith(".*"):
        sub = _get(item, spec[:-2])
        if isinstance(sub, dict):
            for k, v in sub.items():
                yield f"{spec[:-2]}.{k}", v
        elif isinstance(sub, list):
            for k, v in enumerate(sub):
                yield f"{spec[:-2]}.{k}", v
    else:
        yield spec, _get(item, spec)


def extract_entries(ov: dict) -> tuple["OrderedDict[str, str]", list[str]]:
    y = yamlmini.require_pyyaml("extract the YAML overlay")
    base = ov["base_abs"]
    out: "OrderedDict[str, str]" = OrderedDict()
    notes: list[str] = []
    for rule in ov.get("rules") or []:
        files = rule["files"] if isinstance(rule["files"], list) else [rule["files"]]
        paths = []
        for f in files:
            paths += iglob(os.path.join(base, f))
        if not paths:
            notes.append(f"rule {rule['kind']}: no file matches {files}")
        for p in paths:
            with open(p, encoding="utf-8") as fh:
                doc = y.safe_load(fh)
            stem = os.path.splitext(os.path.basename(p))[0]
            segs = [s for s in (rule.get("items") or "").split(".") if s]
            for item, frames in _walk(doc, segs, [_Frame(doc, stem)]):
                if not isinstance(item, dict):
                    continue
                ident = _render_id(rule.get("id", "{$key}"), frames, item, stem)
                if not ident:
                    notes.append(f"{os.path.relpath(p, base)}: item without id in rule {rule['kind']}")
                    continue
                for spec in rule.get("fields") or []:
                    for fname, val in _fields(item, spec):
                        if not isinstance(val, str) or not val.strip():
                            continue
                        val = val.strip()
                        key = f"{rule['kind']}:{ident}:{fname}"
                        if key in out and out[key] != val:
                            n = 2
                            while f"{key}#{n}" in out and out[f"{key}#{n}"] != val:
                                n += 1
                            notes.append(f"duplicate key {key} with different text → {key}#{n}")
                            key = f"{key}#{n}"
                        out[key] = val
    return out, notes


# ------------------------------------------------------------------ db.yaml io
def load_db(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    data = None
    if yamlmini.HAVE_PYYAML:
        data = yamlmini.load(text)
    else:
        data = _load_db_fast(text)
    if not data:
        return []
    entries = data.get("entries") if isinstance(data, dict) else data
    return [dict(e) for e in (entries or [])]


def _load_db_fast(text: str) -> dict:
    """Reader for the exact format save_db writes (no PyYAML needed)."""
    entries, cur = [], None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or line.startswith("entries:"):
            continue
        m = re.match(r"^(- |  )(\w+): (.*)$", line)
        if not m:
            return yamlmini.MiniParser(text).parse()   # hand-edited: generic subset parser
        if m.group(1) == "- ":
            cur = {}
            entries.append(cur)
        cur[m.group(2)] = yamlmini.scalar(m.group(3))
    return {"entries": entries}


FIELD_ORDER = ("key", "en", "en_hash", "fr", "en_prev", "orphan", "note")


def save_db(path: str, entries: list[dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [HEADER, "entries:"]
    for e in entries:
        first = True
        for k in FIELD_ORDER + tuple(k for k in e if k not in FIELD_ORDER):
            if k not in e or (k in ("en_prev", "orphan", "note") and e[k] in (None, False, "")):
                continue
            lines.append(("- " if first else "  ") + f"{k}: {yamlmini.q(e[k])}")
            first = False
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def is_stale(e: dict) -> bool:
    return e.get("fr") is not None and text_hash(e.get("en", ""), en=True) != e.get("en_hash")


# ------------------------------------------------------------------ operations
def extract(ov: dict) -> dict:
    src, notes = extract_entries(ov)
    path = ov["output_abs"]
    old = {e["key"]: e for e in load_db(path)}
    out: list[dict] = []
    stats = {"new": 0, "changed": 0, "orphaned": 0, "dropped": 0}
    for key, en in src.items():
        h = text_hash(en, en=True)
        e = old.pop(key, None)
        if e is None:
            out.append({"key": key, "en": en, "en_hash": h, "fr": None})
            stats["new"] += 1
            continue
        e.pop("orphan", None)
        if e.get("en") != en:
            stats["changed"] += 1
            if e.get("fr") is None:
                e["en_hash"] = h
                e.pop("en_prev", None)
            else:
                if text_hash(e.get("en", ""), en=True) == e.get("en_hash"):
                    e["en_prev"] = e.get("en")
                if h == e.get("en_hash"):
                    e.pop("en_prev", None)
            e["en"] = en
        out.append(e)
    for key, e in old.items():   # no longer in the source
        if e.get("fr") is None:
            stats["dropped"] += 1
            continue
        e["orphan"] = True
        stats["orphaned"] += 1
        out.append(e)
    save_db(path, out)
    stats.update(entries=len(out), words=sum(word_count(e["en"]) for e in out if not e.get("orphan")),
                 notes=notes)
    return stats


def summary(entries: list[dict]) -> dict:
    s = {"entries": len(entries), "translated": 0, "untranslated": 0, "stale": 0, "orphan": 0}
    for e in entries:
        if e.get("orphan"):
            s["orphan"] += 1
        elif e.get("fr") is None:
            s["untranslated"] += 1
        elif is_stale(e):
            s["stale"] += 1
        else:
            s["translated"] += 1
    return s


def build(ov: dict, out_path: str | None = None) -> tuple[str, int]:
    entries = load_db(ov["output_abs"])
    data = OrderedDict()
    for e in entries:
        if e.get("fr") is not None and not e.get("orphan") and not is_stale(e):
            data[e["key"]] = e["fr"]
    out_path = out_path or ov.get("client_json_abs")
    if not out_path:
        raise SystemExit("i18n build: yaml_overlay.client_json not configured")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return out_path, len(data)


def accept(ov: dict, keys: set | None = None) -> int:
    path = ov["output_abs"]
    entries = load_db(path)
    n = 0
    for e in entries:
        if e.get("fr") is None or (keys and e["key"] not in keys):
            continue
        h = text_hash(e["en"], en=True)
        if e.get("en_hash") != h or "en_prev" in e:
            e["en_hash"] = h
            e.pop("en_prev", None)
            n += 1
    save_db(path, entries)
    return n
