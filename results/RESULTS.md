# Results: graph-vs-search benchmark, run 1 (2026-08-31)

> **The graph arm's substrate is dated and has moved.** These numbers were
> measured 2026-09-10/11; a 141,896-edge CITES write landed mid-run, and
> `Method` has grown 63% since. See
> [`../GRAPH_STATE.md`](../GRAPH_STATE.md). Not re-tested.

> **v1 FREEZE (2026-09-03): see FREEZE_RUN.md.** Same 24 tasks re-run
> against serving@bc87485a on the 1,028-V3 catalog: syntology 21/24,
> both 21/24, search 11/24, none 13/24; 18/18 in-catalog fetch-and-pass
> in both graph arms; conditional 37/37 (66/66 cumulative). Run 1
> below is the baseline that comparison is paired against.

> **STRICT-REFEREE CORRECTION (2026-08-31, late — commit 8c7f7a0).**
> The referee audit (<INTERNAL>/22) found the sandbox stringifying
> numpy booleans, which every consumer read as passing. All four run
> sets were re-verified under the fixed, strict referee. Canonical
> corrected numbers: run 1 — none 13/24, search 14/24, syntology
> 13/24, both 14/24 (headline "no pass-rate separation" unchanged);
> v1.1 17/24; v1.2 17/24 (backfill complete); v1.3 18/20 (unchanged).
> Every conditional finding SURVIVES and sharpens: agents that fetched
> served code are now **29/29** on the corrected referee (11/11 run 1,
> 6/6 v1.2, 12/12 v1.3). Tables below are the original run-1 record;
> where they disagree with this block, this block wins.

96/96 runs completed (24 tasks × 4 arms, Sonnet 4.5 subjects, 1h48m,
$37.24 total — under the pre-registered $40 gate). Referee and analysis as
pre-registered; artifacts stamped; every number below re-derivable from
`results.json` / `analysis.json` / `runs/`.

**What this run is, per the scope amendment:** instrument validation, today's
baseline, and serving-ergonomics measurement at 361 served elements on
single-routine tasks. It is NOT a verdict on the edge-composability thesis —
the thesis directs the project; its proof event is real agents completing
real jobs. This document is navigation.

## Headline numbers

Pass rates (referee = full recorded `pass_both` property set, held out):

| arm | in_catalog | off_catalog | overall |
|---|---|---|---|
| none | 7/12 | 6/12 | 13/24 |
| search | 10/12 | 4/12 | 14/24 |
| syntology | 9/12 | 5/12 | 14/24 |
| both | 9/12 | 6/12 | 15/24 |

No paired comparison separates (all p ≥ 0.69, exact sign test). The
benchmark, at this scale and task shape, cannot distinguish
information-access conditions on pass rate — **as the user predicted
mid-flight, and for a measurable reason: the floor is too high.** The
`none` arm passes 13/24 from parametric knowledge alone (prediction #3
said 3–7; the task family has roughly half the headroom the design
assumed). This is the same lesson the federated-ditto E-rung taught:
a ceiling arm cannot discriminate on a saturated benchmark. The v2
(composition-shaped tasks) is the headroom fix, not more n.

Efficiency (median per run) — the thesis's operative metric:

| arm | in_catalog | off_catalog |
|---|---|---|
| none | $0.264 · 131s | $0.275 · 158s |
| search | $0.458 · 133s | $0.471 · 134s |
| syntology | **$0.162 · 68s** | $0.263 · 157s |
| both | $0.488 · 127s | $0.532 · 153s |

Where the catalog covers the task, the graph-only agent is ~2.9× cheaper
and ~2× faster than the search agent at equal-or-comparable pass rate.
That is the efficiency signal the thesis names, visible at n=361 only
inside the covered slice — which is exactly what "coverage is the
bottleneck, scale is the bet" predicts.

## The one mechanism that matters: discovery, not serving

Conditional on the agent fetching served code, serving was perfect:

- syntology arm, `get_reference_implementation` called: **11/11 passed**
  (includes GPTQ, where the V2-floor refusal correctly named the
  available level and the agent deliberately lowered `min_level` — the
  refusal ergonomics worked as designed).
- syntology arm, never called: 3/13 passed.
- `both` arm: **0/24 runs ever called `get_reference_implementation`.**
  With familiar search tools present, the flagship tool was invisible —
  11 search calls in the smoke exemplar, zero graph-code fetches across
  the whole arm.

All three in-catalog syntology failures share one fingerprint: the agent
browsed `list_reference_implementations`, got `total_matching: 0`,
concluded "not in catalog," and hand-rolled to the turn cap without
submitting. Root cause, verified in transcript: the browse tool does
**whole-string substring** matching. The agent queried
`"IS-MBPG momentum"`; the graph holds the method as `IS-MBPG*`; one
descriptive word appended to an exact method name produced a false
zero. A rational agent treats a catalog's zero as ground truth — so a
one-token query mismatch converts a guaranteed win into a 17-turn
failure.

**These two defects — cross-tool salience and brittle name matching —
are scale-independent.** They would cap the value of a 50k-element
corpus exactly as they cap 361. They are also cheap to fix (tokenized
AND-matching with ranking in the list/get resolvers; description-level
positioning for the code-lane tools) and cheap to re-test (re-run one
arm, ~$13).

## Pre-registered predictions, scored

1. syntology ≥10/12 in-catalog, beating search by ≥3 — **wrong** (9/12,
   net −1 vs search); miss caused by the discovery defect, not serving.
2. off-catalog syntology within ±2 of search; both ≥ each single arm —
   **right** (5 vs 4; both ≥ all arms overall and off-catalog).
3. none floor 3–7/24 — **wrong, floor 13/24**; headroom collapse is the
   binding design lesson for v2.
4. syntology in-catalog < 50% of search's cost — **right** ($0.162 vs
   $0.458 median).
5. Dominant graph-arm failure mode = name-resolution/discovery —
   **right, and sharper than predicted** (browse-zero false negative;
   0/24 adoption under tool competition).

## Decision rules, applied

- `both` > `search` by ≥3 discordant overall: **not met** (+4/−3). Per
  the amended rule, no CLAIMS row change beyond a today-baseline
  sub-claim; the postmortem above names the failed stages (headroom;
  discovery).
- `syntology` < `none` anywhere: **nominally triggered off-catalog
  (5 vs 6)**. Examined: the discordance is one solution with a
  network-touching import that fails in a clean sandbox
  (`off_2003.01794`, counted as fail — correctly, the module is not
  self-contained) plus no-submission runs where fallback exploration
  consumed the turn budget. No case of the graph serving *misleading
  content*; classification: turn-budget opportunity cost, watch in v2.
  Not ship-blocking on this evidence.

## Assumptions register (what this model inherits)

1. Referee = LLM-drafted, paper-derived property suites (stage-13
   `pass_both`, revalidated same-day in-sandbox). Paper-faithful within
   drafter quality; suspect tests excluded.
2. Single-routine reproduction as task shape — a proxy that does not
   exercise composition, the thesis's mechanism. v2 replaces it.
3. One subject model (Sonnet 4.5) stands in for "the bots"; adoption
   behavior may differ by agent framework and model.
4. In-catalog asymmetry: served code was verified against this
   referee's own suite at V3-grant time (fetch-and-submit passes by
   construction). Disclosed; it is the product mechanism.
5. Tasks sampled from the corpus's own distribution; "edge job"
   representativeness is not established by this sample, and some
   routines are standard-library-adjacent (hence the high floor).
6. 20-turn budget interacts with tool use (no-submission: none 2,
   search 8, syntology 7, both 5); tools carry an exploration
   opportunity cost at fixed budget.
7. Pricing = on-demand us-east-1 Sonnet 4.5, cache-adjusted; spend
   absorbed by credits.
8. **Arm purity leak, found post-hoc:** `run_python` limited CPU/memory
   but NOT network (system git and urllib were reachable), and subjects
   exploited it — one syntology-arm run successfully `git clone`d the
   method's public repo (`off_2403.05751`, which still failed), and
   network-ish code appears in ~12 transcripts across arms (list via
   `grep -rlE "urlopen|pip install|clone.*github" runs/*/*/transcript.json`).
   "syntology = graph-only" is therefore an approximation with a
   measured hole; the conditional finding (fetched-served-code ⇒ 11/11
   pass) is unaffected, the cross-arm pass deltas carry this caveat.
   v2 fix: network-off execution for subject self-tests.

## Decision-shaped summary (for the bet conversation)

- **Apparatus**: a pre-registered, provenance-stamped, re-runnable
  4-arm working-output benchmark now exists; full run costs ~$37 and
  ~2h; every number re-derivable from stamped artifacts.
- **Today's baseline**: no pass-rate separation at 361 elements on
  single-routine tasks (floor 54%); efficiency separation ~2.9×
  cost / ~2× time inside the covered slice.
- **What the bet buys** (under the model's assumptions): coverage
  moves tasks into the slice where the efficiency signal lives; the
  composition surface grows ~N^1.9 (pairs) / ~N^2.6 (3-chains) —
  fitted on 4 points, unproven beyond N≈900, and worth re-fitting
  continuously as the corpus grows because it is the thesis's
  load-bearing curve.
- **Falsifiers to watch** (what would say the bet is off): the scaling
  exponent collapsing toward ~N^1 as N grows; discovery fixes failing
  to move adoption (agents still not reaching for the tools when
  offered); v2 composition tasks showing no efficiency separation on a
  low-floor task family; no bot arrival through an instrumented,
  registry-listed funnel.
- **Proof event** remains exogenous: real agents completing real jobs.

## Proposed CLAIMS.md updates (not applied — docs are the other
session's lane today)

- Open-debt row "bot with Syntology vs bot with search engine": keep
  open; add sub-row — *"today-baseline measured 2026-08-31: no pass-rate
  separation at 361 elements (floor 13/24); syntology 2.9×/2×
  cost/time advantage in-catalog; discovery, not serving, is the
  binding defect (11/11 pass when fetched; 0/24 fetches under tool
  competition). Re-run: `agent_harness.py` + `verify_solutions.py` +
  `analyze.py`."*
- New measured row: *"An agent that fetches served V3 code passes the
  held-out referee 11/11; a browse-zero (whole-string match miss)
  precedes 3/3 in-catalog graph-arm failures."*

## v1.1 ablation outcome (same day — see ABLATION_V11.md)

Ran as pre-registered: **adoption 1/24 → words are insufficient;
structural rule fires.** Agents adopted the graph's paper tools at
near-parity with search (get_paper 23, get_code_for_paper 18 calls)
and still went to GitHub for code — the workflow prior "graph =
metadata, GitHub = code" overrides any description. Secondary,
suggestive-only: the bundle improved pass (18/24 vs 15/24, +3/−0
paired, p≈0.25), cost (−31%) and wall time (−35%) through some
mechanism other than the intended one.

## Next actions

1. ~~v1.1 description ablation~~ — done; decision above.
2. **Serving fix proposal, now structural** (needs owner sign-off;
   serving files under active edit today): (a) surface
   `verified_reference_implementations` inline in `get_code_for_paper`
   / `get_paper` responses — ride the 18/24-run path agents already
   take instead of training a new habit; (b) tokenized AND-match +
   ranking in the list/get resolvers (the browse-zero defect,
   independent of adoption); (c) MCP server-level `instructions` as
   the system-context lever.
3. **v2 at the ~50k trigger**: composition-shaped tasks, library
   one-liners excluded, efficiency primary / pass-rate gate,
   network-off `run_python`, same harness.
