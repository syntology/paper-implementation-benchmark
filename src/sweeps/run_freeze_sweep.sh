#!/opt/homebrew/bin/bash
# v1 freeze sweep launcher (FREEZE_RUN.md). The harness exits 4 on a Bedrock
# day cap -- a global stop, not a per-run failure -- and skips runs that
# already have meta.json, so the right response is to wait and re-enter, not
# to fail. Same pattern batch-cycles-drain uses. Exits 0 only when all 96
# runs have metas; every attempt is its own registered job (R6).
set -o pipefail   # not -u: .env has a literal $5 (see 753aa90e)
cd "$(dirname "$0")/../.."
set -a; source .env; set +a
# Region override AFTER .env (which pins us-east-1): the Sonnet day cap is per
# source region, measured 2026-09-03T00:35Z -- a full search-arm run completed
# in us-west-2 while us-east-1 capped on its first call. Same model, same
# cross-region profile; only the request origin moves.
export AWS_DEFAULT_REGION="${BEDROCK_REGION:-$AWS_DEFAULT_REGION}"
OUT=<BENCH>/runs_v14
TASKS=<BENCH>/tasks/tasks_freeze.json
WAIT_S=${WAIT_S:-1200}
attempt=0
while :; do
  attempt=$((attempt+1))
  n_done=$(ls "$OUT"/*/*/meta.json 2>/dev/null | wc -l | tr -d ' ')
  echo "$(date -u '+%FT%TZ') attempt $attempt: $n_done/96 metas present"
  if [ "$n_done" -ge 96 ]; then echo "sweep complete"; exit 0; fi
  ./joblog.sh "benchmark-v14-freeze-a$attempt" ./venv/bin/python3 \
    <BENCH>/agent_harness.py \
    --variant v14_freeze --tasks "$TASKS" --out "$OUT" --workers 2 \
    --intent "v1 freeze sweep (FREEZE_RUN.md): 4 arms x 24 tasks against serving@bc87485a; attempt $attempt, resumes past completed metas"
  rc=$?
  if [ "$rc" -eq 0 ]; then continue; fi
  if [ "$rc" -eq 4 ]; then
    echo "$(date -u '+%FT%TZ') day-capped; waiting ${WAIT_S}s"
    sleep "$WAIT_S"; continue
  fi
  echo "$(date -u '+%FT%TZ') harness exit $rc (not a cap); stopping"; exit "$rc"
done
