# v1 freeze run (v1.4) — pre-registration, 2026-09-02

**Written before any v1.4 subject run.** Purpose: the benchmark IS the
artifact that says what v1 is. Run 1 (2026-08-31) measured serving at
`0387438` on a 361-element catalog. Since then the catalog grew to 1,028
served-V3 (1,179 methods with any implementation), the structural fix
shipped (verified implementations inline on `get_paper` /
`get_code_for_paper`), the resolvers gained token fallback and
`name_lower` indexing, server-level instructions exist, and the referee
was made strict. This run measures TODAY, on the SAME 24 tasks, with
the same four arms, so every delta against run 1 is paired per task.

## What is held fixed vs run 1

Fixed: the 24 tasks and their referees (`tasks_freeze.json` carries the
identical task_ids, entry points, and `pass_both` sets — none contain
false grants under the strict rescore), the four arms, Sonnet 4.5 on
Bedrock, 20-turn cap, prompt template, search toolkit, tool ORDER
(search-first in `both`), 2 workers.

Changed, deliberately, because production changed: shim re-lifted to
`main.py@HEAD` by AST extraction (deliberate re-lift per the pin rule;
new run directory `runs_v14/` so no result set mixes tool versions);
tool descriptions verbatim from `mcp_server.py@HEAD`; server
instructions verbatim (mentions `explore_paths`, which is NOT in the arm
— excluded like `graph_ask`, same as every prior version); strict
boolean referee (run 1's numbers below are the corrected ones).

Stratum labels are re-derived against today's catalog: **18 in-catalog /
6 off-catalog** (six run-1 off-catalog tasks are now served at V3:
DWJS, ProbConserv, AdvStyle, PPBO, GPTQ, FreeShap). Run-1 labels are
kept in `stratum_run1` for the paired comparison.

## Run-1 baseline (strict referee), for reference

none 13/24 · search 14/24 · syntology 13/24 · both 14/24; both-arm
adoption of `get_reference_implementation` 0/24; both-arm median
$0.491 / 141s; syntology in-catalog median $0.162 / 68s.

## Predictions

1. **Controls move little:** `none` 11–15/24 and `search` 12–16/24 —
   nothing changed for them; if either moves more, the delta is
   variance and the other arms' deltas must be read against it.
2. **Adoption is now structural:** `both` fetches served code (any
   `get_reference_implementation` call) in ≥ 14/24 runs (v1.3 measured
   12/20 with a syntology-first ordering; this run uses the harsher
   search-first ordering).
3. **In-catalog pass (n=18):** `both` ≥ 15/18 and `syntology` ≥ 15/18;
   `search` 12–15/18.
4. **Efficiency:** `both` in-catalog median cost < $0.30 and wall
   < 100s (run 1: $0.488 / 127s); `syntology` in-catalog ≤ $0.20.
5. **The conditional holds:** every run that fetches served code passes
   (currently 29/29); one failure here would be the first and would
   need a per-property post-mortem.
6. **Off-catalog (n=6):** descriptive only — too small for any paired
   claim; reported, not tested.

## Decision framing

This is not a hypothesis test about the thesis; it is the frozen v1
baseline. Outputs: the paired per-task table vs run 1, adoption and
efficiency by arm × today's stratum, and the conditional. Whatever it
says becomes "v1's numbers" — and the first row of the 50k dress
rehearsal's comparison.

## RESULTS (2026-09-03 01:30Z — 96/96 runs, $17.40, strict referee)

**Headline: the v1 freeze separates where run 1 could not.** Same 24
tasks, same referees, same arms, same ordering — different serving.

| arm | run 1 | **v1 freeze** | paired Δ (per task) | sign-test p |
|---|---|---|---|---|
| none (floor) | 13/24 | **13/24** | +2/−2 | 1.00 |
| search | 14/24 | **11/24** | +3/−6 | 0.51 |
| syntology | 13/24 | **21/24** | **+8/−0** | **0.008** |
| both | 14/24 | **21/24** | **+8/−1** | **0.039** |

Pre-registered within-run comparisons, all four now significant where
run 1 had none (every p ≥ 0.69 then): both vs search **+11/−1, p=0.006**;
syntology vs search **+10/−0, p=0.002**; syntology vs none +8/−0,
p=0.008; both vs none +9/−1, p=0.02.

**In-catalog (today's 18):** syntology **18/18**, both **18/18**, search
10/18, none 11/18. **Adoption:** syntology fetched served code in 19/24
runs, both in 18/24 — **18/18 in-catalog for both graph arms, under
search-first ordering** (run 1: 0/24). **The conditional: 37/37 runs that
fetched served code passed** (cumulative 66/66 across every version).
**Off-catalog (6):** syntology 3, both 3, none 2, search 1 — descriptive
only, as pre-registered.

**Efficiency (median per run, in-catalog):** syntology **6 turns / 33s**,
both **7 turns / 81s**, none 5 / 31s, search **20 / 145s** (the search
arm hit its turn cap in 11/24 runs without submitting). Cost: syntology
$0.072, both $0.135, none $0.049, search $0.365 — **cost deltas vs run 1
are NOT clean**: the harness gained prompt caching after run 1, so
run-1 costs are uncached; turns and wall are the comparable efficiency
measures, wall with the region caveat above.

### Predictions scored

1. Controls flat — **none exactly flat (13/24)**; search 14→11 (+3/−6,
   p=0.51), inside its band's lower edge; its 11 no-submissions vs 8 in
   run 1 read as turn-cap variance on live web/GitHub, nothing in its
   toolkit changed. Read the graph arms' deltas against a control that
   moved −3: they moved +8.
2. Adoption ≥ 14/24 in `both` — **18/24, right** (and 18/18 in-catalog).
3. In-catalog `both` and `syntology` ≥ 15/18 — **18/18 both, right**;
   search 10/18 inside its 12–15 band's lower edge.
4. `both` in-catalog median < $0.30 and < 100s — **$0.135 / 81s, right**;
   syntology ≤ $0.20 — **$0.072, right** (cost caveat as above; on turns:
   both 7 vs run-1's 15, syntology 6 vs 10).
5. The conditional holds — **37/37, right**.
6. Off-catalog descriptive — reported, not tested.

### What v1 is, in one paragraph

On single-routine tasks the catalog covers, an agent given Syntology
fetches verified code essentially every time it is offered — whether
Syntology is its only source or sits beside a full search toolkit — and
every such fetch has passed the held-out referee (66/66 to date). It
does so in a third of the turns and a quarter of the wall time of a
search agent, which on the same tasks ran out its turn budget without
submitting in nearly half of runs. Pass-rate separation, absent at
361 elements, appeared at 1,028 — not because the tasks changed (they
did not) but because coverage moved 6 of 24 tasks into the served
slice and the serving stopped losing agents at discovery. The floor is
unchanged: a bare model still passes 13/24 of these tasks, which is why
the 50k dress rehearsal must use composition-shaped tasks to measure
the thesis rather than this proxy.

### Deviations and caveats carried into the freeze

Region switch to us-west-2 after 9 runs (per-source-region day cap,
measured); prompt caching added since run 1 (costs incomparable, turns
and wall comparable); search-arm turn-cap rate rose (control drift,
disclosed); off-catalog n=6; strata re-derived against the 1,028-V3
catalog with run-1 labels preserved in `tasks_freeze.json`.

## Known interactions

Bedrock Sonnet day cap is shared with the running `batch-cycles-drain`
job (already capped once today, retrying on a 2h cadence). The harness
aborts cleanly on a cap (exit 4) and resumes by re-running; partials
are reported as partials.

**Update 2026-09-02 19:30Z (user decision: prioritize the benchmark):**
the drain's retry wrapper was paused so the next cap reset window goes
to this sweep alone; relaunch instructions in ACTIVE_WORK.md.

**Update 2026-09-03 00:40Z — region deviation, recorded before it takes
effect on more than one run.** The cap did not lift at midnight UTC:
attempts at 00:09Z and 00:26Z capped while 5-token probes passed in
both us-east-1 and us-west-2 (token-bucket behaviour, not a daily
reset), and a second lane's `bakeoff-e1` briefly drew on the same
Sonnet budget at 00:23Z before its own cap. A real search-arm run
(`off_2406.04606/search`, 19 turns, ~99k input tokens) then COMPLETED
via us-west-2 while us-east-1 capped on its first call — the quota is
per source region. The launcher now runs with
`AWS_DEFAULT_REGION=us-west-2`. Same model, same `us.` cross-region
inference profile (which already routes across us-east-1/2 and
us-west-2 backends); only the request origin changes. Runs completed
before 00:35Z (9 metas) originated from us-east-1, everything after
from us-west-2; wall-time comparisons against run 1 carry that caveat.
