# Assembly report

What was scanned, what was found, what was left out, and what still is not
right. Written at packaging time 2026-09-11; revised 2026-09-13 when the tree
was prepared for its own public repository, which closed three of the items in
section 4 and added one that nobody had found.

**2026-09-13 in one paragraph.** Apache-2.0 was chosen and applied
(`LICENSE`, `NOTICE`, headers on authored files; `LICENSE_QUESTION.md` records
the decision). The internal directory names that survived path redaction are
gone, with a gate that refuses on them. Redacted transcripts now ship, and the
mechanism tables re-derive from them byte for byte. The fidelity audit's rows
ship, and the 0.29-0.80 bracket recomputes from them. And a clean-clone check
found that **13 of the 18 modules in `src/` could not import at all** in the
published tree -- including all four analyzers `REPRODUCTION.md` tells a reader
to run. Fixed, and gated.

Everything below is re-derivable: `tools/assemble.py` built the tree,
`tools/scan_secrets.py` gated it, `tools/corpus_license_report.py` measured the
licence position, `tools/verify_claims.py` re-derived the numbers, and
`tools/smoke_referee.py` proved the referee runs here.

---

## 1. Secret scan

`tools/scan_secrets.py`, run over the whole tree.

**Scanned for, in six classes:**

| class | patterns |
|---|---|
| KEY | AWS access key ids (`AKIA`/`ASIA`), AWS secret-access-key assignments, GitHub PATs (`gh[pousr]_`), Semantic Scholar keys (`s2k-`), Slack tokens, Stripe keys, PEM private-key headers, JWTs, `Bearer <token>` literals, `NEO4J_PASSWORD`/`NEO4J_AUTH` literals, and any `password`/`secret`/`api_key`/`access_token`/`client_secret` assigned a 12+ character literal |
| HOST | Neo4j and Aura connection URIs (the `neo4j`, `neo4j+s` and `bolt` schemes), App Runner endpoints, ECR/ELB/API-Gateway/RDS/S3/Lambda AWS endpoints, ARNs carrying a 12-digit account id, RFC-1918 private IPs, a `localhost` address with a port, Cloudflare account ids |
| PATH | `/Users/<name>/`, `/Volumes/<name>/`, and this project's own working-copy directory names |
| EMAIL | every address, with a single public role address allowlisted by name |
| DOTENV | any `.env*`, `credentials`, `*.pem`, `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `*.key`, `id_rsa`/`id_ed25519`/`id_ecdsa` file anywhere in the tree |
| BIGCODE | any `.json`/`.jsonl`/`.py`/`.txt` over 5 MB — the bulk-third-party-code hazard, checked here because it arrives the same way a secret does: copied in without being reread |

A seventh class, **INTERNAL**, was added on 2026-09-13; see finding 2 below
for what it is for. It has two halves: a *shape* rule, always on, that matches
a numbered stage directory in either its slash spelling or its
`Path / "a" / "b"` spelling; and an *exact* rule built from the
`BENCH_INTERNAL_*` environment variables, which is the strict mode the
publisher runs. When those variables are unset the scan prints
`INTERNAL exact rules: NOT CONFIGURED` rather than reporting a pass it did not
earn.

**Result: 0 findings** across 1,265 text files (15.5 MB) — the tree grew with
the redacted transcripts and the audit rows. **15** lines carry an explicit
end-of-line exemption marker: 13 in the scanner's own source (its pattern
definitions and its self-test plants, one of which is a real third-party GitHub
mirror path, `ep-infosec/50_…-tangents`, with the shape of an internal stage
directory — planted to prove the shape rule does *not* fire on it) and 2 in
`tools/assemble.py`, where two redaction regexes have to spell the working
repo's own directory name in order to remove it.

**The marker mechanism had a hole, found while counting these.** It matched
anywhere on a line, so a sentence that merely *mentioned* it — a docstring
explaining the convention, and the sentence in this report you are reading —
exempted its own line from every rule. Three lines were silently exempt that
way, which is exactly what "counted, so never a silent hole" was supposed to
prevent. The marker must now END the line, and the self-test plants a live key
on a line that mentions the marker mid-sentence and requires the hit.

**The scanner was proven able to fail.** `--self-test` plants one live-looking
instance of each class in a throwaway tree and requires a hit on every one. It
**caught a real defect in the gate on its first run**: the App Runner rule was
written as `.apprunner.<region>.amazonaws.com`, which is not the shape AWS
emits (`<id>.<region>.awsapprunner.com`), so that class would have reported
clean forever. A scanner never observed failing is not a verified scanner.

**Two findings that are not defects but should be known:**

1. `src/vendor/api_gateway.py` contains `media@syntology.ai` in the HTTP
   user-agent string. It is a public role address, already sent in every
   request this code has ever made, and it is allowlisted by name rather than
   pattern — a different address would be a finding.
2. **Internal directory names used to survive path redaction. Fixed
   2026-09-13.** Absolute paths were rewritten on the way out — the developer
   home to `<REPO>`, external volumes to `<ARCHIVE_VOLUME>`, any remaining home
   directory to `<HOME>/` — and that left the internal *layout* in plain sight
   inside the very strings it had just shortened: the stage tree's name, its
   numbering scheme, what each stage is called. **3,015 occurrences across 529
   files**, in provenance stamps, in the sweep scripts, in the portability
   patch record, and in `referees/INDEX.json`'s `internal_source` field.

   They are now rewritten to **stable aliases** — `<BENCH>`, `<REFIMPL>`,
   `<AUDIT>`, `<INTERNAL>`, `<CORPUS>` — rather than deleted, because the
   reason they were kept was real: a reader tracing a published file back to
   the artifact it came from needs to see that two files came from two
   *different* internal origins, and which. The aliases carry exactly that and
   nothing else. Machine-specific temp directories (`/var/folders/…`) are
   redacted too; one was sitting in the audit summary.

   Three things make this a fix rather than a pass of find-and-replace:

   - **The names are no longer in the assembler either.** `tools/assemble.py`
     takes `--bench-dir` / `--refimpl-dir` / `--audit-dir` (or the matching
     `BENCH_INTERNAL_*` variables) and has no defaults, because a default is
     the leak. The same is true of `tools/corpus_license_report.py`. Only
     someone holding the working repo can run either, and they know the names.
   - **The `Path / "a" / "b"` spelling is covered.** A slash-shaped rule never
     matches `REPO / "<tree>" / "<NN_stage>"`, which is how three of them rode
     out in `src/PORTABILITY_PATCHES.md`.
   - **A gate refuses on a recurrence.** `tools/scan_secrets.py`'s INTERNAL
     class fails the publish, and its `--self-test` plants one in exactly the
     shape that shipped — a stamp whose machine prefix has been redacted and
     whose directory name has not — and requires the hit. Nine mutations of
     that gate were run; all nine were caught.

---

## 2. Licence findings

`tools/corpus_license_report.py`, read-only against the graph, artifact
`data/corpus/license_census.json`.

**Re-run against the live graph on 2026-09-13, and the published census was
deliberately NOT replaced with the result.** Reports B and C came back
identical — 174 distinct samples fetched across the transcripts, 29 of them
harvested, buckets unchanged; 96/96 task reference implementations
`generated_by_us`. Report A moved: the graph now holds **118,939**
`:CodeSample` nodes, **116,113** harvested, **70.8%** of those carrying no
licence we can rely on, against 118,400 / 115,574 / 71.0% at packaging time.
The corpus kept ingesting; the flat index did not. The published census is the
one the *instrument* belongs to — the 118,400-row haystack the `code_only` arm
actually searched — so it stays, dated, and today's re-measurement is recorded
here instead of overwriting it. Anyone re-running the tool will get today's
numbers and should read this paragraph before concluding the file has drifted. Also `qc_license_gate.py` in the working
repo, which gates the live serving path: **clean — no unlicensed harvested
sample is reachable on a code-serving edge.**

### What ships

**Every task reference implementation is LLM-generated from paper text, not
taken from anyone's repository** — report C: **96/96 `generated_by_us`**, where
96 is the number of task ROWS across the freeze and substitution task files and
**72** is the number of distinct implementations behind them (the freeze's 24
ids are a subset of the substitution set's 72). The check exits 1 and blocks
publication if that ever stops being true. The same holds for the 72 property
suites. Nothing in `referees/` is third-party code.

**That 96-vs-72 distinction was being reported wrong** in this document and in
`LICENSE_QUESTION.md`'s table, which counted 96 suites and 192 implementations
where the tree holds 72 and 144. Corrected, and `tools/verify_claims.py` now
checks the counts against the files on disk so a licence document cannot drift
away from what it licenses.

The remaining licence question is about material Syntology produced, and it is
open by design — `LICENSE_QUESTION.md`, not answered here. The one item that
may need to be **removed** rather than licensed is `impl_llama.py` (72 files),
if Llama's community-licence conditions on derivative materials turn out to be
incompatible with redistribution in a public repo. Nothing in the reproduction
path reads it; its role is evidential.

### What was excluded, and why

**The flat index — 118,400 rows, 613 MB.** 115,574 rows were harvested from
public GitHub repositories:

| | count | share of harvested |
|---|---:|---:|
| upstream repository has no LICENSE file (`NONE`) | 71,236 | 61.6% |
| licence never recorded | 10,784 | 9.3% |
| **not redistributable or not determinable** | **82,020** | **71.0%** |
| permissive, inline-redistributable | 31,515 | 27.3% |
| copyleft or share-alike | 1,983 | 1.7% |

No licence means all rights reserved. Republishing the index would redistribute
71,236 files nobody gave us permission to redistribute. **Excluded.**

A licence-filtered index (~34,000 rows) would be publishable **and would be a
different instrument** — the measured 24/24 belongs to the full haystack,
including the 115,574 level-0 rows the pre-registration predicted would dilute
the ranking and which did not. `data/corpus/CORPUS_MANIFEST.md` documents the
schema so a reader can build their own.

**Raw transcripts — 478 runs, ~36 MB — are still excluded; the REDACTED ones
ship.** Agents pulled **174 distinct code samples** into them in full via
`code_get`. 29 of those are harvested third-party code, and of those 29:

| | count |
|---|---:|
| upstream repository has no LICENSE file | 19 |
| licence never recorded | 3 |
| permissive | 6 |
| copyleft (AGPL-3.0) | 1 |

**22 of 29 are not redistributable.** The `search` and `both` arms are worse:
they fetched files directly from GitHub and web pages, and those bodies sit
verbatim in their transcripts along with paper abstracts from Semantic Scholar
and arXiv. **Excluded.**

**Submitted solutions.** In the substitution arms, 28 of 48 submitted modules
share ≥ 0.5 of a fetched substitute's identifiers, median overlap 0.56, max
0.90 — and some of those substitutes are in the unlicensed bucket above. Rather
than adjudicate 478 files one at a time, **all** submitted solutions are
excluded. **This is the exclusion that costs the repository the most**, and it
is a licence decision, not a completeness one.

**What ships instead:** `data/runs/**/meta.json`, one per run — every tool call
by name and argument *size*, turns, token usage, wall time, stop reason, the
hold-out sha set the run was denied, and its provenance stamp — **and, since
2026-09-13, `transcript.json` beside it, redacted.** 478 of them, 19.7 MB of
retrieved content removed. Every string that could carry something retrieved is
now `<redacted body sha256=… bytes=… field=… origin=…>`; what survives is
message order, tool names, and structural result fields. The rule is
default-deny on a key allow-list with a length cap, so a tool that grows a new
field leaks nothing until someone allows it deliberately, and
`tools/redact_transcripts.py --self-test` plants a body in every place a body
can ride — prompt, assistant text, tool argument, JSON result, non-JSON result
— and requires that not one line of it survives. Eight mutations of the
redactor were run; all eight were caught, including one that was only caught
after the self-test was strengthened to test `CODE_ARGS` on its own terms
rather than through the default-deny rule that was masking it.

The assembler still refuses to emit any result or run file carrying a string
longer than 500 characters outside its provenance block, so "content-free" is
enforced rather than asserted.

**`query_engine`.** Syntology's production paper-resolution and Cypher-template
package, imported by the graph arm. Not published: it is the live serving path
of a private system, not part of this benchmark. `src/vendor/query_engine/` is
a stand-in that raises an explanatory error.

---

## 3. What was verified to work here

| check | result |
|---|---|
| `tools/scan_secrets.py` | 0 findings, 1,262 files (15.5 MB) |
| `tools/scan_secrets.py --self-test` | all 13 plants caught, plus the false-positive check that the INTERNAL shape rule does **not** fire on a third-party repo path; 9 mutations of the INTERNAL gate all caught |
| `tools/verify_claims.py` | **67 checks pass**, 0 fail, 3 things flagged as not checkable here |
| `tools/redact_transcripts.py --self-test` | 6/6, and 8 mutations of the redactor all caught |
| `tools/redact_transcripts.py --verify` | 478 redacted transcripts, 0 findings |
| `tools/recompute_fidelity_bracket.py` | **41 checks pass** — the 0.29-0.80 bracket, both Wilson bounds, both instruments' sensitivity/specificity and the mutation channel, all re-derived from the published rows |
| `src/analyze_code_only_mechanism.py` over the published redacted transcripts | re-derives `data/mechanism_v15.json` **with no differing key** |
| every module in `src/` imports | 18/18 — it was **5/18** before 2026-09-13 |
| `tools/smoke_referee.py` | 3/3 tasks scored correctly, offline, $0 |
| `src/qc/qc_code_only_arm.py` | checks A (arm purity) and B (tokenizer parity) **pass in this tree**; C and D report a partial (exit 4) with no index present. Proven able to refuse: planting a `-[` in the arm module makes it exit 1 with five findings |
| `tools/assemble.py --check` | tree matches `MANIFEST.json` and the internal sources |
| end-to-end `none` arm, run **from this tree** | 13 turns, submitted, 237 s, then scored by `src/verify_solutions.py`: **failed 5/5 properties** — a genuine behavioural failure (the model invented its own `mode` vocabulary and never guessed the paper's), not an environment break |

That last row is the one that matters for the "runnable by an outsider" claim:
the published tree ran a real subject against a real task and the published
referee scored it, with nothing but AWS Bedrock credentials.

---

## 4. Things that are not right yet

Listed because a reader will find them anyway, and finding them unlisted is
worse.

**Closed on 2026-09-13**, with what closed them:

1. ~~**The mechanism tables cannot be re-derived here.**~~ They re-derive.
   `data/runs/**/transcript.json` ships redacted, and
   `src/analyze_code_only_mechanism.py` run over the published tree reproduces
   `data/mechanism_v15.json` with **no differing key** — `matched_by` route
   tallies, "24/24 fetches were the correct sample", and the conditional
   included. The 143 substitute origins re-derive from the same transcripts
   through `analyze_substitution.fetched_origins`, and `verify_claims.py`
   checks the figure under **both** denominators, because the published
   artifact counts all 49 runs (147) and `RESULTS_SUBSTITUTION.md`'s table
   counts the pre-registered 48 (143). Quoting either without its denominator
   is how a number starts drifting.
2. ~~**The fidelity bracket is asserted, not shown.**~~ It is shown.
   `data/fidelity_audit/` carries the audit's pre-registration, its three
   summaries and its **1,536 per-row verdicts**, and
   `tools/recompute_fidelity_bracket.py` re-derives 41 figures from them:
   0.2905 and 0.7965, both Wilson lower bounds, the strict `is_defining`
   reading, the both-families-agree floor, each adjudicator's sensitivity and
   specificity against the gold rows, and the paired mutation flip rate. The
   adjudicators' verbatim paper quotations (`evidence_quote`, and the withheld
   spec/review fields) are dropped on the way out — those are the papers'
   words, not ours — and the recompute does not need them.
3. ~~**No `LICENSE`.**~~ Apache-2.0, decided 2026-09-13. `LICENSE`, `NOTICE`,
   headers on files authored here, and `LICENSE_QUESTION.md` rewritten from a
   question into the record of the decision. `impl_llama.py` is **kept**; the
   one-commit fallback if counsel objects is written down there.

**Still not right:**

4. **The `code_only` arm needs a graph.** `code_get` is a Cypher lookup. The arm
   is code-only in the sense that it traverses nothing — mechanically checked
   by `src/qc/qc_code_only_arm.py` — not in the sense that it is database-free.
   Someone expecting a self-contained retrieval baseline will be disappointed,
   and the README says so rather than letting them find out after cloning.
5. **18 source files carry portability patches.** Small, listed and
   non-behavioural (`src/PORTABILITY_PATCHES.md` has every before/after), but
   they mean 18 of the shipped files are not byte-identical to the ones that
   produced the numbers. `MANIFEST.json` marks each one. One of those patches
   is new and is the subject of item 9.
6. **The task files were path-rewritten** to point at `referees/` instead of the
   internal reference-implementation tree. Marked `path-rewritten`; each referee
   file's internal origin is preserved in `referees/INDEX.json` as
   `<REFIMPL>/…`.
7. **`src/sweeps/*.sh` will not run here.** They `cd` into a working-repo
   layout, `source .env`, and call an internal job-logging wrapper. They ship
   verbatim as the record of how each sweep was actually launched — including
   the resume-past-completed-runs loop and the day-cap wait — not as an entry
   point.
8. **The `search` arm's toolkit has drifted** since the only run it was clean
   for. Anyone re-running it is measuring a different toolkit against a
   different internet.
9. **The tree did not import, and nothing had ever checked.** Found on
   2026-09-13 while preparing the public repository: **13 of the 18 modules in
   `src/` raised `ModuleNotFoundError` on import**, because they resolve the
   shared modules at the working repo's root and this layout keeps them in
   `src/vendor/`. That includes `verify_solutions.py` — the referee — and all
   four analyzers `REPRODUCTION.md` instructs a reader to run. §3 of this
   report had recorded `tools/smoke_referee.py` passing 3/3, which was true
   when run from inside the working repo and not true of the published tree;
   the smoke test was the only thing anyone had executed, and it was executed
   in the one place the defect is invisible. Fixed by a listed portability
   rule, and gated: `tools/assemble.py` now imports every shipped module as a
   subprocess with only the script's own directory on the path, and refuses to
   finish if one fails. The gate was mutation-tested by reverting the rule; it
   reported 14 findings. It also now refuses when a portability rule matches
   **no** file, which is how the ordering bug that briefly re-broke this during
   the fix announced itself.

---

## 5. What a defensible public repo would still need — and what it has

All four items in this section as first written are now done. Kept, with what
was done to each, because the list is more useful as a record than as a wish.

- ~~**A licence.**~~ **Apache-2.0**, one grant over everything, decided
  2026-09-13. `LICENSE` + `NOTICE` + headers on files authored here.
- ~~**An answer on `impl_llama.py`.**~~ **Kept.** Dropping it would remove the
  evidence for the one table where the graph arm won, and the fallback was only
  ever cheap because nothing in the reproduction path reads it — which is also
  why exercising it gains nothing. Counsel has not ruled; if the ruling is
  negative, `LICENSE_QUESTION.md` records the one commit that answers it.
- ~~**A redacted-transcript release.**~~ **Shipped.**
  `tools/redact_transcripts.py` replaces every retrieved body with
  `<redacted body sha256=… bytes=… field=… origin=…>` and keeps the structure
  around it; 478 transcripts, 19.7 MB of content removed, and
  `data/mechanism_v15.json` re-derives from them with no differing key. The
  `licence` field the original sketch asked for is **not** per-body: what
  travels instead is `source_kind` (`generated` vs `harvested`) where the
  record carried it, and `origin`, with the population-level licence position
  in `data/corpus/license_census.json`. A per-body licence lookup would need
  the graph, and nothing in the mechanism tables depends on it.
- ~~**A decision on whether internal directory names may appear.**~~ **No**,
  and the gate enforces it. See §1, finding 2.

What is still outstanding is not in this repository's gift: counsel on the
Llama community licence, and the two decisions `LICENSE_QUESTION.md` says this
choice does not settle — a licence-filtered corpus release, and any graph
snapshot.

## 6. What an outsider still cannot do

Stated as a list because every other section is about what *was* fixed.

- **Run the `syntology` or `syntology_ho` arms.** They read a private graph
  through unpublished serving code.
- **Run the `code_only` arm** without supplying both a flat index and a Neo4j
  store of `:CodeSample` nodes.
- **Re-derive anything that needs the text an agent read or wrote.** The
  redaction is one-way. The identifier-overlap figures in
  `RESULTS_SUBSTITUTION.md` (28 of 48 submissions sharing ≥ 0.5 of a fetched
  substitute's identifiers) are in that category, and submitted solutions are
  not published in any form.
- **Check whether any individual fidelity verdict is right.** The adjudicators
  read the served code and the paper body; neither is here. The audit's own
  primary finding is that the verdicts are unreliable in the permissive
  direction, which is the reason the bracket is a bracket.
- **Re-run `tools/assemble.py`**, which needs the working repo and its internal
  directory names.
