# syntax=docker/dockerfile:1
#
# One image for every SMO process (LINK_DESIGN §5): simulator, space-link
# agent, ground-segment gateway (GSG), MCS, planner, RF bridge and the tools.
# docker/compose.yaml picks the process per service.
#
# Build from the repository root (the context must be the root):
#   SMO_CONFIG_HASH=$(docker/config-hash.sh)
#   docker build -f docker/Dockerfile \
#       --build-arg SMO_CONFIG_HASH=$SMO_CONFIG_HASH \
#       --build-context course_pdfs=../design/docs/pdf \
#       -t smo-suite:$SMO_CONFIG_HASH .
# (course_pdfs: the C2O course books, a second build context; compose.yaml
# passes it as additional_contexts. See "Course PDFs" below.)
# (docker compose does this for you; see docker/compose.yaml.)
#
# The mission config is BAKED IN, and the tag and label carry its hash, so the
# space image and the ground image can be checked for the same config before
# the link's own bind check (§6) rejects a mismatch at HELLO.

FROM python:3.13-slim

ARG SMO_CONFIG_HASH=unknown
ARG SMO_VERSION=dev

LABEL org.opencontainers.image.title="smo-suite" \
      org.opencontainers.image.description="SMO EO-Sat-1 mission simulator, ground segment and smo-link (one image, process chosen per service)" \
      org.opencontainers.image.version="${SMO_VERSION}" \
      org.opencontainers.image.licenses="see LICENSE" \
      ca.uottawa.smo.config="eosat1" \
      ca.uottawa.smo.config-hash="${SMO_CONFIG_HASH}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Non-root runtime user (fixed uid/gid so volume ownership is predictable).
RUN groupadd --system --gid 10001 smo \
 && useradd --system --uid 10001 --gid smo --home-dir /opt/smo \
            --no-create-home --shell /usr/sbin/nologin smo

WORKDIR /opt/smo

# Packages are installed editable from /opt/smo so the repo-relative layout
# the code relies on keeps working: static/vendor symlinks point at
# /opt/smo/vendor, tools/ sit next to configs/, and `workspace/` resolves
# against the working directory.
COPY vendor/ vendor/
COPY packages/smo-common/    packages/smo-common/
COPY packages/smo-simulator/ packages/smo-simulator/
COPY packages/smo-mcs/       packages/smo-mcs/
COPY packages/smo-planner/   packages/smo-planner/
COPY packages/smo-rfsim/     packages/smo-rfsim/
COPY packages/smo-link/      packages/smo-link/
# DEPRECATED (replaced by smo-link); installed only so nothing that still
# imports it breaks. Removal is a later pass.
COPY packages/smo-gateway/   packages/smo-gateway/

# Dependency order: smo-common first (everything depends on it), then the
# services, then smo-link (smo-common + aiohttp).
RUN pip install -e "packages/smo-common[reports]" \
 && pip install -e packages/smo-simulator \
                -e "packages/smo-mcs[voice]" \
                -e packages/smo-planner \
                -e packages/smo-rfsim \
 && pip install -e packages/smo-link \
 && pip install -e packages/smo-gateway \
 && python -c "import smo_common, smo_simulator, smo_mcs, smo_planner, smo_rfsim, smo_link"

COPY tools/ tools/
# The ADCS failure viewer (tools/adcs_sim_viewer.py) imports this physics module.
COPY ADCS_failure_sim/cubesat_adcs_sim.py ADCS_failure_sim/cubesat_adcs_sim.py
COPY configs/eosat1/ configs/eosat1/
COPY docker/config-hash.sh docker/config-hash.sh

# Course PDFs (smo_common/downloads.yaml): copy EXACTLY the listed files to
# /opt/smo/downloads/<repo-relative source>. The books live outside this
# context (C2O design/docs/pdf), so they arrive as the named context
# `course_pdfs`, bind-mounted for this one step: nothing unlisted (drafts,
# pre-cleanup builds, flyers) reaches a layer. sim/docs and configs PDFs come
# from the main context (.dockerignore re-includes docs/*.pdf). A listed file
# missing from either fails the build rather than shipping a hole.
# ~56 MB (textbooks are most of it).
RUN --mount=type=bind,from=course_pdfs,target=/tmp/c2o/design/docs/pdf \
    --mount=type=bind,target=/tmp/c2o/sim \
    python -m smo_common.downloads bundle --src /tmp/c2o --out /opt/smo/downloads

# Record the hash of the config actually baked in, and refuse to build an
# image whose tag/label would lie about it.
RUN actual="$(sh docker/config-hash.sh configs/eosat1)" \
 && echo "$actual" > /opt/smo/CONFIG_HASH \
 && if [ "$SMO_CONFIG_HASH" != "unknown" ] && [ "$SMO_CONFIG_HASH" != "$actual" ]; then \
        echo "ERROR: --build-arg SMO_CONFIG_HASH=$SMO_CONFIG_HASH but configs/eosat1 hashes to $actual" >&2; \
        exit 1; \
    fi

# Writable state lives in volumes (compose.yaml): workspace/ (breakpoints,
# config history, reports, link state), workspace/dumps (S15 dumps) and the
# MCS TM archive. Create them owned by the runtime user so a fresh named
# volume inherits that ownership. configs/ stays root-owned: the image's
# config is the hashed one.
# workspace/logbook: the participant logbooks (LOGBOOK_SPEC.md), setgid
# 2770 so SpaceCDF (another uid, smo group added) writes there too.
RUN mkdir -p /opt/smo/workspace/dumps /opt/smo/workspace/link /var/lib/smo/archive \
             /opt/smo/workspace/logbook \
 && chown -R smo:smo /opt/smo/workspace /var/lib/smo \
 && chmod 2770 /opt/smo/workspace/logbook

ENV SMO_CONFIG_DIR=/opt/smo/configs/eosat1 \
    SMO_DOWNLOADS_DIR=/opt/smo/downloads \
    SMO_DUMP_DIR=/opt/smo/workspace/dumps \
    SMO_LINK_STATE_DIR=/opt/smo/workspace/link \
    SMO_TM_ARCHIVE=/var/lib/smo/archive/tm_archive.db \
    SMO_UI=modern \
    SMO_VR=0 \
    SMO_CONFIG_HASH=${SMO_CONFIG_HASH}

USER smo

# No default service: compose.yaml sets the command for each one.
CMD ["python", "-c", "print('smo-suite image: choose a process, e.g. smo-simulator, smo-link-agent, smo-link-gateway, smo-mcs (see docker/compose.yaml)')"]
