#!/bin/sh
# Print a short, stable hash of a mission config tree (default configs/eosat1)
# for the image tag / label (docker/Dockerfile, docker/compose.yaml).
#
#   SMO_CONFIG_HASH=$(docker/config-hash.sh) docker compose -f docker/compose.yaml --profile ground build
#
# Whole-tree content hash (relative path + sha256 of every file, sorted in
# the C locale), ignoring OS/editor litter that .dockerignore also drops. It
# identifies the image; the link's own strict bind-set check (smo_link
# confighash, LINK_DESIGN §6) is still what accepts or rejects an agent.
set -eu
dir="${1:-configs/eosat1}"
cd "$dir"
find . -type f ! -name '.DS_Store' ! -name '._*' ! -name '*.pyc' \
       ! -path '*/__pycache__/*' -print \
  | LC_ALL=C sort \
  | while IFS= read -r f; do
        printf '%s  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$f"
    done \
  | sha256sum | cut -c1-12
