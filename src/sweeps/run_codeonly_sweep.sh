#!/opt/homebrew/bin/bash
# v1.5 code_only ablation sweep launcher (PREREGISTRATION_CODE_ONLY.md).
#
# Same shape as run_freeze_sweep.sh, and for the same reason: the harness
# exits 4 on a Bedrock day cap -- a global stop, not a per-run failure -- and
# skips runs that already have meta.json, so the right response is to wait
# and re-enter, not to fail. Exits 0 only when all 72 runs have metas; every
# attempt is its own registered job (R6).
#
# 3 arms x 24 tasks. `search` and `both` are deliberately NOT re-run: the
# budget goes to code_only vs syntology, which is the comparison that answers
# the owner's question. none + syntology are re-run in THIS execution rather
# than read off the freeze, so a control that moves is visible as variance.
set -o pipefail   # not -u: .env has a literal $5 (see 753aa90e)
cd "$(dirname "$0")/../.."
set -a; source .env; set +a
export AWS_DEFAULT_REGION="${BEDROCK_REGION:-$AWS_DEFAULT_REGION}"
OUT=<BENCH>/runs_v15
TASKS=<BENCH>/tasks/tasks_freeze.json
ARMS=${ARMS:-none,syntology,code_only}
EXPECT=${EXPECT:-72}
WAIT_S=${WAIT_S:-1200}
attempt=0
while :; do
  attempt=$((attempt+1))
  n_done=$(ls "$OUT"/*/*/meta.json 2>/dev/null | wc -l | tr -d ' ')
  echo "$(date -u '+%FT%TZ') attempt $attempt: $n_done/$EXPECT metas present"
  if [ "$n_done" -ge "$EXPECT" ]; then echo "sweep complete"; exit 0; fi
  ./joblog.sh "benchmark-v15-codeonly-a$attempt" ./venv/bin/python3 \
    <BENCH>/agent_harness.py \
    --variant v14_freeze --tasks "$TASKS" --out "$OUT" --workers 2 \
    --arms "$ARMS" \
    --intent "v1.5 code_only ablation (PREREGISTRATION_CODE_ONLY.md): is the graph load-bearing GIVEN the CodeSamples; 3 arms x 24 tasks, none+syntology re-run as in-execution controls; attempt $attempt, resumes past completed metas"
  rc=$?
  if [ "$rc" -eq 0 ]; then continue; fi
  if [ "$rc" -eq 4 ]; then
    echo "$(date -u '+%FT%TZ') day-capped; waiting ${WAIT_S}s"
    sleep "$WAIT_S"; continue
  fi
  echo "$(date -u '+%FT%TZ') harness exit $rc (not a cap); stopping"; exit "$rc"
done
