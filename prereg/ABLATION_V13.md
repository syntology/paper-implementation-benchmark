# v1.3: measure the STRUCTURAL fix

**Pre-registered 2026-08-31, before any v1.3 run.**

## What changed since v1.2

v1.2 measured `c70c1ea`: token matching in `list`, and the best
trigger-condition description anyone has written for
`get_reference_implementation`. It moved adoption 0/24 → 1/24 → **6/24**
and stopped browse-zero false negatives dead (0 occurrences). But 103
calls still went to GitHub while 31 landed on the two paper tools and 6
on the code tool. Words were measured, three times, and the workflow
prior ("graph = metadata, GitHub = code") survived all three.

So `cbc9a69` stopped arguing and moved the code:

1. **`get_paper` / `get_code_for_paper` now carry
   `verified_reference_implementations` inline** — method, evidence-backed
   verification level, and the exact call to fetch it. The key is absent
   rather than empty when there is nothing, so its presence is the signal.
2. **Server-level `instructions`** — a prior about the whole server is not
   reachable from any single tool's description, so it is stated once where
   the client reads it before choosing tools. The harness had no channel for
   this, which is why v1.2 could not have measured it; added here, applied
   only when syntology tools are in the arm.
3. **`get` resolver token fallback** (`0bd28b9`) — `get` degrades to a near
   match instead of raising "no method named X is in the graph". v1.2
   measured the `list` half of this only.

Shim re-lifted from `main.py@cbc9a69` by **ast extraction, not by hand**, so
shim and production cannot drift silently. Descriptions verbatim from
`mcp_server.py@cbc9a69`.

**Setup:** `both` arm, all 24 tasks, v1.0 tool ordering (search tools first —
the wild is not ours to order), `--variant v13`, output `runs_v13/`.

## The ceiling, measured before running

The inline field cannot fire on a paper that has no reference
implementation. Measured directly against the live graph:

| | inline field fires |
|---|---|
| in_catalog | 11/12 |
| off_catalog | 1/12 |
| **total** | **12/24** |

(`in__2505.24844` is in-catalog but its paper→method→impl path does not
resolve — a real gap, noted, not chased here.)

Of those 12, **six already adopted in v1.2** — and they are exactly the v1.2
adopter list. So the mechanism's entire headroom is six specific tasks:

`in__2502.00270`, `in__2205.12679`, `in__2210.09759`, `in__2210.01241`,
`in__2110.02544`, `in__2305.19587`

**Hard floor 6/24, hard ceiling 12/24.** Any adoption number outside that
range means something other than the inline field moved, and should be
investigated rather than celebrated.

## Predictions

- **Adoption 8–11/24** (2–5 of the six convert). The field is a pointer, not
  code, so converting still costs an extra call, and the agent must call a
  paper tool in that run for the field to be seen at all.
- **Browse-zero false negatives: 0.** Already fixed in v1.2; a regression
  here means the re-lift broke something.
- **Pass 17–20/24.** v1.2 was 18/24; expect no real movement — three runs
  have shown pass rate is dominated by task difficulty, not tool access.
- **Cost median ≤ $0.256** (v1.2). Fetching served code should not cost more
  than searching for it.

## Decision rules

- **adoption ≥ 10/24** → the structural fix works; it is the mechanism, and
  the remaining gap is catalog coverage, not discoverability.
- **8–9/24** → real but partial; the inline field helps some agents and the
  workflow prior still beats it in others. Report as additive, keep looking.
- **≤ 7/24** → the structural fix is ALSO insufficient. That is the
  important negative: it would mean the wall is not tool surfacing at all,
  and the next lever is a different kind of intervention entirely, not
  another round of positioning.
- **adoption > 12/24** → impossible by the ceiling above; treat as a
  measurement bug and find it before reporting anything.

## RESULT (2026-08-31, 20/24 — Sonnet day cap aborted the sweep twice)

**Adoption 12/20**, and the composition of that 12 is the finding: the six
prior v1.2 adopters, plus **all six** headroom tasks. Every paper where the
inline field could fire, fired and converted.

| | v1.0 | v1.1 | v1.2 | **v1.3** |
|---|---|---|---|---|
| adoption | 0/24 | 1/24 | 6/24 | **12/20** |
| lever | plain | descriptions | better descriptions | **structural** |

**Conversion of the pre-registered headroom: 6/6.** Predicted 2–5. The
prediction was wrong in the favourable direction, which is worth stating
plainly rather than quietly banking.

`in__2110.02544`, `in__2205.12679`, `in__2210.01241`, `in__2210.09759`,
`in__2305.19587`, `in__2502.00270` — all six.

**Decision rule fires: adoption ≥ 10/24 → the structural fix works. It is
the mechanism, and the remaining gap is catalog coverage, not
discoverability.**

### The mechanism, not the correlation

Sampled transcripts show one identical chain, with the fetch as the very
next call after the field appears:

```
1. CALL  syntology_get_paper
     ^ result carried verified_reference_implementations
2. CALL  syntology_get_reference_implementation
```

Three ablations argued with the workflow prior and moved adoption 0 → 1 → 6.
Putting the answer in a response the agent had already asked for moved it to
the ceiling.

### Secondary

- **Pass 18/20, paired +2/−0 against v1.2.** Both newly-passing tasks --
  `in__2210.01241`, `in__2210.09759` -- are headroom conversions that failed
  in v1.2 as non-adopters. Adoption produced the passes; nothing regressed.
- **Browse-zero: 0.** The re-lift did not break the v1.2 resolver fix.
- **Cost median $0.262 vs $0.249** on the same 20 tasks: **~5% more
  expensive.** Fetching costs a call that not fetching does not. Wall median
  improved (67.9s). The honest read is that this fix buys correctness and
  adoption, not savings, and the savings claim still rests on run 1.

### Denominator

20/24. Four off-catalog runs remain, aborted by the day cap (twice -- the
same failure that left v1.2 at 22/24). **None of the four fires the inline
field**, so they cannot convert through this mechanism, and the settled
figure is 12/24 -- exactly the pre-registered ceiling. A waiter is queued to
close the denominator when the cap resets; the conclusion does not depend on
it.

### What this does NOT show

The ceiling is catalog coverage. 12 of 24 papers had a verified
implementation to surface; the other 12 got nothing, correctly. Adoption is
now limited by how much code the graph holds, which is the constraint the
harvest and verification lanes exist to move. This run says discoverability
is solved for the covered case -- not that the catalog is big enough.

## Note for a future compose ablation (from syntology-final-6c, 2026-09-01)

`syntology_compose` was called **zero times** across v1.1, v1.2 and v1.3 — no
result in this directory depends on it. If a v1.4 ever adds a compose arm,
the known open item is the serving-side `subj[0]` name-resolution ambiguity
(blocked on main.py's active-edit lock). The compose path's offline consumers
— ranker, typed search, funnel exports — are sha-keyed as of tonight, and the
tables the shim imports are parity-gated by `qc_compose_semantics.py`.
