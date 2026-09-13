# v1.2: measure the shipped production fix behaviorally

**Pre-registered 2026-08-31, before any v1.2 run.** Commit c70c1ea (a
concurrent session, acting on run 1's findings) shipped both discovery
fixes to serving: token matching + never-zero-with-near-matches in
`list_reference_implementations`, and a trigger-condition-first
description for `get_reference_implementation` that names web search as
the beaten alternative and quantifies the measured advantage. The
resolver was verified directly against the failing queries; **adoption
was not** — and v1.1 measured that a cruder description bundle moved
adoption only 0/24 → 1/24. This run measures what production now ships.

**Setup:** `both` arm, all 24 tasks, v1.0 tool ordering (search tools
first — the wild is not ours to order), shim at production parity
(list re-lifted from c70c1ea; descriptions verbatim from mcp_server.py
@c70c1ea), output `runs_v12/`. One bundle: "the shipped fix."

**Predictions:** adoption (any `get_reference_implementation` call)
**2–6/24** — better copy than v1.1's, but v1.1 says the workflow prior
("graph = metadata, GitHub = code") is the wall, so still short of the
≥12 bar; browse-zero false negatives: 0 occurrences (resolver verified);
pass 15–18/24.

**Decision:** adoption ≥ 12 → the shipped fix suffices; withdraw the
structural proposal (inline impls in `get_code_for_paper`) as
unnecessary. 6–11 → propose structural as additive. < 6 → structural
remains the required fix (run-1 conclusion unchanged, now measured
against the best description anyone has written for this tool).

## RESULT (2026-08-31, 22/24 runs — Sonnet day cap aborted the sweep
at run 23; exit 4 per contract; `off_2311.15100`, `off_2406.04606`
pending)

**Adoption 6/22** (5 in-catalog + GPTQ), vs 0/24 plain (v1.0) and 1/24
my salience bundle (v1.1). Both pending runs are off-catalog, where
adoption is least likely, so the full-denominator value is ~6–7/24:
**the 6–11 band → structural proposal STANDS, as additive.** The
shipped trigger-condition copy genuinely outperformed the v1.1 bundle
(top of my predicted 2–6 band), and browse-zero false negatives did
not recur — but ~3/4 of runs still bypassed the verified-code path
after a fix written by someone who knew exactly what to say. Words
help; the workflow prior remains the wall.

Secondary: pass 17/22 (10/12 in-catalog, 7/10 off-catalog), best
both-arm rate yet; **adopters 6/6 passed** (fetched-served-code is now
17/17 across v1.0+v1.2); arm cost $6.81 (~half of v1.0's $12.94),
median $0.256/run; no-submission down to 1.

**Backfill:** re-running the identical joblog command after the day
cap resets completes the 2 pending runs (the harness skips existing
metas); re-run `verify_solutions.py --runs runs_v12` and update this
block's denominators.

## Efficiency trajectory, explicit (per-run; same 24 tasks throughout)

The earlier version-table used arm TOTALS over unequal n (22 vs 24) —
these per-run figures are the fair comparison:

| configuration | n | cost/run med | cost/run mean | wall med | turns med |
|---|---|---|---|---|---|
| none (run 1) | 24 | $0.264 | $0.285 | 139s | 13 |
| search (run 1) | 24 | $0.458 | $0.490 | 133s | 17 |
| syntology (run 1) | 24 | $0.223 | $0.238 | 113s | 13.5 |
| both v1.0 | 24 | $0.491 | $0.539 | 141s | 18 |
| both v1.1 | 24 | $0.358 | $0.369 | 88s | 15 |
| both v1.2 | 22 | $0.256 | $0.310 | 82s | 13 |

Read: the `both` configuration began as the most expensive way to run
an agent — paying two toolsets' exploration tax, costlier than search
alone — and after the fixes it costs what the lean arms cost (median
within $0.03 of `none`) while passing the most.

**Attribution (paired, same task, v1.0 → v1.2):** adopter tasks (6)
median saving **$0.292 and 74s per run** (GPTQ: $0.652→$0.249,
286s→106s); non-adopter tasks (16) $0.127 and 50s. The fixes pay
~2.3× more where adoption actually fires; the non-adopter saving is
real but mixes description-driven less-flailing, near_matches
shortening dead ends, and run-to-run variance. Caveats: n=6 adopters,
one stochastic run per cell — directionally consistent, not tight.


## BACKFILL COMPLETE (2026-08-31, later same day — denominator closed at 24/24)

The Sonnet day cap reset; re-ran the identical harness command, which
skipped the 22 existing metas and executed only `off_2311.15100` and
`off_2406.04606`. Shim untouched — still the frozen replica pinned at
`c70c1ea`, so all 24 runs measure the same tools. (Re-lifting before this
backfill would have silently mixed two tool versions into one result set;
`main.py`'s `get` resolver changed in `0bd28b9` after this ablation was
specified.)

| | at 22 | **final, 24** |
|---|---|---|
| adoption | 6/22 | **6/24** |
| pass | 17/22 | **18/24** |
| browse-zero false negatives | 0 | **0** |

Both backfilled runs were non-adopters, exactly as the pending-run caveat
predicted. The decision is unchanged and now rests on a full denominator:
**6/24 sits in the 6–11 band → the structural proposal STANDS, as additive.**

**The asymmetry that justifies it, counted across the 24 transcripts:**

| tool | calls |
|---|---|
| `github_search_code` + `github_fetch_file` | **103** |
| `syntology_get_code_for_paper` | 16 |
| `syntology_get_paper` | 15 |
| `syntology_get_reference_implementation` | **6** |

31 calls already land on the two paper tools; 6 reach the code tool; 103 go
to GitHub. That is the case for inlining rather than persuading — the traffic
is already arriving at a tool that was not telling it what the graph held.
Shipped in `cbc9a69` (inline `verified_reference_implementations` in both
paper tools, plus server-level `instructions`), and NOT measured here: doing
so requires a re-lift and a new arm.

**Method note.** A first pass at counting adoption searched the transcript
text for `get_reference_implementation` and reported 0/24. The tools are
namespaced `syntology_*` and calls are `tool_use` blocks, not bare strings;
the real figure is 6/24. Recorded because a substring probe that returns a
clean zero is indistinguishable from a real one — the same failure this whole
ablation series exists to fix, reproduced in the measurement of it.
