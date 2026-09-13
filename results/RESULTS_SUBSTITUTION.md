# RESULTS — the substitution experiment (v1.6), 2026-09-11

Pre-registered in `PREREGISTRATION_SUBSTITUTION.md`, committed at `8505db391`
**before any subject token was spent**. 146 runs, **$15.81**, zero throttles,
zero day caps. Referee, hold-out and task file unchanged from the
pre-registration.

## The headline, in the words the brief asked for

**No. The neighbourhood does not find substitutes the flat index cannot.**

And the run says something sharper than that, which was not the question but
is the more important answer:

**Neither arm beats having no tools at all, once the exact answer is gone.**

| arm (pre-registered n=48) | passed | mean property fraction |
|---|---|---|
| `none` (no information tools) | **24/48** (50.0%) | 0.641 |
| `syntology_ho` (graph, answer held out) | **24/48** (50.0%) | 0.678 |
| `code_only_ho` (flat index, answer held out) | **23/48** (47.9%) | 0.663 |

| paired comparison | discordant | sign test | Δ pass rate, 95% CI | Wilcoxon on property fraction |
|---|---|---|---|---|
| **`syntology_ho` vs `code_only_ho`** | **+6 / −5** | **p = 1.00** | **+2.1%, [−11.5%, +15.6%]** | p = 0.89 |
| `syntology_ho` vs `none` | +3 / −3 | p = 1.00 | 0.0%, [−10.0%, +10.0%] | p = 0.46 |
| `code_only_ho` vs `none` | +4 / −5 | p = 1.00 | −2.1%, [−14.3%, +10.2%] | p = 0.76 |

The pre-registered decision rule for |Δ| ≤ 2 tasks with both p > 0.2 says to
report it in those words, with the interval attached and without the word
"equivalent". Δ is **1 task in 48**. Both p are 1.00. Wilcoxon, the
co-primary that exists precisely to catch a difference the binary metric
would miss, is p = 0.89.

The eleven discordant tasks, named so the split can be audited rather than
taken on the count:

- **graph wins (6):** `off_2209.02257` · `sub_2010.02089` · `sub_2210.05922` ·
  `off_2311.15100` · `in__2505.24844` · `sub_2006.05849`
- **flat wins (5):** `in__2009.14794` · `off_2101.08543` · `off_2402.05367` ·
  `off_2006.06051` · `sub_2202.08836`

Note what the arms' *own* discordances against `none` say: 3 of the graph's
6 wins over the flat index (`sub_2010.02089`, `sub_2210.05922`,
`off_2311.15100`) are tasks where the **flat arm lost to no-tools**, not
tasks where the graph gained anything. The graph's genuine gains over
no-tools are three tasks (`off_2209.02257`, `in__2505.24844`,
`off_2210.17323`) against three genuine losses.

## The mechanism, which is where this run actually earns its money

A tie between two arms is easy to dismiss as "neither arm tried." That is not
what happened. Mined from all 96 hold-out transcripts:

| | `syntology_ho` | `code_only_ho` |
|---|---|---|
| runs that received **actual source** for something | **2 / 48** | **48 / 48** |
| distinct substitute papers the source came from | 4 | **143** |
| runs whose submitted solution shares ≥ 0.5 of the substitute's identifiers | 1 | **28 / 48** |
| median identifier overlap, fetched → submitted | 0.48 | **0.56** (max 0.90) |
| arm-tool calls | 168 | 369 |
| `syntology_compose` calls | **0** | — |
| held-out origin appearing in any fetched record | **0** | **0** |

Read the `code_only_ho` column again. **The flat index found a substitute in
every single run, from 143 different papers, and the agent visibly built on
it in 28 of 48 — and the pass rate was 23/48 against a no-tools floor of
24/48.** The substitute was surfaced, fetched, and used. It bought nothing.

The graph arm's column is a different failure and worth naming separately:
with its own method held out, the graph **had almost nothing to hand over**.
It made 66 `list_reference_implementations` calls, 50 `get_paper`, 48
`get_code_for_paper` — and only **4** `get_reference_implementation` calls in
48 runs, because the browse step had already told it the catalog does not
hold the method. It looked, found nothing, and fell back on the model's own
knowledge at a median of 3 arm-tool calls and 7 turns. That is honest
behaviour by the serving surface; it is also a surface with no answer to give.

Efficiency, median per run, primary 48:

| arm | turns | wall | cost | no-submission | total |
|---|---|---|---|---|---|
| `none` | 5 | 30.1 s | $0.046 | 0/48 | $2.31 |
| `syntology_ho` | 7 | 51.1 s | $0.085 | 0/48 | $4.43 |
| `code_only_ho` | **10** | 57.3 s | **$0.179** | 1/48 | $8.85 |

`code_only_ho` spent **3.9× the money and 2× the turns of `none`** to arrive
one task behind it.

## The exclusion — how the hold-out was proven, and what it cost

`verify_holdout.py`, run on all 72 tasks before a single subject token of the
main sweep, **0 findings**. What it established, mechanically:

- **372 of 372 held-out shas exist as rows in the flat index**, so removing
  them removes something real.
- **372 of 372 refused by `code_get`**, with the same error an unknown sha
  gets. `code_get` by the task's **entry name** refused in **72/72**.
- **Capability (the test of the test): with the hold-out OFF**, the
  adversarial battery reached the held-out sample in the top 50 — entry name
  **72/72**, method + first sentence **72/72**, signature **72/72**, bare
  method name 42/72 — and the graph served it in **72/72**. So the absence
  results below are not vacuous.
- **With the hold-out ON:** `list_reference_implementations` listed the target
  method in **0/72**; `get_code_for_paper` advertised a verified
  implementation in **0/72**; `get_reference_implementation` fell back in
  67/72 and in the other 5 served a **different** method reached through its
  `CONTAINS` branch — a substitute, not a leak, and checked as such on the
  code text.
- **Thread cross-talk: clean.** Two threads, two hold-outs, concurrent
  searches, no bleed — and the positive control confirms the probe query does
  reach its own sample when unheld.
- **Post-sweep audit:** every one of the 96 hold-out transcripts scanned for
  every held-out sha and for every held-out source verbatim. **0 leaks, 0
  tasks invalidated.** The 143 substitute origins the flat arm fetched include
  **zero** held-out papers.

**Two pre-run deviations, both corrections to my own checks, recorded rather
than quietly fixed:**

1. The first verification run reported **[G] compose resolved the held-out
   entry** on 3 tasks. It had not. `compose`'s third resolution tier is a
   substring match, so with the exact subject removed it lands on a different
   routine from a different paper — `ppo_clip_objective` →
   `ppo_clip_objective_gradient_step` (2110.02544), `ddim_step` →
   `ddim_step_with_cfg` (2403.14148), `binary_cross_entropy_loss` →
   `ted_binary_cross_entropy_loss` (2207.05480). That is the proximity
   behaviour the experiment exists to measure, not a breach. The check now
   tests the resolved `(entry, origin)` pair against the hold-out by sha.
   **This also falsifies the pre-registration's own claim that the hold-out
   makes `compose` inoperable** — it stays invocable on 3 of 72 tasks. Left
   as written, scored as written.
2. **[P] parity** fired on `off_2306.12360` for comparing the rank of "the
   first held-out sha" against the probe's record for the *correct* sha. The
   hold-out is wider than the probe's target (H4 removes same-named samples
   from other papers), so a different held-out row legitimately outranked it.
   The check now compares the probe's own target. Both corrections were made,
   the verification re-run end to end, and it came back **0 findings**.

## The offline probe — what each arm HAD to offer, independent of the agent

`probe_substitution.py`, all 72 tasks, zero subject spend. This separates a
corpus fact from a behavioural one: if both arms score badly it matters
whether neither surface held a substitute, or the agents did not use the one
that was there.

**The flat index always had something, and usually something verified.**

| under hold-out, 72 tasks | |
|---|---|
| non-empty ranked list for method + first sentence | **72 / 72** |
| rank-1 substitute at a **backed level 3** | **42 / 72** |
| rank-1 substitute at backed level 2 | 10 / 72 |
| rank-1 substitute at level 0 (harvested) | 20 / 72 |

So in **52 of 72** tasks the flat index's single best substitute was
machine-verified code. Behaviour matched: the agents fetched one in 48/48 and
built on it in 28/48. It did not move the referee.

**The graph's "best available" is mostly a URL it cannot open.**

| `get_reference_implementation(method)` under hold-out | |
|---|---|
| `fallback: repo_known` (a GitHub link) | **56 / 72** |
| `fallback: paper_only` | 11 / 72 |
| served a *different* method via the `CONTAINS` branch | 5 / 72 |
| raised | 0 / 72 |
| `list_reference_implementations(method)` reporting `total_matching: 0` | **66 / 72** (near matches offered on 42) |

The `syntology` arm has **no web tools** — that is the arm's definition — so
`repo_known`, its most common degradation, is a dead end by construction. The
graph degraded honestly and had nothing actionable to degrade *to*.

**The `compose` counterfactual: what the graph would have offered if the
hold-out had not made its subject unresolvable.** Run with the hold-out OFF,
so this is the tool at full strength:

| | |
|---|---|
| subjects `compose` resolves | **72 / 72** |
| **median typed partners** | **0** (zero on 59 / 72; mean 12.6, a long tail) |
| median adapter partners | 0 (zero on 52 / 72) |
| `effectively_terminal` | 46 / 72 |
| tasks where the flat index's top substitutes appear among `compose`'s partners | **1 / 72** |

Two things follow, and the second is the one that matters.

1. Even at full strength the typed-adjacency affordance is thin for these
   subjects: zero typed partners on 59 of 72, and effectively terminal on 46.
2. **`compose` answers a different question from the one the hold-out asks.**
   It returns what fits *with* a routine — downstream consumers of its output
   — not what could stand *in place of* it. The 1/72 overlap is not a failure
   of compose; it is evidence that the two notions of "nearby" are simply
   different. **The serving surface has no substitution affordance at all.**
   Proximity was specified as *composition* and built as composition, and the
   owner's sentence — "when surfaced code is not exactly what's needed" — is
   about *substitution*. That gap is a design finding, and it explains
   `syntology_compose`'s zero calls better than any story about tool
   descriptions: the agents were right not to call it.

## Power, stated the way it was promised

The pre-registration said n = 72 at a 20–30% discordance rate would give
D ≈ 14–22 and be powered only for π ≥ ~0.72.

**The design produced exactly the discordance it predicted, and the split was
even.** Observed on the primary comparison: **D = 11 of 48 (22.9%)**, split
**6 / 5**. A two-sided exact sign test needs **9 of 11 in one direction** for
p < 0.05. We got 6.

So the honest bound is not rule-of-three (that applies at D = 0); it is the
interval on the paired difference: **the graph's per-task advantage over the
flat index under hold-out is between −11.5% and +15.6%, point estimate
+2.1%.** That excludes a large effect. It does not prove zero. **This is not
evidence of equivalence** — it is evidence that any advantage is small, on
tasks of this shape.

What would have been needed: at the observed discordance rate, detecting
π = 0.7 needs **D ≈ 25 → n ≈ 110 tasks**; π = 0.65 needs **D ≈ 43 → n ≈ 190**.
At this run's measured $0.33 per task-pair that is **$36 and $63** of subject
spend respectively — affordable, and I did not spend it, because the
three-way result below makes a bigger n answer a smaller question.

**Why n was 48 and not the 72 that were built.** The pre-registered extension
rule was cost-only and blinded to outcomes: extend to 72 if the 12-run smoke
projected the 216-run matrix at ≤ $22. The smoke measured $0.2999 per
task-pair, which projects **$24.83** for 72 — above the gate. So n stayed at
the pre-registered 48 and the run came in at **$15.81**. The extra 24 tasks
were built, hold-out-verified and are sitting in `tasks_substitution.json`;
the incremental cost of running them is about **$8.30**.

## Predictions scored

| # | prediction | outcome |
|---|---|---|
| 1 | both hold-out arms land in the 40–80% band, not at ceiling or floor | **right** — 50.0% and 47.9%, against a v1.5 ceiling of 100% |
| 2 | `code_only_ho` ≈ `syntology_ho`, \|Δ\| ≤ 5, p > 0.05 | **right** — Δ = 1 task, p = 1.00 |
| 3 | `syntology_compose` called ≤ 2 times | **right, and at the floor** — **0** calls, in the one condition built to elicit it |
| 4 | both hold-out arms beat `none` by ≥ 5 tasks | **WRONG, and this is the run's real finding** — 0 and −1 |
| 5 | adoption ≥ 80% of hold-out runs fetch an artifact | **split** — `code_only_ho` 48/48; `syntology_ho` **2/48** |
| 6 | graded metric separates the arms more than the binary | **wrong** — Wilcoxon p = 0.89 vs sign p = 1.00; it separated nothing either |
| 7 | flat non-empty ≥ 95%; graph falls back 100%; list reports 0 for the majority | **mostly right** — flat non-empty 72/72 (median 55 results returned); graph fell back 67/72, served a different method 5/72; list reported 0 for the target in 72/72 |

Being wrong on **4** is the point of the run, and being wrong on **6** kills
the mitigation I had built for the power problem: I added the graded metric
because I expected partial credit to reveal a difference the binary hid.
There was no difference to reveal.

## What this changes

**It closes the owner's first assumption, on this task family.** *"The graph
will offer efficient proximity searching for agents when surfaced code is not
exactly what's needed."* Tested for the first time, with the exact code
removed from both arms under a mechanically verified hold-out: the graph's
neighbourhood was **not better than a flat index's**, and neither
neighbourhood was **better than nothing**. `syntology_compose`, the one tool
built for this exact situation, was called **zero times** — in the condition
designed to elicit it, by an agent that had already been told the catalog
does not hold what it needs.

**The forward-deploy thesis does not survive this task family.** "Surface a
newer same-slot alternative beside what was asked for" was executed
perfectly by the flat arm — 143 distinct alternatives, fetched in 48 of 48
runs, adapted in 28 — and it moved the outcome by −1 task.

**Three things this does NOT license.**

1. **It is a middle-of-the-range tie, not equivalence.** ±13% on the arm
   comparison. A real 10% edge would have been invisible here.
2. **It is about *this* substitution task.** "Implement routine X when X's
   code is gone" is a hard substitution problem: the referee is X's own
   paper-derived property suite, so a neighbour has to be adapted into X
   exactly. A task where the *user's* requirement is loose — "give me
   something that does this job" — is a different question, and this run does
   not answer it. **That is now the honest next question**, and it needs a
   different referee, because a deterministic X-specific property suite
   cannot score "close enough."
3. **It says nothing about identity, provenance or attribution**, which is
   where v1.5 already put the graph's remaining justification.

**What would separate the arms, since this did not.** Not more tasks of this
shape — the arms are neither at ceiling nor floor here, they are simply
equal, and n ≈ 110–190 would only tighten an interval that is already
centred on zero. Two constructions could, and the probe says which is which:

1. **A task whose answer is a composition** — two routines that must be wired
   together, one served and one not — because that is the only shape in which
   a typed adjacency edge is the thing being asked for. Every task in this
   benchmark is a single routine, and `compose`'s 0 calls across six
   benchmark versions is the consequence, not the cause. The probe tempers
   even this: median typed partners is **0**, so the affordance would have to
   be thickened before it could be tested.
2. **A substitution tool that actually exists.** The probe's sharpest finding
   is that the serving surface has **no** substitution affordance — `compose`
   answers "what fits with this", never "what could stand in for this". Any
   future test of proximity has to build that tool first, or it is testing
   the absence of a feature rather than the value of the graph.

## Deviations and caveats carried

- **n = 48 of a 72-task set**, by the pre-registered cost rule. The `none`
  floor is re-run **in this execution** (24/48), not read off v1.5.
- **Two extra `*_ho` runs** exist on `sub_2304.03274`, a smoke task outside
  the primary 48. They are in `runs_v16/` and in the 49-task table that
  `analysis_substitution.json` reports; they are **not** in the primary 48
  above. Including them moves `syntology_ho` to 25/49 and `code_only_ho` to
  24/49 and changes no comparison.
- **v1.5 is the no-hold-out condition**, not re-run. Licensed by the
  verification's parity check, which fails if either arm stops returning what
  v1.5 measured with no hold-out installed.
- **Server instruction text kept byte-identical to v1.5** even though it now
  slightly overstates the corpus under hold-out. Changing it would have
  measured the prompt.
- **The hold-out is wider than "the one right sample"** — 372 shas over 72
  tasks, median 3, because H1 removes the origin paper's harvested repository
  files too. Both arms lose exactly the same rows.
- **One subject model, one run per task × arm, one task shape.** Everything
  `RESULTS.md`'s assumptions register says still applies.
- Analyzer defects found and fixed **before** the primary analysis, on the
  partial dry run: a paired Wilcoxon that defaulted a missing arm's run to
  0.0 (it inverted a +0.28 lead into a −0.30 deficit), and an adoption
  counter that scanned raw transcript text for `"origin_arxiv_id": "` — which
  is escaped inside the stored JSON, so it read the graph arm's adoption as
  0/6 and then, once parsed, as 6/6 by counting pointer-shaped records with
  no source attached. Adoption is now counted only when a record actually
  carries code.
