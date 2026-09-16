# Can an agent implement a method from its paper?

A pre-registered benchmark that asks one question — *given a paper's method
name, entry point and one sentence of description, can a coding agent produce a
working implementation?* — and varies **only what retrieval the agent is given**.

Four arms, identical prompt, identical budgets, identical held-out referee:

| arm | what the agent gets |
|---|---|
| `none` | a Python sandbox and nothing else |
| `search` | Semantic Scholar, arXiv, GitHub code search, file fetch |
| `syntology` | six tools over a knowledge graph of papers, methods and code |
| `code_only` | two tools over a **flat index** of the same code, with the graph removed |

It has been run four times, each time against a pre-registration written and
committed before any subject token was spent. The **kill criteria** are the
stopping rule in [`prereg/PREREGISTRATION_SUBSTITUTION.md`](prereg/PREREGISTRATION_SUBSTITUTION.md),
and they read cost alone — never a result. Total subject spend across all
four: **$75.88** — the sum of four per-run totals ($37.24 + $17.40 + $5.43 +
$15.81); the per-run figures are in `data/`, the addition is not shipped as a
command.

**Most** numbers here re-derive from `data/` — `tools/verify_claims.py` checks
67 of them and names 3 it cannot. Spend totals, the corpus census and the
mid-run overlap counts are **not** among them: they rest on a private graph and
a write ledger this repository does not ship. Corrected 2026-09-16 after an
outside reader pointed out that "every number" was false.

---

## Check it yourself — 15 seconds, no credentials, $0

```bash
python3 -m venv .venv && . .venv/bin/activate      # CPython 3.10+
pip install -r requirements.txt

python3 tools/smoke_referee.py     # the referee really runs here: 3 tasks, offline
python3 tools/verify_claims.py     # 67 checks re-derive every table below from data/
```

You should see `referee smoke: PASS` and
`71 checks passed, 0 failed, 4 figures not checkable here`. **Those four are
printed rather than passed over** — what genuinely cannot be checked outside
Syntology is named, not quietly skipped.

Using a coding agent? Hand it this:

> Read `REPRODUCTION.md` in this repository, run the credential-free
> verification, and tell me which claims it could **not** check here and why.

Timings, the Debian/Ubuntu `python3-venv` caveat, and the paid arms are under
[Running it](#running-it); [`REPRODUCTION.md`](REPRODUCTION.md) is the full
answer, including [what cannot be re-run outside Syntology](#why-the-flat-index-is-not-in-this-repository).

---

## The headline is a null result about our own product

We built the graph. We built this benchmark to find out whether an agent given
it does better work. On this task family, it does not do better than an agent
given the same code with the graph stripped out.

**A flat BM25 + cosine index over 118,400 code samples — no method nodes, no
paper nodes, not one relationship traversed — matched the graph arm on every
single task.**

*The census file is dated packaging-time; the live graph is not checkable here.*

| v1.5, 2026-09-10 | in-catalog (18) | off-catalog (6) | overall |
|---|---|---|---|
| `none` (floor) | 8/18 | 2/6 | **10/24** |
| `syntology` (graph) | 18/18 | 6/6 | **24/24** |
| `code_only` (flat index) | **18/18** | **6/6** | **24/24** |

> **Read this table as dated.** The `syntology` arm reads a private graph that
> has changed since: `Method` is up **63%**, and **141,896 CITES were written
> while the run was executing**. Neither arm has been re-tested.
> [**GRAPH_STATE.md**](GRAPH_STATE.md) states the graph these numbers were
> measured against, the mid-run write, and which way it biases the null.

*Author measurement, not checkable in this repository:* the `Method +63%` growth and the tranche SIZE rest on the private graph. The 90 overlapping writes behind them now re-derive from [`data/run_window_ledger.json`](data/run_window_ledger.json); the graph's own state does not.

**Paired: +0 / −0 discordant tasks. Exact two-sided sign test p = 1.00.**
Same 6 median turns. All 24 flat-index fetches retrieved the exact sample the
graph serves — and that clause is now checkable here like the rest of the
table: `data/runs/**/transcript.json` ships each run **redacted**, with every
retrieved body replaced by a `sha256`/`bytes` digest and the structure kept, so
`src/analyze_code_only_mechanism.py` re-derives `data/mechanism_v15.json` from
the published tree byte for byte. `tools/verify_claims.py` runs that
re-derivation as one of its own checks.

Then we removed the answer from both arms and asked each for the next best
thing. Neither arm beat having no tools at all.

| v1.6, 2026-09-11, pre-registered n = 48 | passed | mean property fraction |
|---|---|---|
| `none` (no information tools) | **24/48** | 0.641 |
| `syntology_ho` (graph, answer held out) | **24/48** | 0.678 |
| `code_only_ho` (flat index, answer held out) | **23/48** | 0.663 |

Graph vs flat: **+6 / −5, p = 1.00**, Δ = +2.1% with 95% CI **[−11.5%, +15.6%]**;
Wilcoxon on the graded metric p = 0.89. `syntology_compose`, the one tool built
for exactly this situation, was called **zero** times — as it has been in every
run of every version of this benchmark.

Both nulls are reported here because they are the most credible thing the
repository contains. A benchmark whose authors have a product in one of the arms
is worth reading exactly to the extent that it can say the arm did not win.

**"Not measurable here" is not "not there."** See *What is NOT claimed*, below.

---

## What the benchmark did separate

The same instrument is not uniformly null. On the frozen v1 run, the graph arm
beat the web-search arm decisively:

| v1 freeze, 2026-09-02 | overall | in-catalog (18) | median turns | no submission |
|---|---|---|---|---|
| `none` | 13/24 | 11/18 | 5 | 0/24 |
| `search` | 11/24 | 10/18 | **20** (the cap) | **11/24** |
| `syntology` | **21/24** | **18/18** | **6** | 0/24 |
| `both` | **21/24** | **18/18** | 10 | 0/24 |

`syntology` vs `search`: **+10 / −0, p = 0.002.** The search agent ran out its
20-turn budget without submitting in nearly half its runs.

**Read that table with its asymmetry attached, which the pre-registration
disclosed before the run.** For in-catalog tasks the code the graph serves was
itself verified against this referee's own property suite at grant time, so
fetch-and-submit passes *by construction*. That asymmetry is the product
mechanism under test, not a flaw in the design — but it means the in-catalog
cells measure "does the agent find and fetch the artifact", not "can the agent
implement the method". The `none` floor and the off-catalog stratum are what
keep the row honest, and the v1.5 null above is what the comparison looks like
once a second arm gets the same artifact by a different route.

---

## What is NOT claimed

Read this section before quoting any number above.

**1. Neither null is a claim of equivalence.**
v1.5 is a *ceiling* tie — both arms scored 100%, and a saturated benchmark
cannot rank two conditions. With 0 discordant pairs in 24, the rule of three
puts the 95% upper bound on the graph's per-task advantage at **3 tasks in 24
(12.5%)**. It does not show zero. v1.6 is a mid-range tie with a measured
interval of **[−11.5%, +15.6%]**: it excludes a large effect and nothing
smaller. More tasks *of this shape* would not fix either: the n that matters is
a task family where an arm can still fail.

**2. No implementation in this repository carries a correctness claim.**
Each task ships two LLM-drafted implementations — `impl_sonnet.py` (used only to
revalidate that the property suite is satisfiable) and `impl_llama.py` (the
artifact the graph served to the `syntology` arm). Both were drafted from the
paper's algorithm description. **Neither is the paper authors' code**, and
neither is audited as faithful to the paper.

An audit of the population these come from — all 2,831 served
reference-implementation edges, pre-registered, n = 400 — put paper fidelity in
a **bracket of 0.29–0.80**, with *no adjudicator earning the right to narrow
it* (the permissive instrument's sensitivity measured 0.25 against a 0.50 bar, and
it caught only 18.6% of deliberately mutated code — a paired flip rate of
0.1862, so it approved roughly four mutants in five). **That audit is in this
repository**: its pre-registration, its adjudicator summaries and its 1,536
per-row verdicts are under `data/fidelity_audit/`, and
`tools/recompute_fidelity_bracket.py` re-derives every figure in this sentence
from them.

> **Corrected 2026-09-16, by an outside reader.** This sentence previously said
> the instrument "approved 83.8% of deliberately mutated code". 83.8% is
> 145/173 — the rate at which it correctly approved UNMUTATED originals, a
> different statistic pointing the other way. The mutant figure is the paired
> flip rate, 0.1862. The claim above it, that the tool re-derives every figure
> in the sentence, was therefore also false: the tool never emitted 83.8% as a
> mutant statistic, and running it would have shown that. It does now. What you cannot check here is whether any individual verdict is
right — the adjudicators read the served code and the paper body, neither of
which is published — and the audit's own primary finding is that on its own
evidence they largely are not. The audit's sharpest
finding is directly relevant here: **the V0–V3 verification ladder buys no
fidelity** — V2 scored 0.839 against V3's 0.772, the wrong way — because no rung
of it reads the paper. The characteristic failure is *generic code under a
specific name*: `brownian_bridge` served as "Brownian Interval". Nothing in this
repo is a verification badge, and the `verification_level` field the tools
return should be read as "what execution checks it passed", never as "this is
the paper's method".

**3. The referee is an LLM-drafted property suite, not ground truth.**
`referees/<task>/property_tests.py` was drafted from each paper's algorithm
description, and a run passes iff every property in that task's recorded
`pass_both` set passes. It is deterministic, local, blind to the arms, and
identical across every run — which is what makes the *comparisons* sound. It is
not a proof that a passing module implements the paper.

**4. The corpus is a product of the graph.**
The 118,400 code samples the flat index searches were harvested, generated,
verified and attributed by pipelines that read the graph. v1.5 tests whether the
graph is load-bearing **at query time**. It is not evidence that the graph could
be deleted.

**5. Proximity was never built, so it was never really tested.**
The offline probe in v1.6 found that `compose` — the graph's adjacency tool —
returns what fits *with* a routine, never what could stand *in for* it: its
partners overlap the flat index's substitutes on **1 of 72** tasks, and its
median typed-partner count is **0**. The serving surface has no substitution
affordance at all. v1.6 measured the absence of a feature as much as the value
of a graph.

**6. One subject model, one run per task × arm, one task shape.**
Claude Sonnet 4.5 on Bedrock throughout; single-routine reproduction tasks;
20-turn cap. Adoption behaviour in particular is known to move with tool
descriptions and framework — run 1 measured **0/24** graph-code fetches in the
`both` arm and the v1 freeze measured **18/24** with the same tools and
different server instructions.

**7. Run 1 carried a measured arm-purity leak.** `run_python` limited CPU and
memory but not network, and subjects exploited it (one graph-arm run
successfully `git clone`d the method's public repo). Fixed afterwards; v1.5
verified 0 of 72 transcripts show network use. Run 1's cross-arm deltas carry
the caveat; the conditional findings do not.

---

## Layout

If you are standing at the root wondering which files are load-bearing: the
four that answer *does this work* are `README.md`, `REPRODUCTION.md`,
`requirements.txt` and `tools/` — and the two commands in **Running it**,
below, exercise all of them. `MANIFEST.json` (322 KB) is a hash record for
machines, not reading. `ASSEMBLY_REPORT.md` is where the defects and the
exclusions are written down, `CLAIMS_TO_PREREG.md` maps each claim to the
pre-registration that predicted it, and `LICENSE_QUESTION.md` records a
decision rather than asking one. `llms.txt` is the same map for an agent.

```
prereg/     the pre-registrations, verbatim, as committed before each run
            PREREGISTRATION.md            run 1  (2026-08-31)
            FREEZE_RUN.md                 v1.4   (2026-09-02) - prereg + results
            PREREGISTRATION_CODE_ONLY.md  v1.5   (2026-09-10)
            PREREGISTRATION_SUBSTITUTION.md v1.6 (2026-09-10)
            ABLATION_V1{1,2,3}.md         the description/structure ablations
results/    the results documents, verbatim, with predictions scored
src/        the harness, the four arm modules, the referee, the analyzers
            src/vendor/  shared modules the harness imports
            src/qc/      the mechanical gate that proves the flat arm traverses
                         no relationship, no :Method and no :Paper
tasks/      the four task sets and the hold-out sets, with provenance stamps
referees/   per task: property_tests.py + the two LLM-drafted implementations
data/       per-run metadata, referee outcomes, analyses, probes, hold-out
            verification, and the corpus licence census
            data/runs/   per run: meta.json (structure) + transcript.json
                         (redacted — every retrieved body digested away)
            data/fidelity_audit/  the audit behind the 0.29–0.80 bracket:
                         pre-registration, summaries, 1,536 per-row verdicts
tools/      assemble.py            built this tree; --check re-verifies it
            scan_secrets.py        the publication gate, with a --self-test
            redact_transcripts.py  what made the transcripts publishable;
                                   self-tested, and it verifies its own output
            verify_claims.py       re-derives the 67 checkable numbers; names 3 it cannot
            recompute_fidelity_bracket.py  re-derives the 0.29–0.80 bracket
            smoke_referee.py       proves the referee runs here, offline, $0
            check_clean_clone.py   compile / import / declared-deps / manifest,
                                   self-tested; the gate for the defect in §4.9
            validate_schemas.py    the shipped artifacts against schemas/
            corpus_license_report.py *(author-only: needs Neo4j)*  the licence census behind the exclusions
schemas/    artifacts.schema.json  JSON Schema for the task, run-metadata,
                                   referee-verdict and manifest shapes —
                                   checked against every artifact in CI
.github/    workflows/ci.yml       every credential-free gate, fresh clone,
                                   CPython 3.10–3.14, Linux and macOS
llms.txt    the machine-oriented map of this repository
LICENSE     Apache-2.0, the full text
NOTICE      what the grant covers, and the two things it cannot
CITATION.cff   machine-readable citation metadata
CONTRIBUTING.md  what is in scope, and what an outsider cannot run
SECURITY.md    how to report, and what executing this tree actually does
MANIFEST.json  every file, its sha256, and the internal artifact it came from
```

## Running it

### Quickstart — no credentials, $0

```bash
git clone <this repository> && cd <repo>
python3 -m venv .venv && . .venv/bin/activate      # CPython 3.10+
pip install -r requirements.txt

python3 tools/smoke_referee.py     # the referee really runs here: 3 tasks, offline
python3 tools/verify_claims.py     # 67 checks re-derive every table above from data/
```

**Measured, not estimated: 15 seconds** end to end — 0.5 s clone, 3.1 s venv,
**8.1 s for a genuinely cold `pip install`** (empty pip cache, 37 MB of wheels
fetched), 2.2 s smoke, 0.8 s claims. Taken 2026-09-13 in a fresh
`python:3.12-slim` container with no pip cache and no network shaping; this
file used to say "about two minutes", which was a guess, and the cold install
is the only part that will move much on your machine — it is a 37 MB download,
so on a slow link budget for that rather than for the checks.

**On Debian or Ubuntu, `python3 -m venv` fails** until you install the venv
package — `sudo apt install python3-venv` (measured on `ubuntu:24.04`:
*"ensurepip is not available"*). Skipping the venv is not a way around it;
Ubuntu 24.04 then refuses `pip install` with `externally-managed-environment`
(PEP 668). The Docker `python:*` images and macOS need neither step.

You should see `referee smoke: PASS` and
`71 checks passed, 0 failed, 4 figures not checkable here`. That is the whole
claim of this repository in two commands: **the referee runs in your
environment, and the numbers `verify_claims` covers re-derive from the
artifacts in `data/`** — including the mechanism analysis, re-run over the
redacted transcripts, and the fidelity bracket, re-derived from the audit rows.
The three it prints as *not* checkable here are printed rather than passed over.

What it does **not** cover, and did not before this sentence was corrected:
subject spend, the corpus licence census, and the mid-run write counts in
`GRAPH_STATE.md`. Those depend on a private graph and on a write ledger that is
not published, so they are assertions here rather than derivations.

Three more, all offline, all $0:

```bash
python3 tools/check_clean_clone.py   # this clone compiles, imports, and matches MANIFEST.json
python3 tools/scan_secrets.py        # the publication gate: credentials, hosts, paths
python3 src/qc/qc_code_only_arm.py   # exits 4 — see below; that is it working
```

`qc_code_only_arm.py` exits **4**, not 0, and that is the answer: checks A and
B — *the flat arm traverses no relationship and reads no `:Method` or `:Paper`
node*, the claim the whole ablation rests on — pass here with no index and no
graph, while C and D report a partial because they need an index you would have
to build. Every exit code in this project means something: `0` clean, `1`
findings, `2` drift, `3` unaccepted exclusions, `4` unresolved partials. **An
exit 3 or 4 is a tool refusing to claim completeness, not a crash.**

Everything above runs on every push, on CPython 3.10 through 3.14, on Linux and
macOS, against a fresh clone: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
It exists because on 2026-09-13 this tree did **not** import from a clean clone
and nothing had ever checked — `ASSEMBLY_REPORT.md` §4.9.

### Then, if you have AWS Bedrock: the floor arm, end to end, for about a dime

```bash
export AWS_DEFAULT_REGION=us-west-2
python3 src/agent_harness.py --tasks tasks/tasks_freeze.json --arms none \
    --only off_2210.17323 --variant v14_freeze --out runs --workers 1
python3 src/verify_solutions.py --tasks tasks/tasks_freeze.json --runs runs \
    --out my_results.json
```

One task, one arm, a real subject model, scored by the published referee. When
this was last run from a clean clone it took 7 turns and 50 seconds, cost about
$0.09, and **failed 4 of 4 properties** — a behavioural result, not an
environment break, and the shape a reader should expect. `--variant
v14_freeze` pins the tool descriptions the freeze used; leaving it off changes
the experiment.

### The rest

**`REPRODUCTION.md` is the real answer** — including, in detail, what an
outsider cannot reproduce and why. The short version:

| arm | runs outside Syntology? |
|---|---|
| `none` | **yes** — needs only AWS Bedrock credentials and Python |
| `search` | **yes, with your own keys** — a GitHub token and a Semantic Scholar key. Note the results docs' caveat: this toolkit drifted after the v1 freeze and `arxiv.org` began refusing our requests, so the freeze is its last clean measurement |
| `code_only` | **only over a code corpus you supply.** Ours is not in this repository — see below |
| `syntology` | **no.** It reads a private Neo4j graph and imports serving code that is not published |

**What this repository needs and cannot provide: a private knowledge graph and
a 118,400-row code index it has no licence to republish — so the headline
comparison is re-derivable from `data/`, not re-runnable.**

To score your own agent's submissions against these tasks — offline, no
credentials, the same referee every arm was judged by:

```bash
python3 src/verify_solutions.py --tasks tasks/tasks_freeze.json --runs <your runs dir>
```

`REPRODUCTION.md` has the directory shape it expects. Results from a different
subject model are the single most interesting thing this repository does not
have.

### Why the flat index is not in this repository

The `code_only` arm searched 118,400 code samples, of which 115,574 were
harvested from public GitHub repositories. Measured (`data/corpus/license_census.json`):

| | count | share of harvested |
|---|---:|---:|
| no LICENSE file in the upstream repository | 71,236 | 61.6% |
| no licence recorded at all | 10,784 | 9.3% |
| **neither redistributable nor determinable** | **82,020** | **71.0%** |
| permissive, inline-redistributable (MIT/Apache-2.0/BSD/…) | 31,515 | 27.3% |
| copyleft or share-alike | 1,983 | 1.7% |

**Republishing that index would redistribute other people's source code, most
of it under no licence at all.** So it is excluded, and the arm is documented as
requiring a corpus you supply rather than shipped in a state that silently fails.
`src/build_code_index.py` builds one and `data/corpus/CORPUS_MANIFEST.md`
documents the record schema it needs. A licence-filtered index is *not* the same
instrument — a 34k-row haystack would not reproduce the measured result — and
that is stated rather than papered over.

**Raw** transcripts are excluded for the same reason: 29 harvested samples
were pulled into them in full, and **22 of the 29 carry no licence we can rely
on**. What ships instead is each run's structure — every tool call by name,
turns, tokens, wall time, stop reason — in `meta.json`, plus a **redacted
transcript** beside it in which every retrieved body, every assistant message
and the subject's own submitted code have become
`<redacted body sha256=… bytes=…>`. `tools/redact_transcripts.py` did that,
default-deny on a key allow-list, with a self-test that plants a body in every
place a body can ride and requires that not one line of it survives.

---

## Licence

**Apache-2.0, one licence over everything here** — decided 2026-09-13. `LICENSE`
is the full text; `NOTICE` names the project and the year and states what the
grant covers and what it cannot. There is no code/data split: the harness, the
pre-registrations and results prose, the task metadata, the run metadata and
redacted transcripts, the analyses and audit rows, and the 72 property suites
and 144 generated implementations in `referees/` are all under the same grant.
`LICENSE_QUESTION.md` records the decision, what was weighed, and the two
things it deliberately does **not** settle — a future corpus release, and any
graph snapshot.

Two things a permissive licence should not be read as: it is not a claim that
anything here is correct (see *What is NOT claimed*), and it cannot convey
rights Syntology does not hold — `NOTICE` names the models that produced the
generated implementations and says that each provider's terms govern its own
output.

## Citing it

`CITATION.cff` carries the citation metadata, validated on every push —
GitHub renders it as *Cite this repository*, and `cffconvert -f bibtex` gives
you the BibTeX. There is **no DOI**; `CONTRIBUTING.md` says what taking one
would involve and why it is the owner's call. If you cite a number, cite the
run it belongs to (v1, v1.4 freeze, v1.5, v1.6) — they are different
experiments against different pre-registrations.

## Provenance

`tools/assemble.py` built this tree from internal artifacts and `MANIFEST.json`
records the sha256 and origin of every one of its 1,275 files (2026-09-16;
`python3 -c "import json;print(len(json.load(open('MANIFEST.json'))['files']))"`,
and the manifest cannot record its own hash, which is the 1,273rd);
`tools/assemble.py --check` re-verifies the tree against that recorded manifest
rather than recomputing both sides. `tools/verify_claims.py` re-derives every
mechanically checkable number in this repository from `data/` — 67 checks,
including re-running the mechanism analyzer over the redacted transcripts and
the fidelity recompute over the audit rows — and prints the three things that
still rest on evidence not published here rather than letting them read as
checked. `tools/smoke_referee.py` proves the referee runs
in your environment before you spend anything. `tools/scan_secrets.py` gates the tree against credentials,
internal hostnames, developer paths and bulk third-party code, and carries a
`--self-test` that plants one instance of each class and requires a hit — a
scanner never observed failing is not a verified scanner. `ASSEMBLY_REPORT.md`
records what was scanned, what was found, and everything that was deliberately
left out.
