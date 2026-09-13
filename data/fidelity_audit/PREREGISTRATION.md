# Pre-registration — fidelity audit of `HAS_REFERENCE_IMPL` / generated

**Written 2026-09-11, BEFORE any row was drawn and BEFORE any model call.**
Nothing below was chosen after seeing a result. Deviations are recorded **in
this file, as dated amendments**, with the reason and with the statement of what
had and had not been observed when each was made — not edited out. Three were
made; all three are below, and each was committed before the model call it
affected. Results live in `audit_audit.json` / `audit_validate.json` /
`audit_mutate.json` and in the `accuracy_ledger.json` record those produce.

Modelled on `<INTERNAL>/PREREGISTRATION.md`, whose sampling
and Wilson machinery this lane imports rather than rewrites
(`audit_llm_strata.build_fulltext_index / fetch_docs / enumerate_frame / draw /
wilson_lower`, and `corroborate_method_names_by_citers.bounded` for word
boundaries — the one copy of that rule in the repo).

## 0. What is being audited, and why it is not already covered

`(:Method)-[:HAS_REFERENCE_IMPL]->(:CodeSample)` is the edge every code-serving
surface traverses — `get_reference_implementation`,
`list_reference_implementations`, `compose`, `have`, `assembly`, and the
`get_code_for_method` family of lookups as users describe them.

Measured 2026-09-11, read-only:

| fact | value |
|---|---|
| edges | **2,831** |
| distinct CodeSamples | 2,826 (5 samples are attached to two Methods each) |
| distinct Methods | 2,831 |
| `source_kind` | **`generated` on 2,831 of 2,831 — no exceptions** |
| producer | `llm:us.meta.llama3-3-70b-instruct-v1:0` |
| cross-checker on the edge provenance | `llm:us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| harvested population (`HAS_HARVESTED_IMPL`, Paper-attached) | 115,574, **disjoint** |
| parsed full text held for the origin paper | **2,827 / 2,831 (99.9%)** |
| `batch_runs/<arxiv_id>/` artifacts on disk | 2,831 / 2,831 |

So every byte of code this graph serves under a method's name was **written by a
model**, not harvested from the paper's repository, and the accuracy ledger has
**no stratum registered for it at all** — `qc_accuracy_ledger.py`'s
`SERVED_RELTYPES` does not list `HAS_REFERENCE_IMPL`, so its absence does not
even report as an unresolved partial. It is the one served population the gate
cannot see.

Composition of the frame, by the properties that plausibly move the rate:

| `spec_review` | n | what produced that value |
|---|---:|---|
| `unreviewed` | 1,654 | `build_v2_load_file.py` writes the string; nothing reviewed them |
| `clean` | 967 | the **two-reviewer `auto_clean` gate** (`batch_runs/gate_reviews.jsonl`) — two models, not a person |
| `(null)` | 203 | the `settle_at_scale_2026-08-27` contract load; no value written |
| `note_only` | 3 | the 2026-08-26 external human-relayed review |
| `repaired_pending_re_review` | 3 | same review, defect found, repaired, regenerated |
| `label_fix` | 1 | same review |

| `verification_level` | n |
|---|---:|
| 3 | 1,826 |
| 2 | 965 |
| 0 | 25 |
| 1 | 15 |

**22 of 2,831 have ever been spec-reviewed by a human-directed pass — 0.8%** —
and those 22 were hand-picked by an external reviewer, plausibly for suspicion,
so their 15/22 defect rate is not an unbiased estimate of anything. Producing an
unbiased one is this lane's whole job.

## 1. The claim under test

> **Does this code implement the method it is attached to, as that method's
> paper defines it?**

Not "does it run" — V0–V3 already measure that and are recorded in
`verification_report` on every node, which is why this audit executes nothing.
Not "is the math correct in isolation" — `s4_convolution_kernel` was
brute-force-verified as a correct dense SSM convolution kernel and was still
**pulled from production** because S4's defining contribution is the structured
(HiPPO / normal-plus-low-rank) parameterization, which the code did not have.
**Correct-adjacent is the failure mode here**, and nothing that only checks
execution can see it.

**The grain question, pinned before the draw because it decides the number.**
These samples are *core routines*, not whole methods: the pipeline
(`generate_reference_impl.py`, `run_batch_cycles.py`) extracts one pure function
from the paper's own algorithm block. Two readings are defensible and they give
different rates, so both are pre-registered and both are reported:

- **Lenient (the headline).** The code faithfully implements **a routine the
  paper itself specifies as part of this method**, correctly, under the right
  name. This is the reading the serving payload itself asserts — *"Generated
  from arXiv:X's own algorithm description; reference implementation, not
  audited production code."* The headline fidelity rate is computed this way.
- **Strict (reported beside it).** The routine must additionally be **the named
  method's own defining content**, not a generic ingredient the paper happens to
  use. Collected as a separate pre-registered boolean per row
  (`is_defining`), never as the verdict — the same treatment
  `<INTERNAL>/38` gave `wrong_kind`, so a reader who holds the strict standard
  can read their own number off the same table.

The S4 case is INCORRECT under **both** readings and that is deliberate: the S4
paper's own definition of its convolution kernel *includes* the structured
parameterization, so a dense-A kernel is not a faithful implementation of the
routine the paper specifies, quite apart from whether the routine is defining.
An instrument that needs the strict reading to catch S4 would be untestable
against the validation set below.

## 2. Sampling frame, seed, draw

Simple random sampling **over edges**. Not stratified, and not clustered by
paper: the annotation unit is one model call per edge, so the Wilson interval's
own assumption is exactly the draw being made. Rates **are** reported split by
`spec_review`, `verification_level`, `spec_source` and edge provenance after the
fact — reporting a split is free; drawing on one buys a design effect.

- **Frame predicate:** `MATCH (m:Method)-[r:HAS_REFERENCE_IMPL]->(cs:CodeSample)`
  — the whole thing, 2,831 rows, no filter. Every row is `generated`, so there
  is no `/generated` sub-selection to make.
- **Draw procedure**, so it is re-derivable and checkable: build each row's
  composite key `origin_arxiv_id || entry || occurrence index`, sort
  lexicographically, record `sha256` of the sorted key list and the frame size,
  then `random.Random(SEED).sample(range(N), n)`. Seed and every drawn key go
  into the report. Not `ORDER BY rand()`: unseedable, so the draw cannot be
  re-derived and a reader has to take the sampler's word for it.
- **SEED = 20260911. n = 400.**

The frame is 2,831, so n = 400 is **14.1% of the population**. The Wilson
interval carries **no finite-population correction**, which makes it
conservative here — the true interval is narrower than the one reported. Left
uncorrected on purpose; erring wide is the safe direction and it keeps this
bound comparable to the ledger's other records.

### What n = 400 can and cannot detect

Wilson 95% lower bound, computed before spending:

| true rate | LB at n=400 | clears 0.80? |
|---|---|---|
| 0.95 | 0.924 | yes |
| 0.90 | 0.868 | yes |
| 0.85 | 0.812 | yes, narrowly |
| 0.83 | 0.790 | **no** |
| 0.75 | 0.706 | no |
| 0.60 | 0.551 | no |

It cannot see a defect mode rarer than ~1 in 400 (0.25%, ~7 edges), and it
cannot resolve the 5 double-attached samples or the 15 rows at
`verification_level < 2` as sub-populations — those are expected to contribute
0–3 rows each.

## 3. Threshold, declared now

**Serving threshold = Wilson 95% lower bound ≥ 0.80**, the house convention for
every `llm-involved` stratum in `accuracy_ledger.json`.

Recorded alongside, not substituted: an artifact served as a *reference
implementation* under a named method, with a machine-verification level
attached, is arguably owed the **0.95** bar the deterministic strata carry. The
report states the verdict against both, because the choice between them is an
owner call and printing both costs nothing.

## 4. Adjudication: three outcomes, undetermined never rounded

Every row gets exactly one of **CORRECT** / **INCORRECT** / **UNDETERMINED**.
`n` and `n_correct` are over CORRECT + INCORRECT; the undetermined count travels
with them in the record and in the report, and is folded into neither.

INCORRECT failure modes — **the `spec_review_ledger.json` vocabulary, not a new
one**, so the output feeds the existing scheme:

| mode | meaning |
|---|---|
| `hard_error` | mathematically wrong as written, judged against the paper's own equations (wrong objective, wrong sign, identically zero) |
| `not_the_method` | the routine is not part of the named method as the paper defines it — the paper never specifies it, or it is a generic ingredient standing in for the structure the paper actually defines (the S4 shape) |
| `label_fix` | the code correctly implements a *different, identifiable* routine or method; the attached `Method` name is wrong |
| `fidelity_flag` | right routine, wrong details — a missing term, a wrong normalizer, a wrong parameterization, an unstated simplification |
| `not_in_paper` | the paper does not contain this routine at all |

Extra booleans collected per row, reported separately, **never the verdict**:
`is_defining` (the strict reading of §1) and `runs_but_differs` (the
`fidelity_flag` shape as the reviewer defined it).

**Two rates are reported, both pre-registered:**

1. **Fidelity rate** = CORRECT / adjudicable. The headline, against the 0.80 bar.
2. **Never-serve rate** = (`hard_error` + `not_the_method`) / adjudicable. These
   are exactly the verdicts `spec_review.NEVER_VERIFIED` says must never be
   served as machine-verified. `fidelity_flag` and `label_fix` are *servable
   with a note* under the existing rule, so they are excluded from this second
   rate and reported on their own line — the question "how much is mislabelled"
   and the question "how much must not ship at all" have different answers and
   deserve different numbers.

## 5. Evidence bundle (deterministic, built before any model call)

Per row, from the graph and the corpus, never from a model:

1. Method name, origin arXiv id, paper title, paper abstract (graph).
2. **The code itself** — `cs.code`, `cs.entry`, `cs.signature`. Median 1,275
   chars, p90 2,119, max 5,387, so it is shown in full and never truncated.
3. **Selected paper body text** from the parsed corpus, deterministically
   chosen: each section scored by word-bounded hits of the method name (weight
   3), hits of the entry name's significant tokens (capped at 5 each), and a
   bonus if the heading carries one; sections taken by score, emitted in
   document order, each capped at 4,000 chars, total capped at 14,000, with the
   opening 1,200 chars of the first section always included so "what this paper
   is about" is never absent. The chosen headings are recorded on the row.

**Withheld from every adjudicator, recorded on every row for human spot-check:**
`spec.json`'s `spec_text` (the producer's own input — showing a judge the
producer's brief turns an audit into a compliance check), `spec_review`,
`review_note`, `verification_level`, `verification_report`, `generated_by`,
`spec_source`. `<INTERNAL>/38` withheld the extractor's `justification` for the
same reason and it is the same reason.

The prompt states explicitly that execution, robustness, edge cases and style
are **already separately verified and are not what is being judged** — so a
judge cannot spend its verdict on a crash that V1 has already priced.

## 6. Adjudicators — and one exclusion that matters

- **Primary: Mistral Large 3** (`bedrock_client.MISTRAL`).
- **Secondary: DeepSeek V3.2** (`bedrock_client.DEEPSEEK`), on every row.

Both are different families from the Llama-3.3-70B producer. Adjudicating
Llama's output with Llama is agreement, not accuracy — the false premise that
made the v1 PROPOSES audit worthless (`PROGRAM.md`, *"the v1 accuracy audit
measured agreement, not accuracy"*). **No Llama call is made anywhere in this
audit.**

**Claude Sonnet 4.5 is excluded as an adjudicator**, and this is a stronger
exclusion than `<INTERNAL>/38` needed. Sonnet is not a bystander here: it is the
`cross_checked_by` model on all 2,831 edges — its independent implementation
*is* the V2 evidence — it drafted a share of the specs, and per
`spec_review_ledger.json` it performed the repairs. A participant in the
artifact's production cannot be its auditor. It is not used, not as a
tie-breaker, and not as a third opinion.

All calls go through `bedrock_client` (the ONE way; no `.invoke_model`
anywhere), batch lane, `us-east-1`.

## 7. Instrument validation — pre-registered, with bars it can fail

**This is the part that decides whether the rate gets reported at all.**
`<INTERNAL>/38` measured PROPOSES at a clean-looking 0.868 and then found its
adjudicator caught 23.3% of known-bad rows against its own declared 25% bar,
which put the honest estimate below threshold. A blind instrument returns a
flattering number on any population.

Two channels, both measured before the fidelity rate is believed.

### V-A — the 22 reviewed rows (natural negatives, an external human-directed pass)

Reconstructed deterministically from `spec_review_ledger.json` +
`batch_runs/batch_results.jsonl`; each of the 22 entry names maps to exactly one
`(arxiv_id, method, entry)` — verified, no collisions. Same prompt, same
evidence bundle, same models.

- **Known-bad (16):** 13 `fidelity_flag` + 1 `hard_error`
  (`compute_guidance_gradient`) + 1 `label_fix` (`corrector_step_ve`) + 1
  `pulled_not_the_method` (`s4_convolution_kernel`).
- **Positive control (6):** 3 `note_only` + 3 `repaired_pending_re_review`,
  the latter judged on `repair/impl_llama.py` — the version that would actually
  be served, which the reviewer's own second pass recorded as corrected and
  re-verified.

**Three bars, all of which must hold:**

- **(a) Severe gate — 3 of 3.** `compute_guidance_gradient`,
  `corrector_step_ve` and `s4_convolution_kernel` must each come back
  INCORRECT. An adjudicator that cannot re-find the one mathematically wrong
  objective, the one misattribution and the one pulled-as-not-the-method has not
  earned the right to score the other 2,809.
- **(b) Sensitivity ≥ 0.50** over the 16 known-bad. Higher than
  `<INTERNAL>/38`'s 0.25 bar on purpose: those 16 are the *easiest* negatives
  that exist here — a reader found every one of them unaided and wrote down
  why — and this adjudicator is shown the code and the paper, not a title and
  an abstract.
- **(c) Specificity ≥ 0.50** over the 6 positives. Without (c), an instrument
  that answers INCORRECT to everything scores 16/16 on (b) and 3/3 on (a) and is
  worthless. This is the control, and it is the reason 6 weak positives are worth
  running.

### V-B — paired mutation, on the audited population itself

V-A's 22 are hand-picked and n = 22. V-B measures the same instrument on the
population the rate is actually about, with an n that supports a bound.

**60 rows drawn from the frame with the same seed and disjoint from the audit
sample.** Each gets one **deterministic, single-site, fidelity-breaking**
mutation — chosen by a fixed ordered rule list over the Python AST, first
matching rule wins, the fired rule recorded per row:

1. first `Sub` → `Add`
2. first `np.mean(` call → `np.sum(`
3. first `Div` → `Mult`
4. first `Pow` with a literal exponent 2 → 3
5. first `np.sqrt(` call → `np.square(`
6. first numeric literal `c ∉ {0, 1}` → `2*c`

No model writes a mutation: a model-generated corruption is another model's
opinion, and the point of this channel is that the ground truth is mechanical.
Rows where no rule fires are skipped and counted. The mutant is re-emitted with
`ast.unparse` and shown to the judge exactly as any other code — no marker.

Both the original and the mutant are adjudicated.

- **Paired flip rate** = among pairs where the **original** was called CORRECT,
  the fraction whose **mutant** was called INCORRECT. Conditioning on the
  original removes the confound that an original may genuinely be unfaithful,
  which a raw "mutants caught" number cannot.
- **Pre-registered bar: paired flip rate ≥ 0.60.** A single-site edit that
  contradicts the paper's own equation is the easiest fidelity error there is;
  an instrument below 0.60 there cannot be trusted on the subtle ones.
- The raw mutant-caught rate and the originals-passed rate are both reported.
  The latter is **not** barred: it is confounded with the population's real
  error rate, which is the thing being measured.

### AMENDMENTS, 2026-09-11 — both made BEFORE the first model call

Everything below was found by running the evidence builder with `--dry-run`,
which calls no model. Nothing here was chosen after seeing a verdict.

**AMENDMENT 1 — V-B draws 200, not 60.** Two deterministic measurements, free:

- **Every one of the 2,831 served code samples parses as valid Python** (0
  unparseable). That is worth recording on its own: it is the first thing an
  audit of generated code should be able to say, and it is now said.
- **13.6% (385 / 2,831) contain no site any of the six rules can edit**, so a
  draw of 60 yields 48 pairs, and the flip rate is computed only on the subset
  whose *original* was called CORRECT — which could leave ~25 usable pairs.
  A bar measured on 25 rows is not a bar. Drawing 200 yields ~173 pairs at the
  measured skip rate, and costs ~$3 of a $50 budget.

Rule coverage over the whole frame, recorded now so the mutation mix is not a
surprise later: `sub_to_add` 1,795 · `div_to_mult` 386 · `mean_to_sum` 129 ·
`scale_const` 91 · `sqrt_to_square` 28 · `pow2_to_pow3` 17. The channel leans
heavily on sign inversion; the flip rate is therefore also reported **by rule**,
because "the instrument sees a flipped sign" and "the instrument sees a fidelity
defect" are not the same claim.

**AMENDMENT 2 — both halves of a mutation pair are re-emitted through
`ast.unparse`, not just the mutant.** Showing a raw original beside an unparsed
mutant hands the judge a tell: `ast.unparse` drops every `#` comment and
normalises quoting, so *which of these two was edited* becomes answerable from
formatting alone. The flip rate would then measure the judge's eye for
reformatting, not its eye for fidelity. Both halves are now unparsed, so the
only difference within a pair is the mutation. This makes the mutation channel's
code presentation differ from the audit channel's (which shows the code exactly
as served); that is correct, because V-B is a **within-pair** comparison and the
audit is not.

**AMENDMENT 3 — `clears_bar` is evaluated on the PRIMARY, and §7 did not say
so.** A real gap, closed before the validation run and before any bar was
measured: the bars in V-A and V-B are computed per model, and §7 said "all four
clear" without naming whose. It is the pre-registered primary, **Mistral Large
3**, whose bars decide `instrument_validation.clears_bar` — chosen in advance
precisely so it cannot be chosen afterwards to flatter. The secondary's
validation is reported in full beside it, and **if the primary fails its bars
while the secondary clears them, that is a finding to report, not a licence to
swap them and quote the secondary's rate as the headline.**

### Smoke run, 6 rows, seed 999, $0.07 — recorded, and nothing changed in response

`rows_smoke_seed999.jsonl` / `audit_smoke_seed999.json`. Run before the real
draw, on a throwaway seed, to catch mechanical defects the way
`<INTERNAL>/38`'s smoke run did. Mechanically the instrument is sound: 12/12
calls returned parseable JSON, zero call errors, every row had body text.

What it found instead is about the adjudicators, and it is recorded here
**before** the validation channels run so that nothing below can be read as
chosen after the fact:

- **The two families disagreed on 4 of 6 rows.** Mistral answered CORRECT
  6/6. DeepSeek answered CORRECT 2/6 — `fidelity_flag` ×2, `hard_error` ×1,
  `not_in_paper` ×1.
- On `2010.13160` / `most_sim` (Neuron Merging) DeepSeek quoted the paper —
  *"We set the scale value as an l₂-norm ratio of the two neurons"* — against a
  code path computing a projection coefficient, while Mistral answered CORRECT
  with a generic *"correctly implements … as specified in the paper's Algorithm
  2."* Specific-and-checkable against generic-and-approving, on the same
  evidence.
- Mistral set `is_defining: true` on 6 of 6, so that field may be degenerate for
  it.
- On one row Mistral's `evidence_quote`, required to be verbatim **from the
  paper**, was copied out of a comment in the **code**.

**No change was made to the prompt, the evidence bundle, the primary, or any
bar.** Measuring which of those two families is right is exactly what §7's
channels exist for, and re-tuning the instrument against a 6-row impression of
the answer is how an audit becomes a way of producing the number you expected.
The smoke rows are on seed 999 and enter no reported rate.

### The verdict this produces

`instrument_validation.clears_bar` — the field `qc_accuracy_ledger.py` reads —
is **true only if V-A (a) AND (b) AND (c) AND V-B's paired flip rate all
clear**. If any bar fails:

> the report **says the rate is unsafe rather than quoting it as an accuracy**,
> the ledger record is still written with the measured sensitivity leading its
> `method` string, and `clears_bar` is `false` — so the gate renders it as a
> blind instrument rather than as a clean stratum. A bound from an unmeasured
> lens must be labelled as one, not left as an implied clean result.

## 8. Cost

$50 with a binding 10% slush ($55 hard stop). Projection **reported before any
spend past $25, and the run stops rather than exceeding the cap.**

Projected from real prompt lengths in a `--dry-run` pass before the first call:
~400 audit rows + 22 validation rows + 120 mutation-pair rows ≈ **542
adjudications × 2 families ≈ 1,084 calls**, at ~10k input / ~450 output tokens,
priced by `bedrock_client.dollar_cost` (Mistral $0.50/$1.50 per 1M; DeepSeek
priced at DeepSeek-R1's $1.35/$5.40 as a deliberate **upper bound**; ×1.10
regional surcharge) → **≈ $13**. Actuals from `InvocationStats` are recorded per
run and reported.

## 9. What this lane writes, and what it does not

- **No Neo4j writes.** Read-only, per the operating contract. Every artifact is
  stamped via `provenance.write_json` / `write_sidecar` (R1), exclusions counted
  and enforced (R3), and the run is registered through `joblog.sh` (R6).
- **`accuracy_ledger.json` gains a `HAS_REFERENCE_IMPL/llm-generated` stratum
  record** in the format `qc_accuracy_ledger.py` already reads — including
  `instrument_validation` and, if a correction is warranted,
  `sensitivity_corrected`. The record is written **whether or not the instrument
  clears its bar**, for `<INTERNAL>/38`'s reason: a weak audit that is invisible
  is worse than one that is labelled. Registering it means the gate will judge
  it, and if the bound is below 0.80 the suite goes red — that is the gate
  working, not breakage.
- **No change to `qc_accuracy_ledger.py`**, its thresholds, its record format,
  or the instrument-state logic a lane added to it today. Its `SERVED_RELTYPES`
  omits `HAS_REFERENCE_IMPL`, which is a real gap and is **reported as a finding
  with the one-line change proposed**, not made here.
- **`spec_review_ledger.json` is not edited.** Rows the adjudicator calls
  `hard_error` or `not_the_method` are emitted to a separate
  `spec_review_proposals.json` in that file's own shape — an LLM's nomination
  for a human-reviewed ledger is a queue entry, not a verdict. Per R4 the
  proposal file names its consumer: the owner's review, and the report says so
  out loud rather than leaving a queue nothing reads.
