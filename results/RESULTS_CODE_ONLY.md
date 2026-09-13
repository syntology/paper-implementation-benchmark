# RESULTS — the `code_only` ablation (v1.5), 2026-09-10

Pre-registered in `PREREGISTRATION_CODE_ONLY.md` (written before any subject
token, with a pre-run deviation recorded at 20:00Z). 72/72 runs, 20 minutes,
**$5.43**, zero throttles, zero day caps. Referee, tasks and `pass_both` sets
identical to the v1 freeze.

## The headline, stated plainly

**`code_only` and `syntology` passed the same 24 tasks. All of them. There is
not one task where the graph arm succeeded and the flat index failed, or the
reverse.**

| arm | in-catalog (18) | off-catalog (6) | overall |
|---|---|---|---|
| `none` (floor) | 8/18 | 2/6 | **10/24** |
| `syntology` | 18/18 | 6/6 | **24/24** |
| **`code_only`** | **18/18** | **6/6** | **24/24** |

| paired comparison | discordant | exact sign test |
|---|---|---|
| **`code_only` vs `syntology`** | **+0 / −0** | **p = 1.00** |
| `code_only` vs `none` | +14 / −0 | p = 0.0001 |
| `syntology` vs `none` | +14 / −0 | p = 0.0001 |

Efficiency, median per run — the freeze's sharpest measure, and it separates
these two arms no better than pass rate does:

| arm | turns | wall | cost | arm-tool calls | input tokens | no-submission |
|---|---|---|---|---|---|---|
| `none` | 5 | 28.4 s | $0.045 | 0 | 11,052 | 0/24 |
| `syntology` | 6 | 36.8 s | **$0.081** | 3 | 37,096 | 0/24 |
| `code_only` | 6 | **34.0 s** | $0.096 | 3 | 46,676 | 0/24 |

Adoption was total in both: **24/24 runs fetched served code in each arm**.
The conditional held again — **24/24 in both arms, cumulative 90/90** across
every version of this benchmark.

## What that means, without hedging

**On this task family the graph is not load-bearing for code discovery.** A
flat index over the 118,400 CodeSamples — BM25 over the function name and the
first 1,200 characters of source, fused with exhaustive cosine over the same
Titan vectors the graph stores — found the correct implementation on all 24
tasks, in the same number of turns, at the same pass rate, with no `:Method`
node, no `:Paper` node and no relationship traversed.

The graph's remaining justification on the evidence of this run is
**identity, provenance and attribution** — the things the CodeSample record
carries — **not surfacing.** That is the owner's third assumption
("CodeSamples alone are not sufficient without the graph rails") falsified
for discovery, on the benchmark the project built to test it.

Four things must be said in the same breath, because each of them limits how
far that sentence travels.

### 1. It is a ceiling tie, and a ceiling tie is weaker evidence than a tie

Both arms scored 100%. A benchmark where both conditions max out cannot rank
them; run 1 already taught this project that lesson from the other direction
(*"a ceiling arm cannot discriminate on a saturated benchmark"*). The floor
proves there is headroom versus no tools at all — `none` is 10/24, and the
tool arms clear it by 14 tasks — but there is no headroom left *between* the
two tool arms.

The honest power statement: with 0 discordant pairs in 24, the rule of three
puts the **95% upper bound on the graph's per-task advantage at 3 tasks in
24 (12.5%)**. So this run is consistent with the graph being worth up to
about three tasks, and inconsistent with more. It is not evidence that the
advantage is exactly zero. It is evidence that it is small on tasks of this
shape.

**What n would be needed.** A two-sided exact sign test needs **6 discordant
pairs, all in one direction**, before it can reach p < 0.05 (5 pairs gives
p = 0.0625). So the task count required to detect a real graph advantage of
rate δ is roughly 6/δ:

| true per-task graph advantage δ | tasks needed | P(seeing 0 in this n=24) |
|---|---|---|
| 12.5% (this run's upper bound) | ~48 | 0.04 |
| 10% | ~60 | 0.08 |
| 5% | ~120 | 0.29 |
| 2% | ~300 | 0.62 |

Read the right-hand column as the reason this result must not be quoted as
equivalence: a graph worth 2 tasks in 100 would have shown exactly what we
observed, 62% of the time. **But more tasks of this shape would not fix it.**
Both arms are at 100%; a ceiling cannot rank two conditions no matter how
wide it gets. The n that matters is not 48 or 300 more single-routine
reproductions — it is a task family where either arm can still fail.

### 2. Proximity — the owner's *first* claim — was not tested, at all

*"The graph will offer efficient proximity searching for agents when
surfaced code is not exactly what's needed."* These 24 tasks are
single-routine reproductions where the exact code exists and both arms found
it. A neighbour was never needed. `syntology_compose` has been called **zero
times across every run of every version of this benchmark**, this one
included. Nothing here confirms or refutes the proximity claim, and anyone
quoting this result against it is over-reading it.

This is now the sharpest open question in the lane, and it is testable: hold
the correct sample out of both arms and ask each for its best alternative,
then run the held-out referee on that alternative. The referee is local and
deterministic, so the subject cost is one sweep. That experiment does not
exist yet.

### 3. The corpus is a product of the graph

The 118,400 CodeSamples were harvested, generated, verified and attributed by
pipelines that read the graph. `paper_attribution` — the origin arXiv id the
flat index tokenises — is a `PROPOSES` edge denormalised onto a node. This
run tests whether the graph is load-bearing **at query time**. It is not
evidence that the graph could be deleted and the corpus would still exist.

### 4. Both controls moved, and only one of them has an explanation

Pre-registered bands were `none` 11–15/24 and `syntology` 19–23/24. Both
landed outside, by one task each.

| control | freeze | v1.5 | paired | p |
|---|---|---|---|---|
| `none` | 13/24 | **10/24** | +1/−4 | 0.375 |
| `syntology` | 21/24 | **24/24** | +3/−0 | 0.250 |
| `syntology` in-catalog only | 18/18 | **18/18** | **+0/−0** | 1.00 |

`syntology`'s move is fully explained and was **predicted before the run**:
all three gains are off-catalog, where its adoption went from 1/6 to 6/6
because coverage grew between 2026-09-02 and today (the pre-run deviation —
the graph now serves a backed level-3 sample for all 24 tasks, and the
frozen labels still say `-1`). In-catalog, where coverage did not change, it
reproduced the freeze exactly.

`none`'s move has **no mechanism**: nothing in that arm changed. Read it as
run-to-run variance in the bare model (p=0.375, not significant), and read
the tool arms' +14 against a floor that drifted −3 rather than against the
freeze's 13.

**Neither drift threatens the primary comparison**, because `code_only` vs
`syntology` is paired *within this execution*, on the same tasks, in the same
hour, against the same referee.

## Mechanism — what actually did the work

This is where the run says something the pass rates cannot.

**`code_only`: 24/24 fetches were the correct sample.** Not one wrong-sample
fetch, and not one haystack failure — the pre-registered failure mode
(prediction 6: harvested level-0 near-misses outranking the verified answer)
did not occur once.

| route that surfaced the fetched sample | runs |
|---|---|
| `keyword` | 26 |
| `semantic` | 26 |
| `origin_id` (shared with the above) | 8 |
| `entry_exact` | 2 |
| **`origin_id` as the ONLY route** | **0** |

**Both disclosed asymmetries came out inert.**

- *Asymmetry 1 (the searchable origin arXiv id).* Zero fetches depended on
  it. Every hit it contributed to was also carried by keyword and semantic
  matching, and the offline probe's counterfactual — the same queries with
  the origin route disabled — moved recall by **exactly 0** in every cell.
- *Asymmetry 2 (the prompt hands the agent the exact entry name).* Agents
  barely used it. Of 38 `code_search` calls, 4 were entry names; only **2**
  fetches came through the exact-entry pin. What agents actually typed was
  method name + description, often with the arXiv id appended —
  `"CHAMELEON domain weights affinity matrix"`,
  `"UOT-FM unbalanced optimal transport flow matching"`,
  `"empirical Neural Tangent Kernel eNTK prediction"`. The flat index
  answered those, which is a much stronger result than an entry-name oracle
  would have been.

**The verified facet — the one affordance I added that had no graph
counterpart — was never load-bearing.** It lists up to five backed-level-≥2
matches separately, so an unfiltered ranking cannot bury the verified answer
under harvested near-duplicates. **Zero fetches came from it.** Of the
fetches whose search response could be attributed, **18 were at rank 1** of
the plain ranked list and the rest at ranks 2–4. The flat ranking simply put
the right sample on top.

**`syntology`: 24/24 resolutions were exact `:Method` name hits.** The
token-overlap near-match ladder — the machinery built after the A/B run
traced three failures to `"IS-MBPG momentum"` against a graph holding
`"IS-MBPG*"` — **never fired on the serving path**: all 24
`get_reference_implementation` calls resolved exactly, and the fallback tier
fired zero times. On these tasks the ontology acted as a lookup table keyed
on a name the prompt already supplied.

*Corrected 2026-09-10 on independent re-verification (the original text here
read "fired zero times", full stop).* The ladder did fire **twice**, both
times on the browse tool `list_reference_implementations` rather than on
resolution, and both times it returned an irrelevant suggestion:
`"PPO clip"` → `"Automatic Clipping"` (a differential-privacy method), and
`"NLPO PPO"` → `"E2M1 with supernormal support"` (a numeric format). Both
searches had returned `total_matching: 0`; the agent ignored the near-matches
and passed both tasks anyway. Nothing in the result changes — the serving
path is what the claim was about — but "zero times" was wrong as written, and
the two firings say the ladder's precision is untested rather than good.

**The one place the ontology measurably beats the flat index** is in the
offline retrieval probe, and it is worth naming precisely because it is the
only positive signal for the graph in this whole run:

| query form (in-catalog, n=18) | recall@1 | @5 | @15 | @50 |
|---|---|---|---|---|
| Q1 entry function name | 17 | 18 | 18 | 18 |
| **Q2 method name ALONE** | **6** | **8** | **10** | **11** |
| Q3 method name + first sentence | 17 | 18 | 18 | 18 |

A bare method name finds the right code **10/18** in the flat index and
**24/24** through the graph's exact `:Method` lookup. *That* is the
ontology's contribution, measured: a name→code mapping the code text does not
contain. It did not bind in this run because agents do not query with bare
method names — they add a description, and one sentence of description takes
the flat index from 10/18 to 18/18.

## Predictions scored

| # | prediction | outcome |
|---|---|---|
| primary | `code_only` in-catalog 15–18 | **right** — 18 |
| 1 | `code_only` ≈ `syntology` in-catalog, ±2 | **right** — exactly equal, +0/−0 |
| 2 | controls hold (`none` 11–15, `syntology` 19–23) | **wrong, both** — 10 and 24, one outside each band; `syntology`'s explained by coverage growth, `none`'s not |
| 3 | `code_only` ≤ 9 turns and ≤ $0.20, worse than `syntology` | **right** — 6 turns / $0.096 vs 6 / $0.081; +19% cost, −8% wall |
| 4 | off-catalog `code_only` ≥ `syntology` | **right but vacuous** — 6 = 6; the premise was falsified before the run |
| 5 | the conditional survives | **right** — 24/24, cumulative 90/90 |
| 6 | failure mode = haystack dilution | **wrong** — 0 wrong-sample fetches, 0 failures |
| probe | Q1 ≥ 15/18 @1 · Q2 ≥ 8/18 @15 · Q3 ≥ 10/18 @15 · origin drop ≤ 2 | **all right** — 17 · 10 · 18 · 0 |

Being wrong on 2 and 6 is the useful part. 6 in particular: I expected the
115,574 unverified harvested samples to be a haystack that would cost the
flat arm tasks. They cost it nothing, which is a stronger statement about
flat retrieval than the pass rate alone.

## Deviations and caveats carried

- **Stale strata** (recorded pre-run): all 24 tasks are now served at V3;
  the `18/6` split is the frozen 2026-09-02 labelling, kept for pairing.
  Any comparison of this run's off-catalog cell against the freeze's is
  measuring coverage growth.
- **`search` and `both` were not re-run.** `search_arm_tools.py` changed
  three times since the freeze (S2 politeness gate, spoofed-UA removal) and
  `arxiv.org` now 403s us, so a re-run would be a number confounded by
  toolkit drift rather than a control. The freeze's search numbers
  (11/24, 20 turns, $0.365, 11/24 no-submissions) stand as the last clean
  measurement of that arm.
- **`code_only` still reads Neo4j** — `code_get` is a single-node lookup on
  the indexed `code_sha256`, and the index was built from the graph. What it
  never uses is *structure*. The finding is about edges and node types, not
  about the storage engine.
- **Arm purity held**: 0 of 72 transcripts show network use from
  `run_python` (run 1's measured leak did not recur), and
  `qc_code_only_arm.py` gates the no-traversal claim mechanically —
  mutation-tested, and its R2 check failed its first mutant and was
  strengthened.
- Sampling: one run per task×arm, one subject model (Sonnet 4.5), one task
  shape. Everything `RESULTS.md`'s assumptions register says still applies.

## What this changes, and what it does not

**Changes.** "The CodeSamples are not sufficient without the graph rails" is
falsified for discovery on single-routine reproduction tasks, at 118,400
samples, against an arm built to be as strong as honesty allowed. Any future
claim that the graph makes code discoverable has to be made about a task
shape this benchmark does not cover, and has to name it.

**Does not change.** The graph is still where the corpus comes from, where
identity and attribution live, and where the untested proximity claim lives.
And this benchmark is now saturated for tool-equipped arms: it cannot answer
the next question. The next question needs the substitution experiment in
§2, not another run of this one.
