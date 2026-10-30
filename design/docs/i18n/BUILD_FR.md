# Building the French PDFs

One command rebuilds every French PDF in this repo (course books, Week 3 pack, OER):

```bash
FR_COURSE_DIR=<Drive>/docs/course/fr EN_COURSE_DIR=<Drive>/docs/course \
    bash docs/build_course_pdfs_fr.sh          # add --no-oer to skip the OER (about 80 s)
```

The defaults are `docs/course/fr` and `docs/course`. The English books are read only for anchor mapping.

In the cloud workspace: `cd /home/claude/work/cdf && FR_COURSE_DIR=/home/claude/work/out/course_fr EN_COURSE_DIR=/home/claude/work/drive_course bash docs/build_course_pdfs_fr.sh`

| Output | Source |
|---|---|
| `docs/pdf/fr/SpaceCDF_Textbook_FR.pdf` | `facilitator_book_expanded` + `orbit_north_week3` (Partie 2) + `back_cover` |
| `docs/pdf/fr/SpaceCDF_Workbook_FR.pdf` | `learner_workbook_expanded` + `orbit_north_week3_workbook` |
| `docs/pdf/fr/SpaceCDF_Instructor_Book_FR.pdf` | `instructor_book` |
| `docs/pdf/fr/ORBIT_NORTH_W3_<Name>_FR.pdf` (8) | `docs/orbit_north/week3/fr/<name>.md` |
| `docs/pdf/Concurrent_Spacecraft_Design_OER_FR.pdf` | `docs/oer/fr/chapters/*.md` |

Individual builds:

```bash
cd docs/oer && python3 build_oer.py --lang fr        # OER only (English: no flag, unchanged)
python3 docs/build_course_books.py --lang fr --src DIR --en-src DIR [--only textbook workbook instructor week3]
python3 docs/build_course_books.py --lang en --src DIR   # English twin of the course books -> docs/pdf/en/
```

Prerequisites (same as English): `pip install --break-system-packages weasyprint markdown matplotlib pymupdf`, plus the
Carlito and DejaVu fonts (`make -C docs/oer deps`). Both fonts have U+202F (NNBSP), so French spacing renders as written.
Run `python3 docs/assets/figures/make_all.py` once if `docs/assets/figures/fig_*.png` are missing.

How it works:

* **Anchors.** French headings slugify differently. Each build renders the English source through the same pipeline and gives the n-th French heading the id of the n-th English heading. The structure is 1:1 and checked with `i18n/mdparity.py`; the build stops if the heading counts differ. Each build prints `internal links N, unresolved M`.
* **Build text.** All text the build adds is in French: cover, « Table des matières », running heads, « Page N sur M », and the CC BY 4.0 notice. The page has `<html lang="fr">` and `hyphens: auto` on prose.
* **Figures.** Raster figures are the English ones. See `docs/oer/fr/FIGURES_TODO.md`.
