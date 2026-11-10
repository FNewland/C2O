#!/usr/bin/env bash
# Re-render course videos, EN and FR, with the cloned voice, then make the
# H5P packages Moodle-ready and publish them to sim/workspace/videos.
#
#   bash video/scripts/render_all.sh                 # all videos
#   bash video/scripts/render_all.sh sim             # simulator videos (V-OPS-*, V-PLN-*)
#   bash video/scripts/render_all.sh scdf            # SpaceCDF videos (V-SCDF-*)
#   bash video/scripts/render_all.sh design          # design lectures (V-DES-*)
#   bash video/scripts/render_all.sh concepts        # concept explainers (V-CON-*)
#   bash video/scripts/render_all.sh V-OPS-02 V-DES-05   # just these videos
#   bash video/scripts/render_all.sh sim V-DES-05    # groups and single videos can be mixed
#   bash video/scripts/render_all.sh list            # show the groups and video IDs, render nothing
#
# Options (set in front of the command):
#   FORCE=1    redo videos already marked done      e.g.  FORCE=1 bash video/scripts/render_all.sh sim
#   LANG_ONLY=en   one language only (en or fr)     e.g.  LANG_ONLY=en FORCE=1 bash video/scripts/render_all.sh sim
#   DRY=1      print what would be rendered, render nothing
#
# Safe to stop and restart: finished videos are skipped, and every narrated
# sentence is cached, so an interrupted video resumes where its narration stopped.
# A log is written to video/out/render_all.log.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
log=out/render_all.log

all_ids=($(ls storyboards/*.yaml | xargs -n1 basename | sed 's/\.yaml$//'))

ids_with_prefix() {  # every storyboard whose ID starts with one of the given prefixes
  local id p
  for id in "${all_ids[@]}"; do
    for p in "$@"; do [[ "$id" == "$p"* ]] && { echo "$id"; break; }; done
  done
}

show_list() {
  echo "Groups:"
  echo "  all       every video (${#all_ids[@]})"
  echo "  sim       simulator / mission control: $(ids_with_prefix V-OPS- V-PLN- | wc -l) videos"
  echo "  scdf      SpaceCDF: $(ids_with_prefix V-SCDF- | wc -l) videos"
  echo "  design    design lectures: $(ids_with_prefix V-DES- | wc -l) videos"
  echo "  concepts  concept explainers: $(ids_with_prefix V-CON- | wc -l) videos"
  echo
  echo "Videos:"
  local id title
  for id in "${all_ids[@]}"; do
    title=$(grep -m1 -A1 '^title' "storyboards/$id.yaml" | sed -n 's/^ *en: *"\{0,1\}\(.*\)"\{0,1\}$/\1/p' | sed 's/"$//')
    done_mark=""; [ -f "out/$(echo "$id" | tr 'A-Z' 'a-z')/.voice-done" ] && done_mark=" [done]"
    printf "  %-10s %s%s\n" "$id" "$title" "$done_mark"
  done
}

# Expand the arguments: group names, ID prefixes (e.g. V-OPS) or exact IDs.
ids=()
[ $# -gt 0 ] || set -- all
for arg in "$@"; do
  case "$(echo "$arg" | tr 'A-Z' 'a-z')" in
    list|ls|help|-h|--help) show_list; exit 0 ;;
    all)                     ids+=("${all_ids[@]}") ;;
    sim|simulator|ops)       ids+=($(ids_with_prefix V-OPS- V-PLN-)) ;;
    scdf|spacecdf)           ids+=($(ids_with_prefix V-SCDF-)) ;;
    des|design)              ids+=($(ids_with_prefix V-DES-)) ;;
    con|concepts)            ids+=($(ids_with_prefix V-CON-)) ;;
    *)
      up=$(echo "$arg" | tr 'a-z' 'A-Z')
      if [ -f "storyboards/$up.yaml" ]; then ids+=("$up")
      else
        found=($(ids_with_prefix "$up"))
        [ ${#found[@]} -gt 0 ] || { echo "unknown video or group: $arg   (bash video/scripts/render_all.sh list)"; exit 1; }
        ids+=("${found[@]}")
      fi ;;
  esac
done
# drop duplicates, keep order
ids=($(printf '%s\n' "${ids[@]}" | awk '!seen[$0]++'))

lang_args=()
case "${LANG_ONLY:-}" in
  "") ;;
  en|fr) lang_args=(--lang "$LANG_ONLY") ;;
  *) echo "LANG_ONLY must be en or fr"; exit 1 ;;
esac

echo "${#ids[@]} video(s): ${ids[*]}${LANG_ONLY:+   (language: $LANG_ONLY only)}"
[ -n "${DRY:-}" ] && exit 0

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
  if python3 -m c2ovideo narrate "$id" ${lang_args[@]+"${lang_args[@]}"} >>"$log" 2>&1 \
     && python3 -m c2ovideo build "$id" ${lang_args[@]+"${lang_args[@]}"} --publish >>"$log" 2>&1; then
    # a single-language run does not mark the video done, so the other language is still rendered later
    [ ${#lang_args[@]} -eq 0 ] && touch "$mark"
    echo "   ok"
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
