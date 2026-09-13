# Reproduction

This document is deliberately more interested in what you **cannot** reproduce
than in what you can. A benchmark repository whose instructions only work for
its authors is a demo; naming the boundary is what makes the rest credible.

**Every command below was executed from a fresh `git clone` of this repository
on 2026-09-13, in a new virtualenv, before this version was written.** That
mattered more than expected. A reproduction document nobody has run is a claim,
not an instrument, and running this one found six things wrong with it:

| what broke | fix |
|---|---|
| **13 of the 18 modules in `src/` would not import** — the referee among them, and all four analyzers this document tells you to run | a listed portability patch puts `src/vendor/` on the path; `tools/assemble.py` now imports every shipped module and refuses to package a tree that fails |
| `requirements.txt` omitted `requests`, so **no arm would start**, not even the credential-free floor | declared, and the assembler now refuses on any undeclared unguarded third-party import |
| `analyze.py` was documented with a `--tasks` flag it does not accept | command corrected |
| `compare_runs.py` was documented without its two required `--*-runs` arguments, and resolved relative paths against `src/` | command corrected; path resolution is a listed portability patch |
| `analyze_substitution.py` was documented as runnable without a graph; it is not, at all | stated plainly below |
| `tools/redact_transcripts.py --verify` defaulted to a directory that does not exist in the shipped tree | default corrected to `data/runs` |

Five of the six were invisible from inside the working repository, which is
where every previous check had been run. That is now mechanical rather than
remembered: `tools/check_clean_clone.py` asks whether this tree compiles,
imports, declares its dependencies and matches `MANIFEST.json`, and
`.github/workflows/ci.yml` runs it — and every other credential-free gate here
— against a **fresh clone**, on five interpreters, on every push.

## The short version

| what | reproducible by you? |
|---|---|
| **the referee** — score any submission against any task | **yes, offline, no credentials, $0** |
| **the analyses** — every table in `results/` from `data/` | **yes, offline, $0** |
| **the `none` arm** — re-run the floor end to end | **yes**, with your own AWS Bedrock access |
| **the `search` arm** | **yes**, with your own GitHub and Semantic Scholar keys — but see the drift caveat |
| **the `code_only` arm** | **only over a code corpus you supply.** Ours is not published |
| **the `syntology` arm** | **no.** It reads a private graph through unpublished serving code |

Everything in `data/` came from runs you cannot repeat against the same
backends. That is why the run metadata, the **redacted transcripts**, referee
outcomes, probe outputs, hold-out verification and the fidelity audit's rows
are all here: **the numbers are auditable even where the runs are not
repeatable.**

## Install

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

**Python 3.10+, measured rather than assumed.** The runs used 3.14 and this
file's transcript was produced on 3.14.6, but every credential-free check in
this document is run on CPython 3.10, 3.11, 3.12, 3.13 and 3.14, on Linux and
macOS, against a fresh clone, on every push: `.github/workflows/ci.yml`.

This file said "3.11+" until the floor was actually measured, and the truth is
more useful than the guess. On **CPython 3.9** — still the system Python on
macOS, and what the first outside reader to clone this happened to run — the
referee path works completely: `smoke_referee.py`, `verify_claims.py` and
`recompute_fidelity_bracket.py` all pass. But **five modules do not import**,
`src/agent_harness.py` among them, because PEP 604 annotations (`str | None`)
are evaluated at module load. So on 3.9 you can score submissions all day and
then find that **no arm will start**. The `python-3-9-boundary` job in CI pins
both halves of that and turns red if either moves.

`numpy` is required by the referee; `boto3` and `botocore` by any arm
that calls a model; **`requests` by every arm**, because the outbound HTTP
gateway is a module-level import in the harness's import chain — it was missing
from `requirements.txt` until a clean clone tried the floor arm and died at
`ModuleNotFoundError: No module named 'requests'`, and `tools/assemble.py` now
refuses to package a tree with an undeclared unguarded import. `neo4j` only by
the two arms that read a graph; `scipy` only to sharpen one Wilcoxon p-value.

**This install was executed, not written from memory**: `python3 -m venv`,
`pip install -r requirements.txt`, on macOS with CPython 3.14.6, into a fresh
`git clone` of this repository with nothing else on the path. Re-measured
2026-09-13 on Linux, from a clone of a **bare** clone — which is the shape a
remote actually has — in a container with an empty pip cache: 0.5 s to clone,
3.1 s for the venv, **8.1 s for the cold `pip install`** (37 MB of wheels),
2.2 s for the smoke test, 0.8 s for `verify_claims.py`. Fifteen seconds, not
the two minutes this file used to guess.

**Two things that will stop you before any of that, neither of them ours:**

- **Debian/Ubuntu ships `venv` separately.** `python3 -m venv .venv` prints
  *"ensurepip is not available"* and creates nothing until you
  `sudo apt install python3-venv` (measured on `ubuntu:24.04`, system CPython
  3.12.3). Skipping the venv does not help: pip then refuses with
  `error: externally-managed-environment` (PEP 668). The `python:*` Docker
  images and macOS need neither step.
- **An old `pip` is fine.** Measured on the 3.10 floor: the stock pip 23.0.1
  installs cleanly, and so does a deliberately ancient pip 21.3.1 with
  setuptools 58.0.4 — every requirement resolves from wheels, nothing here
  builds from source. You will get a nag about upgrading pip and nothing else.

**Line endings, if you are on Windows.** `.gitattributes` pins `eol=lf`,
because every file here is hashed in `MANIFEST.json` and
`tools/check_clean_clone.py` compares your checkout byte for byte. Before that
file existed, a `git -c core.autocrlf=true clone` — the Git-for-Windows
installer default — produced **1,272 findings** on an otherwise perfect clone
while every other gate passed; the `crlf-checkout` job in CI now clones that
way on purpose and requires CLEAN, and proves the point by deleting
`.gitattributes` and requiring the failure back. If you somehow see it anyway,
the gate now names it as a line-ending conversion and tells you to re-clone
with `core.autocrlf=false` rather than reporting your download as corrupt.
**Whether the checks themselves pass on Windows is UNMEASURED** — there is no
Windows leg in CI, nothing here is obviously POSIX-only, and the activate line
above is the Unix one (`.venv\Scripts\activate` on Windows). Reports welcome.

## Check your install before spending anything

```bash
python3 tools/smoke_referee.py
```

Builds a throwaway run tree, submits each task's own `impl_sonnet.py`, and runs
the real referee over it. Three tasks, offline, no credentials, a few seconds.
A failure here means either this tree is broken or a property suite has stopped
being satisfiable in your numpy — both worth knowing before you buy tokens.

```bash
python3 tools/verify_claims.py              # 67 checks, offline, a few seconds
python3 tools/recompute_fidelity_bracket.py # the 0.29-0.80 bracket, from rows
python3 tools/check_clean_clone.py          # does THIS clone compile, import,
                                            # declare its deps, match MANIFEST?
python3 tools/check_clean_clone.py --self-test    # prove that gate can fire
python3 tools/scan_secrets.py               # anyone
python3 tools/scan_secrets.py --self-test   # prove it can fire
python3 tools/redact_transcripts.py --self-test   # prove the redactor can fire
python3 tools/redact_transcripts.py --verify      # check the shipped transcripts
python3 tools/validate_schemas.py           # artifacts vs schemas/ (needs
                                            # `pip install 'jsonschema>=4.18'`)

# authors only -- needs the working repo AND its internal directory names,
# which this repository deliberately does not carry:
python3 tools/assemble.py --check --source <repo> \
    --bench-dir <dir> --refimpl-dir <dir> --audit-dir <dir>
```

`verify_claims.py` is the one to run if you only run one. It re-derives the
published tables from `data/`, re-runs `src/analyze_code_only_mechanism.py`
over the redacted transcripts and compares the result to the published
`data/mechanism_v15.json`, re-derives the fidelity bracket from the audit rows,
and prints the three things that still are not checkable here instead of
letting them pass as checked.

## Running the referee on your own agent

This is the part most likely to be useful to you, and it needs nothing from us
beyond the task set. Produce a directory shaped like a sweep's output:

```
runs/<task_id>/<arm_name>/solution.py      the module your agent submitted
runs/<task_id>/<arm_name>/meta.json        {"task_id": ..., "arm": ..., "submitted": true}
```

then:

```bash
python3 src/verify_solutions.py \
    --tasks tasks/tasks_freeze.json \
    --runs  runs \
    --out   my_results.json

python3 src/analyze.py --results my_results.json --runs runs \
    --arms auto --out my_analysis.json
```

`--arms auto` matters: without it `analyze.py` uses the four arm names from
run 1, and a grid of your own arm prints empty rather than erroring. Both
commands above were run against a hand-built `runs/` tree from a fresh clone
of this repository before this paragraph was written.

**If you get the directory shape wrong, it now says so.** Measured 2026-09-13,
six ways of getting it wrong all printed `verified 0 runs (0 passed)` and
exited **0**: a `--runs` path that does not exist, an empty one,
`<arm>/<task>` instead of `<task>/<arm>`, a missing `meta.json`, a typo'd task
id, and — worst of the six — a submission named anything but `solution.py`,
which came back as `verified 1 runs (0 passed)` and reads as *your agent
failed* when nothing was ever loaded. `verify_solutions.py` refuses with
**exit 3** on all six now, prints what it examined and what it excluded, and
treats a `meta.json` claiming `submitted: true` beside no `solution.py` as a
malformed input rather than a failing run. `--allow-partial` accepts those
exclusions if an empty result is genuinely what you meant.

A run **passes** iff every property in the task's recorded `pass_both` set
passes, checked with `is True` — the strictness exists because an earlier
version of the sandbox stringified numpy booleans and every consumer read
`"False"` as passing. `suspect_tests` (properties the drafter is known to have
got wrong) are excluded from `pass_both` and ignored.

The prompt your agent should receive, if you want comparability with the arms
here, is in `src/agent_harness.py` (`SYSTEM` and `TASK_TMPL`). The subject is
given the method name, the paper, the entry function, its exact signature, and
**the first sentence of the spec only** — deriving the rest of the contract is
the work the tools exist for.

## Re-running an arm

```bash
export AWS_DEFAULT_REGION=us-west-2         # the sweeps' region; see FREEZE_RUN.md
python3 src/agent_harness.py \
    --tasks tasks/tasks_freeze.json \
    --arms none \
    --variant v14_freeze \
    --out runs --workers 2
```

`--variant v14_freeze` is what every run from the v1 freeze onward used: it
pins the tool descriptions and MCP server instructions to the versions
production shipped at the time. Leaving it off changes the prompt and therefore
the experiment.

Runs are resumable: a task × arm directory that already has `meta.json` is
skipped, so re-entering the command after an interruption continues rather than
repeating. On a Bedrock day cap the harness exits **4** and the whole sweep
stops — that is the exit-code contract working, not a crash.

`BENCH_PYTHON` pins the interpreter the subject's `run_python` tool uses
(default: the one running the harness). `BENCH_REPO_ROOT` overrides where the
harness looks for `tasks/`, `referees/` and `data/`.

### `none` — yes

Needs AWS Bedrock credentials with access to
`us.anthropic.claude-sonnet-4-5-20250929-v1:0`. Nothing else. This is the arm
that makes the benchmark meaningful to an outsider: it is the floor every other
arm is measured against, and the floor is high — 13/24 in the v1 freeze, 24/48
in the substitution run. A large part of what these tasks measure is what the
model already knows.

### `search` — yes, with your own keys, and read the caveat

`GITHUB_TOKEN` and `SEMANTIC_SCHOLAR_API_KEY` in your environment. The arm goes
out through `src/vendor/api_gateway.py`, which rate-limits per host and
identifies itself with a research-bot user agent.

The floor arm was re-run from a clean clone of this repository on 2026-09-13
as the last step of checking this document: one task, `off_2210.17323`,
`--variant v14_freeze`, 7 turns, submitted, 50 s, about $0.09 — and it
**failed 4 of 4 properties**. That is a behavioural result, not an environment
break, and it is the shape a reader should expect: the floor is high but it is
a floor.

**Caveat, from `results/RESULTS_CODE_ONLY.md`:** this toolkit changed three
times after the v1 freeze (a Semantic Scholar politeness gate, removal of a
spoofed user agent) and `arxiv.org` began returning 403 to our requests. The
freeze's numbers — 11/24, 20 median turns, 11/24 no-submissions — are the last
clean measurement of this arm, and it was deliberately **not** re-run in v1.5
or v1.6 because a re-run would have measured toolkit drift rather than the
arm. Your numbers will differ for reasons that have nothing to do with your
agent.

### `code_only` — only over a corpus you supply

This arm needs **two** things we do not ship:

1. **A flat index** — `lexicon.pkl`, `all_vectors.npy`, `all_shas.json`,
   `records.jsonl` — built by `src/build_code_index.py` and
   `src/build_code_vectors.py`. Point the arm at it with `CODE_ONLY_INDEX`.
2. **A Neo4j store of `:CodeSample` nodes.** `code_search` ranks from the
   index, but `code_get` is a single-node Cypher lookup that returns the
   source, the verification report and the test cases. The arm is *code-only*
   in the sense that it traverses no relationship and reads no `:Method` or
   `:Paper` node — `src/qc/qc_code_only_arm.py` checks that mechanically — not
   in the sense that it is database-free.

`data/corpus/CORPUS_MANIFEST.md` documents the node properties both builders
read, so you can load your own corpus and run the arm against it.

`src/qc/qc_code_only_arm.py` is the gate that makes the arm's central claim
mechanical rather than editorial. It runs here as shipped:

```
qc_code_only_arm: UNVERIFIED (exit 4) -- not a pass
  [PARTIAL] alignment: .../code_index/lexicon.pkl missing
```

**Check A (arm purity) and check B (tokenizer parity) pass in this tree** —
so the claim the whole ablation rests on, *this arm traverses no relationship
and reads no `:Method` or `:Paper` node*, is checkable by you right now, with
no index and no graph. Checks C (row alignment) and D (no unbacked level in the
index) need an index, and report as a **partial (exit 4)** until you build one
rather than as a failure. Plant a `-[` in the arm module and the gate exits 1
with a refusal; that is worth doing once, so you know it fires.

**Why ours is not here.** The index covered 118,400 samples, 115,574 of them
harvested from public GitHub repositories. 71.0% of those carry no licence we
can rely on (`data/corpus/license_census.json`). Republishing the index would
redistribute other people's source code, most of it under no licence at all.
A licence-filtered index would ship — about 34,000 rows — but it would be a
different instrument, and the measured result belongs to the 118,400-row
haystack, not to a third of it.

### `syntology` — no

`src/syntology_arm_tools.py` is here so you can read exactly what the graph arm
was given: the six tools, their production descriptions, the resolver ladder,
the refusal behaviour, the Cypher. It will not run. It reads a private Neo4j
graph and imports `query_engine`, Syntology's production serving package, which
is not published; `src/vendor/query_engine/` is a stand-in that raises a
sentence explaining this rather than failing obscurely.

Publishing a graph snapshot is a separate decision from publishing this
benchmark, and it is not taken here.

## Reproducing the analyses from `data/`

Every table in `results/` comes from these, offline:

```bash
python3 src/analyze.py --results data/results_v14.json --runs data/runs/runs_v14 \
                       --out /tmp/a.json

python3 src/compare_runs.py \
    --a data/results.json     --a-runs data/runs/runs \
    --b data/results_v14.json --b-runs data/runs/runs_v14 \
    --tasks tasks/tasks_freeze.json --out /tmp/c.json

# v1.5 mechanism tables, from the redacted transcripts. Give it an --out:
# the default writes over the published data/mechanism_v15.json in place.
python3 src/analyze_code_only_mechanism.py --out /tmp/mech.json
```

**Every command in this block was run from a fresh clone before it was written
here, and four of the five that used to be in it did not work.** `analyze.py`
had a `--tasks` flag it does not accept; `compare_runs.py` was missing its two
required `--a-runs`/`--b-runs` arguments *and* resolved relative result paths
against `src/` rather than the repository root (fixed by a listed portability
patch); `analyze_code_only_mechanism.py` silently overwrote a published
artifact; and `analyze_substitution.py` does not belong in this list at all —
see below.

Two honest caveats about re-running the analyzers here:

- `analyze.py` and `compare_runs.py` recompute cost from token counts using
  on-demand us-east-1 Sonnet 4.5 pricing hard-coded in `analyze.py` as of
  2026-08. If prices have moved, your dollar figures will differ from the
  published ones while every token, turn and wall figure stays identical.
  **Costs across run 1 and the v1 freeze are not comparable anyway**: prompt
  caching was added between them, so run 1's costs are uncached. Turns and wall
  time are the comparable efficiency measures.
- **`analyze_substitution.py` cannot be run here at all**, and an earlier
  version of this document was wrong to imply otherwise. It opens a Neo4j
  session at the top of `main()` for the hold-out leak audit, before any table
  is computed, so without `NEO4J_URI` it exits with `KeyError: 'NEO4J_URI'` and
  nothing downstream runs. The published `data/analysis_substitution.json`
  carries the full output, and `tools/verify_claims.py` re-derives its
  substitute-origin figure from the redacted transcripts without touching a
  graph.
- The analyzers that mine transcripts read the **redacted** ones in
  `data/runs/`, and that is enough: `analyze_code_only_mechanism.py` re-derives
  `data/mechanism_v15.json` from them byte for byte, including the "24/24
  fetches were the correct sample" cell and the 90/90 conditional.
  `analyze_substitution.py`'s substitute-origin tally re-derives too (147 over
  all 49 runs, 143 over the pre-registered 48 — the figure
  `RESULTS_SUBSTITUTION.md` quotes). What the redaction costs is the *content*:
  you can see that a body of N bytes with sha256 X was fetched from origin Y,
  and not what was in it.

## What `data/runs/` contains, and what it does not

Two files per run. `meta.json`: arm, task, stratum, model id, variant, every
tool call **by name and argument size**, turns, token usage, wall time, stop
reason, Bedrock retry/throttle counts, the hold-out sha set the run was denied,
and a provenance stamp naming the exact command.

And `transcript.json`, **redacted**. Message order and roles, every tool call
with its structural arguments, and the structural fields of every tool result:
shas, entry names, `matched_by` routes, verification levels, counts, ratings,
statuses. Every string that could carry something retrieved — source bodies,
verification reports, test cases, fetched files and web pages, paper abstracts,
OpenReview review prose, the subject's own `run_python` and `submit_solution`
code, `stdout`/`stderr`, and every assistant message — is replaced by

```
<redacted body sha256=<64 hex> bytes=<n> field=<path> origin=<id|->>
```

The rule is **default-deny**: `tools/redact_transcripts.py` keeps only key
names on an explicit allow-list, and caps even those, so a tool that grows a
new field leaks nothing until someone adds it deliberately. Its `--self-test`
plants a body in every place a body can ride and requires that not one line
survives; `--verify` re-checks the shipped tree.

**What this still costs.** Submitted solutions are not published in any form —
in the substitution arms 28 of 48 share half their identifiers with a fetched
substitute, some of which are in the unlicensable bucket. And the redaction is
one-way: a digest proves *that* a body of a given size and hash was fetched,
never what it said. Anything that would need the text itself — re-running the
identifier-overlap measurement, or auditing what an agent read — remains
outside this repository. That is a licence decision, not a completeness one.

## Known gaps, listed so nobody has to discover them

- **Raw transcripts are not published.** The redacted ones are, and they carry
  enough to re-derive `data/mechanism_v15.json` exactly; what they cannot
  support is any measurement over the *text* the agent read or wrote — the
  identifier-overlap figures in `RESULTS_SUBSTITUTION.md` among them.
- **Submitted solutions are not published at all**, in any form.
- **The `syntology`/`syntology_ho` arms cannot be executed** by anyone outside
  Syntology.
- **The `code_only` arm cannot be executed** without a corpus and a graph store
  you provide.
- **The task builders** (`src/build_task_set*.py`, `src/build_holdout_sets.py`)
  read the Syntology graph and a stage-13 verification ledger. They are here as
  the record of how the task set was drawn, not as something you can re-run.
- **One subject model.** Nothing here tells you how a different model, or a
  different agent framework, behaves — and run 1 versus the v1 freeze showed
  adoption of the *same* tools moving from 0/24 to 18/24 on prompt changes
  alone.
