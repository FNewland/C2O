"""`translate --stale` (work bundle or Anthropic API) and `apply DIR`."""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import re

from . import TOOL_VERSION, catalogs, overlay, typo
from .config import Config, expand
from .docs import analyse, old_en_section
from .mdsync import Alignment, Pair, build_state, fit_section, save_state, segment
from .textutil import text_hash

STYLE_SUMMARY = """\
French style (binding; full guide STYLE_FR.md, terminology glossary.csv):
1. International/European French (not Canadian). Books: formal, « vous ». UI: terse; actions in the
   infinitive (« Acquitter »), ALL-CAPS labels stay all caps with accents (« ÉTAT »). Procedures: infinitive.
2. Identifiers never change: mnemonics, parameter IDs, enum/mode names (SAFE, NOMINAL), PUS service IDs,
   APIDs, procedure IDs (LEOP-001), file names, anything in `code` or fenced code, {{placeholders}}.
3. Keep byte-identical: code, LaTeX maths (except real words in \\text{…}), URLs/link targets, image paths,
   {#id}/{: .class} blocks, HTML comments/tags, front-matter keys, table shape, heading count and levels.
4. Procedures: keep the parsed keys **TC:** **Verify:** **LABEL:** **BRANCH:** **GO/NO-GO:** **Action:**
   **Note:** in English; never write step-jump prose (« passer à l'étape 3 »).
5. Numbers: every EN number appears in FR. Prose: decimal comma (3,5 kg). Values an operator types,
   thresholds, command arguments, code and maths keep the decimal point.
6. Engineering « budget » → « bilan ». Voice-loop words (Go/No-Go, Standby, Hold, Mark, Roger) stay English.
7. Do NOT insert special spaces before ; : ! ? or inside « » — the tool applies French typography itself.
8. Do not fix or improve the technical content; mirror the English exactly.
"""

UPDATE_RULE = ("Update FR_CURRENT so that it reflects the change from EN_OLD to EN_NEW. Edit only the "
               "affected sentences and keep every other French word exactly as it is.")
FRESH_RULE = "Translate EN_NEW into French. Return the complete section (heading line included)."


# ------------------------------------------------------------------ glossary
class Glossary:
    def __init__(self, path: str | None):
        self.rows = []
        if path and os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    if r.get("en"):
                        rx = re.compile(r"(?<![\w-])" + re.escape(r["en"].strip()) + r"(?:s|es)?(?![\w-])", re.I)
                        self.rows.append((rx, r))

    def matching(self, text: str) -> list[dict]:
        return [r for rx, r in self.rows if rx.search(text)]

    @staticmethod
    def line(r: dict) -> str:
        n = (r.get("note") or "").strip()
        return f"{r['en']} → {r['fr']}" + (f"  ({n})" if n else "")


# ------------------------------------------------------------------ collect
def collect(cfg: Config, only: set, files: set | None, include_conflicts: bool, gl: Glossary,
            max_items: int | None = None) -> list[dict]:
    items: list[dict] = []
    want = {"stale", "missing"} | ({"conflict"} if include_conflicts else set())
    if "docs" in only:
        for pair in cfg.docs:
            if files and not ({pair.en, pair.fr} & files):
                continue
            ds = analyse(pair)
            for p in ds.al.pairs:
                if p.en is None or p.status not in want:
                    continue
                if p.en.level == 0 and not p.en.text.strip():
                    continue
                en_hash = p.en.hash(en=True)
                items.append({
                    "kind": "doc", "status": p.status,
                    "en_path": cfg.ref(pair.en), "fr_path": cfg.ref(pair.fr),
                    "section_id": p.en.id, "level": p.en.level,
                    "en_hash": en_hash, "fr_hash": p.fr.hash(en=False) if p.fr else None,
                    "en_new": p.en.text,
                    "en_old": old_en_section(ds, p.en.id, (p.rec or {}).get("en_hash")) if p.rec else None,
                    "fr_current": p.fr.text if p.fr else None,
                    "glossary": [Glossary.line(r) for r in gl.matching(p.en.text)],
                })
    if "catalogs" in only:
        allc = {c.name: c for c in cfg.catalogs}
        for c in cfg.catalogs:
            if files and not ({c.fr} & files):
                continue
            res = catalogs.check_catalog(c, allc)
            keys = catalogs.expected_keys(c)
            for k in res["missing"]:
                en = catalogs.en_text_for(k, keys, None)
                items.append({"kind": "catalog", "catalog": c.name, "key": k, "en": en,
                              "plural_form": (k[len(catalogs.strip_plural(k)):] or None) if catalogs.is_plural_form(k, keys) else None,
                              "glossary": [Glossary.line(r) for r in gl.matching(en)], "fr": None})
    if "overlay" in only and cfg.overlay:
        for e in overlay.load_db(cfg.overlay["output_abs"]):
            if e.get("orphan"):
                continue
            stale = overlay.is_stale(e)
            if e.get("fr") is None or stale:
                items.append({"kind": "overlay", "key": e["key"], "en": e["en"],
                              "en_old": e.get("en_prev") if stale else None,
                              "fr_current": e.get("fr"), "en_hash": text_hash(e["en"], en=True),
                              "glossary": [Glossary.line(r) for r in gl.matching(e["en"])], "fr": None})
    if max_items:
        items = items[:max_items]
    for n, it in enumerate(items, 1):
        it["id"] = ("d%04d" if it["kind"] == "doc" else "s%04d") % n
    return items


# ------------------------------------------------------------------ emit
INSTRUCTIONS = """# i18n work bundle — {n_docs} doc section(s), {n_str} string(s)

Created {created} by tools/i18n {version}. Process every item, then run
`python3 -m tools.i18n apply {dir}` from the repo root.

## Doc sections (docs/)
For each `docs/<id>.en.md` write `docs/<id>.fr.md` containing the complete French section:
exactly one heading line of the same level as the English (none for a `_preamble` item), then the body.
* `<id>.fr_current.md` present → {update_rule}
* `<id>.en_old.md` present → it is the English the current French was made from; diff it against `.en.md`.
* No `.fr_current.md` → {fresh_rule}
* `<id>.glossary.txt` lists the binding glossary terms that occur in the section.
* `manifest.json` gives each item's file, section id and status.

## Strings (strings.json)
Fill the `"fr"` field of each item (leave `null` to skip). Keep `{{{{placeholders}}}}`, `$t(...)`, `<0>` tags,
mnemonics and numbers exactly. `plural_form` `_one`/`_other` = the French singular/plural form of the
string. Overlay items with `fr_current` are stale: make the smallest edit for the `en_old`→`en` change.

{style}"""


def emit(cfg: Config, items: list[dict], out_dir: str) -> str:
    ddir = os.path.join(out_dir, "docs")
    os.makedirs(ddir, exist_ok=True)
    for f in os.listdir(ddir):            # never let an old result leak into a new bundle
        if f.endswith((".md", ".txt")):
            os.remove(os.path.join(ddir, f))
    manifest = {"tool_version": TOOL_VERSION, "config": cfg.path,
                "created": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                "items": []}
    strings = []
    for it in items:
        if it["kind"] == "doc":
            base = os.path.join(out_dir, "docs", it["id"])
            _w(base + ".en.md", it["en_new"])
            if it.get("en_old"):
                _w(base + ".en_old.md", it["en_old"])
            if it.get("fr_current"):
                _w(base + ".fr_current.md", it["fr_current"])
            if it["glossary"]:
                _w(base + ".glossary.txt", "\n".join(it["glossary"]) + "\n")
            manifest["items"].append({k: v for k, v in it.items()
                                      if k not in ("en_new", "en_old", "fr_current", "glossary")})
        else:
            strings.append(it)
    with open(os.path.join(out_dir, "strings.json"), "w", encoding="utf-8") as f:
        json.dump(strings, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write("\n")
    n_docs = sum(1 for i in items if i["kind"] == "doc")
    _w(os.path.join(out_dir, "INSTRUCTIONS.md"), INSTRUCTIONS.format(
        n_docs=n_docs, n_str=len(strings), created=manifest["created"], version=TOOL_VERSION,
        dir=out_dir, update_rule=UPDATE_RULE, fresh_rule=FRESH_RULE, style=STYLE_SUMMARY))
    return out_dir


def _w(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ------------------------------------------------------------------ API
def run_api(cfg: Config, out_dir: str, model: str, max_tokens: int = 16000) -> int:
    try:
        import anthropic  # type: ignore
    except ImportError:
        raise SystemExit("i18n translate --api: the `anthropic` package is not installed "
                         "(pip install anthropic) — or omit --api to write a work bundle.")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("i18n translate --api: ANTHROPIC_API_KEY is not set.")
    client = anthropic.Anthropic()
    with open(os.path.join(out_dir, "manifest.json"), encoding="utf-8") as f:
        man = json.load(f)
    system = ("You are a professional EN→FR technical translator for spacecraft operations and "
              "engineering education material.\n" + STYLE_SUMMARY)
    done = 0
    for it in man["items"]:
        base = os.path.join(out_dir, "docs", it["id"])
        en_new = _r(base + ".en.md")
        en_old, fr_cur, gl = _r(base + ".en_old.md"), _r(base + ".fr_current.md"), _r(base + ".glossary.txt")
        parts = []
        if en_old:
            parts.append(f"<EN_OLD>\n{en_old}</EN_OLD>")
        parts.append(f"<EN_NEW>\n{en_new}</EN_NEW>")
        if fr_cur:
            parts.append(f"<FR_CURRENT>\n{fr_cur}</FR_CURRENT>")
        if gl:
            parts.append(f"<GLOSSARY>\n{gl}</GLOSSARY>")
        parts.append((UPDATE_RULE if fr_cur else FRESH_RULE) +
                     " Reply with the French section only, inside <FR>…</FR>.")
        msg = client.messages.create(model=model, max_tokens=max_tokens, system=system,
                                     messages=[{"role": "user", "content": "\n\n".join(parts)}])
        text = "".join(getattr(b, "text", "") for b in msg.content)
        m = re.search(r"<FR>\n?(.*?)</FR>", text, re.S)
        if m:
            _w(base + ".fr.md", m.group(1))
            done += 1
    spath = os.path.join(out_dir, "strings.json")
    strings = json.load(open(spath, encoding="utf-8"))
    for i in range(0, len(strings), 40):
        batch = strings[i:i + 40]
        payload = [{k: s.get(k) for k in ("id", "en", "en_old", "fr_current", "plural_form", "glossary") if s.get(k)}
                   for s in batch]
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content":
                       "Translate each item's `en` into French (UI labels / database descriptions). "
                       "For items with fr_current, make the smallest edit reflecting en_old→en. "
                       "Reply with a JSON object {id: french} only.\n\n" + json.dumps(payload, ensure_ascii=False)}])
        text = "".join(getattr(b, "text", "") for b in msg.content)
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            continue
        try:
            got = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        for s in batch:
            if isinstance(got.get(s["id"]), str):
                s["fr"] = got[s["id"]]
                done += 1
    with open(spath, "w", encoding="utf-8") as f:
        json.dump(strings, f, ensure_ascii=False, indent=1)
    return done


def _r(p):
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------------ apply
def _abs(cfg: Config, ref: str) -> str:
    return expand(ref, cfg.root, cfg.raw)[0]


def apply(cfg: Config, bundle: str, log) -> tuple[set, int]:
    """Write results back. Returns (touched absolute paths, number of problems)."""
    with open(os.path.join(bundle, "manifest.json"), encoding="utf-8") as f:
        man = json.load(f)
    touched: set = set()
    problems = 0
    by_file: dict[str, list] = {}
    for it in man["items"]:
        res = _r(os.path.join(bundle, "docs", it["id"] + ".fr.md"))
        if res is not None and res.strip():
            by_file.setdefault(it["fr_path"], []).append((it, res))
    pairs = {(_abs(cfg, p.fr)): p for p in cfg.docs}
    for fr_ref, its in by_file.items():
        fr_path = _abs(cfg, fr_ref)
        pair = pairs.get(fr_path)
        if pair is None:
            log(f"ERROR {fr_ref}: not a configured doc pair"); problems += 1
            continue
        ds = analyse(pair)
        by_id = {p.en.id: p for p in ds.al.pairs if p.en is not None}
        repl: dict[str, str] = {}
        for it, res in its:
            p = by_id.get(it["section_id"])
            if p is None or p.en.hash(en=True) != it["en_hash"]:
                log(f"SKIP  {fr_ref} [{it['section_id']}]: English changed since the bundle was made")
                problems += 1
                continue
            cur = p.fr.hash(en=False) if p.fr else None
            if cur != it.get("fr_hash"):
                log(f"SKIP  {fr_ref} [{it['section_id']}]: French changed since the bundle was made")
                problems += 1
                continue
            new = typo.fix(res)
            heads = [s for s in segment(new) if s.level > 0]
            want = 0 if p.en.level == 0 else 1
            if len(heads) != want or (want and heads[0].level != p.en.level):
                log(f"ERROR {fr_ref} [{it['section_id']}]: result must contain exactly {want} heading(s)"
                    f"{' of level ' + str(p.en.level) if want else ''}; got {[h.level for h in heads]}")
                problems += 1
                continue
            repl[p.en.id] = fit_section(new, p.en)
        if not repl:
            continue
        parts = []
        for p in ds.al.pairs:
            if p.en is not None and p.en.id in repl:
                parts.append((p, repl[p.en.id]))
            elif p.fr is not None:
                parts.append((p, p.fr.text))
            elif p.en is not None and p.en.level == 0:
                parts.append((p, ""))
        texts = [t for _, t in parts]
        for k in range(len(texts) - 1):
            if texts[k] and not texts[k].endswith("\n"):
                texts[k] += "\n"
        new_fr = "".join(texts)
        os.makedirs(os.path.dirname(fr_path), exist_ok=True)
        with open(fr_path, "w", encoding="utf-8") as f:
            f.write(new_fr)
        new_secs = segment(new_fr)
        if len(new_secs) == len(parts):
            al = Alignment([Pair(p.en, s, p.rec) for (p, _), s in zip(parts, new_secs)])
        else:
            from .mdsync import align
            al = align(segment(ds.en_text), new_secs, None)
            log(f"WARN  {fr_ref}: re-segmentation differs; state rebuilt positionally")
        st = build_state(cfg.ref(pair.en), al, ds.state, set(repl))
        save_state(fr_path, st)
        touched.add(fr_path)
        log(f"wrote {fr_ref}: {len(repl)} section(s)")
    # strings
    spath = os.path.join(bundle, "strings.json")
    strings = json.load(open(spath, encoding="utf-8")) if os.path.exists(spath) else []
    cats = {c.name: c for c in cfg.catalogs}
    cat_data: dict[str, dict] = {}
    db = None
    for s in strings:
        fr = s.get("fr")
        if not isinstance(fr, str) or not fr.strip():
            continue
        fr = typo.fix(fr, markdown=False)
        errs = catalogs.string_problems(s["en"], fr, s.get("key", ""), bool(s.get("plural_form")))
        if errs:
            log(f"ERROR {s['kind']} {s['key']!r}: " + "; ".join(errs)); problems += 1
            continue
        if s["kind"] == "catalog":
            c = cats.get(s["catalog"])
            if c is None:
                continue
            if c.name not in cat_data:
                cat_data[c.name] = catalogs.load_catalog(c.fr) if os.path.exists(c.fr) else {}
            cat_data[c.name][s["key"]] = fr
        elif s["kind"] == "overlay" and cfg.overlay:
            if db is None:
                db = {e["key"]: e for e in overlay.load_db(cfg.overlay["output_abs"])}
            e = db.get(s["key"])
            if e is None or text_hash(e["en"], en=True) != s.get("en_hash"):
                log(f"SKIP  overlay {s['key']}: English changed since the bundle was made"); problems += 1
                continue
            e["fr"] = fr
            e["en_hash"] = s["en_hash"]
            e.pop("en_prev", None)
    for name, data in cat_data.items():
        catalogs.save_catalog(cats[name].fr, data)
        touched.add(cats[name].fr)
        log(f"wrote {cfg.rel(cats[name].fr)}")
    if db is not None:
        overlay.save_db(cfg.overlay["output_abs"], list(db.values()))
        touched.add(cfg.overlay["output_abs"])
        log(f"wrote {cfg.rel(cfg.overlay['output_abs'])}")
    return touched, problems
