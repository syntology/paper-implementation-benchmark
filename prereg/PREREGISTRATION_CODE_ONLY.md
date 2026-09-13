# Pre-registration: the `code_only` ablation (v1.5)

**Written 2026-09-10, before any v1.5 subject token is spent and before any
retrieval measurement against the 24 tasks.** Deviations get logged in
`RESULTS_CODE_ONLY.md` as deviations, in the same style `RESULTS.md` and
`FREEZE_RUN.md` log theirs.

## The question, and why the existing benchmark cannot answer it

The owner, 2026-09-10:

> "The graph will offer efficient proximity searching for agents when
> surfaced code is not exactly what's needed. The CodeSamples alone are not
> sufficient without the graph rails… if it isn't truly serving the purpose
> of the CodeSamples surfacing, it may no longer be necessary for the
> project to continue supporting and developing. The graph needs to truly
> justify its own existence."

`ARM_TOOLS` has been `none / search / syntology / both` since run 1. Every
arm tests the graph **together with** the code or **neither**. So the v1
freeze's headline — syntology 21/24 vs search 11/24, p=0.002, 6 turns vs 20,
search failing to submit in 11/24 — establishes that **graph+code beats web
search** and says nothing at all about whether the graph is load-bearing
*given* the code. This run adds the missing arm.

## Arms (identical prompt, identical budgets, identical referee)

| arm | tools | role |
|---|---|---|
| `none` | `run_python`, `submit_solution` | floor; control paired against the freeze |
| `syntology` | + the 6 graph tools, `--variant v14_freeze` verbatim | control paired against the freeze |
| **`code_only`** | + `code_search`, `code_get` | **the arm under test** |

`none` and `syntology` are re-run in the same execution, not read off the
freeze. If a control moves, this comparison is variance and the report must
say so. Their configuration is byte-identical to `FREEZE_RUN.md`'s: same
`--variant v14_freeze` descriptions, same server instructions, same tool
order, same 20-turn cap, same model
(`us.anthropic.claude-sonnet-4-5-20250929-v1:0`), same 2 workers. The new
`ARM_SYSTEM_SUFFIX` mechanism is keyed on the **arm**, so nothing about
`none` or `syntology` changes.

`search` and `both` are **not** re-run. The budget goes to the paired
comparison that answers the question, per the operating contract.

## What `code_only` is

`code_only_arm_tools.py`. Two tools over the 118,400 `:CodeSample` nodes:

- **`code_search(query, limit, min_level)`** — hybrid retrieval, fused by
  reciprocal rank (RRF, k=60, untuned):
  - **lexical**: BM25 over `entry` (weighted ×3), `signature`,
    `paper_attribution`, and the first 1,200 characters of `code`, with
    snake_case/CamelCase splitting so `compute_chameleon_domain_weights` is
    reachable from `chameleon`;
  - **semantic**: exhaustive cosine over all 118,400 Titan-v2 vectors —
    brute force, not ANN, because the read credential cannot execute
    `db.index.vector.queryNodes` and because exact ranking is the only way a
    `min_level` filter stays meaningful when the filtered slice is 2.6% of
    the rows;
  - an **exact entry-name match** pinned above the fused list;
  - a **verified facet**: up to 5 machine-verified (backed level ≥ 2)
    matches listed separately, because 115,574 of the 118,400 are harvested
    level-0 code that can outrank the verified answer on wording alone.
- **`code_get(code_sha256)`** — the full record: source, signature,
  verification level *and its report*, the test cases the level was measured
  on, env, generated_by, cross_checked_by, spec_review, origin arXiv id,
  attribution string.

**What is removed:** every `:Method` node, every `:Paper` node, every
relationship (no query in the file contains a `-[`), `compose`, `have`,
neighborhoods, `explore_paths`, and the inline
`verified_reference_implementations` structural fix (which is a
Paper→Method→CodeSample traversal grafted onto a paper tool). Tool
descriptions and server instructions are written to the same register and
length as the graph arm's, because the freeze run showed server instructions
are the lever that moves adoption, and a salience gap between the arms would
measure the prompt rather than the graph.

R2 discipline is preserved: a `verification_level` with no
`verification_report` behind it is reported as 0.

## Disclosed asymmetries — read these before reading the result

1. **`paper_attribution` is searchable.** The origin arXiv id is
   denormalised onto every CodeSample node, and the flat index tokenises it.
   The graph arm reaches the same artifact from an arXiv id via
   `get_code_for_paper`, so withholding the flat equivalent would be tuning
   this arm to lose — which the brief forbids at least as strongly as tuning
   it to win. Hits that matched on it are tagged `origin_id`, and the result
   is reported **with and without** that route.
2. **The task prompt hands the subject the exact entry function name.** It
   has to: the referee imports and calls it. A flat code index is naturally
   queried by function name, so `code_only` can exact-match on a key the
   graph arm's resolvers cannot use — while the graph arm is handed the
   method name, which *its* resolvers key on exactly. Both arms get their
   own natural key from the same prompt. This is the single largest threat
   to the run's external validity and the offline probe below exists to
   quantify it.
3. **The corpus is a product of the graph.** The 118,400 CodeSamples were
   harvested, generated, verified and attributed by pipelines that read the
   graph. This ablation tests whether the graph is load-bearing **at
   discovery time**, not whether it was needed to build the corpus. A null
   result here is not a claim that the graph could be deleted.
4. **Haystack asymmetry, in the graph's favour.** The graph arm browses a
   curated 1,179-method catalog where everything has an implementation;
   `code_only` searches 118,400 rows of which 115,574 are unverified
   harvested code. The verified facet narrows this; it does not close it.

## What this ablation CANNOT answer, stated before the result

The owner names **proximity** first: *"efficient proximity searching for
agents when surfaced code is not exactly what's needed."* **These 24 tasks
do not exercise proximity.** They are single-routine reproductions with an
exact entry point and a held-out property suite; a neighbour is never
needed, and `syntology_compose` was called **zero** times across every
benchmark version ever run. So:

- A `code_only ≈ syntology` result falsifies the **discovery** assumption
  and says nothing about the **proximity** assumption.
- The nearest thing to a proximity probe here is the off-catalog stratum
  (n=6), which is descriptive only, as pre-registered in `FREEZE_RUN.md`.
- Anyone quoting this result as "the graph does not help" beyond discovery
  is over-reading it, and the report must say so in its own voice.

## Predictions (falsifiable, fixed before any run)

**Primary — `code_only` in-catalog (n=18): 15–18.** Reasoning, stated so the
prediction can be scored on its mechanism and not just its number: the
prompt gives the exact entry name, the index pins exact entry matches, and
the freeze run established that *every* agent that fetched served code
passed (66/66 cumulative). The discovery step this arm has to clear is
therefore easy, and the serving artifact is identical to the graph arm's.

1. **`code_only` ≈ `syntology` in-catalog**, within ±2 tasks. I expect the
   graph to be **not load-bearing for discovery** on this task family.
2. **Controls hold:** `none` 11–15/24 and `syntology` 19–23/24 (freeze:
   13/24 and 21/24). If either lands outside its band, every delta below is
   read against that movement and the comparison is reported as variance.
3. **Efficiency:** `code_only` in-catalog median ≤ 9 turns and ≤ $0.20 —
   worse than `syntology`'s 6 turns / $0.072 (a 118,400-row haystack costs
   at least one extra sift) but nowhere near `search`'s 20 turns / $0.365.
   **If `code_only` matches on pass rate but needs ≥ 15 turns, that is a
   different answer and gets reported as one.**
4. **Off-catalog (n=6): `code_only` ≥ `syntology`.** The graph serves 1,179
   methods; the flat index searches 118,400 samples, so an off-catalog task
   is likelier to have *something* relevant in the flat corpus than in the
   curated catalog. Descriptive only at n=6; reported, not tested.
5. **The conditional survives:** every run that fetches a backed level-≥2
   sample passes. Cumulative 66/66. One failure would be the first ever and
   gets a per-property post-mortem.
6. **Failure mode I expect from `code_only`:** haystack dilution — the agent
   queries the *method* name rather than the entry name, gets harvested
   level-0 near-misses from public repositories, and treats one as
   authoritative. If this dominates, the defect is that a flat index has no
   name vocabulary, which is the one thing the ontology genuinely supplies.

## Offline retrieval probe (zero subject spend, run before the sweep)

The arm's ceiling, independent of agent behaviour. For each of the 18
in-catalog tasks, ground truth is the CodeSample the graph serves for that
task's method (resolved once, graph-side, for **analysis only** — the arm
never sees it). Three query forms are issued to `code_search(min_level=0)`
and the target's rank recorded:

- **Q1** the entry name alone
- **Q2** the method name alone
- **Q3** the method name + the task's first sentence (the natural-language form)

and each is re-scored with the `origin_id` lexical route disabled, giving
the asymmetry-1 counterfactual.

Predicted: **Q1 recall@1 ≥ 15/18** · **Q2 recall@15 ≥ 8/18** · **Q3
recall@15 ≥ 10/18** · and **Q3 recall@15 drops by ≤ 2** with `origin_id`
disabled (Q3 contains no arXiv id, so it should barely move; Q1/Q2 likewise).

## Metrics

- **Primary:** referee pass rate per arm × stratum, reported for the 18
  in-catalog and 6 off-catalog **separately**, as pre-registered in the
  original.
- **Paired primary comparison:** `code_only` vs `syntology`, per task,
  exact two-sided sign test on discordant pairs. Secondary: `code_only` vs
  `none`, and both controls vs their v1-freeze counterparts
  (`compare_runs.py`).
- **Efficiency, co-primary with pass rate:** turns, wall, cost, and
  no-submission rate. The freeze's sharpest result was not pass rate.
- **Mechanism:** the `matched_by` tally over every `code_search` result the
  agent actually acted on (`entry_exact` / `keyword` / `origin_id` /
  `semantic`), mined from the transcripts.
- **Adoption:** did the agent call `code_get` at all when offered it.

## Decision rules (what each outcome means, fixed now)

- **`code_only` ≈ `syntology`** (|Δ| ≤ 2 in-catalog, sign test p > 0.2) →
  **the graph is not load-bearing for discovery on this task family.** Its
  remaining justification is identity, provenance and attribution, not
  surfacing. Reported plainly, with the proximity caveat above.
- **`code_only` ≈ `none`/`search`-level** (in-catalog ≤ 12/18) → the rails
  are the product; the corpus without them does not serve.
- **In between** → name the discordant tasks individually and say what the
  graph supplied that the flat index did not, per task.
- **`code_only` > `syntology`** → report it as found. The flat index reaches
  118,400 samples and the graph's serving path reaches 1,179; if that
  matters, the finding is about the serving path's reach, not the ontology.
- **Efficiency override:** any pass-rate conclusion is qualified by turns.
  Parity at 2× the turns is not parity.
- **Cost gate:** if the 6-run smoke projects the 72-run sweep above **$40**,
  stop and report the projection rather than half-running the matrix.
  Session ceiling is $50 + a binding 10% slush.

## Provenance

New run directory `runs_v15/` so no result set mixes arm rosters. Task set
is `tasks/tasks_freeze.json`, unchanged and unchanged-in-place — same 24
task_ids, same entry points, same `pass_both` sets, same referee
(`verify_solutions.py`, strict boolean). Index artifacts
(`code_index/records.jsonl`, `lexicon.pkl`, `all_vectors.npy`,
`all_shas.json`) carry provenance sidecars naming the graph URI, the node
count and the field list (R1). Both index builds are registered jobs (R6).
This file, the probe output and `RESULTS_CODE_ONLY.md` land in the commits
that carry the run (R7). No Neo4j writes at any point (C3).

---

## PRE-RUN DEVIATION, recorded 2026-09-10T20:00Z — before any subject token

**The frozen strata are stale, and the direction matters.**
`tasks_freeze.json` carries `served_level_today: -1` for the six
`off_catalog` tasks, derived 2026-09-02. Re-derived today by
`probe_code_only_retrieval.py` against the live graph, **all 24 tasks now
have a backed level-3 CodeSample and the graph serves it** —
`Paper-[:PROPOSES]->Method-[:HAS_REFERENCE_IMPL]->CodeSample` returns
exactly the correct sample for 24 of 24. Coverage grew between the freeze
and today.

Consequences, fixed now rather than argued later:

1. The pre-registered split **still reports as 18 / 6 using the frozen
   labels**, because that is what makes this run paired with the freeze.
   But the 6 are no longer off-catalog, and any comparison of this run's
   off-catalog cell against the freeze's (syntology 3/6) is confounded by
   coverage growth, not by anything either arm did. The report must say
   this in the same breath as the number.
2. **Prediction 4's premise is falsified before the fact.** It reasoned
   that the flat index (118,400) would out-reach the graph's curated
   catalog (1,179 methods) off-catalog. The graph now serves all six, so
   the reasoning no longer applies. The prediction is left exactly as
   written and will be scored as written; the premise failure is the point
   of recording it.
3. Both arms see the same corpus, so the primary paired comparison
   (`code_only` vs `syntology`) is **unaffected**. What changes is that this
   run is now a full-coverage test — every task's answer exists, in both
   arms — which is a cleaner test of discovery than the freeze was.

No task, referee, `pass_both` set or stratum label is edited. Editing them
would break the pairing that makes the controls meaningful.
