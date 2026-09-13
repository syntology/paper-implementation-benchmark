# All four runs, in one place

Every figure here is recomputed from `data/` by `tools/verify_claims.py`, which
fails if any of them drifts. The full write-ups — including every scored
prediction, every deviation and every caveat — are the other documents in this
directory and `prereg/FREEZE_RUN.md`. **Read this table with the "What is NOT
claimed" section of `README.md` beside it.**

## Pass rates

| | run 1 | v1 freeze | v1.5 | v1.6 (answer held out) |
|---|---|---|---|---|
| date | 2026-08-31 | 2026-09-02 | 2026-09-10 | 2026-09-11 |
| tasks × arms | 24 × 4 | 24 × 4 | 24 × 3 | 48 × 3 |
| `none` | 13/24 | 13/24 | 10/24 | **24/48** |
| `search` | 14/24 | **11/24** | not re-run | not run |
| `syntology` | 13/24 | **21/24** | **24/24** | **24/48** (held out) |
| `both` | 14/24 | **21/24** | not re-run | not run |
| `code_only` | — | — | **24/24** | **23/48** (held out) |
| subject spend | $37.24 | $17.40 | $5.43 | $15.81 |

Run 1's numbers are the **strict-referee corrected** ones: an audit found the
sandbox stringifying numpy booleans, and all four run sets were re-verified
under the fixed referee. `RESULTS.md` carries the correction block.

## The comparisons that were pre-registered as primary

| run | comparison | discordant | exact sign test |
|---|---|---|---|
| run 1 | `both` vs `search` | +4 / −3 | 1.00 |
| run 1 | `syntology` vs `search` | +6 / −6 | 1.00 |
| v1 freeze | `syntology` vs `search` | **+10 / −0** | **0.002** |
| v1 freeze | `both` vs `search` | **+11 / −1** | **0.006** |
| v1.5 | **`code_only` vs `syntology`** | **+0 / −0** | **1.00** |
| v1.5 | `code_only` vs `none` | +14 / −0 | 0.0001 |
| v1.5 | `syntology` vs `none` | +14 / −0 | 0.0001 |
| v1.6 | **`syntology_ho` vs `code_only_ho`** | **+6 / −5** | **1.00** |
| v1.6 | `syntology_ho` vs `none` | +3 / −3 | 1.00 |
| v1.6 | `code_only_ho` vs `none` | +4 / −5 | 1.00 |

v1.6 also ran a pre-committed co-primary on the graded metric (property
fraction, paired Wilcoxon): graph vs flat **p = 0.89**. It was added because the
pre-registration expected partial credit to reveal a difference the binary hid.
There was none to reveal.

## What the ties do and do not bound

| | v1.5 | v1.6 |
|---|---|---|
| shape of the tie | **at the ceiling** — both arms 100% | **mid-range** — both near 50% |
| discordant pairs | 0 of 24 | 11 of 48 (22.9%) |
| bound on a graph advantage | rule of three: **≤ 3 tasks in 24 (12.5%)** | **+2.1%, 95% CI [−11.5%, +15.6%]** |
| what would be needed to detect a real edge | *not more tasks of this shape* — a ceiling cannot rank two conditions | π = 0.70 needs n ≈ 110; π = 0.65 needs n ≈ 190 |

Neither is evidence of equivalence. Both exclude a large effect.

## Efficiency (median per run)

| run | arm | turns | wall | cost | never submitted |
|---|---|---|---|---|---|
| v1 freeze | `none` | 5 | 31.4 s | $0.049 | 0/24 |
| v1 freeze | `search` | **20** (the cap) | 142.9 s | $0.380 | **11/24** |
| v1 freeze | `syntology` | 6 | 36.7 s | $0.070 | 0/24 |
| v1 freeze | `both` | 10 | 97.3 s | $0.188 | 0/24 |
| v1.5 | `none` | 5 | 28.5 s | $0.045 | 0/24 |
| v1.5 | `syntology` | 6 | 38.0 s | $0.081 | 0/24 |
| v1.5 | `code_only` | 6 | 34.0 s | $0.096 | 0/24 |
| v1.6 | `none` | 5 | 30.1 s | $0.046 | 0/48 |
| v1.6 | `syntology_ho` | 7 | 50.5 s | $0.085 | 0/48 |
| v1.6 | `code_only_ho` | **10** | 57.0 s | **$0.179** | 1/49 |

The v1.6 rows are the medians in `data/analysis_substitution.json`, which
covers **49** runs per hold-out arm — the pre-registered 48 plus two extra runs
on a smoke task outside the primary set. `RESULTS_SUBSTITUTION.md` quotes the
primary-48 medians, which differ by 0.3 s of wall and nothing else. Both are
correct about their own population; neither changes a comparison.

**Costs are not comparable across run 1 and everything after it** — prompt
caching was added in between, so run 1's are uncached. Turns and wall time are.
Dollar figures are recomputed from token counts at on-demand us-east-1 Sonnet
4.5 prices as of 2026-08 (`src/analyze.py`, `PRICE`).

The sharpest efficiency line in the whole benchmark is v1.6's last row: the flat
arm spent **3.9× the money and 2× the turns of having no tools at all**, to land
one task behind it.

## Adoption

| run | arm | runs that called the code-fetch tool |
|---|---|---|
| run 1 | `syntology` | 11/24 |
| run 1 | `both` | **0/24** |
| v1 freeze | `syntology` | 19/24 (**18/18 in-catalog**) |
| v1 freeze | `both` | 18/24 (**18/18 in-catalog**) |
| v1.5 | `syntology` | 24/24 |
| v1.5 | `code_only` | 24/24 |
| v1.6 | `syntology_ho` | **2/48 received actual source** |
| v1.6 | `code_only_ho` | **48/48** |

Run 1 versus the v1 freeze is the single most useful row here for anyone
building an agent tool: **the same tools, with different descriptions and
server-level instructions, went from 0/24 adoption to 18/24.** Three ablations
(`prereg/ABLATION_V1{1,2,3}.md`) sit between them and show that words alone
moved adoption to 1/24 — the structural change, putting the verified
implementation inline in the response the agent was already reading, is what
moved it.

`syntology_compose` was called **0 times across all 478 published runs**,
including the 48 designed to elicit it. That one you can check yourself from
`data/runs/`.

## The conditional

Every run that fetched a machine-verified served sample passed the held-out
referee: **90/90 cumulative** (11/11 run 1 · 6/6 v1.2 · 12/12 v1.3 · 37/37 v1
freeze · 24/24 + 24/24 v1.5). Pre-registered in advance in both later
pre-registrations, with a per-property post-mortem promised on the first
failure. There has not been one.

Two things this does not mean. For in-catalog tasks the served code was itself
verified against this referee's own property suite at grant time, so a
fetch-and-submit passes **by construction** — the conditional measures the
serving path, not the model. And passing that suite is not evidence the code is
faithful to its paper; see `README.md`, "What is NOT claimed", point 2.

## The retrieval probes (zero subject spend)

**Flat index recall, in-catalog n = 18** (`data/probe_code_only_retrieval.json`):

| query form | @1 | @5 | @15 | @50 |
|---|---|---|---|---|
| entry function name | 17 | 18 | 18 | 18 |
| **method name alone** | **6** | **8** | **10** | **11** |
| method name + first sentence | 17 | 18 | 18 | 18 |

A bare method name finds the right code 10/18 flat and **24/24** through the
graph's exact `:Method` lookup. That is the ontology's measured contribution: a
name→code mapping the code text does not contain. It did not bind because
agents add a description, and one sentence takes the flat index from 10/18 to
18/18.

**What the graph had to offer under hold-out** (`data/probe_substitution.json`,
72 tasks):

| | |
|---|---|
| flat index returned a non-empty ranked list | 72/72 |
| its single best substitute was machine-verified | 52/72 |
| graph fell back to `repo_known` — a GitHub link the arm cannot open | 56/72 |
| `list_reference_implementations` reported `total_matching: 0` | 66/72 |
| `compose` at full strength: median typed partners | **0** (zero on 59/72) |
| `compose` partners overlapping the flat index's substitutes | **1/72** |

The last row is the design finding: `compose` returns what fits **with** a
routine, never what could stand **in for** it. The serving surface has no
substitution affordance at all — which explains `compose`'s zero calls better
than any story about tool descriptions.

## The hold-out, verified before any spend

`data/holdout_verification.json`, all 72 tasks, **0 findings**: 372/372 held-out
shas exist as real index rows; 372/372 refused by `code_get` **with the same
error an unknown sha gets**; the target method listed 0/72; and — the test of
the test — with the hold-out off, the adversarial battery reached the sample
72/72 and the graph served it 72/72. Post-sweep, all 96 hold-out transcripts
were scanned verbatim for every held-out sha and source: **0 leaks, 0 tasks
invalidated**.
