# Every claim, and the pre-registration that fixed its decision rule

The point of pre-registration is that the rule for reading a number was written
down before the number existed. This document is the audit trail: for each
claim made anywhere in this repository, **which pre-registration fixed its
rule, when that file was committed relative to the run, and which artifact the
number comes out of.**

Claims that were *not* pre-registered are marked **post-hoc** and say so in
their own row. There are five of them (the post-hoc set is enumerated in full below; if that list and this count ever disagree, the list wins). Each is in the conservative
direction — a bound, a caveat, or a licence measurement made at packaging time.

`tools/verify_claims.py` re-derives the mechanically checkable subset of this
table from `data/` and fails if any of them has drifted. As of 2026-09-13 that
subset includes everything that used to be transcript-derived — the redacted
transcripts ship — and the fidelity bracket, whose audit rows ship too.

---

## The four runs

| run | date | prereg file | committed | runs | subject spend |
|---|---|---|---|---|---|
| run 1 | 2026-08-31 | `prereg/PREREGISTRATION.md` | before the first subject token | 96 | $37.24 |
| v1.4 "the v1 freeze" | 2026-09-02 | `prereg/FREEZE_RUN.md` | before any v1.4 run | 96 | $17.40 |
| v1.5 `code_only` | 2026-09-10 | `prereg/PREREGISTRATION_CODE_ONLY.md` | before any v1.5 token and before any retrieval measurement against the tasks | 72 | $5.43 |
| v1.6 substitution | 2026-09-11 | `prereg/PREREGISTRATION_SUBSTITUTION.md` | commit `8505db391`, before any subject token | 146 | $15.81 |

Three description/structure ablations (v1.1–v1.3) sit between run 1 and the
freeze; their pre-registrations are `prereg/ABLATION_V1{1,2,3}.md`.

---

## Headline claims

### 1. A flat index ties the graph arm, 24/24 each, +0/−0, p = 1.00

| | |
|---|---|
| **rule fixed by** | `PREREGISTRATION_CODE_ONLY.md` → *Metrics* (paired primary: `code_only` vs `syntology`, exact two-sided sign test on discordant pairs) and *Decision rules* (`\|Δ\| ≤ 2` in-catalog with p > 0.2 → "the graph is not load-bearing for discovery on this task family") |
| **predicted in advance** | prediction 1, *"`code_only` ≈ `syntology` in-catalog, within ±2 tasks"* — scored **right** |
| **artifact** | `data/results_v15.json` → `data/analysis_v15.json` |
| **verifiable here** | yes — `tools/verify_claims.py` |
| **disclosed before the run** | four asymmetries, including that the flat index can exact-match the entry name the prompt hands the subject, and that the corpus is itself a product of the graph |

### 2. Rule of three caps the graph's per-task advantage at ≤ 3 tasks in 24

**Post-hoc.** The v1.5 pre-registration fixed the test and the decision rule but
did not name this bound in advance; `PREREGISTRATION_SUBSTITUTION.md` fixed the
equivalent discipline one run later (*"the report will carry the rule-of-three
bound for whatever D it observes rather than the word 'equivalent'"*). It is
included because it is the conservative reading: it says the tie is
**consistent with the graph being worth up to about three tasks**, not that the
advantage is zero. Derived from D = 0 at n = 24; stated in
`results/RESULTS_CODE_ONLY.md` §1 alongside the power table.

### 3. With the answer held out, neither arm beats no tools at all

| | |
|---|---|
| **numbers** | `none` 24/48 · `syntology_ho` 24/48 · `code_only_ho` 23/48 |
| **rule fixed by** | `PREREGISTRATION_SUBSTITUTION.md` → *Scoring* (primary binary task success, paired exact sign test; co-primary property fraction, paired Wilcoxon — **both chosen before any output was looked at**) and *Decision rules* (`\|Δ\| ≤ 2`, both p > 0.2 → *"the neighbourhood does not find substitutes the flat index cannot"*, reported in those words, without the word "equivalent") |
| **n fixed by** | a stopping rule that **reads cost and nothing else**: extend to 72 if a 12-run smoke projects the full matrix ≤ $22. It projected $24.83, so n stayed at the pre-registered 48. Pass/fail does not exist until `verify_solutions.py` runs, which is after the sweep — so the choice of n is structurally blind to outcomes, not merely promised to be |
| **falsified prediction** | prediction 4, *"both hold-out arms beat `none` by ≥ 5 tasks"* — **wrong, by 0 and −1**, and that is the run's actual finding |
| **artifact** | `data/results_v16.json` → `data/analysis_substitution.json` |
| **caveat that travels with it** | the published analysis reports **n = 49** for the two hold-out arms, because two extra runs exist on `sub_2304.03274`, a smoke task outside the primary set. The pre-registered primary is **48**. Including them moves `syntology_ho` to 25/49 and `code_only_ho` to 24/49 and changes no comparison. Disclosed in `results/RESULTS_SUBSTITUTION.md` → *Deviations* |

### 4. The interval, not the word "equivalent"

Graph vs flat under hold-out: **+2.1%, 95% CI [−11.5%, +15.6%]**; sign test
p = 1.00 on D = 11 (6/5); Wilcoxon on the graded metric p = 0.89. The
pre-registration stated the power position **before the run**: at n = 72 with a
20–30% discordance rate, D ≈ 14–22, *"powered for π ≥ ~0.72 — a large asymmetry
— and **not** powered for a modest edge… if this run returns a tie on the binary
metric, that is not evidence of equivalence."* Observed D = 11 of 48 (22.9%),
inside the predicted band.

### 5. `syntology_compose` has been called zero times, ever

Across **every run of every version** of this benchmark: run 1, v1.1, v1.2,
v1.3, the v1 freeze, v1.5, and v1.6 — including the one condition built
specifically to elicit it. Pre-registered as prediction 3 of
`PREREGISTRATION_SUBSTITUTION.md` (*"called ≤ 2 times"*) — scored **right, and
at the floor**.

**This is the one headline you can verify yourself without trusting us**:
every published `data/runs/**/meta.json` lists each tool call by name.
`tools/verify_claims.py` counts them.

### 6. The graph arm beat the web-search arm on the frozen v1 run

| | |
|---|---|
| **numbers** | `syntology` 21/24 vs `search` 11/24; **+10/−0, p = 0.002**; in-catalog 18/18 vs 10/18; `search` hit its 20-turn cap without submitting in 11/24 runs |
| **rule fixed by** | `FREEZE_RUN.md` → *Predictions* 1–6, written before any v1.4 run; the within-run paired comparisons were fixed in `PREREGISTRATION.md` → *Metrics* |
| **artifact** | `data/results_v14.json` → `data/analysis_v14.json` |
| **asymmetry disclosed in advance** | `PREREGISTRATION.md` → *Referee*: for in-catalog tasks the served code was itself verified against this referee's own property suite at grant time, so **fetch-and-submit passes by construction**. The in-catalog cells measure finding and fetching, not implementing |

### 7. Run 1 separated nothing, and the reason was the floor

All paired comparisons p ≥ 0.69. The floor arm passed **13/24** against a
pre-registered prediction of **3–7/24** (prediction 3, scored **wrong**) — the
task family has roughly half the headroom the design assumed. Artifact:
`data/results.json` → `data/analysis.json`.

**Instrument change after the fact, disclosed:** a referee audit found the
sandbox stringifying numpy booleans, which every consumer read as passing. The
referee was made strict and **all four run sets were re-verified** under it.
The numbers above are the corrected ones; `results/RESULTS.md` carries the
correction block and says which tables it overrides. Changing a measuring
instrument after a run is exactly the move that needs to be announced rather
than absorbed.

### 8. Every run that fetched served code passed the held-out referee

90/90 cumulative across every version (11/11 run 1 · 6/6 v1.2 · 12/12 v1.3 ·
37/37 v1 freeze · 24/24 + 24/24 v1.5). Pre-registered as prediction 5 in both
`FREEZE_RUN.md` and `PREREGISTRATION_CODE_ONLY.md`, with a per-property
post-mortem promised on the first failure.

**Verifiable here since 2026-09-13.** `data/runs/**/meta.json` lets you count
which runs *called* `get_reference_implementation` or `code_get`, and
`data/results_*.json` gives each run's pass/fail — so the "called it and
passed" conditional was always checkable. Whether the sample fetched was the
*correct* one was established from transcripts, and the transcripts now ship
redacted: `src/analyze_code_only_mechanism.py` run over `data/runs/` reproduces
`data/mechanism_v15.json` exactly, `fetch_correctness` cell included.
`tools/verify_claims.py` runs that re-derivation rather than trusting the
artifact.

### 9. The hold-out was proven, not asserted

`verify_holdout.py`, all 72 tasks, **0 findings before the sweep**: 372/372
held-out shas exist as index rows, 372/372 refused by `code_get` **with the
same error an unknown sha gets**, target method listed 0/72, and — the test of
the test — with the hold-out **off** the adversarial battery reached the sample
72/72 and the graph served it 72/72. Post-sweep, all 96 hold-out transcripts
scanned verbatim: 0 leaks, 0 tasks invalidated.

Six checks fixed in `PREREGISTRATION_SUBSTITUTION.md` → *Exclusion
verification*. Artifact: `data/holdout_verification.json`.

**Two corrections to the checks themselves are recorded rather than quietly
fixed**, one of which **falsifies the pre-registration's own claim** that the
hold-out makes `compose` inoperable — it stays invocable on 3 of 72 tasks. The
prediction was left as written and scored as written.

### 10. Where the ontology measurably beats the flat index

A bare method name finds the right code **10/18** in the flat index and
**24/24** through the graph's exact `:Method` lookup. Pre-registered as the
offline probe in `PREREGISTRATION_CODE_ONLY.md`, with thresholds fixed in
advance (Q1 ≥ 15/18 @1 · Q2 ≥ 8/18 @15 · Q3 ≥ 10/18 @15 · origin-route drop
≤ 2) and all four scored **right** (17 · 10 · 18 · 0). Artifact:
`data/probe_code_only_retrieval.json`.

It did not bind in the run because agents do not query with bare method names —
one sentence of description takes the flat index from 10/18 to 18/18. This is
the only positive signal for the graph in the whole ablation and it is reported
as such.

### 11. The serving surface has no substitution affordance

`compose` returns what fits **with** a routine, never what could stand **in
for** it: its partners overlap the flat index's substitutes on **1 of 72**
tasks, median typed-partner count **0** (zero on 59/72), `effectively_terminal`
on 46/72. Measured offline with the hold-out **off**, so it is the tool at full
strength. Fixed in `PREREGISTRATION_SUBSTITUTION.md` → *What the hold-out costs
the graph arm* (*"the cost is measured, offline, for free"*). Artifact:
`data/probe_substitution.json`.

---

## Claims not covered by any pre-registration in this repository

**12. Reference-implementation fidelity sits in a bracket of 0.29–0.80.**
Cited in `README.md` as the reason nothing here carries a correctness claim. It
comes from a separate audit — all 2,831 served reference-implementation edges,
SRS n = 400, seed 20260911, pre-registered before the draw and the first model
call.

**It used to be asserted on our own authority, which was the weakest line in
this tree. Since 2026-09-13 it is shown.** `data/fidelity_audit/` carries that
pre-registration verbatim, the three adjudicator summaries, and all **1,536
per-row verdicts**; `tools/recompute_fidelity_bracket.py` re-derives 0.2905 and
0.7965, both Wilson lower bounds (0.2476 / 0.7542), the strict `is_defining`
reading (0.706), the both-families-agree floor (0.2784), each adjudicator's
sensitivity and specificity against the 22 gold rows (Mistral 0.25 / 1.00,
DeepSeek 0.875 / 0.167), and the paired mutation flip rate (27/145 = 0.1862).

The adjudicators' verbatim paper quotations are **removed** from the published
rows — `evidence_quote` and the two withheld-field markers — because those are
the papers' words, not ours. Nothing the bracket is computed from depends on
them.

**Two things are still not checkable here, and `verify_claims.py` prints both
rather than letting them pass:** whether any individual verdict is right (the
adjudicators read the served code and the paper body, neither of which is
published — and the audit's own primary finding is that the verdicts are
unreliable in the permissive direction), and that the 400 rows are an SRS of
the 2,831-edge frame (the frame is the private graph; its sha256 and the seed
are recorded in `audit_summary.json`).

**13. The corpus licence census.** 118,400 samples; 115,574 harvested; 71.0%
with no licence we can rely on. Measured at packaging time by
`tools/corpus_license_report.py`, artifact `data/corpus/license_census.json`.
Not part of any experiment. It is re-derivable only against the Syntology
graph.

**14. What 29 harvested samples pulled into transcripts are licensed under.**
Same tool, same caveat. It is the basis for excluding raw transcripts.

**15. The rule-of-three bound** — see claim 2.

**16. "The task set carries no harvested third-party code."** Checked
mechanically (`corpus_license_report.py` report C: 96/96 reference
implementations are LLM-generated), but the check is ours and runs against our
graph. What you *can* check here is the files themselves, in `referees/`.
