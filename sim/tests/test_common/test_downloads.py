"""Course PDFs offered for download (smo_common/downloads.yaml + downloads.py).

* the manifest: every listed file exists at its size, pairs are symmetric,
  nothing instructor-only or excluded is marked for students, and every PDF
  tracked in the repository is either listed or excluded with a reason (so a
  new book cannot go missing silently, nor a draft leak);
* the routes: students get the student list only, instructor ids answer 404
  on a student server exactly like unknown ids, a request can name only a
  manifest id (no path), and the file goes out as application/pdf with an
  attachment (or inline) Content-Disposition;
* the three mounts (doc viewer, MCS, instructor console + GSG) and the image
  packaging (Dockerfile step, compose second context, .dockerignore);
* the shared renderer (smo_common/ui/downloads.js) under node, EN and FR.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common import downloads as D

SIM = Path(__file__).resolve().parents[2]
C2O = SIM.parent
MAN = D.load_manifest()
DOCS = MAN["documents"]
BY_ID = {d["id"]: d for d in DOCS}

#: File-name markers of material that must never reach a student server.
INSTRUCTOR_MARKERS = re.compile(
    r"Instructor|Facilitator|Breakpoint|Failure_Modes|Code_Design|software_architecture",
    re.I)


# ── manifest ──────────────────────────────────────────────────────────

def test_manifest_lives_outside_the_hashed_mission_config():
    # configs/eosat1 is identified by docker/config-hash.sh; course books
    # must not change that hash.
    assert D.MANIFEST.parent.name == "smo_common"
    assert not (SIM / "configs/eosat1/manual/downloads.yaml").exists()


def test_every_listed_file_exists_at_its_listed_size():
    for d in DOCS:
        p = C2O / d["source"]
        assert p.is_file(), f"{d['id']}: {d['source']} missing"
        assert p.stat().st_size == d["size"], (
            f"{d['id']}: size {d['size']} != {p.stat().st_size} "
            "(python3 -m smo_common.downloads sizes)")
        with open(p, "rb") as f:
            assert f.read(5) == b"%PDF-", f"{d['source']} is not a PDF"


def test_pairs_are_symmetric_and_bilingual():
    assert D.validate(DOCS, MAN["excluded"]) == []
    for d in DOCS:
        if d.get("pair"):
            o = BY_ID[d["pair"]]
            assert o["pair"] == d["id"] and {o["lang"], d["lang"]} == {"en", "fr"}
    # the bilingual student core is complete
    for base in ("oer-textbook", "spacecdf-textbook", "spacecdf-workbook",
                 "on-w3-tool-reference", "on-w3-procedure-quickref"):
        assert BY_ID[f"{base}-en"]["audience"] == "student"
        assert BY_ID[f"{base}-fr"]["audience"] == "student"


def test_no_instructor_only_or_excluded_file_is_offered_to_students():
    excluded = {x["source"] for x in MAN["excluded"]}
    for d in DOCS:
        if d["audience"] != "student":
            continue
        assert d["source"] not in excluded
        assert not INSTRUCTOR_MARKERS.search(d["source"]), \
            f"{d['source']} looks instructor-only but is listed for students"
        assert ".pre-cleanup" not in d["source"]
        assert "exports_demo" not in d["source"]
        assert "Recruitment" not in d["source"]
    assert {d["audience"] for d in DOCS if INSTRUCTOR_MARKERS.search(d["source"])} == {"instructor"}


def _tracked_pdfs() -> set[str]:
    try:
        out = subprocess.run(["git", "ls-files", "-z", "*.pdf"], cwd=C2O,
                             capture_output=True, check=True).stdout
        files = {f for f in out.decode("utf-8").split("\0") if f}
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return {p.relative_to(C2O).as_posix() for p in C2O.rglob("*.pdf")
            if not any(s in p.parts for s in (".git", "node_modules", "workspace"))}


def test_every_pdf_in_the_repository_is_listed_or_excluded():
    listed = {d["source"] for d in DOCS}
    excluded = {x["source"] for x in MAN["excluded"]}
    tracked = _tracked_pdfs()
    unclassified = sorted(tracked - listed - excluded)
    assert not unclassified, (
        "PDFs neither listed nor excluded in smo_common/downloads.yaml "
        f"(classify them): {unclassified}")
    stale = sorted(excluded - tracked)
    assert not stale, f"excluded entries for files that are gone: {stale}"


def test_validate_catches_bad_entries():
    good = dict(BY_ID["oer-textbook-en"], pair=None)
    assert D.validate([good], []) == []
    assert D.validate([dict(good, id="../x")], [])
    assert D.validate([dict(good, source="/etc/passwd.pdf")], [])
    assert D.validate([dict(good, source="design/../../x.pdf")], [])
    assert D.validate([dict(good, audience="everyone")], [])
    assert D.validate([dict(good, pair="nobody")], [])
    assert D.validate([good], [{"source": good["source"], "reason": "x"}])


def test_bundle_copies_exactly_the_listed_files(tmp_path):
    assert D.main(["bundle", "--src", str(C2O), "--out", str(tmp_path),
                   "--audience", "student"]) == 0
    got = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.pdf")}
    assert got == {d["source"] for d in DOCS if d["audience"] == "student"}


def test_bundle_fails_on_a_missing_file(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    assert D.main(["bundle", "--src", str(src), "--out", str(tmp_path / "o")]) == 1


# ── routes ────────────────────────────────────────────────────────────

async def _client(audience, **kw):
    app = web.Application()
    D.register_download_routes(app, audience=audience, **kw)
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


async def test_student_listing_has_students_only():
    c = await _client("student")
    try:
        j = await (await c.get("/api/downloads")).json()
        ids = {d["id"] for d in j["documents"]}
        assert j["audience"] == "student"
        assert ids == {d["id"] for d in DOCS if d["audience"] == "student"}
        oer = next(d for d in j["documents"] if d["id"] == "oer-textbook-en")
        assert oer["pair"] == "oer-textbook-fr" and oer["licence"] == "CC BY 4.0"
        assert oer["url"] == "/api/downloads/oer-textbook-en"
        assert oer["size"] == BY_ID["oer-textbook-en"]["size"]
        assert set(oer["title"]) == {"en", "fr"}
        assert not any("source" in d for d in j["documents"])   # no server paths
    finally:
        await c.close()


async def test_student_server_serves_a_pdf_as_attachment_or_inline():
    c = await _client("student")
    try:
        r = await c.get("/api/downloads/on-w3-tool-reference-fr")
        assert r.status == 200
        assert r.headers["Content-Type"] == "application/pdf"
        cd = r.headers["Content-Disposition"]
        assert cd.startswith("attachment;")
        assert 'filename="ORBIT_NORTH_W3_Student_Tool_Reference_FR.pdf"' in cd
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        body = await r.read()
        assert body[:5] == b"%PDF-" and len(body) == BY_ID["on-w3-tool-reference-fr"]["size"]
        r = await c.get("/api/downloads/on-w3-tool-reference-fr?inline=1")
        assert r.headers["Content-Disposition"].startswith("inline;")
        r = await c.head("/api/downloads/on-syllabus-en")
        assert r.status == 200
    finally:
        await c.close()


async def test_student_server_hides_instructor_books_and_paths():
    c = await _client("student")
    try:
        for bad in ("/api/downloads/spacecdf-instructor-book-en",
                    "/api/downloads/on-w3-breakpoint-spec-fr",
                    "/api/downloads/nope",
                    "/api/downloads/..%2F..%2Fetc%2Fpasswd",
                    "/api/downloads/%2e%2e",
                    "/api/downloads/design%2Fdocs%2Fpdf%2FSpaceCDF_Textbook.pdf",
                    "/api/downloads/SpaceCDF_Facilitator_Book.pre-cleanup.pdf"):
            r = await c.get(bad)
            assert r.status == 404, bad
        r = await c.get("/api/downloads/../../etc/passwd")
        assert r.status == 404
    finally:
        await c.close()


async def test_instructor_listing_has_everything():
    c = await _client("instructor")
    try:
        j = await (await c.get("/api/downloads")).json()
        assert {d["id"] for d in j["documents"]} == set(BY_ID)
        r = await c.get("/api/downloads/spacecdf-instructor-book-fr")
        assert r.status == 200 and r.headers["Content-Type"] == "application/pdf"
    finally:
        await c.close()


async def test_files_missing_on_this_host_are_left_out(tmp_path):
    c = await _client("student", search=[tmp_path])
    try:
        j = await (await c.get("/api/downloads")).json()
        assert j["documents"] == []
        assert (await c.get("/api/downloads/oer-textbook-en")).status == 404
    finally:
        await c.close()


async def test_image_directory_wins_over_the_checkout(tmp_path, monkeypatch):
    d = BY_ID["on-syllabus-en"]
    p = tmp_path / d["source"]
    p.parent.mkdir(parents=True)
    p.write_bytes(b"%PDF-1.4 image copy")
    monkeypatch.setenv(D.ENV_DIR, str(tmp_path))
    assert D.resolve(d) == p
    assert D.roots()[-1] == D.REPO_ROOT


# ── the three mounts + packaging ──────────────────────────────────────

def _load_doc_viewer():
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("_dl_doc_viewer", SIM / "tools/doc_viewer.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


async def test_doc_viewer_downloads_page_and_student_api(tmp_path):
    (tmp_path / "manual").mkdir()
    (tmp_path / "manual/a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    dv = _load_doc_viewer()
    c = TestClient(TestServer(dv.create_app(tmp_path)))
    await c.start_server()
    try:
        r = await c.get("/downloads?lang=fr")
        t = await r.text()
        assert r.status == 200 and '<html lang="fr">' in t
        assert "/static/shared/downloads.js" in t and 'id="dl-list"' in t
        assert 'href="/downloads?lang=fr"' in t and 'aria-current="page"' in t
        idx = await (await c.get("/")).text()
        assert 'href="/downloads"' in idx                       # sidebar entry
        j = await (await c.get("/api/downloads")).json()
        assert j["audience"] == "student"
        assert all(d["audience"] == "student" for d in j["documents"])
        assert (await c.get("/api/downloads/smo-failure-modes-catalog-en")).status == 404
        assert (await c.get("/static/shared/downloads.js")).status == 200
    finally:
        await c.close()


def test_mcs_serves_only_the_student_list_and_not_on_the_manual_page():
    """The MAN page is the spacecraft manual and the procedure cards; the
    course PDFs live on the documentation viewer's Downloads page
    (SCREEN_REVIEW #16). The MCS route stays student-only."""
    src = (SIM / "packages/smo-mcs/src/smo_mcs/server.py").read_text(encoding="utf-8")
    assert 'register_download_routes(app, audience="student")' in src
    js = (SIM / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js").read_text(encoding="utf-8")
    man = js[js.index("function buildManPage"):js.index("async function loadProcedureCards")]
    assert 'id="man-downloads"' not in man


def test_instructor_console_and_gsg_offer_every_entry():
    from smo_simulator.instructor.app import create_instructor_app

    class _E:
        config_dir = SIM / "configs/eosat1"
    app = create_instructor_app(_E())
    canon = {r.resource.canonical for r in app.router.routes() if r.resource is not None}
    assert "/api/downloads" in canon and "/api/downloads/{id}" in canon
    html = (SIM / "packages/smo-simulator/src/smo_simulator/instructor/static/modern/index.html"
            ).read_text(encoding="utf-8")
    assert 'id="downloads-list"' in html and "/static/shared/downloads.js" in html
    gsg = (SIM / "packages/smo-link/src/smo_link/gateway.py").read_text(encoding="utf-8")
    assert 'register_download_routes(local, audience="instructor")' in gsg
    assert gsg.index("register_download_routes(local") < gsg.index('"/{tail:.*}"')


def test_image_ships_the_listed_pdfs():
    df = (SIM / "docker/Dockerfile").read_text(encoding="utf-8")
    assert "from=course_pdfs,target=/tmp/c2o/design/docs/pdf" in df
    assert "python -m smo_common.downloads bundle --src /tmp/c2o --out /opt/smo/downloads" in df
    assert "SMO_DOWNLOADS_DIR=/opt/smo/downloads" in df
    compose = (SIM / "docker/compose.yaml").read_text(encoding="utf-8")
    assert re.search(r"additional_contexts:\s*\n\s*course_pdfs: \.\./\.\./design/docs/pdf", compose)
    ign = (SIM / "docker/.dockerignore").read_text(encoding="utf-8").splitlines()
    assert "!docs/*.pdf" in ign and ign.index("!docs/*.pdf") > ign.index("docs")
    for d in DOCS:   # each source is reachable from one of the two contexts
        s = d["source"]
        assert s.startswith("design/docs/pdf/") or s.startswith("sim/"), s
        if s.startswith("sim/"):
            rel = s[len("sim/"):]
            assert rel.startswith(("configs/", "docs/")) and rel.count("/") <= 3, s


# ── shared renderer (node) ────────────────────────────────────────────

NODE = shutil.which("node") or shutil.which("nodejs")


@pytest.mark.skipif(NODE is None, reason="node is required")
def test_renderer_groups_pairs_filters_and_translates(tmp_path):
    from tests.test_common.test_i18n_runtime import run_js
    import json
    docs = D.listing("instructor")
    real_fr = (SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json").read_text(encoding="utf-8")
    body = """
      Object.assign(__cats['/static/shared/i18n/fr.json'], %s);
      await M.I18n.ready;
      const L = await import('./downloads.js');
      const docs = %s;
      const all = L.renderDownloads(docs, 'all', 'en');
      const fr = L.renderDownloads(docs, 'fr', 'en');
      const en = L.renderDownloads(docs, 'en', 'en');
      return { all, fr, en, groups: L.groupDocs(docs).length,
               mb: L.fmtSize(12402724), kb: L.fmtSize(41162) };
    """ % (real_fr, json.dumps(docs))
    out = run_js(tmp_path, body)
    n_pairs = sum(1 for d in docs if d.get("pair")) // 2
    assert out["groups"] == len(docs) - n_pairs
    a = out["all"]["html"]
    assert out["all"]["shown"] == out["groups"]
    assert a.count('data-dl="oer-textbook-') == 1           # a pair is one row
    assert 'href="/api/downloads/oer-textbook-fr?inline=1"' in a
    assert 'download="Concurrent_Spacecraft_Design_OER_FR.pdf"' in a
    assert "Instructor only" in a and "CC BY 4.0" in a
    assert (a.index(">Textbooks<") < a.index(">Workbooks and worksheets<")
            < a.index(">References<") < a.index(">Guides<"))
    # FR filter: EN-only documents disappear, no EN file line remains
    assert "smo-installation-guide-en" not in out["fr"]["html"]
    assert 'class="dl-f" lang="en"' not in out["fr"]["html"]
    assert out["fr"]["shown"] < out["all"]["shown"] and out["en"]["shown"] == out["all"]["shown"]
    assert out["mb"] == "12.4 MB" and out["kb"] == "41 kB"

    out = run_js(tmp_path, body, search="?lang=fr")
    a = out["all"]["html"]
    assert ">Manuels<" in a and "Télécharger" in a and "Enseignants seulement" in a
    assert out["mb"] == "12.4 Mo" and out["kb"] == "41 ko"
