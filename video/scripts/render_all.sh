#!/usr/bin/env bash
# Re-render every course video, EN and FR, with the cloned voice, then make the
# H5P packages Moodle-ready and publish them to sim/workspace/videos.
#
#   bash video/scripts/render_all.sh                 # everything
#   bash video/scripts/render_all.sh V-OPS-02 V-DES-05   # just these
#   FORCE=1 bash video/scripts/render_all.sh         # redo videos already marked done
#
# Safe to stop and restart: finished videos are skipped, and every narrated
# sentence is cached, so an interrupted video resumes where its narration stopped.
# A log is written to video/out/render_all.log.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
log=out/render_all.log
ids=("$@")
[ ${#ids[@]} -gt 0 ] || ids=($(ls storyboards/*.yaml | xargs -n1 basename | sed 's/\.yaml$//'))

stack_of() {  # sim for the mission-control videos; SpaceCDF and explainers start themselves
  case "$1" in V-OPS-*|V-PLN-*) echo sim ;; *) echo auto ;; esac
}

python3 -m c2ovideo validate >/dev/null || { echo "storyboard validation failed: python3 -m c2ovideo validate"; exit 1; }

failed=()
sim_up=0
start=$(date +%s)
for id in "${ids[@]}"; do
  low=$(echo "$id" | tr 'A-Z' 'a-z')
  mark="out/$low/.voice-done"
  if [ -z "${FORCE:-}" ] && [ -f "$mark" ] && [ "$mark" -nt "storyboards/$id.yaml" ]; then
    echo "skip $id (done)"; continue
  fi
  if [ "$(stack_of "$id")" = sim ] && [ $sim_up = 0 ]; then
    python3 -m c2ovideo stack up sim >>"$log" 2>&1 && sim_up=1
  fi
  echo "== $id  $(date +%H:%M)" | tee -a "$log"
  # Narration first, on its own, so the voice model is not competing with the browser for memory.
  if python3 -m c2ovideo narrate "$id" >>"$log" 2>&1 \
     && python3 -m c2ovideo build "$id" --publish >>"$log" 2>&1; then
    touch "$mark"; echo "   ok"
  else
    failed+=("$id"); echo "   FAILED (see $log)"
  fi
done
[ $sim_up = 1 ] && python3 -m c2ovideo stack down sim >>"$log" 2>&1
python3 -m c2ovideo stack down spacecdf >>"$log" 2>&1 || true
python3 -m c2ovideo stack down viz >>"$log" 2>&1 || true

echo
echo "elapsed: $(( ($(date +%s) - start) / 60 )) min"
if [ ${#failed[@]} -gt 0 ]; then
  echo "failed: ${failed[*]}"
  echo "re-run with those IDs once fixed:  bash video/scripts/render_all.sh ${failed[*]}"
  exit 1
fi
echo "All rendered. Packages: video/out/<id>/<id>.{en,fr}.h5p"
echo "Optional check of the narration by speech recognition:  python3 -m c2ovideo check <ID>"
