#!/opt/homebrew/bin/bash
# v1.6 substitution sweep launcher (PREREGISTRATION_SUBSTITUTION.md).
#
# Same shape as run_codeonly_sweep.sh, and for the same reason: the harness
# exits 4 on a Bedrock day cap -- a global stop, not a per-run failure -- and
# skips runs that already have meta.json, so the right response is to wait
# and re-enter, not to fail. Exits 0 only when every expected run has a meta;
# every attempt is its own registered job (R6).
#
# 3 arms (none, syntology_ho, code_only_ho). The two _ho arms REFUSE to run
# without a hold-out for their task -- an unheld arm under a hold-out name
# would silently be v1.5's ceiling arm landing in this run's table.
set -o pipefail   # not -u: .env has a literal $5 (see 753aa90e)
cd "$(dirname "$0")/../.."
set -a; source .env; set +a
export AWS_DEFAULT_REGION="${BEDROCK_REGION:-$AWS_DEFAULT_REGION}"
GW=<BENCH>
OUT=${OUT:-$GW/runs_v16}
TASKS=${TASKS:-$GW/tasks/tasks_substitution.json}
HOLDOUT=${HOLDOUT:-$GW/tasks/holdout_sets.json}
ARMS=${ARMS:-none,syntology_ho,code_only_ho}
EXPECT=${EXPECT:-216}
WAIT_S=${WAIT_S:-1200}
ONLY_ARG=()
[ -n "$ONLY" ] && ONLY_ARG=(--only "$ONLY")
attempt=0
while :; do
  attempt=$((attempt+1))
  n_done=$(ls "$OUT"/*/*/meta.json 2>/dev/null | wc -l | tr -d ' ')
  echo "$(date -u '+%FT%TZ') attempt $attempt: $n_done/$EXPECT metas present"
  if [ "$n_done" -ge "$EXPECT" ]; then echo "sweep complete"; exit 0; fi
  ./joblog.sh "benchmark-v16-substitution-a$attempt" ./venv/bin/python3 \
    $GW/agent_harness.py \
    --variant v14_freeze --tasks "$TASKS" --holdout "$HOLDOUT" \
    --out "$OUT" --workers 2 --arms "$ARMS" "${ONLY_ARG[@]}" \
    --intent "v1.6 substitution experiment (PREREGISTRATION_SUBSTITUTION.md): hold each task's own code out of BOTH arms and measure what each offers instead; tests proximity, which no version of this benchmark has ever tested; attempt $attempt, resumes past completed metas"
  rc=$?
  if [ "$rc" -eq 0 ]; then continue; fi
  if [ "$rc" -eq 4 ]; then
    echo "$(date -u '+%FT%TZ') day-capped; waiting ${WAIT_S}s"
    sleep "$WAIT_S"; continue
  fi
  echo "$(date -u '+%FT%TZ') harness exit $rc (not a cap); stopping"; exit "$rc"
done
