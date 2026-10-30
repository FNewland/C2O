# Reproducible build of the open textbook PDF.
#   docker build -t spacecdf-oer -f docs/oer/Dockerfile .
#   docker run --rm -v "$PWD/docs/pdf:/out" spacecdf-oer
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv fontconfig \
      fonts-crosextra-carlito fonts-dejavu-core \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libcairo2 libffi8 \
    && rm -rf /var/lib/apt/lists/* && fc-cache -f

RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir \
      weasyprint==70.0 markdown matplotlib numpy pymupdf
ENV PATH="/venv/bin:$PATH" MPLBACKEND=Agg

WORKDIR /src
COPY docs/ /src/docs/

# Regenerate figures, build the PDF, copy it out.
CMD cd docs/assets/figures && python3 make_all.py \
 && cd ../../oer && python3 build_oer.py \
 && cp ../pdf/Concurrent_Spacecraft_Design_OER.pdf /out/ \
 && python3 -c "import pymupdf; d=pymupdf.open('/out/Concurrent_Spacecraft_Design_OER.pdf'); print(sorted({f[3] for p in d for f in p.get_fonts(full=True)}), d.page_count, 'pages')"
