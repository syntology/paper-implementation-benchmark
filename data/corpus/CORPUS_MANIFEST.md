# The corpus the `code_only` arm searched, and how to supply your own

The `code_only` arm is the one that ties the graph arm 24/24. It searched a flat
index over **118,400 Python code samples**. That index is **not in this
repository** and this document says exactly what it was, why it is absent, and
what you need to put in its place.

## What it was

| | |
|---|---|
| rows | **118,400** |
| harvested from public GitHub repositories | 115,574 (97.6%) |
| generated from paper text by an LLM | 2,826 (2.4%) |
| carrying a **backed** verification level ≥ 2 | 3,125 |
| at level 0 | 115,574 |
| embedding model | `amazon.titan-embed-text-v2:0`, 1,024 dims, L2-normalised |
| rows with no embedding | **0** |
| lexical fields indexed | `entry` (×3 weight), `signature`, `paper_attribution`, `code[:1200]` |
| vocabulary | 109,360 tokens |
| relationships traversed to build it | **none** — `:CodeSample` node properties only |

A "backed" level means a `verification_level` with a `verification_report`
behind it. A level with no report is reported as **0**, in the index and in the
arm, every time — the discipline exists because 313 samples were once served as
machine-verified on a hard-coded 3.

## Why it is not here

Measured at packaging time by `tools/corpus_license_report.py`, artifact
`license_census.json` in this directory:

| harvested rows, by upstream licence | count | share |
|---|---:|---:|
| repository has **no LICENSE file** | 71,236 | 61.6% |
| licence never recorded | 10,784 | 9.3% |
| **not redistributable, or not determinable** | **82,020** | **71.0%** |
| permissive, inline-redistributable (MIT, Apache-2.0, BSD-2/3, ISC, CC0, Unlicense, MIT-0) | 31,515 | 27.3% |
| copyleft or share-alike (GPL-2/3, AGPL-3, LGPL, MPL-2, CC-BY, CC-BY-SA) | 1,983 | 1.7% |

Publishing the index would redistribute 71,236 files of other people's source
code from repositories that granted no licence at all. That is not a formality:
no licence means all rights reserved.

**A licence-filtered index would be publishable and would not be this
instrument.** Filtering to the permissive bucket leaves roughly 34,000 rows —
under 30% of the haystack. The measured result (24/24, with 18 of the
attributable fetches at rank 1) belongs to the 118,400-row corpus including its
115,574 unverified rows, and the pre-registration's stated failure mode was
precisely that those rows would *dilute* the ranking. They did not, and that is
part of the finding. A third-sized index does not test the same thing.

The two vector/lexicon artifacts are also 485 MB and 49 MB, which would be a
release-asset decision even with no licence question at all.

## Supplying your own

`code_search` ranks from the index; `code_get` is a single-node Cypher lookup.
So the arm needs a Neo4j database of `:CodeSample` nodes **and** an index built
from it. The arm traverses no relationship and reads no other label — that is
checked mechanically by `src/qc/qc_code_only_arm.py`, which refuses on any `-[`
pattern, any `:Method`, any `:Paper`, and on any index row carrying a level > 0
with no report behind it.

### Node properties the builders read

| property | used by | notes |
|---|---|---|
| `code_sha256` | both, and identity | the primary key. Entry names collide — 386 of 1,179 served names do — so identity is the hash, never the name |
| `entry` | index, `code_get` | function name; weighted ×3 lexically |
| `signature` | index, `code_get` | |
| `code` | index (first 1,200 chars), `code_get` (in full) | |
| `language` | index, `code_get` | |
| `source_kind` | index, `code_get` | `harvested` or `generated` |
| `verification_level` | index, `code_get` | **reported as 0 unless `verification_report` is present** |
| `verification_report` | index (presence), `code_get` (in full) | |
| `test_cases`, `test_cases_provenance`, `test_cases_n` | `code_get`, index (count) | |
| `paper_attribution` | index, `code_get` | origin arXiv id, denormalised onto the node |
| `env`, `generated_by`, `cross_checked_by`, `spec_review`, `review_note` | `code_get` | |
| `embedding`, `embedding_model` | vector build | 1,024-dim float; absent rows are **counted**, never silently dropped |
| `embedding_truncated` | `code_get` | |

A range index on `code_sha256` is assumed: both builders page with a
`WHERE c.code_sha256 > $cursor ... ORDER BY c.code_sha256` cursor so a dropped
connection resumes where it stopped.

### Build

```bash
export NEO4J_URI=... NEO4J_USER=... NEO4J_PASSWORD=... NEO4J_DATABASE=neo4j
python3 src/build_code_index.py   --out ./code_index      # lexicon.pkl + records.jsonl
python3 src/build_code_vectors.py --out ./code_index      # all_vectors.npy + all_shas.json
export CODE_ONLY_INDEX=./code_index
python3 src/qc/qc_code_only_arm.py                        # must exit 0
```

`--limit` exists on the lexical builder for smoke tests and **a limited index is
not valid for a run** — the arm's own docstring says so and the QC gate does not
excuse it.

Row *i* of `lexicon.pkl` and row *i* of `all_vectors.npy` must be the same
sample. Both builds use the same `ORDER BY c.code_sha256` cursor, and the
alignment is **asserted at load time**, not assumed: a misalignment would return
the code of a different sample from the one that was ranked, silently.

### Retrieval, for the record

Hybrid, fused by reciprocal rank (RRF, k = 60, untuned):

- **lexical**: BM25 (k1 = 1.2, b = 0.75) over the fields above, with
  snake_case and CamelCase splitting so `compute_chameleon_domain_weights` is
  reachable from `chameleon`; tokens appearing in more than 30% of the corpus
  are dropped;
- **semantic**: exhaustive cosine over every vector — brute force, not ANN,
  because the read credential could not execute `db.index.vector.queryNodes`
  and because exact ranking is the only way a `min_level` filter stays
  meaningful when the filtered slice is 2.6% of the rows;
- an **exact entry-name match** pinned above the fused list;
- a **verified facet**: up to 5 backed level ≥ 2 matches listed separately, so
  115,574 rows of level-0 harvested code cannot bury the verified answer.

Two of those affordances turned out to be inert in the run, which is reported
rather than quietly dropped: **zero** fetches came from the verified facet, and
only **two** came through the exact-entry pin. What agents actually typed was a
method name plus a description, and the plain fused ranking put the right sample
on top.
