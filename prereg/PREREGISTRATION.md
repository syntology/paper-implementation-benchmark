# Pre-registration: graph-vs-search working-output benchmark

**Written 2026-08-31, before any subject run.** This measures the top row of
`CLAIMS.md`'s "Open debt" table: *"A bot using Syntology outperforms a bot with
a search engine — never tested; the falsifiable form is same tasks, two agents,
measure working output."* Everything below is fixed before the first subject
token is spent; deviations get logged in RESULTS.md as deviations.

## SCOPE AMENDMENT (2026-08-31, user, sweep mid-flight, pre-analysis)

The product thesis this benchmark serves is NOT "today, Syntology beats an
internet search." It is: **once ~50k composable verified code examples exist,
an MCP agent completes from-the-edge computing jobs (not in standard ML
libraries) more efficiently — edge-code composability is the thesis.** At
today's 361 served elements, with single-routine tasks, this run is therefore:

1. **instrument validation** — the harness, referee, and strata work;
2. **today's baseline** — the numbers the ~50k re-run gets compared against;
3. **serving-ergonomics measurement** — discovery/adoption defects transfer
   to any scale and are actionable on today's evidence.

It is NOT a verdict on the thesis, in either direction. Second refinement,
same day: the thesis is a direction-setting commitment (the scale build-out
consumes the credit runway past easy pivoting), and its actual proof event is
exogenous — real agents showing up and completing real jobs. No internal
benchmark settles it; the ~50k re-run is a dress rehearsal, whose design
shifts toward the thesis: composition-shaped tasks, standard-library
one-liners excluded, efficiency-to-working-output as the primary metric with
pass rate as the gate. Nothing else below is changed by this amendment (arms, tasks,
referee, metrics, decision rules as written) — except that the first decision
rule's phrase "the CLAIMS row is MEASURED" is downgraded to "the row gains a
measured TODAY-BASELINE sub-claim; the headline row stays open debt."

## Subjects

Claude Sonnet 4.5 via Bedrock (`us.anthropic.claude-sonnet-4-5-20250929-v1:0`),
through `bedrock_client.py` converse, agentic tool loop, temperature default,
max 20 assistant turns, per-run output cap 4,096 tokens/turn. One run per
task×arm (repeats only if the primary comparison lands within noise — see
decision rules).

## Arms (identical prompt, identical budgets; only tools differ)

| arm | tools |
|---|---|
| `none` | `run_python`, `submit_solution` |
| `search` | + `search_semantic_scholar`, `search_arxiv`, `get_arxiv_abstract`, `github_search_code`, `github_fetch_file` |
| `syntology` | + `syntology_list_reference_implementations`, `syntology_get_reference_implementation`, `syntology_get_code_for_method`, `syntology_get_paper`, `syntology_get_code_for_paper`, `syntology_compose` |
| `both` | `search` ∪ `syntology` |

The `syntology` tools replicate the live MCP serving path byte-for-byte where
possible (Cypher lifted from `main.py@0387438`, retrieval via
`query_engine.templates`), read-only Neo4j credentials, no auth layer (the
graph's usefulness is under test, not the token plumbing).

## Tasks

Single-routine implementation tasks. The subject receives: method name, origin
arXiv id, paper title, entry-point name, exact signature, and the FIRST
SENTENCE of the spec only. The full contract (shapes, tie-breaking, edge
cases) is deliberately withheld — deriving it is the work the tools exist for.

Two strata, sampled with `random.Random(20260831)`:

- `in_catalog` (n=12): methods served by the live graph at V3
  (`HAS_REFERENCE_IMPL`, `verification_level=3` with report) ∩ V3-granted in
  `batch_runs/v3_results.jsonl` ∩ local `property_tests.py` + `spec.json`
  present.
- `off_catalog` (n=12): V3-granted in `v3_results.jsonl` (referee proven
  satisfiable) but NOT served by the live graph at level ≥ 2 — the graph can
  offer at most fallback tiers (`repo_known` / `paper_only`) for these.

Referees are validated before use: the recorded impl must still pass its
`pass_both` property set in today's sandbox; tasks whose referees fail
revalidation are excluded and counted (R3 ledger in `tasks.json`).

## Referee (held out from all arms)

`run_sandboxed.run_check(solution.py, entry, property_tests.py)` — the same
paper-derived property suite and conservative rule the V3 stage uses. A run
**passes** iff every property in that task's recorded `pass_both` set passes.
`suspect_tests` (recorded drafter errors) are ignored. Subjects never see the
property tests; the graph's served `test_cases` (V1/V2 inputs) are visible to
`syntology`/`both` arms by design — that is the product, and it is disclosed
here; the referee is the property suite, not those cases.

Known asymmetry, disclosed: in-catalog served code was itself verified against
this property suite at V3-grant time, so a fetch-and-submit strategy passes by
construction. That IS the claim under test ("verified code on tap beats
re-derivation"); the `search` arm's route to the same artifact (paper → repo →
adapt) is exactly the route the product exists to replace. The off-catalog
stratum and the `none` floor keep this honest.

## Metrics

- **Primary:** working-output rate (referee pass) per arm × stratum.
- **Paired primary comparisons** (per-task, McNemar-style discordant counts):
  1. `both` vs `search` — the marginal-value claim (an agent that adds
     Syntology to its search).
  2. `syntology` vs `search` — the substitution claim (the row as written).
- **Secondary:** turns used, input+output tokens (converse usage), wall time,
  Syntology-tool invocation count (did the agent actually use the graph when
  offered), fallback-tier encounters off-catalog.

## Predictions (falsifiable, before any run)

1. `in_catalog`: `syntology` ≥ 10/12, beating `search` by ≥ 3 tasks.
   `search` lands 5–9/12 (repos exist for many; adaptation is the tax).
2. `off_catalog`: `syntology` within ±2 tasks of `search` (fallback tiers
   should not HURT); `both` ≥ each single arm in both strata.
3. `none` floor: 3–7/24 overall (some routines are guessable from the first
   sentence — this is the non-triviality discount, measured not assumed).
4. Token cost: `syntology` in-catalog uses < 50% of `search`'s tokens.
5. Failure mode I expect from the graph arm: name-resolution misses (agent
   asks for "GFlowNet trajectory selection", graph has the method under a
   different name) — if this dominates, the actionable defect is serving-side
   discovery, not coverage.

## Decision rules

- `both` > `search` by ≥ 3 discordant tasks overall → the CLAIMS row is
  MEASURED with this benchmark as its re-run command.
- `both` ≈ `search` (< 3) → the claim stays open debt; the postmortem must
  name which stage failed (discovery, serving ergonomics, coverage) before any
  re-run — per the E-rung feedback-loop rule, only predictable failures
  recalibrate.
- `syntology` < `none` anywhere → serving is actively misleading agents;
  that's a ship-blocking defect to file, not a benchmark artifact.
- Cost gate: if the 8-run smoke projects the 96-run sweep above $40 Bedrock,
  stop and ask with the projection (budget rule).

## Provenance

Task set, per-run records, and results are `provenance.write_json`-stamped
(R1) with exclusion ledgers (R3); the sweep registers via `joblog.sh` (R6);
this file plus `RESULTS.md` land in the commit that carries the run (R7).

## Planned arm for the scaled re-runs: LAG DITHERING (user decision, 2026-09-02)

The ~50k re-run named in the scope amendment above is to happen
iteratively, with these agents simulating real use as the catalog grows.
**When it does, injected tool latency becomes an arm of those runs.**

Motivation: `<INTERNAL>/27`'s relevance tier costs +1.2 s per trace for
+4.9 pp reach (`LATENCY.md`), and whether that reads to an agent as
acceptable, as "no response", or as lag that accumulates across a long
session is currently a guess. Production telemetry can answer it once
traffic exists (`PREREG_latency_tolerance.md`), but this harness can
answer a sharper version earlier and under our own task mix: **at what
delay does an agent stop calling the tool?**

Shape, so the design is waiting rather than invented later:

- Dither the delay across runs — 0 / 1 / 2 / 5 / 10 s injected into the
  syntology tool handlers only — rather than testing a single value, so
  the output is a **patience curve**, not a pass/fail on one guess.
- Primary metric is **substitution**, not pass rate: calls to the
  delayed tool as a share of all tool calls, versus the 0 s arm. Pass
  rate is a gate, since a slower tool that still gets used is fine.
- Secondary: turns to completion, wall time, cost, and no-submission
  rate, all of which this harness already records.
- Run it as part of a scaled sweep, never standalone: the incremental
  cost is small when the harness is already executing, and a curve
  measured on the current 361-element catalog with single-routine tasks
  would describe a task mix we are deliberately leaving behind.

**Explicitly not run now**, and the standalone $18–30 version is
withdrawn rather than pending.
