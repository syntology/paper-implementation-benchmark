# Security

## The thing to know before you run anything

**This repository ships 216 machine-generated Python files and executes them.**
Each of the 72 tasks carries a property suite and two LLM-drafted
implementations under `referees/`, and `tools/smoke_referee.py` — the first
command `REPRODUCTION.md` tells you to run — imports and runs them on your
machine. `src/verify_solutions.py` does the same to whatever an agent
submitted.

The sandbox around that is honest about what it is. `src/vendor/run_sandboxed.py`
says so in its own docstring: it applies CPU and memory rlimits, a wall-clock
timeout, and a Python-level preamble that replaces `socket.socket` to stop
network use — and it is **"deliberately not a security boundary against
adversarial code"**, because its inputs were our own generated files. A
monkeypatched `socket` module is not egress control; `RLIMIT_AS` is
best-effort on macOS; nothing here is a container.

Two consequences:

- **Run this in a VM or container if you do not trust the tree**, particularly
  if you have modified `referees/` or are scoring submissions from an agent
  you did not write. Give it no credentials it does not need.
- **Do not treat a passing referee run as a safety property.** The referee
  checks behaviour against a property suite. It is not a malware check, and
  `README.md`'s "What is NOT claimed" says why it is not a correctness check
  either.

The benchmark has already measured one containment failure of exactly this
shape, and it is published rather than buried: in run 1 the subject's
`run_python` tool limited CPU and memory **but not network**, and a subject
exploited it — one graph-arm run successfully `git clone`d the method's public
repository. Fixed afterwards, and v1.5 verified 0 of 72 transcripts show
network use (`README.md`, "What is NOT claimed", point 7).

## What to report

Please report:

- **A credential, token, private hostname or internal path anywhere in the
  tree.** `tools/scan_secrets.py` gates the publication against seven classes
  of these, reports 0 findings over every text file here, and runs on every
  push — but a scanner is a set of patterns, and yours may be the one it does
  not have.
- **A leak through the redaction.** `data/runs/**/transcript.json` is supposed
  to carry no retrieved body — every one replaced by
  `<redacted body sha256=… bytes=…>`. If you find text that survived,
  that is the most serious class of bug this repository can have: it would mean
  third-party source is being redistributed without a licence.
- **Code execution beyond what the sandbox claims** — a way for a scored
  implementation to reach the network, escape the rlimits, or write outside its
  temp tree.
- **A path traversal or arbitrary-write** in the harness, the referee or the
  tools, reachable from task metadata or a submitted solution.
- **A dependency-resolution problem** that would install something other than
  what `requirements.txt` names.

Please **do not** report as a security issue: an implementation in `referees/`
that does not match its paper (that is a correctness question, and the
repository's own fidelity audit already brackets it at 0.29–0.80), a property
suite that is wrong, or the fact that the `syntology` arm will not run without
a private graph.

## How to report

- **Preferred:** GitHub's private vulnerability reporting on this repository
  (Security → Report a vulnerability), which keeps the report non-public until
  there is a fix.
- **Otherwise:** email **media@syntology.ai** with `SECURITY` in the subject.
  That is the project's published role address; it is not monitored around the
  clock, so use it for things that can wait a few days, and do not send secrets
  in the body.

Please include the command you ran, the output, and your OS and Python version.
If you found a live credential, say so in the first line and **do not** open a
public issue — it will be rotated before anything else happens.

There is no bug-bounty programme, and no formal SLA. Realistically: an
acknowledgement within a few days, and a fix for anything in the first two
categories above ahead of everything else this repository is doing.

## Scope and versions

The scope is this repository. It is **not** the Syntology graph, the serving
API, `syntology.ai`, or any Syntology product — those are separate systems, and
nothing in this tree can reach them (the graph arm's serving code is not
published; `src/vendor/query_engine/` is a stand-in that raises).

There are no maintained release branches. Fixes land on `main`, which is the
only supported version; `MANIFEST.json` records the sha256 of every file, so
you can always tell whether the tree you have is the tree that was published.
