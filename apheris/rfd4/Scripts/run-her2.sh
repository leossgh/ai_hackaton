#!/usr/bin/env bash
# Design HER2 CDRH3 variants, refold the best with Boltz-2 and score them, on a hackathon VM.
# Usage, from the folder holding Data/: bash Scripts/run-her2.sh <design|prepare|predict|score|all>
# Settings: N designs (4), TOPN refolded (2), IMG design image tag suffix, OUT folder (runs/her2).
set -euo pipefail

Q=quay.io/apheris/oslo-hackathon
RFD=$Q:apheris-rfd4-proteina-v0.3.0-${IMG:-her2-novel-2026-11-09}
BOLTZ=$Q:apheris-boltz-v1.3.0-boltz2
N=${N:-4}
TOPN=${TOPN:-2}
OUT=${OUT:-runs/her2}

run=(docker run --rm --gpus all --shm-size 16g --user "$(id -u):$(id -g)"
     -e HOME=/tmp -v /etc/passwd:/etc/passwd:ro -v "$PWD:/work" -w /work)

design() {
  rm -rf "$OUT/design"
  "${run[@]}" "$RFD" module-run design \
    --input Data/12-her2/her2_cdrh3.yaml --output "$OUT/design" \
    --num-replicates "$N" --seed 1 --recycle-strategy high/front_loaded
}

prepare() {
  rm -rf "$OUT/prepared"
  "${run[@]}" "$RFD" module-run refold-prepare \
    --input "$OUT/design" --output "$OUT/prepared" --top-n "$TOPN"
}

predict() {
  rm -rf "$OUT/boltz2"
  "${run[@]}" "$BOLTZ" python -m apheris_boltz.cli predict \
    --input "$OUT/prepared/holo/queries.json" --output "$OUT/boltz2" \
    --template-paths "$OUT/prepared/holo/template.cif" \
    --write-detailed-scores true --num-diffusion-samples 1 \
    --seeds 42 --query-failures skip
}

score() {
  rm -rf "$OUT/scored-boltz2"
  "${run[@]}" "$RFD" module-run refold-score \
    --input "$OUT/design" --output "$OUT/scored-boltz2" \
    --predictions "$OUT/boltz2" --model boltz2
  column -s, -t < "$OUT/scored-boltz2/refold_metrics.csv" | cut -c1-200
}

case "${1:-}" in
  design|prepare|predict|score) "$1" ;;
  all) design; prepare; predict; score ;;
  *) sed -n '2,4p' "$0"; exit 1 ;;
esac
