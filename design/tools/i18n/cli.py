#!/usr/bin/env python3
"""i18n — keep French in sync with English (docs, UI catalogs, YAML overlay).

    python3 -m tools.i18n <command> [options]      (from the repo root)
    python3 tools/i18n/cli.py <command> [options]

Commands: status, check, extract, translate, apply, accept, backport, build, typo.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in (None, ""):   # run as a script: make `tools.i18n` importable
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, _root)
    __package__ = "tools.i18n"

from tools.i18n import TOOL_VERSION  # noqa: E402
from tools.i18n import catalogs, config as cfgmod, docs, gitutil, overlay, translate, typo  # noqa: E402


def _files_filter(cfg, files):
    if not files:
        return None
    out = set()
    for f in files:
        if not f:
            continue
        p = f if os.path.isabs(f) else os.path.join(cfg.root, f)
        out.add(os.path.normpath(p))
    return out


def _doc_selected(pair, sel):
    if sel is None:
        return True
    from tools.i18n.mdsync import sidecar_path
    return bool({pair.en, pair.fr, sidecar_path(pair.fr)} & sel)


def _cat_selected(cat, sel):
    if sel is None:
        return True
    if cat.fr in sel or (cat.en and cat.en in sel):
        return True
    for pat in cat.sources:
        if set(cfgmod.iglob(pat)) & sel:
            return True
    return False


def _overlay_selected(cfg, sel):
    if not cfg.overlay:
        return False
    if sel is None:
        return True
    if cfg.overlay["output_abs"] in sel:
        return True
    base = cfg.overlay["base_abs"]
    for r in cfg.overlay.get("rules") or []:
        for f in (r["files"] if isinstance(r["files"], list) else [r["files"]]):
            if set(cfgmod.iglob(os.path.join(base, f))) & sel:
                return True
    return False


# ------------------------------------------------------------------ status
def cmd_status(cfg, a):
    sel = _files_filter(cfg, a.files)
    rep = {"docs": [], "catalogs": [], "overlay": None,
           "unavailable": [{"group": g, "path": p, "reason": r} for g, p, r in cfg.unavailable]}
    tot: dict = {}
    for pair in cfg.docs:
        if not _doc_selected(pair, sel):
            continue
        ds = docs.analyse(pair)
        for k, v in ds.al.counts.items():
            tot[k] = tot.get(k, 0) + v
        rep["docs"].append({"en": cfg.ref(pair.en), "fr": cfg.ref(pair.fr), "group": pair.group,
                            "status": ds.file_status, "note": ds.al.note, "counts": ds.al.counts,
                            "sections": [{"id": (p.en.id if p.en else (p.rec or {}).get("id")),
                                          "status": p.status} for p in ds.al.pairs]
                            if a.sections else None})
    allc = {c.name: c for c in cfg.catalogs}
    for c in cfg.catalogs:
        if _cat_selected(c, sel):
            r = catalogs.check_catalog(c, allc)
            rep["catalogs"].append({"name": c.name, "fr": cfg.rel(c.fr), **r["stats"],
                                    "errors": len(r["errors"])})
    if _overlay_selected(cfg, sel):
        ents = overlay.load_db(cfg.overlay["output_abs"])
        rep["overlay"] = {"path": cfg.rel(cfg.overlay["output_abs"]), **overlay.summary(ents)}
    rep["totals"] = tot
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0
    print(f"i18n {TOOL_VERSION} — {cfg.rel(cfg.path)}")
    print("\nDOCS (sections: ok/stale/fr-edited/conflict/missing/orphan/untracked)")
    groups: dict = {}
    for d in rep["docs"]:
        groups.setdefault(d["group"], []).append(d)
    for g, ds_ in groups.items():
        print(f"  [{g}]")
        for d in ds_:
            if d["status"] == "ok" and not a.verbose:
                continue
            c = " ".join(f"{k} {v}" for k, v in sorted(d["counts"].items()))
            print(f"    {d['status']:<17} {d['en']}  →  {d['fr']}   {c}" + (f"  ({d['note']})" if d["note"] else ""))
            if a.sections and d["sections"]:
                for s in d["sections"]:
                    if s["status"] != "ok" or a.verbose:
                        print(f"        {s['status']:<10} {s['id']}")
        n_ok = sum(1 for d in ds_ if d["status"] == "ok")
        print(f"    {len(ds_)} file(s), {n_ok} fully in sync")
    print("  totals: " + (", ".join(f"{k} {v}" for k, v in sorted(tot.items())) or "none"))
    if rep["catalogs"]:
        print("\nCATALOGS (i18next v4, natural-language keys)")
        for c in rep["catalogs"]:
            ex = "" if c.get("fr_exists") else "  [fr file absent]"
            print(f"  {c['name']:<16} expected {c.get('expected', 0):>4}  translated {c.get('translated', 0):>4}  "
                  f"missing {c.get('missing', 0):>4}  orphans {c.get('orphans', 0)}  {c['fr']}{ex}")
    if rep["overlay"]:
        o = rep["overlay"]
        print(f"\nYAML OVERLAY {o['path']}: {o['entries']} entries — translated {o['translated']}, "
              f"untranslated {o['untranslated']}, stale {o['stale']}, orphan {o['orphan']}")
    if rep["unavailable"]:
        print("\nUNAVAILABLE (reported, not fatal)")
        for u in rep["unavailable"]:
            print(f"  [{u['group']}] {u['path']}: {u['reason']}")
    return 0


# ------------------------------------------------------------------ check
def run_check(cfg, strict=False, sel=None, verbose=False, out=print) -> tuple[int, int]:
    errors: list[str] = []
    warnings: list[str] = []
    no_fr: dict = {}
    for pair in cfg.docs:
        if not _doc_selected(pair, sel):
            continue
        ds = docs.analyse(pair)
        if ds.fr_text is None:
            g = no_fr.setdefault(pair.group, [0, 0])
            g[0] += 1
            g[1] += len(ds.al.pairs)
            if verbose:
                warnings.append(f"{cfg.rel(pair.en)}: no FR file")
            continue
        e, w = docs.check_doc(cfg, ds, strict)
        errors += e
        warnings += w
    for g, (nf, ns) in no_fr.items():
        (errors if strict else warnings).append(f"[{g}] {nf} file(s) have no French yet ({ns} sections)")
    allc = {c.name: c for c in cfg.catalogs}
    for c in cfg.catalogs:
        if not _cat_selected(c, sel):
            continue
        r = catalogs.check_catalog(c, allc)
        errors += r["errors"]
        if r["missing"]:
            msg = f"catalog {c.name}: {len(r['missing'])} key(s) without French" + \
                  ("" if os.path.exists(c.fr) else f" ({cfg.rel(c.fr)} absent)")
            (errors if strict else warnings).append(msg)
            if verbose:
                warnings += [f"  missing: {k!r}" for k in r["missing"][:200]]
        (errors if strict else warnings).extend(r["warnings"])
    if _overlay_selected(cfg, sel):
        path = cfg.overlay["output_abs"]
        ents = overlay.load_db(path)
        if not os.path.exists(path):
            warnings.append(f"overlay {cfg.rel(path)} absent (run: i18n extract)")
        s = overlay.summary(ents)
        for e in ents:
            if e.get("fr") is None or e.get("orphan"):
                continue
            for m in catalogs.string_problems(e["en"], e["fr"]):
                errors.append(f"overlay {e['key']}: {m}")
        tgt = errors if strict else warnings
        if s["stale"]:
            tgt.append(f"overlay: {s['stale']} stale entr(y/ies) (English changed)")
        if s["untranslated"]:
            tgt.append(f"overlay: {s['untranslated']} untranslated entr(y/ies)")
        if s["orphan"]:
            tgt.append(f"overlay: {s['orphan']} orphan entr(y/ies) (source key removed)")
    for u in cfg.unavailable:
        warnings.append(f"unavailable [{u[0]}] {u[1]}: {u[2]}")
    for e in errors:
        out(f"ERROR {e}")
    shown = warnings if verbose else _summarise(warnings)
    for w in shown:
        out(f"WARN  {w}")
    out(f"i18n check: {len(errors)} error(s), {len(warnings)} warning(s)" + ("" if strict else " (non-strict)"))
    return len(errors), len(warnings)


def _summarise(warnings, limit=25):
    if len(warnings) <= limit:
        return warnings
    return warnings[:limit] + [f"… {len(warnings) - limit} more (use -v)"]


def cmd_check(cfg, a):
    files = list(a.files or [])
    if a.staged:
        files += gitutil.staged_files(cfg.root)
        if not [f for f in files if f]:
            print("i18n check: no staged files")
            return 0
    sel = _files_filter(cfg, files) if (a.files or a.staged) else None
    n_err, _ = run_check(cfg, a.strict, sel, a.verbose)
    return 1 if n_err else 0


# ------------------------------------------------------------------ extract
def cmd_extract(cfg, a):
    only = set(a.only.split(",")) if a.only else {"overlay", "catalogs"}
    if "overlay" in only and cfg.overlay:
        st = overlay.extract(cfg.overlay)
        print(f"overlay {cfg.rel(cfg.overlay['output_abs'])}: {st['entries']} entries, {st['words']} English words "
              f"(new {st['new']}, changed {st['changed']}, orphaned {st['orphaned']}, dropped {st['dropped']})")
        for n in st["notes"]:
            print(f"  note: {n}")
    if "catalogs" in only:
        for c in cfg.catalogs:
            r = catalogs.extract_catalog(c, create=a.create, prune=a.prune)
            if r.get("skipped"):
                print(f"catalog {c.name}: {cfg.rel(c.fr)} absent — skipped (use --create)")
            else:
                print(f"catalog {c.name}: +{r['added']} key(s), {len(r['orphans'])} orphan(s), {r['total']} total")
                for k in r["orphans"][:50]:
                    print(f"  orphan: {k!r}")
    return 0


# ------------------------------------------------------------------ translate / apply
def cmd_translate(cfg, a):
    if not a.stale:
        print("i18n translate: only --stale mode is implemented (stale + missing items)")
        return 2
    only = set(a.only.split(",")) if a.only else {"docs", "catalogs", "overlay"}
    gl = translate.Glossary(cfg.glossary)
    items = translate.collect(cfg, only, _files_filter(cfg, a.paths), a.include_conflicts, gl, a.max_items)
    if not items:
        print("i18n translate: nothing stale or missing")
        return 0
    out_dir = a.emit or os.path.join(cfg.root, "tools", "i18n", "work")
    translate.emit(cfg, items, out_dir)
    nd = sum(1 for i in items if i["kind"] == "doc")
    print(f"bundle {out_dir}: {nd} doc section(s), {len(items) - nd} string(s)")
    if a.api:
        model = a.model or (cfg.raw.get("translate") or {}).get("model") or "claude-opus-5-5"
        n = translate.run_api(cfg, out_dir, model)
        print(f"API ({model}): {n} item(s) translated; applying…")
        return cmd_apply(cfg, argparse.Namespace(dir=out_dir, verbose=False))
    print(f"next: process {out_dir}/INSTRUCTIONS.md, then  python3 -m tools.i18n apply {out_dir}")
    return 0


def cmd_apply(cfg, a):
    touched, problems = translate.apply(cfg, a.dir, print)
    if not touched:
        print("apply: nothing written")
        return 1 if problems else 0
    n_err, _ = run_check(cfg, False, touched, getattr(a, "verbose", False))
    return 1 if (n_err or problems) else 0


# ------------------------------------------------------------------ accept / backport / build / typo
def cmd_accept(cfg, a):
    targets = a.paths or []
    sel_paths, sections = set(), {}
    for t in targets:
        path, _, sec = t.partition("#")
        p = os.path.normpath(path if os.path.isabs(path) else os.path.join(cfg.root, path))
        sel_paths.add(p)
        if sec:
            sections[p] = sec
    n = 0
    for pair in cfg.docs:
        if targets and not ({pair.en, pair.fr} & sel_paths):
            continue
        ds = docs.analyse(pair)
        if ds.fr_text is None:
            continue
        sec = sections.get(pair.en) or sections.get(pair.fr)
        msg = docs.accept(cfg, ds, init=a.init, waive=a.waive, section=sec)
        if not msg.startswith("skip") or targets or a.verbose:
            print(f"{cfg.rel(pair.fr)}: {msg}")
        n += 0 if msg.startswith("skip") else 1
    if cfg.overlay and (not targets or cfg.overlay["output_abs"] in sel_paths or a.key):
        if os.path.exists(cfg.overlay["output_abs"]) and not a.init:
            k = overlay.accept(cfg.overlay, set(a.key) if a.key else None)
            if k:
                print(f"overlay: {k} entr(y/ies) accepted")
    print(f"accept: {n} doc(s) recorded")
    return 0


def cmd_backport(cfg, a):
    sel = _files_filter(cfg, a.paths)
    any_ = False
    for pair in cfg.docs:
        if not _doc_selected(pair, sel):
            continue
        lines = docs.backport(cfg, docs.analyse(pair))
        if lines:
            any_ = True
            print("\n".join(lines))
    if not any_:
        print("backport: no fr-edited sections")
    return 0


def cmd_build(cfg, a):
    if not cfg.overlay:
        print("build: no yaml_overlay configured")
        return 0
    path, n = overlay.build(cfg.overlay, a.out)
    print(f"build: {n} translated key(s) → {cfg.rel(path)}")
    return 0


def cmd_typo(cfg, a):
    rc = 0
    for f in a.files:
        n, _ = typo.fix_file(f, write=a.fix)
        if n:
            print(f"{f}: {n} line(s) {'fixed' if a.fix else 'need French spacing'}")
            rc = 0 if a.fix else 1
    return rc


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(prog="i18n", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="path to i18n.yaml (default: search upward from cwd)")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--version", action="version", version=TOOL_VERSION)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default=argparse.SUPPRESS)
    common.add_argument("-v", "--verbose", action="store_true", default=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add = sub.add_parser

    def add_parser(name, **kw):
        return _add(name, parents=[common], **kw)
    sub.add_parser = add_parser

    s = sub.add_parser("status", help="sync state of every tracked item (no AI)")
    s.add_argument("--json", action="store_true")
    s.add_argument("--sections", action="store_true", help="list non-ok sections")
    s.add_argument("files", nargs="*")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("check", help="gate: parity/placeholders/identifiers = errors; stale = warnings")
    s.add_argument("--strict", action="store_true", help="stale/missing also fail")
    s.add_argument("--staged", action="store_true", help="only items touched by staged git files")
    s.add_argument("--files", nargs="*", default=None, help="only items touched by these files")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("extract", help="refresh overlay db.yaml and catalog skeletons")
    s.add_argument("--only", help="overlay,catalogs")
    s.add_argument("--create", action="store_true", help="create absent catalog files")
    s.add_argument("--prune", action="store_true", help="drop untranslated orphan catalog keys")
    s.set_defaults(fn=cmd_extract)

    s = sub.add_parser("translate", help="bundle (or translate via API) stale/missing items")
    s.add_argument("--stale", action="store_true")
    s.add_argument("--emit", metavar="DIR")
    s.add_argument("--api", action="store_true", help="use the anthropic SDK (ANTHROPIC_API_KEY)")
    s.add_argument("--model")
    s.add_argument("--only", help="docs,catalogs,overlay")
    s.add_argument("--include-conflicts", action="store_true")
    s.add_argument("--max-items", type=int)
    s.add_argument("paths", nargs="*")
    s.set_defaults(fn=cmd_translate)

    s = sub.add_parser("apply", help="write a processed bundle back, then check")
    s.add_argument("dir")
    s.set_defaults(fn=cmd_apply)

    s = sub.add_parser("accept", help="record current EN/FR hashes as synced")
    s.add_argument("--init", action="store_true", help="onboard pairs that have no sidecar yet")
    s.add_argument("--waive", action="store_true", help="also waive current parity findings")
    s.add_argument("--key", action="append", help="overlay key(s) to accept")
    s.add_argument("paths", nargs="*", help="EN or FR path, optionally PATH#section-id")
    s.set_defaults(fn=cmd_accept)

    s = sub.add_parser("backport", help="show fr-edited sections with diffs, for EN back-porting")
    s.add_argument("paths", nargs="*")
    s.set_defaults(fn=cmd_backport)

    s = sub.add_parser("build", help="overlay → client JSON (translated, non-stale only)")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("typo", help="French typography check / fix")
    s.add_argument("files", nargs="+")
    s.add_argument("--fix", action="store_true")
    s.set_defaults(fn=cmd_typo)

    a = ap.parse_args(argv)
    if a.cmd == "typo":
        return cmd_typo(None, a)
    cfg = cfgmod.load(a.config)
    return a.fn(cfg, a)


if __name__ == "__main__":
    sys.exit(main())
