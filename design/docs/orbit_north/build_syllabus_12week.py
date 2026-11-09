"""Build the 12-week ORBIT NORTH syllabus PDFs (EN + FR) with the course-book styling.

    python orbit_north/build_syllabus_12week.py   # -> docs/pdf/ORBIT_NORTH_Syllabus_12wk_{EN,FR}.pdf
"""
import pathlib
import sys

DOCS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOCS))
import build_course_books as b  # noqa: E402

for lang in ("en", "fr"):
    src = DOCS / "orbit_north" / f"syllabus_12week_{lang}.md"
    meta, body = b.split_yaml(src.read_text(encoding="utf-8"))
    en_body = b.split_yaml((DOCS / "orbit_north" / "syllabus_12week_en.md").read_text(encoding="utf-8"))[1]
    sub = meta["subtitle"]
    b.build(lang, "syllabus-12wk", f"ORBIT NORTH — {sub.split(' — ')[1]}", meta["course-codes"],
            DOCS / "pdf" / f"ORBIT_NORTH_Syllabus_12wk_{lang.upper()}.pdf", meta, body, "",
            en_body if lang == "fr" else None, meta["title"], sub, "ORBIT NORTH", meta["term"])
