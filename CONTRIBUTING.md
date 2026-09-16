# Contributing

This is a **frozen research artifact**, not a library. Four runs have happened,
each against a pre-registration committed before any subject token was spent,
and the numbers in `results/` belong to those runs. That shapes what a useful
contribution looks like here, so this document is mostly about scope.

The most valuable thing you can send is **a way in which this repository is
wrong about itself**: a check that passes when it should fail, a number that
does not re-derive, an instruction that does not work on your machine. Two of
the three most serious defects found so far were found that way, by running the
documented commands from a clean clone and watching them fail.

---

## Before anything else: what you cannot run

This is not a complete instrument outside Syntology, and the boundary is not
soft. `ASSEMBLY_REPORT.md` §6 and `REPRODUCTION.md` are the long form.

| | |
|---|---|
| `syntology` / `syntology_ho` arms | **cannot be run by anyone outside Syntology.** They read a private Neo4j graph through production serving code that is not published. `src/vendor/query_engine/` is a stand-in that raises an explanatory error. |
| `code_only` arm | needs **both** a flat index you build (`src/build_code_index.py`) and a Neo4j store of `:CodeSample` nodes. Ours is not published: 71.0% of its harvested rows carry no licence that permits redistribution. |
| `src/analyze_substitution.py` | **cannot be run here at all.** It opens a Neo4j session before any table is computed. The published `data/analysis_substitution.json` carries its full output. |
| `tools/assemble.py` | needs the working repo and its internal directory names. It refuses with exit 2 without them, deliberately. |
| `none` / `search` arms | run, with **your own** AWS Bedrock credentials (and a GitHub + Semantic Scholar key for `search`). About $0.056 per `none`-arm task. |
| everything else | runs offline, with no credentials, for $0. That is the referee, all four gates, the claim re-derivations and the fidelity recompute. |

**Say it plainly:** the headline comparison — the graph arm against the flat
index, the result the README leads with — **is not re-runnable outside
Syntology.** It is *re-derivable*: `data/runs/**/` ships every run's structure
and a redacted transcript, and `tools/verify_claims.py` recomputes the tables,
the mechanism analysis and the fidelity bracket from them. But you cannot
re-run the experiment, because one arm reads a private graph and the other
searches a 118,400-row index we have no licence to republish. If that is
disqualifying for your purposes, it should be — it is the largest thing wrong
with this artifact, and no amount of auditing the outputs substitutes for
being able to run the thing.

---

## In scope

- **A check that is wrong.** A gate that passes where it should fail, a
  self-test that cannot actually fire, a floor set below what the tool really
  does. Mutation-test your fix: plant the defect, show the gate catches it.
- **A published number that does not re-derive** from `data/` on your machine.
  Send the command, the output and your Python version.
- **Portability.** A platform, interpreter or numpy version where something
  breaks. The CI matrix is Linux and macOS on CPython 3.10–3.14; everything
  outside that is unmeasured, and reports are welcome. **Windows is the
  specific gap.** `.gitattributes` pins `eol=lf` so the bytes you check out
  are the bytes `MANIFEST.json` hashed — that much is gated, by cloning with
  `core.autocrlf=true` on purpose in CI — but no check in this repository has
  ever been *run* on Windows. If you are there, that is the most useful report
  we do not have.
- **Documentation that does not match the code.** Every command in
  `REPRODUCTION.md` was executed from a clean clone before it was written, and
  four of five commands in one block were wrong when that was first done. If
  one is wrong again, that is a real bug.
- **Machine-readability.** `schemas/artifacts.schema.json` is a checked
  contract for the task, run-metadata, referee-verdict and manifest shapes. If
  a consumer needs a field the schema does not describe, say so.
- **Running the referee against your own agent.** `REPRODUCTION.md` has the
  directory shape. You do not need us for this, and results from a different
  subject model are the single most interesting thing this repository does not
  have.

## Not in scope

- **New tasks, new arms, or changes to the referee.** Those change the
  instrument. A pre-registered benchmark whose task set moves between runs
  measures nothing, and the referee is identical across all four runs on
  purpose — that is what makes the *comparisons* sound.
- **New numbers from re-run arms.** Results here come from pre-registered
  sweeps. A PR that adds a table from an unregistered run will not be merged
  however good the number is; that rule is the whole reason the null results
  are believable.
- **Restyling the prose.** The documents are written the way they are
  deliberately — the README opens with a null result about the product that
  funded it, and `verify_claims.py` prints what it *cannot* check instead of
  passing over it. Those are features.
- **New dependencies.** `requirements.txt` is five packages and a gate refuses
  any unguarded third-party import that is not in it. An optional dependency
  goes inside a `try/except` at its import site, like `scipy` and
  `python-dotenv`.
- **Anything that needs the raw transcripts or the submitted solutions.** They
  are not published and will not be: they contain third-party source fetched
  by the agents, 22 of 29 samples under no licence we can rely on. That is a
  licence decision, not an oversight.

---

## Sending a change

1. Open an issue first for anything beyond a typo. Include the exact command,
   the exit code and the last twenty lines of output.
2. **CI must be green.** `.github/workflows/ci.yml` runs every credential-free
   gate on five interpreters against a fresh clone. Run them locally first:

   ```bash
   python3 tools/check_clean_clone.py      # compiles, imports, deps, manifest
   python3 tools/verify_claims.py          # 74 checks, offline, seconds
   python3 tools/smoke_referee.py          # the referee really runs here
   python3 tools/scan_secrets.py           # the publication gate
   ```

3. **If you touch a file, `MANIFEST.json` must change with it.**
   `tools/check_clean_clone.py` verifies every file in the tree against its
   recorded sha256, so a content change with a stale manifest fails CI. The
   manifest is regenerated by `tools/assemble.py`, which only the publisher can
   run — so for an outside PR, say so in the description and a maintainer will
   regenerate it.
4. **Exit codes are a contract**, everywhere in this project: `0` clean, `1`
   findings, `2` drift, `3` unaccepted exclusions, `4` unresolved partials. A
   script exiting 3 or 4 is refusing to claim completeness, and that is it
   working. Do not "fix" it by returning 0.
5. Commit messages say **what changed and why**, in the present tense, stating
   the motivation rather than the mechanics. Look at `git log` before writing
   one.
6. By contributing you agree your contribution is licensed under Apache-2.0,
   like the rest of the repository (`LICENSE`, `NOTICE`).

---

## Conduct

Be straightforward and stay on the technical substance; assume the person on
the other end is trying to get something right. Harassment, or persistent
bad-faith argument, gets you blocked from the repository.

**There is no separate `CODE_OF_CONDUCT.md`, deliberately.** A code of conduct
is a governance instrument for a community — it earns its place when there are
maintainers, contributors and a process for handling reports between them. This
is an artifact with a closed task set and no contributor community to govern,
and a Contributor-Covenant file would be one more unread document in a
repository whose whole argument is that its documents are read. The paragraph
above is the substance; if this ever grows a contributor base, the file should
be added then and actually staffed.

---

## Citing this, and the DOI question

`CITATION.cff` is the machine-readable citation, validated in CI — GitHub
renders it as "Cite this repository".

**There is no DOI yet, and registering one was deliberately left to the owner.**
If you want one, the path is short: enable the Zenodo–GitHub integration for
the repository, cut a tagged release, and Zenodo archives that tag and mints a
DOI (plus a concept DOI that always resolves to the newest version). Then add
it back here as an `identifiers:` entry in `CITATION.cff` and a line in the
README. Two things to decide first, because a DOI is permanent:

- **What gets archived.** Zenodo takes a snapshot of the tagged tree. This one
  is **3.5 MB as the zip GitHub hands Zenodo** (14.9 MB unpacked, 1,273 files,
  measured 2026-09-13 with `git archive --format=zip HEAD`), well inside
  Zenodo's 50 GB limit, and it is exactly the artifact you would want archived
  — the numbers stay re-derivable even if the repository moves. The zip path
  is checked, not assumed: every credential-free gate was run 2026-09-13
  against an unpacked `git archive` with no `.git` directory at all, and all
  of them pass.
- **Authorship.** The Zenodo record's author list comes from `CITATION.cff`,
  which currently names the organisation rather than individuals.

A DOI is worth having here for a reason more specific than citability: this
repository's argument depends on the pre-registrations having existed *before*
the runs, and an archived, immutable, dated release is stronger evidence of
that than a git history the owner controls.
