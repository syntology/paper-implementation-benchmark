# The licence question -- answered

**Decided 2026-09-13 by the owner: a single Apache-2.0 licence over
everything in this repository.** `LICENSE` carries the full text, `NOTICE`
names the project, the year and what the grant does and does not cover, and
the short header is on every file authored for this repository.

The rest of this document is what the decision was made from. It is kept
rather than deleted, because a licence choice that leaves no record of what was
weighed is indistinguishable from a default -- and because two of the three
questions below have answers that outlive the choice.

## What was decided, question by question

**Q1 -- one licence or a split: ONE.** A single Apache-2.0 grant covers the
code, the pre-registrations and results prose, the task metadata, the run
metadata and redacted transcripts, the analyses, the audit rows, and rows 5
and 6 -- the 72 property suites and the 144 generated implementations.
Licensing prose as if it were software is unusual and harmless; a split would
have required adjudicating which of rows 4-7 are "data", and every boundary
drawn there is a place a user has to stop and ask permission. Apache-2.0 over
Apache-2.0, no seams.

Apache rather than MIT for the reason Q1 named: the express patent grant and
the retaliation clause. This repository implements 72 published methods. Neither
licence changes what the papers' authors hold, but Apache-2.0 does settle what
Syntology grants over its own contribution, and a benchmark whose whole
proposition is that people should re-run it should not leave that ambiguous.

**Q2 -- can Syntology license LLM-generated code: it grants what it holds,
and says so.** Rows 5 and 6 ship. (Their counts in the table below were wrong
when this document was first written and are corrected in place: there are
**72** distinct tasks, so 72 property suites and 144 generated implementations,
not 96 and 192. The "96" was a count of task *rows* across two task files whose
24 freeze ids are a subset of the substitution set's 72 --
`tools/verify_claims.py` checks the real counts now, because a number that
drifted into a licence document is exactly the kind this repository exists to
catch.) `NOTICE` states plainly that the grant
cannot convey rights Syntology does not have, names the two producing models
(Claude Sonnet 4.5 for the property suites and `impl_sonnet.py`, Llama 3.3 70B
for `impl_llama.py`) and records that each provider's terms govern its own
output. Where the output is not copyrightable the grant is a no-op that removes
doubt for a user; where it is, the grant is real.

`impl_llama.py` is **kept**, not dropped. It is the artifact the graph arm
actually served, so removing it would remove the evidence for the one table
where the graph arm won, and the cheap fallback in Q2.2 was only ever cheap
because nothing in the reproduction path reads it -- which is also why nothing
is gained by exercising it. **The fallback stays available and is one commit:
delete `referees/*/impl_llama.py`, remove its entry from the referee index
builder in `tools/assemble.py`, and record the exclusion in
`ASSEMBLY_REPORT.md`. Counsel's answer on the Llama community licence has not
been sought and is not what this decision waits on; if it comes back negative,
that commit is the response.**

**Q3 -- attribution to the papers: machine-readable, and the wording stands.**
`referees/INDEX.json` lists every task with its arXiv id, paper title, method
and entry point, and `NOTICE` points at it. The per-sample attribution string
the tools return -- *"Reference implementation attributed to arXiv:<id>;
reference code, not audited production code"* -- is kept unchanged, because it
is accurate and it is what the live product says.

## What this decision still does not settle

Both carried over from below, unchanged:

1. **It says nothing about a future corpus release.** A licence-filtered flat
   index would carry each row's own upstream licence and its own attribution
   surface (`data/corpus/CORPUS_MANIFEST.md`). Apache-2.0 here does not reach
   it.
2. **It says nothing about the graph.** No snapshot is in this repository and
   publishing one is its own decision.

---

*Everything below is the document as it stood before the decision, unedited
except for this heading. It is the record of what the choice was made from.*

# The original question -- for the owner, as written 2026-09-11

**There is deliberately no `LICENSE` file in this repository.** Choosing one is
the owner's decision. This document exists so that decision can be made from
facts rather than from a default, and it does not recommend one.

Until a licence is chosen, this tree is **all rights reserved** — which for a
public repository is a real position, not a placeholder: nobody may copy,
modify or redistribute it, which for a benchmark meant to be re-run by other
people is probably not what is intended.

---

## The good news first: the hard part is already excluded

The single thing most likely to make a public benchmark repository a liability
is third-party source code shipped under an unclear licence. **There is none in
this tree**, and that was checked rather than assumed:

- **No harvested code.** `tools/corpus_license_report.py` report C confirms all
  96 task rows -- 72 distinct reference implementations -- are LLM-generated
  from paper text, not taken from anyone's repository.
- **The flat index is not here.** 115,574 of its 118,400 rows were harvested
  from public GitHub repositories and **71.0% of those carry no licence we can
  rely on** — 61.6% from repositories with no LICENSE file at all.
- **Raw transcripts are not here.** 29 harvested samples were pulled into them
  in full; 22 of the 29 are in that same unlicensable bucket.
- `tools/scan_secrets.py` finds no credentials, internal hostnames, developer
  paths or bulk-corpus files in the tree, and its `--self-test` proves the
  detector fires.

So the question below is only about **material Syntology produced**. That is a
much smaller and more tractable question than it would otherwise be.

---

## What would be licensed

| # | material | count | what it is |
|---|---|---|---|
| 1 | the harness, four arm modules, referee, analyzers, builders, probes, gates, tools | ~30 files | written by Syntology |
| 2 | vendored shared modules (`src/vendor/`) | 10 files | written by Syntology; `query_engine/` is a stand-in written for this repo |
| 3 | pre-registrations and results documents | 13 files | written by Syntology |
| 4 | task metadata — method name, arXiv id, paper title, entry name, signature, first sentence | 72 tasks | factual metadata plus one sentence of our own paraphrase per task |
| 5 | **property test suites** (`referees/*/property_tests.py`) | 72 files | drafted by Claude Sonnet from each paper's algorithm description |
| 6 | **generated implementations** (`referees/*/impl_sonnet.py`, `impl_llama.py`) | 144 files | generated by Claude Sonnet and by Llama 3.3 70B, from paper text |
| 7 | run metadata, referee outcomes, analyses, probes | ~495 files | derived data produced by (1) |

Rows 5 and 6 are the ones that need thought. Everything else is ordinary
first-party work product.

---

## The three questions that need answers

### Q1. One licence, or a code/data/prose split?

Most benchmark repositories do one of two things:

- **A single permissive licence over everything** (MIT or Apache-2.0). Simplest
  to state and to comply with; also licenses the pre-registrations and results
  prose as if they were software, which is unusual but harmless.
- **A split**: code under MIT or Apache-2.0, data and documents under CC-BY-4.0
  or CC0-1.0. More precise, more to explain, and requires deciding which of
  rows 4–7 count as "data".

**Apache-2.0 vs MIT matters in one specific way**: Apache-2.0 carries an express
patent grant and a patent-retaliation clause; MIT carries neither. If any method
implemented in `referees/` is plausibly patented by its authors, neither licence
changes their rights — but Apache-2.0 does change ours over anything we
contributed. This is a strategy question, not a correctness one.

### Q2. Can Syntology license LLM-generated code at all — and do the model providers' terms allow it?

This is the question that genuinely needs an answer before publishing, and it is
legal rather than engineering. Three parts:

1. **Is there copyright to grant?** Output produced without human authorship may
   not attract copyright in the US at all. If rows 5 and 6 are not copyrightable,
   a permissive grant over them is at worst a no-op and at best removes doubt
   for a user. It is *not* a reason to skip the question, because the answer
   differs by jurisdiction.
2. **Do the providers' terms permit redistributing output this way?** The
   implementations were generated through AWS Bedrock using Anthropic's Claude
   Sonnet 4.5 and Meta's Llama 3.3 70B. Each provider's terms govern what may be
   done with output. **Llama's community licence in particular carries naming
   and attribution conditions on derivative materials**, and 72 of the 144
   generated files came from Llama. Whether shipping them in a public repository
   under an unrelated licence is compatible with those conditions is a question
   for counsel, and it has a cheap fallback: **drop `impl_llama.py` from the
   repository.** Its role here is evidential — it is the artifact the graph arm
   served — not functional. Nothing in the reproduction path reads it.
3. **Are they derivative works of the papers?** They implement algorithms
   described in published papers. Algorithms are not copyrightable; particular
   expression is. These were drafted from a restatement of the algorithm rather
   than copied from an implementation, which is the position a benchmark wants
   to be in — but it is worth stating in whatever notice ships.

### Q3. What attribution does the repository owe the papers?

Every task names an arXiv paper by id and title and describes one of its
methods. That is citation, not licensed reuse, and citation is what the
material already does. Two choices remain:

- a `NOTICE` or `CITATION.cff` listing the 72 papers so attribution is
  machine-readable and complete rather than scattered across task files; and
- whether the per-sample attribution string the tools return — *"Reference
  implementation attributed to arXiv:<id>; reference code, not audited
  production code"* — is the wording to keep. It is accurate and it is already
  what the live product says.

---

## Two things a licence choice should NOT be read as settling

1. **It says nothing about a future corpus release.** If a licence-filtered flat
   index is ever published, every row in it carries its upstream repository's
   own licence and needs per-file attribution. That is a separate decision with
   a separate compliance surface (`data/corpus/CORPUS_MANIFEST.md`), and
   whatever is chosen here should not be assumed to extend to it.
2. **It says nothing about the graph.** No graph snapshot is in this repository,
   and publishing one is its own decision.

## What this repository needs when a decision is made

- a `LICENSE` file at the root;
- one paragraph in `README.md` stating the choice and the split, if any;
- if rows 5–6 are treated differently from rows 1–3, a note in
  `referees/INDEX.json` saying so, since that file is what a tool reads;
- if `impl_llama.py` is dropped under Q2.2, a line in `ASSEMBLY_REPORT.md`
  recording the exclusion and the reason, and the `PORTABILITY_PATCHES.md`
  entry for it removed from `tools/assemble.py`.
