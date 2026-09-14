# What graph these numbers were measured against

Every arm in this benchmark except `syntology` runs on artifacts in this
repository. The `syntology` arm reads a private Neo4j graph that is not
published and **cannot be re-run by a reader** (`REPRODUCTION.md`). That makes
one obligation unavoidable: the graph arm's result is only interpretable if the
graph it was measured against is stated. This file states it, including the
part that does not flatter us.

**Nothing here has been re-tested against the current graph.** The tables in
`README.md` and `results/` are a dated measurement, not a description of
Syntology today.

---

## The run window

The v1.5 and v1.6 transcripts in `data/` span

```
2026-09-10T19:47:12  ->  2026-09-11T13:54:14
```

taken from 412 ISO timestamps inside the shipped transcripts, so a reader can
re-derive the window from the artifacts rather than take our word for it.

## A write landed in the middle of the run

Syntology's write ledger records three CITES backfill tranches on 2026-09-10:

| when | edges | relative to the run |
|---|---:|---|
| 18:12:07 | +16,634 | before it started |
| 19:25:55 | +67,276 | before it started |
| **20:41:46** | **+141,896** | **during the run** |

**141,896 CITES were added to the graph while the benchmark was executing.**
By transcript timestamps, **22%** of run activity precedes that write and
**78%** follows it. The graph arm did not read one fixed graph; it read a graph
that gained citation edges partway through.

**And it was not one write. A gate built afterwards to detect exactly this
found 39.** The CITES tranche dominates by four orders of magnitude, but the
run window also contains 36 author-correction *undo round trips* from
`audit_author_extraction.py` (net `AUTHORED_BY` 0, `Author` +12) and two
institution deletions (`Institution` −2, `AFFILIATED_WITH` −8). So the graph
did not only grow underneath the run — it also **lost nodes and edges** while
being scored. An earlier version of this file said "a write"; it was 39, and
the correction is kept here rather than quietly folded in.

This should not have happened, and it is disclosed here rather than discovered
by a reader. It is now also prevented rather than merely regretted: the sweep
runner records its own window, snapshots the graph at both edges, and **exits
2 rather than reporting a score** if the write ledger shows any non-dry,
non-zero-delta write overlapping that window. Run against the 2026-09-10
window it refuses with all 39, which is the only test of such a gate that
means anything.

**Which way it biases the headline.** The published result is a *null*: the
graph arm tied a flat BM25+cosine index at 24/24 with no discordant tasks. The
mid-run write **added** retrievable structure to the graph arm and to nothing
else, so the arm that changed is the one the null is about, and it changed in
the direction that would help it. On that reading the tie is conservative.

We are not claiming that settles it. More edges can also dilute a retrieval,
and 22% of the run saw the smaller graph while 78% saw the larger, so the arm
was not internally uniform either. **Only a re-run against a frozen graph can
close this**, and that re-run has not been done.

## The graph at the end of the run

Reconstructed from the write ledger by subtracting every post-run write from a
measurement taken **2026-09-14T15:52 MDT**, before an in-progress metadata
backfill. It is a reconstruction, not an observation: no node counts were
captured at run time, which is itself a defect this file exists to stop
repeating.

| | at the run (reconstructed) | 2026-09-14 (measured) | change |
|---|---:|---:|---:|
| `Paper` | 523,883 | 527,098 | +3,215 |
| `Method` | **54,440** | **88,587** | **+34,147 (+63%)** |
| `PROPOSES` | 60,576 | 94,744 | +34,168 |
| `Author` | 234,494 | 240,327 | +5,833 |
| `AUTHORED_BY` | 745,460 | 761,802 | +16,342 |
| `CITES` | 3,526,639 | 3,526,639 | 0 |
| `CodeSample` | — | — | +751 |
| `Concept` | 86,461 | 86,541 | +80 |

## Why this matters for reading the tables

The headline compares two arms whose substrates have since moved **very
unevenly**. The graph arm's `Method` population grew **63%**; the `code_only`
arm's flat index is built from `CodeSample`, which grew by 751. A tie measured
on 2026-09-10 is not evidence of a tie today, in either direction, and this
repository does not claim one.

The pre-registrations, the transcripts and the referee are all fixed artifacts
and re-derive exactly as published — `tools/verify_claims.py` checks 67 of
them. What is dated is the *graph*, and only the `syntology` arm depends on it.

## What would close this

1. Freeze graph writes for the duration of any scored run, and fail the run if
   the ledger records a write inside its window.
2. Capture node and edge counts **at run time**, into the results artifact, so
   the state is observed rather than reconstructed.
3. Re-run all four arms against a frozen graph, under a fresh pre-registration,
   and publish both results side by side.

None of the three is done. (1) and (2) are cheap and are the real lesson; (3)
is a decision about spend and timing.
