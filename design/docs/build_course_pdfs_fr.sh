#!/bin/bash
# Build every French PDF of the SpaceCDF repo into docs/pdf/ (see docs/i18n/BUILD_FR.md).
#
#   FR_COURSE_DIR=<French single-file books> EN_COURSE_DIR=<English single-file books> \
#   FIG_DIR=<Drive assets/figures copy> bash docs/build_course_pdfs_fr.sh [--no-oer]
#
# FIG_DIR: folder holding fig_*.png/svg and their French fig_*_fr.* variants
# (default <EN_COURSE_DIR>/../assets/figures, the Drive layout).
#
#   docs/pdf/fr/SpaceCDF_Textbook_FR.pdf          facilitator_book_expanded + orbit_north_week3 + back_cover
#   docs/pdf/fr/SpaceCDF_Workbook_FR.pdf          learner_workbook_expanded + orbit_north_week3_workbook
#   docs/pdf/fr/SpaceCDF_Instructor_Book_FR.pdf   instructor_book
#   docs/pdf/fr/ORBIT_NORTH_W3_*_FR.pdf           docs/orbit_north/week3/fr/*.md
#   docs/pdf/Concurrent_Spacecraft_Design_OER_FR.pdf   docs/oer/fr/chapters (build_oer.py --lang fr)
#
# The English books are needed only for anchor mapping (French headings get
# the English heading ids, so the index and #links resolve).
set -eo pipefail
DOCS="$(cd "$(dirname "$0")" && pwd)"
FR_COURSE_DIR="${FR_COURSE_DIR:-$DOCS/course/fr}"
EN_COURSE_DIR="${EN_COURSE_DIR:-$DOCS/course}"

FIG_ARGS=()
[ -n "${FIG_DIR:-}" ] && FIG_ARGS=(--fig-dir "$FIG_DIR")

python3 "$DOCS/build_course_books.py" --lang fr --src "$FR_COURSE_DIR" --en-src "$EN_COURSE_DIR" "${FIG_ARGS[@]}" 2>&1 \
    | { grep -v -E "^WARNING|^ *$" || true; }
if [ "$1" != "--no-oer" ]; then
    (cd "$DOCS/oer" && python3 build_oer.py --lang fr 2>&1 | { grep -v -E "^WARNING|^ *$" || true; })
fi
for f in "$DOCS"/pdf/fr/*.pdf "$DOCS"/pdf/*_FR.pdf; do
    [ -f "$f" ] && printf "%5s pages  %s\n" "$(python3 -c "import pymupdf,sys;print(pymupdf.open(sys.argv[1]).page_count)" "$f" 2>/dev/null || echo '?')" "${f#$DOCS/}"
done
