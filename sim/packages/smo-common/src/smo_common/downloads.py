"""Course PDFs offered for download (textbooks, workbooks, references).

The list is ``smo_common/downloads.yaml`` (see its header). Three servers
mount :func:`register_download_routes`:

  * the documentation viewer (tools/doc_viewer.py)  ``audience="student"``
  * the MCS (manual page)                            ``audience="student"``
  * the instructor console (simulator, behind IAP)   ``audience="instructor"``

A request names a manifest **id**, never a path: the file is looked up from
the manifest, so nothing outside the listed files can be served, and an
instructor-only id answers 404 on a student server exactly like an unknown
one.

Where the files are: ``$SMO_DOWNLOADS_DIR/<source>`` (the image copies the
listed files there at build time, see docker/Dockerfile), else the C2O
checkout this package sits in (``<repo>/<source>``), so a laptop running
start.sh serves them with no build step. A listed file that is in neither
place is left out of the listing (and logged), never a broken link.

CLI (from sim/)::

    python3 -m smo_common.downloads check            # every listed file exists, sizes match
    python3 -m smo_common.downloads sizes            # rewrite the size: fields
    python3 -m smo_common.downloads bundle --src ROOT --out DIR [--audience student]
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

MANIFEST = Path(__file__).resolve().with_name("downloads.yaml")
#: The C2O checkout root when running from a clone
#: (sim/packages/smo-common/src/smo_common/downloads.py -> parents[5]).
REPO_ROOT = Path(__file__).resolve().parents[5]
ENV_DIR = "SMO_DOWNLOADS_DIR"

AUDIENCES = ("student", "instructor")
CATEGORIES = ("textbook", "workbook", "reference", "guide")
LANGS = ("en", "fr")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


# ── manifest ──────────────────────────────────────────────────────────

def load_manifest(path: Path | str = MANIFEST) -> dict[str, Any]:
    """The parsed manifest, validated. Raises ValueError on a bad entry."""
    import yaml
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    docs = data.get("documents") or []
    excluded = data.get("excluded") or []
    errors = validate(docs, excluded)
    if errors:
        raise ValueError("downloads.yaml: " + "; ".join(errors))
    return {"documents": docs, "excluded": excluded}


def validate(docs: list[dict], excluded: list[dict]) -> list[str]:
    errs: list[str] = []
    ids: dict[str, dict] = {}
    for d in docs:
        i = str(d.get("id", ""))
        if not ID_RE.match(i):
            errs.append(f"bad id {i!r}")
        if i in ids:
            errs.append(f"duplicate id {i}")
        ids[i] = d
        t = d.get("title") or {}
        if not (isinstance(t, dict) and t.get("en") and t.get("fr")):
            errs.append(f"{i}: title needs en and fr")
        if d.get("lang") not in LANGS:
            errs.append(f"{i}: lang must be one of {LANGS}")
        if d.get("audience") not in AUDIENCES:
            errs.append(f"{i}: audience must be one of {AUDIENCES}")
        if d.get("category") not in CATEGORIES:
            errs.append(f"{i}: category must be one of {CATEGORIES}")
        src = str(d.get("source", ""))
        if (not src.lower().endswith(".pdf") or src.startswith("/")
                or ".." in Path(src).parts):
            errs.append(f"{i}: source must be a relative .pdf path")
        if not isinstance(d.get("size"), int):
            errs.append(f"{i}: size must be an integer")
    for d in docs:
        p = d.get("pair")
        if p is None:
            continue
        other = ids.get(p)
        if other is None:
            errs.append(f"{d['id']}: pair {p} is not listed")
        elif other.get("pair") != d["id"]:
            errs.append(f"{d['id']}: pair {p} does not point back")
        elif other.get("lang") == d.get("lang"):
            errs.append(f"{d['id']}: pair {p} has the same language")
        elif other.get("audience") != d.get("audience"):
            errs.append(f"{d['id']}: pair {p} has another audience")
    listed = {str(d.get("source")) for d in docs}
    for x in excluded:
        if not x.get("reason"):
            errs.append(f"excluded {x.get('source')}: no reason")
        if x.get("source") in listed:
            errs.append(f"{x.get('source')} is both listed and excluded")
    return errs


@lru_cache(maxsize=1)
def _cached_manifest() -> dict[str, Any]:
    return load_manifest()


def roots() -> list[Path]:
    """Where listed files are looked for, in order."""
    out = []
    env = os.environ.get(ENV_DIR)
    if env:
        out.append(Path(env))
    out.append(REPO_ROOT)
    return out


def resolve(doc: dict, search: Iterable[Path] | None = None) -> Path | None:
    """The file for a manifest entry, or None if it is not on this host."""
    rel = Path(str(doc["source"]))
    for root in (search if search is not None else roots()):
        p = Path(root) / rel
        if p.is_file():
            return p
    return None


def visible(docs: list[dict], audience: str) -> list[dict]:
    """Entries a server for *audience* may offer."""
    if audience not in AUDIENCES:
        raise ValueError(f"audience must be one of {AUDIENCES}")
    return [d for d in docs if audience == "instructor" or d["audience"] == "student"]


def listing(audience: str, *, manifest: dict | None = None,
            search: Iterable[Path] | None = None, prefix: str = "/api/downloads") -> list[dict]:
    """JSON-ready entries that exist on this host, with their real size."""
    m = manifest or _cached_manifest()
    search = list(search) if search is not None else roots()
    out = []
    shown = visible(m["documents"], audience)
    shown_ids = {d["id"] for d in shown}
    for d in shown:
        p = resolve(d, search)
        if p is None:
            logger.warning("download %s: %s not found under %s", d["id"], d["source"],
                           ", ".join(str(r) for r in search))
            continue
        out.append({
            "id": d["id"], "title": dict(d["title"]), "lang": d["lang"],
            "audience": d["audience"], "category": d["category"],
            "size": p.stat().st_size, "filename": p.name,
            "pair": d.get("pair") if d.get("pair") in shown_ids else None,
            "licence": d.get("licence"),
            "url": f"{prefix}/{d['id']}",
        })
    return out


# ── HTTP ──────────────────────────────────────────────────────────────

def register_download_routes(app: Any, *, audience: str, prefix: str = "/api/downloads",
                             manifest: dict | None = None,
                             search: Iterable[Path] | None = None) -> Any:
    """Mount ``GET {prefix}`` (JSON listing) and ``GET {prefix}/{id}`` (the PDF).

    ``?inline=1`` on a file asks the browser to open it in a tab
    (``Content-Disposition: inline``); otherwise it is an attachment.
    """
    from aiohttp import web
    if audience not in AUDIENCES:
        raise ValueError(f"audience must be one of {AUDIENCES}")
    search = list(search) if search is not None else None

    def _m() -> dict:
        return manifest or _cached_manifest()

    async def _list(request):
        try:
            items = listing(audience, manifest=_m(), search=search, prefix=prefix)
        except (OSError, ValueError) as e:      # a broken manifest must not 500 a page
            logger.warning("downloads listing unavailable: %s", e)
            items = []
        return web.json_response({"audience": audience, "documents": items},
                                 headers={"Cache-Control": "no-cache"})

    async def _file(request):
        doc_id = request.match_info["id"]
        if not ID_RE.match(doc_id):
            raise web.HTTPNotFound(text="unknown document")
        try:
            docs = {d["id"]: d for d in visible(_m()["documents"], audience)}
        except (OSError, ValueError):
            docs = {}
        d = docs.get(doc_id)
        path = resolve(d, search) if d else None
        if path is None:
            raise web.HTTPNotFound(text="unknown document")
        disp = "inline" if request.query.get("inline") in ("1", "true") else "attachment"
        name = path.name
        ascii_name = re.sub(r'[^A-Za-z0-9._-]', "_", name)
        from urllib.parse import quote
        return web.FileResponse(path, headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f"{disp}; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=3600",
        })

    app.router.add_get(prefix, _list)
    app.router.add_get(prefix + "/{id}", _file)
    return app


# ── CLI ───────────────────────────────────────────────────────────────

def _check(m: dict, search: list[Path]) -> list[str]:
    probs = []
    for d in m["documents"]:
        p = resolve(d, search)
        if p is None:
            probs.append(f"missing  {d['source']}")
        elif p.stat().st_size != d["size"]:
            probs.append(f"size     {d['source']}: manifest {d['size']}, file {p.stat().st_size}")
    return probs


def _rewrite_sizes(search: list[Path]) -> int:
    text = MANIFEST.read_text(encoding="utf-8")
    m = load_manifest()
    n = 0
    for d in m["documents"]:
        p = resolve(d, search)
        if p is None or p.stat().st_size == d["size"]:
            continue
        pat = re.compile(r"(source: " + re.escape(d["source"]) + r"\n\s+size: )\d+")
        text, k = pat.subn(lambda mo: mo.group(1) + str(p.stat().st_size), text)
        n += k
    MANIFEST.write_text(text, encoding="utf-8")
    return n


def _bundle(src: Path, out: Path, audience: str) -> int:
    """Copy the listed files from a tree laid out like the repository
    (``src/<source>``) to ``out/<source>``. Missing files are an error:
    an image must not ship with a hole in its list."""
    m = load_manifest()
    missing = []
    total = 0
    for d in visible(m["documents"], audience):
        s = src / d["source"]
        if not s.is_file():
            missing.append(d["source"])
            continue
        dst = out / d["source"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(s, dst)
        total += s.stat().st_size
    if missing:
        print("missing listed PDFs:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1
    print(f"bundled {len(visible(m['documents'], audience))} PDFs, "
          f"{total / 1e6:.1f} MB -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m smo_common.downloads")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("sizes")
    b = sub.add_parser("bundle")
    b.add_argument("--src", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--audience", choices=AUDIENCES, default="instructor",
                   help="instructor (default) ships every listed file")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        probs = _check(load_manifest(), roots())
        print("\n".join(probs) or "downloads.yaml: ok")
        return 1 if probs else 0
    if a.cmd == "sizes":
        print(f"updated {_rewrite_sizes(roots())} size field(s)")
        return 0
    return _bundle(a.src, a.out, a.audience)


if __name__ == "__main__":
    raise SystemExit(main())
