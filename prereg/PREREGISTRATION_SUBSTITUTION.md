# Pre-registration: the substitution experiment (v1.6)

**Written 2026-09-10, before any v1.6 subject token is spent and before any
retrieval measurement under hold-out.** Deviations get logged in
`RESULTS_SUBSTITUTION.md` as deviations, in the same style
`RESULTS_CODE_ONLY.md` and `FREEZE_RUN.md` log theirs.

## The question, and why every previous run of this benchmark cannot answer it

The owner's *first* assumption about the graph, stated before any of the
others:

> "The graph will offer efficient proximity searching for agents when
> surfaced code is not exactly what's needed."

`syntology_compose` has been called **zero times in every version of this
benchmark ever run** — run 1, v1.1, v1.2, v1.3, the v1 freeze, and v1.5.
Proximity has never been tested, not once. The reason is structural, not an
oversight: all 24 tasks are single-routine reproductions where the exact code
exists in the corpus, both arms find it, and a neighbour is never needed.
v1.5 made that unavoidable — `code_only` and `syntology` tied 24/24, 18/18
in-catalog, +0/−0 paired, p = 1.00, not one discordant task — and its own
results doc named the successor experiment:

> "hold the correct sample out of both arms and ask each for its best
> alternative, then run the held-out referee on that alternative."

This is that experiment.

## The design in one paragraph

The task is unchanged: *implement routine X from paper P*. What changes is
that **X's own code is removed from the corpus, for both arms, before the
run starts.** Neither arm can retrieve the answer; each can only retrieve
something else. Whatever it retrieves instead **is** its best alternative —
we do not have to ask for one, because the situation asks for one. The
referee is the same held-out, paper-derived property suite the 24-task line
has always used, run unchanged on whatever the agent finally submits.

That framing is deliberate and it is the reading of "ask each for its best
alternative" this run commits to. The alternative reading — change the
prompt to "find me a substitute" — was rejected because it breaks prompt
parity with every previous run of this benchmark, and because it does not
model the real serve-time situation: an agent asking for code it needs does
not know the corpus lacks it.

## Arms

| arm | tools | hold-out | role |
|---|---|---|---|
| `none` | `run_python`, `submit_solution` | n/a | floor, re-run **in this execution** |
| `syntology_ho` | the 6 graph tools, `--variant v14_freeze` verbatim | **on** | arm under test |
| `code_only_ho` | `code_search`, `code_get` | **on** | arm under test |

Rosters, tool descriptions, server instructions, tool order, turn cap (20),
model (`us.anthropic.claude-sonnet-4-5-20250929-v1:0`) and worker count are
resolved through `ARM_BASE` from the v1.5 arms, so there is no second copy
of a roster or a system suffix that could drift. `search` and `both` are not
run; `search_arm_tools.py` has drifted since the freeze and arxiv.org 403s
us, so those numbers would be confounded by toolkit drift.

**The v1.5 runs are the no-hold-out condition.** `syntology` and `code_only`
scored 24/24 each on the 24 carried-forward tasks four hours ago, with the
same referee and the same task file. Re-running them would buy a manipulation
check that the mechanical exclusion verification below buys more cheaply and
more rigorously. `verify_holdout.py`'s parity check (P) is what licenses
this: it fails if either arm, with no hold-out installed, stops returning
what v1.5 measured.

**Server instruction text is kept byte-identical to v1.5** even though it now
slightly overstates the corpus under hold-out ("118,400 Python code samples",
"1,179 methods"). Changing it would measure the prompt instead of the
hold-out. Disclosed, not fixed.

## The hold-out rule

`build_holdout_sets.py`. Per task, the union of four rules; both arms enforce
**the same sha set**, which is the only thing that makes "unreachable to
both" a fact rather than an assertion:

| rule | removes |
|---|---|
| **H1** | every CodeSample with `paper_attribution` = the task's arXiv id |
| **H2** | every CodeSample reachable as `(:Method {the task's method})-[:HAS_REFERENCE_IMPL]->` |
| **H3** | every CodeSample reachable as `(:Paper {arxiv_id})-[:PROPOSES]->(:Method)-[:HAS_REFERENCE_IMPL]->` |
| **H4** | every CodeSample whose entry name normalises to the task's entry name |

H1 exists because holding out only the served sample would leave the paper's
own harvested repository files one query away, and an arm that retrieved one
of those found the answer, not a substitute. H4 exists because the prompt
hands the subject the exact entry function name (the referee calls it) and
the flat index pins exact entry matches above everything else — a same-named
sample from another paper is the answer arriving under a different sha. H4
is the one rule that can remove genuinely unrelated code, since 386 of 1,179
served entry names collide; it removes 4 extra samples across the 24 carried
tasks, which is a price worth paying for not arguing case by case.

Measured on the 72-task set: **372 shas held out, median 3 per task, range
1–26**, and the sample the graph serves is inside the hold-out for **72 of
72** tasks.

Everything else stays: other papers' code, other methods, near-duplicates of
the same routine written for a different paper. **Those are the substitutes**,
and the experiment is about whether either arm finds them.

### What the hold-out costs the graph arm, stated before the result

`compose` resolves its subject out of the same universe it draws partners
from, so a held-out subject is unresolvable and the graph's one dedicated
proximity tool cannot be invoked on the thing the agent actually needs. That
is a real handicap and it is not excepted away, because allowing the subject
through would return `verification_level`, `input_contract` and
`shape_contract` for the held-out artifact — telling the subject that a
verified implementation exists and is being withheld, which is a different
experiment and a leak a transcript would not obviously show.

Instead the cost is **measured, offline, for free**: `probe_substitution.py`
records what `compose` *would* have offered as neighbours of each held-out
subject. If those neighbours are good and the tool was inoperable, the
finding is that the graph's proximity tool keys on the artifact you do not
have — a serving-design defect, and a more useful result than a quietly
relaxed hold-out.

## Exclusion verification — how the hold-out is proven, not asserted

`verify_holdout.py`, run before the sweep, exit 1 on any finding. Six checks:

- **P — parity.** With no hold-out installed, the graph serves the same
  sample for every task and the flat index ranks the correct sha where
  `probe_code_only_retrieval.json` recorded it. The hold-out machinery is a
  no-op when off; this is what licenses reusing v1.5.
- **C — capability (the test of the test).** With the hold-out **off**, each
  task's adversarial query battery — entry name, method name, method + first
  sentence, signature — must actually *reach* the held-out sample in the top
  50, and the graph must actually serve it. An absence result from a query
  that could never have found it proves nothing.
- **F — flat exclusion.** With the hold-out **on**, no held-out sha appears
  anywhere in a `code_search` response for any battery query (ranked list,
  verified facet, or exact-entry pin), and `code_get` refuses every held-out
  sha **with the same error an unknown sha gets** — a distinct "held out"
  message would tell the subject an exact answer exists and is being
  withheld.
- **G — graph exclusion.** Checked on the code **text**, not on a sha,
  because the graph tools do not return shas: every held-out source is
  fetched once analysis-side and any tool response containing one verbatim is
  a leak. `get_reference_implementation`, `get_code_for_paper`,
  `list_reference_implementations` and `compose` are each exercised on the
  target.
- **T — thread cross-talk.** The harness runs `--workers 2` as threads in one
  process over module-global caches, so a hold-out that was not thread-local
  would apply task A's exclusions to task B's run and nothing about the
  numbers would look wrong. Two threads, two hold-outs, concurrent searches;
  each must see only its own — plus a positive control, because "no leak"
  from a query that returns nothing is not evidence.
- **X — index coverage.** Every held-out sha must be a row in the flat index,
  or "removed from the flat index" is a claim about rows that were never
  there.

Filtering happens **before ranking**, not after: removing rows from a finished
list would leave the excluded sample occupying a rank slot and hand the
subject a short page — an observable footprint of the hold-out.

**After the sweep**, every `*_ho` transcript is scanned for every held-out sha
and for every held-out source verbatim. Any hit invalidates that task and it
is reported as invalidated, not dropped.

## The referee, and its blindness

`verify_solutions.py`, unchanged, on `tasks_substitution.json`'s `pass_both`
sets. It is deterministic, local, strict-boolean, reads only
`runs/<task>/<arm>/solution.py`, and has no channel through which the arm
could reach it. The property suites were drafted in stage 13 from each
paper's own algorithm description, long before this experiment and by a
different process from either arm's answer. **No LLM judge is introduced.**

## Scoring — fixed before any output is looked at

The brief's requirement is that "best alternative" gets a scoring rule fixed
in advance, because a substitute is not pass/fail the way an exact
reproduction is. It is answered with two pre-committed measures, both
deterministic and both from the same blind referee:

1. **Primary — task success (binary).** Did the submitted module pass every
   property in the task's `pass_both` set. Chosen as primary because it is
   the only measure comparable to the entire 24-task line, and because a
   substitute that does not let the agent finish the job is not a substitute
   in any commercially meaningful sense. Paired, exact two-sided sign test on
   discordant pairs.
2. **Co-primary — property fraction (graded usability).** `(required −
   failed) / required` per run, with 0 for a non-submission or a referee
   crash. This is the usability measure, and it is deterministic rather than
   judged: an alternative that gets 4 of 5 paper-derived properties right is
   measurably more usable than one that gets 0, and the binary metric is
   blind to that difference. Paired **Wilcoxon signed-rank** over all n
   tasks. Pre-committed reasoning: this is where the statistical power lives,
   because it uses the pairs where both arms fail the binary and one is much
   closer than the other.

Secondary and descriptive, all mined from transcripts at zero extra spend:
**substitute adoption** (did the arm fetch any artifact at all), **substitute
provenance** (which paper the fetched artifact came from, and its distance
from the target), **turns / wall / cost / no-submission rate**, and the
**`syntology_compose` call count**, which has been zero forever and which
this condition exists to elicit.

## Power, stated up front

An exact two-sided sign test on D discordant pairs with k in the minority
reaches p < 0.05 only at these splits:

| D | 6 | 7 | 9 | 10 | 12 | 13 | 16 | 20 |
|---|---|---|---|---|---|---|---|---|
| max minority k | 0 | 0 | 1 | 1 | 2 | 2 | 3 | 5 |

so significance needs roughly `|2π − 1|·√D ≳ 1.96`, where π is the share of
discordant pairs favouring one arm. Translated:

| true π (share of discordant pairs favouring the graph) | discordant pairs needed |
|---|---|
| 0.90 | ≈ 7 |
| 0.80 | ≈ 11 |
| 0.70 | ≈ 25 |
| 0.65 | ≈ 43 |
| 0.60 | ≈ 96 |

At n = 72 with a plausible discordance rate of 20–30% we expect **D ≈ 14–22**,
which is powered for **π ≥ ~0.72** — a large asymmetry — and is **not**
powered for a modest edge. This is stated now so it cannot be discovered
afterwards: **if this run returns a tie on the binary metric, that is not
evidence of equivalence**, and the report will carry the rule-of-three bound
for whatever D it observes rather than the word "equivalent". The Wilcoxon
co-primary is the mitigation, not a fix.

The floor arm is what makes a tie interpretable at all: `none` establishes
how much of any score is the model's prior rather than either retrieval
surface.

## n, and the stopping rule — which depends on cost only

**Kill criteria — this section is them.** If you came looking for the phrase
and could not grep it, that was our fault and this paragraph is the fix. There
is exactly one pre-specified rule for when this benchmark stops, it is the
stopping rule below, and it reads **cost and nothing else**.

`tasks_substitution.json`: **72 tasks** — the 24 from `tasks_freeze.json`
(carried forward unedited, so they stay paired with v1.5's ceiling result)
plus **48 new** admitted by a stricter rule than the original builder's:
V3-granted in `v3_results.jsonl` **and** the recorded implementation still
passes its full `pass_both` set in today's sandbox **and** the graph serves a
report-backed level ≥ 2 sample for the method **and** the flat index holds a
sample carrying that paper's arXiv id and that entry name. Conditions 3 and 4
exist so the hold-out removes a would-be win from *both* arms; without them a
task could be measuring an arm that never had the answer. 53 candidates
screened, 48 admitted, 1 excluded for `graph_serves_below_v2` and 4 for
`referee_regressed`. All 72 are served at a **live backed V3** today.

**Primary n = 48** (the 24 carried + the first 24 new in the file's fixed,
seeded-shuffle order), 3 arms, 144 runs.

**Pre-committed extension:** if the 12-run smoke's measured per-run cost
projects the full 216-run matrix at **≤ $22**, the run extends to all 72
tasks. If the 144-run matrix itself projects above **$25**, the sweep stops
and the projection is reported instead of half-running the matrix.

**The stopping rule reads cost and nothing else.** The harness prints tokens,
turns and `submitted`; pass/fail exists only after `verify_solutions.py`,
which is not run until the sweep completes. So the choice of n is
structurally blind to outcomes, not merely promised to be.

Session ceiling: **$50 + a binding 10% slush**, with a standing instruction
to stop and report above **$25**. C3: **no Neo4j writes** at any point.

## Predictions (falsifiable, fixed before any run)

1. **Both hold-out arms land strictly between the floor and the ceiling** —
   in the 40–80% band. Falsified upward if either ≥ 90% (the hold-out did not
   bite; the model's prior is enough), falsified downward if either is within
   2 tasks of `none` (retrieval contributes nothing once the exact answer is
   gone).
2. **`code_only_ho` ≈ `syntology_ho`, |Δ| ≤ 5 tasks, sign test p > 0.05.** I
   expect a tie, and the mechanism matters more than the number: the graph's
   catalog is 1,179 methods and the flat index is 118,400 samples over the
   same corpus, so where a neighbour exists the flat index has strictly more
   of them to rank; the graph's advantage would have to come from *typed*
   adjacency, and its typed-adjacency tool cannot be invoked on a held-out
   subject.
3. **`syntology_compose` is called ≤ 2 times across all runs.** It has never
   been called. If this condition — the exact condition it was built for —
   still does not elicit it, that is a finding about the tool, not about
   proximity.
4. **Both hold-out arms beat `none` by ≥ 5 tasks.** Retrieving *something*
   relevant should still help even when it is not the answer. If this fails,
   the corpus is only useful when it holds the exact answer, and that is the
   sharpest possible verdict on the forward-deploy thesis.
5. **Adoption stays high: ≥ 80% of hold-out runs still fetch an artifact.**
   v1.5 was 24/24 in both arms. An arm whose adoption collapses under
   hold-out is telling us its results look empty *to the agent*.
6. **Failure mode I expect:** the arm surfaces a plausible neighbour, the
   agent adapts it, and the result fails the paper-specific properties while
   passing the generic ones. So the **graded metric separates the arms more
   than the binary does**, and mean property fraction lands well above the
   binary pass rate in both arms.
7. **Offline probe, under hold-out:** the flat index returns a non-empty
   ranked list for ≥ 95% of tasks (it ranks the whole corpus, so it always
   has something to say); `get_reference_implementation` on the target method
   falls back rather than serving in **100%** of tasks; and
   `list_reference_implementations(method)` reports `total_matching: 0` for
   the majority, with `near_matches` present.

## Decision rules (what each outcome means, fixed now)

- **|Δ| ≤ 2 tasks, sign test p > 0.2, Wilcoxon p > 0.2** → **the
  neighbourhood does not find substitutes the flat index cannot.** Reported
  in those words, with the rule-of-three bound attached and without the word
  "equivalent".
- **`syntology_ho` > `code_only_ho`, significant** → proximity pays. Name the
  discordant tasks individually and the mechanism that supplied the
  substitute on each.
- **`code_only_ho` > `syntology_ho`, significant** → the flat corpus's
  neighbourhood beats the curated catalog's; the finding is about the serving
  path's reach (1,179 vs 118,400), not about the ontology.
- **Both ≈ `none`** → neither retrieval surface substitutes. The corpus is
  load-bearing only when it holds the exact answer, and the forward-deploy
  thesis does not survive this task family.
- **Both ≥ 90%** → the hold-out did not bite; the model's prior is enough and
  this task family cannot test proximity at all. Report and say what would.
- **Ceiling or floor for both arms** → the run answered nothing about ranking
  the arms. Say so plainly, and name the task construction that would
  separate them, rather than shipping a second p = 1.00.
- **Efficiency override:** any pass-rate conclusion is qualified by turns.
  Parity at 2× the turns is not parity.

## Disclosed asymmetries and limits

1. **The corpus is a product of the graph** (carried from v1.5). This tests
   query-time behaviour, not whether the graph could be deleted.
2. **The flat arm still reads Neo4j** for `code_get`'s single-node lookup.
   The finding is about structure — node types and edges — not about the
   storage engine.
3. **The hold-out is bigger than "the one right sample"** (372 shas over 72
   tasks). It has to be, and H1's harvested-repo removal is why. Both arms
   lose exactly the same rows.
4. **`compose` is inoperable on a held-out subject** — see above; measured
   offline instead of excepted.
5. **One run per task × arm, one subject model, one task shape.** Everything
   `RESULTS.md`'s assumptions register says still applies.
6. **A tie here is a tie in the middle of the range, not at a ceiling** — a
   strictly more informative tie than v1.5's, and still not equivalence.

## Provenance

New run directory `runs_v16/`. `tasks_substitution.json`,
`holdout_sets.json`, `holdout_verification.json` and the probe output all
carry provenance stamps naming their inputs and hashes (R1). Index builds are
unchanged and already registered (R6); the sweep runs under `joblog.sh`. This
file, the verification, the probe and `RESULTS_SUBSTITUTION.md` land in the
commits that carry the run (R7). `qc_code_only_arm.py` passes clean with the
hold-out machinery in place — the arm still contains no relationship pattern,
no `:Method` and no `:Paper`. **No Neo4j writes at any point (C3).**
