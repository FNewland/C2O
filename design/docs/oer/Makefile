# Build the open textbook PDF on Linux or macOS.
#
#   make deps      # one-off: system packages + Python packages (Debian/Ubuntu or Homebrew)
#   make figures   # regenerate all figures with matplotlib (optional; PNGs are committed)
#   make           # build ../pdf/Concurrent_Spacecraft_Design_OER.pdf
#   make check     # list the fonts embedded in the PDF (should be Carlito + DejaVu only)
#   make docker    # build inside a clean Debian container (no local deps needed)
#
# WeasyPrint picks fonts through fontconfig, so the build machine must have
# Carlito (metric-compatible with Calibri, SIL OFL) and DejaVu installed; the
# CSS names only those two families so the result is identical everywhere.

PY      ?= python3
PDF     := ../pdf/Concurrent_Spacecraft_Design_OER.pdf
CHAPTERS:= $(wildcard chapters/*.md)
FIGDIR  := ../assets/figures

.PHONY: all deps figures check docker clean

all: $(PDF)

$(PDF): $(CHAPTERS) build_oer.py ../_render_math.py $(wildcard $(FIGDIR)/fig_*.png)
	$(PY) build_oer.py

figures:
	cd $(FIGDIR) && $(PY) make_all.py

check: $(PDF)
	$(PY) -c "import pymupdf,sys; d=pymupdf.open('$(PDF)'); print(sorted({f[3] for p in d for f in p.get_fonts(full=True)})); print(d.page_count,'pages')"

deps:
	@if command -v apt-get >/dev/null; then \
	  sudo apt-get install -y python3-pip fonts-crosextra-carlito fonts-dejavu-core \
	    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev libcairo2 fontconfig; \
	elif command -v brew >/dev/null; then \
	  brew install pango cairo libffi fontconfig; \
	  brew install --cask font-carlito font-dejavu || true; \
	fi
	$(PY) -m pip install --user weasyprint markdown matplotlib numpy pymupdf
	fc-cache -f >/dev/null 2>&1 || true
	fc-match Carlito; fc-match "DejaVu Sans Mono"

docker:
	docker build -t spacecdf-oer -f Dockerfile ../.. && \
	docker run --rm -v "$$(pwd)/../pdf:/out" spacecdf-oer

clean:
	rm -f book.md book.math.md
