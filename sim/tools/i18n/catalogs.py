"""UI catalogs in i18next-v4 JSON with natural-language keys.

Key = the exact English source text (so English renders byte-identically with no
catalog). Plurals: key_one / key_other (key_many optional; _zero/_two/_few
tolerated). Context: key_<context> (satisfied by the plain key too).
Placeholders {{var}} / {{- var}}. The file is FLAT (keySeparator:false,
nsSeparator:false). null or "" = untranslated (the runtime falls back to English).

Expected keys are scanned from the configured sources:
  JS/TS/TSX/HTML:  t('…')  tText("…")  tHtml(`…`) (no ${…})  i18n.t(…)  i18next.t(…)
                   — names configurable per catalog (`functions:`);
                   `count` in the options ⇒ plural; `context: 'x'` ⇒ key_x;
                   `plural: '…'` gives the English other-form text
  HTML/SVG:        data-i18n="key", or data-i18n="" = each direct text node of the
                   element (whitespace-collapsed); data-i18n-html (value or the
                   collapsed inner HTML); data-i18n-{title,placeholder,aria-label}
                   (value or the attribute's own text); data-i18n-context="x"
  TSX:             i18nKey="…" (react-i18next <Trans>)
  JS/TS tables:    string values of the {…}/[…] literal assigned right after a
                   `// English text is the i18n key` (or `// i18n-keys`) comment
plus every key of the optional EN catalog file (`en:`).
"""
from __future__ import annotations

import html
import json
import os
import re
from collections import OrderedDict
from html.parser import HTMLParser

from .config import Catalog, iglob
from .textutil import identifiers, number_counter, placeholders

PLURAL_SUFFIXES = ("_zero", "_one", "_two", "_few", "_many", "_other")
REQUIRED_PLURALS = ("_one", "_other")
DEFAULT_FUNCTIONS = ("t", "tText", "tHtml")
DOM_ATTRS = ("title", "placeholder", "aria-label")
_TRANS_KEY = re.compile(r"""i18nKey\s*=\s*\{?\s*(?P<q>["'`])(?P<v>(?:\\.|(?!(?P=q)).)*?)(?P=q)""")
_JS_ESC = {"n": "\n", "t": "\t", "r": "\r", "'": "'", '"': '"', "\\": "\\", "`": "`"}
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source",
         "track", "wbr", "path", "circle", "rect", "line", "use", "stop", "polyline", "polygon", "ellipse"}
_COLLAPSE = re.compile(r"\s+")


def collapse(s: str) -> str:
    return _COLLAPSE.sub(" ", s).strip()


def _call_re(functions) -> re.Pattern:
    names = "|".join(re.escape(f) for f in sorted(set(functions), key=len, reverse=True))
    return re.compile(
        r"(?<![\w$])(?:(?:i18n|i18next|I18n)\.)?(?:" + names + r")\(\s*(?P<q>['\"`])"
        r"(?P<k>(?:\\.|(?!(?P=q)).)*?)(?P=q)\s*(?P<end>[,)])", re.S)


def _unescape_js(s: str) -> str:
    def rep(m):
        c = m.group(1)
        if c.startswith("u"):
            return chr(int(c[1:], 16))
        return _JS_ESC.get(c, c)
    return re.sub(r"\\(u[0-9a-fA-F]{4}|.)", rep, s)


def _call_args(text: str, pos: int) -> str:
    """Argument text after the key, up to the call's closing ')'."""
    depth, i, q = 1, pos, None
    while i < len(text) and i < pos + 2000:
        ch = text[i]
        if q:
            if ch == "\\":
                i += 2
                continue
            if ch == q:
                q = None
        elif ch in "'\"`":
            q = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return text[pos:i]
        i += 1
    return text[pos:i]


def _add(found, k, *flags):
    if k is None or not str(k).strip():
        return
    fl = {f for f in flags if f}
    if not any(f.startswith("ctx:") for f in fl):
        fl.add("plain")          # used at least once without a context
    found.setdefault(k, set()).update(fl)


def strip_js_comments(text: str) -> str:
    """Blank out // and /* */ comments (string- and template-aware) keeping offsets."""
    out = list(text)
    i, n, q = 0, len(text), None
    while i < n:
        ch = text[i]
        if q:
            if ch == "\\":
                i += 2
                continue
            if ch == q or (ch == "\n" and q != "`"):
                q = None
            i += 1
            continue
        if ch in "'\"`":
            q = ch
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def scan_js(text: str, functions=DEFAULT_FUNCTIONS) -> dict[str, set]:
    """{key: flags}; flags: 'plural', 'ctx:<name>', 'pl:<english other form>'."""
    found: dict[str, set] = {}
    raw, text = text, strip_js_comments(text)
    for m in _call_re(functions).finditer(text):
        k = m.group("k")
        if m.group("q") == "`" and "${" in k:
            continue
        k = _unescape_js(k)
        flags = set()
        if m.group("end") == ",":
            args = _call_args(text, m.end())
            if re.search(r"\bcount\b", args):
                flags.add("plural")
                p = re.search(r"\bplural\s*:\s*(['\"`])((?:\\.|(?!\1).)*)\1", args)
                if p and "${" not in p.group(2):
                    flags.add("pl:" + _unescape_js(p.group(2)))
                o = re.search(r"\bdefaultValue_one\s*:\s*(['\"`])((?:\\.|(?!\1).)*)\1", args)
                if o and "${" not in o.group(2):
                    flags.add("one:" + _unescape_js(o.group(2)))
            c = re.search(r"\bcontext\s*:\s*['\"](\w+)['\"]", args)
            if c:
                flags.add("ctx:" + c.group(1))
        if not any(f.startswith("ctx:") for f in flags):
            flags.add("plain")
        _add(found, k, *flags)
    for m in _TRANS_KEY.finditer(text):
        _add(found, _unescape_js(m.group("v")))
    for k in _marked_tables(raw):
        _add(found, k)
    # explicit data-i18n="…" inside JS template strings (no ${})
    for m in re.finditer(r"""data-i18n(?:-(?:html|title|placeholder|aria-label))?=(["'])([^"'$<>{}]+)\1""", text):
        _add(found, html.unescape(m.group(2)))
    return found


_TABLE_MARK = re.compile(r"//\s*(?:English text is the i18n key|i18n-keys)\b[^\n]*\n")
_STR = r"(['\"])((?:\\.|(?!\1)[^\\\n])*)\1"


def _marked_tables(text: str):
    """String values of the object/array literal that follows a marker comment
    `// English text is the i18n key` (or `// i18n-keys`): used as t(TABLE[k])."""
    for m in _TABLE_MARK.finditer(text):
        i = m.end()
        j = text.find("=", i)
        if j < 0 or j - i > 300:
            continue
        k = j + 1
        while k < len(text) and text[k] in " \t\n":
            k += 1
        if k >= len(text) or text[k] not in "[{":
            continue
        block = text[k: k + len(_call_args(text, k + 1)) + 2]
        if block.startswith("{"):
            vals = re.finditer(r":\s*" + _STR, block)
        else:
            vals = re.finditer(r"(?:^|[\[,(])\s*" + _STR + r"\s*(?=[,\])])", block)
        for v in vals:
            yield _unescape_js(v.group(2))


class _DomScan(HTMLParser):
    def __init__(self, src: str):
        super().__init__(convert_charrefs=True)
        self.src = src
        self.found: dict[str, set] = {}
        self.stack: list[dict] = []
        self._line_starts = [0]
        for i, ch in enumerate(src):
            if ch == "\n":
                self._line_starts.append(i + 1)

    def _offset(self):
        ln, col = self.getpos()
        return self._line_starts[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        ctx = a.get("data-i18n-context") or ""
        flag = "ctx:" + ctx if ctx else None
        for attr in DOM_ATTRS:
            if f"data-i18n-{attr}" in a:
                _add(self.found, collapse(a[f"data-i18n-{attr}"] or a.get(attr) or ""), flag)
        frame = {"tag": tag, "text": False, "html": None, "flag": flag}
        if "data-i18n" in a:
            if a["data-i18n"]:
                _add(self.found, a["data-i18n"], flag)
            else:
                frame["text"] = True
        if "data-i18n-html" in a:
            if a["data-i18n-html"]:
                _add(self.found, a["data-i18n-html"], flag)
            else:
                frame["html"] = self._offset() + len(self.get_starttag_text() or "")
        if tag not in _VOID:
            self.stack.append(frame)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID and self.stack:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                fr = self.stack[i]
                if fr["html"] is not None:
                    _add(self.found, collapse(self.src[fr["html"]:self._offset()]), fr["flag"])
                del self.stack[i:]
                return

    def handle_data(self, data):
        if self.stack and self.stack[-1]["text"] and self.stack[-1]["tag"] not in ("script", "style"):
            if data.strip():
                _add(self.found, collapse(data), self.stack[-1]["flag"])


def scan_html(text: str, functions=DEFAULT_FUNCTIONS) -> dict[str, set]:
    found = scan_js(re.sub(r"<!--.*?-->", " ", text, flags=re.S), functions)   # inline <script> blocks
    p = _DomScan(text)
    try:
        p.feed(text)
        p.close()
    except Exception:   # malformed markup: keep what we have
        pass
    for k, fl in p.found.items():
        _add(found, k, *fl)
        found.setdefault(k, set())
    return found


def scan_file(path: str, functions=DEFAULT_FUNCTIONS) -> dict[str, set]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith((".html", ".htm", ".svg")):
        return scan_html(text, functions)
    return scan_js(text, functions)


def expected_keys(cat: Catalog) -> dict[str, set]:
    keys: dict[str, set] = {}
    funcs = cat.functions or DEFAULT_FUNCTIONS
    for pat in cat.sources:
        for p in iglob(pat):
            if not os.path.isfile(p):
                continue
            try:
                found = scan_file(p, funcs)
            except (UnicodeDecodeError, OSError):
                continue
            for k, fl in found.items():
                keys.setdefault(k, set()).update(fl)
    if cat.en and os.path.exists(cat.en):
        for k in load_catalog(cat.en):
            base = strip_plural(k)
            if base != k:
                keys.setdefault(base, set()).add("plural")
            else:
                keys.setdefault(k, set())
    return keys


def load_catalog(path: str) -> "OrderedDict[str, object]":
    with open(path, encoding="utf-8") as f:
        data = json.load(f, object_pairs_hook=OrderedDict)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: catalog must be a JSON object")
    return data


def save_catalog(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def strip_plural(k: str) -> str:
    for s in PLURAL_SUFFIXES:
        if k.endswith(s) and len(k) > len(s):
            return k[: -len(s)]
    return k


def expected_entries(keys: dict[str, set]) -> "OrderedDict[str, tuple]":
    """Concrete FR keys expected -> (source key, alternative keys that also satisfy it)."""
    out: "OrderedDict[str, tuple]" = OrderedDict()
    for k, fl in keys.items():
        ctxs = sorted(f[4:] for f in fl if f.startswith("ctx:"))
        targets = ([(k, ())] if ("plain" in fl or not ctxs) else []) + [(f"{k}_{c}", (k,)) for c in ctxs]
        for b, alts in targets:
            if "plural" in fl:
                for s in REQUIRED_PLURALS:
                    out[b + s] = (k, tuple(a + s for a in alts) + (() if s == "_one" else (b,)))
            else:
                out[b] = (k, alts)
    return out


def source_key(key: str, keys: dict) -> str | None:
    """The natural-language source key a concrete FR key derives from (None = unknown)."""
    if key in keys:
        return key
    base = strip_plural(key)
    if base in keys and (base != key):
        return base
    for cand in (base, key):
        head = cand.rsplit("_", 1)[0]
        if "_" in cand and head in keys:
            return head
    return None


def _translated(v) -> bool:
    return isinstance(v, str) and v != ""


def en_text_for(key: str, keys: dict, en_cat: dict | None) -> str:
    src = source_key(key, keys) or strip_plural(key)
    if en_cat:
        for k in (key, src + "_other", src):
            if isinstance(en_cat.get(k), str) and en_cat[k]:
                return en_cat[k]
    if key.endswith("_one"):
        one = [f[4:] for f in keys.get(src, ()) if f.startswith("one:")]
        if one:
            return one[0]
    if key.endswith(("_other", "_many")):
        pl = [f[3:] for f in keys.get(src, ()) if f.startswith("pl:")]
        if pl:
            return pl[0]
    return src


def is_plural_form(key: str, keys: dict) -> bool:
    src = source_key(key, keys)
    return src is not None and "plural" in keys.get(src, ()) and key != src


def check_catalog(cat: Catalog, all_cats: dict[str, Catalog]) -> dict:
    res = {"errors": [], "warnings": [], "missing": [], "orphans": [], "stats": {}}
    keys = expected_keys(cat)
    exp = expected_entries(keys)
    en_cat = load_catalog(cat.en) if cat.en and os.path.exists(cat.en) else None
    files = []
    for path in cat.fr_files():
        if not os.path.exists(path):
            continue
        try:
            files.append((path, load_catalog(path)))
        except (ValueError, json.JSONDecodeError) as e:
            res["errors"].append(f"{cat.name}: cannot parse {path}: {e}")
    have: set = set()
    seen_val: dict = {}
    for path, data in files:
        have |= {k for k, v in data.items() if _translated(v)}
        for k, v in data.items():
            if _translated(v):
                if k in seen_val and seen_val[k][1] != v:
                    res["warnings"].append(f"{cat.name}: {k!r} translated differently in "
                                           f"{os.path.basename(seen_val[k][0])} and {os.path.basename(path)}")
                seen_val.setdefault(k, (path, v))
    for fb in cat.fallback:
        fc = all_cats.get(fb)
        if not fc:
            continue
        for path in fc.fr_files():
            if os.path.exists(path):
                try:
                    have |= {k for k, v in load_catalog(path).items() if _translated(v)}
                except (ValueError, json.JSONDecodeError):
                    pass
    keep = [re.compile(p) for p in cat.keep]
    translated = 0
    for path, data in files:
        tag = cat.name if len(files) == 1 else f"{cat.name}/{os.path.basename(path)}"
        for k, v in data.items():
            if isinstance(v, dict):
                res["errors"].append(f"{tag}: nested object under {k!r} (catalog must be flat; keySeparator:false)")
                continue
            if source_key(k, keys) is None and not any(r.search(k) for r in keep):
                res["orphans"].append(k)
                res["errors"].append(f"{tag}: FR key not used in sources: {k!r}")
                continue
            if v is None or v == "":
                continue
            if not isinstance(v, str):
                res["errors"].append(f"{tag}: value for {k!r} is not a string")
                continue
            translated += 1
            en = en_text_for(k, keys, en_cat)
            plural = is_plural_form(k, keys)
            res["errors"] += [f"{tag}: {k!r}: {m}" for m in string_problems(en, v, k, plural)]
            res["warnings"] += [f"{tag}: {k!r}: {m}" for m in string_warnings(en, v)]
    for k, (_src, alts) in exp.items():
        if k not in have and not any(a in have for a in alts):
            res["missing"].append(k)
    res["stats"] = {"expected": len(exp), "translated": translated,
                    "missing": len(res["missing"]), "orphans": len(res["orphans"]),
                    "fr_exists": os.path.exists(cat.fr)}
    return res


def string_problems(en: str, fr: str, key: str = "", plural: bool = False) -> list[str]:
    """Hard errors for one translated string."""
    out = []
    pe, pf = placeholders(en), placeholders(fr)
    if plural or key.endswith("_one"):
        pe.pop("{{count}}", None)
        pf.pop("{{count}}", None)
    if pe != pf:
        out.append(f"placeholder mismatch: EN {sorted(pe.elements())} FR {sorted(pf.elements())}")
    miss = identifiers(en) - identifiers(fr)
    if miss:
        out.append(f"identifiers not preserved: {sorted(miss)}")
    if not plural:
        ne, nf = number_counter(en), number_counter(fr)
        if ne - nf:
            out.append(f"numbers missing in FR: {sorted((ne - nf).elements())}")
    return out


def string_warnings(en: str, fr: str) -> list[str]:
    out = []
    if en != en.upper():   # mixed-case EN: acronyms should usually survive
        weak = identifiers(en, strong_only=False) - identifiers(fr, strong_only=False)
        if weak:
            out.append(f"acronyms not found in FR: {sorted(weak)}")
    return out


def extract_catalog(cat: Catalog, create: bool = False, prune: bool = False) -> dict:
    """Add expected keys missing from FR (value null); report / optionally drop orphans."""
    if not os.path.exists(cat.fr) and not create:
        return {"skipped": True}
    keys = expected_keys(cat)
    exp = expected_entries(keys)
    fr = load_catalog(cat.fr) if os.path.exists(cat.fr) else OrderedDict()
    added = 0
    for k, (_src, alts) in exp.items():
        if k not in fr and not any(a in fr for a in alts):
            fr[k] = None
            added += 1
    orphans = []
    for k in list(fr):
        if source_key(k, keys) is None and not any(re.search(p, k) for p in cat.keep):
            orphans.append(k)
            if prune and not _translated(fr[k]):
                del fr[k]
    save_catalog(cat.fr, fr)
    return {"added": added, "orphans": orphans, "total": len(fr)}
