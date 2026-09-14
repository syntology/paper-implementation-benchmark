#!/usr/bin/env python3
"""
Build the FLAT CodeSample index that the `code_only` benchmark arm serves
(PREREGISTRATION_CODE_ONLY.md).

WHAT THIS IS FOR. Every prior arm of this benchmark tested the graph *with*
the code (`syntology`, `both`) or neither (`none`, `search`). Nothing has
tested the code *without* the graph, which is the owner's actual question:
is the graph load-bearing for discovery given that the CodeSamples exist?
This builds the honest answer's substrate -- all 118,400 :CodeSample nodes
as a flat table, with no relationship ever traversed and no :Method or
:Paper node ever read.

WHY A LOCAL INDEX AND NOT CYPHER. There is no index on `CodeSample.entry`
and no fulltext index on `CodeSample.code`, so a lexical query in Cypher is
a 400 MB full scan per call (and `toLower(property)` in a predicate is the
title-scan latency incident, which this project does not repeat). The vector
side needs no local copy: `codesample_embedding` is an ONLINE vector index
and `db.index.vector.queryNodes` is a read. So the lexical half is built
here, once, offline, and the semantic half stays server-side.

READ-ONLY. C3 for this session: no Neo4j writes. This script only reads,
and it reads nothing but `:CodeSample` node properties.

WHAT GOES IN THE LEXICAL INDEX, and why each field. Building the arm to
lose would be worse than not running the ablation at all, so the index gets
every field a real flat code index would carry:
  entry                 -- the function name (weighted x3: it is the field
                           a code index is most often queried by)
  signature             -- present on 104 nodes; free when it is there
  paper_attribution     -- the origin arXiv id, DENORMALISED ONTO THE NODE.
                           This is disclosed as an asymmetry in the
                           pre-registration, not smuggled: the graph arm has
                           the same route via get_code_for_paper, so
                           excluding it here would be tuning the arm to lose.
                           Hits that matched on it are tagged `origin_id` so
                           the mechanism analysis can separate them.
  code head (1,200 ch)  -- def line, docstring and the first statements.
                           The full 400 MB body is not indexed lexically;
                           the semantic half covers whole-function meaning
                           (the corpus vectors embed entry + up to 24k chars
                           of code, per generate_code_embeddings.py).

R1: records.jsonl and lexicon.pkl each get a provenance sidecar naming the
graph URI, the node count, and the field list they were built from.

    ./venv/bin/python3 <BENCH>/build_code_index.py
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import numpy as np  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402

import provenance  # noqa: E402

CODE_HEAD_CHARS = 1200
ENTRY_WEIGHT = 3          # entry tokens counted 3x in the bag of words
BATCH = 2000

# Same generic-token list the graph arm's resolvers import from one place
# (syntology_arm_tools.GENERIC_METHOD_TOKENS): three resolver paths had the
# same bug independently -- matching a query on a shared word like "method".
# Imported rather than re-typed so the two arms cannot drift apart on it.
sys.path.insert(0, str(HERE))
from syntology_arm_tools import GENERIC_METHOD_TOKENS  # noqa: E402

_TOK = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens, plus the camelCase/snake_case pieces.

    `compute_chameleon_domain_weights` must be findable by "chameleon", so a
    snake_case identifier contributes its parts as well as itself. Same for
    CamelCase. This is standard code-search tokenisation, not a benchmark
    affordance -- GitHub code search does it too.
    """
    out = []
    for t in _TOK.findall((text or "").lower()):
        out.append(t)
    # split the ORIGINAL casing for camelCase before it was lowered
    for piece in re.findall(r"[A-Za-z][a-z0-9]*|[0-9]+", text or ""):
        p = piece.lower()
        if p and p not in out:
            out.append(p)
    return out


def fetch_all(session, limit: int | None = None):
    """Stream :CodeSample nodes ordered by the indexed code_sha256.

    Cursor on code_sha256 rather than SKIP/LIMIT: `cs_code_sha256` is a RANGE
    index, so each page is a seek, and a resume after a dropped connection
    lands exactly where it stopped instead of re-counting 118k rows.
    """
    cursor = ""
    n = 0
    while True:
        rows = session.run("""
            MATCH (c:CodeSample)
            WHERE c.code_sha256 > $cursor
            RETURN c.code_sha256 AS sha, c.entry AS entry,
                   c.signature AS signature, c.language AS language,
                   c.source_kind AS source_kind,
                   c.verification_level AS level,
                   c.verification_report IS NOT NULL AS has_report,
                   c.paper_attribution AS origin,
                   c.test_cases_n AS test_cases_n,
                   size(c.code) AS code_len,
                   left(c.code, $head) AS code_head
            ORDER BY c.code_sha256
            LIMIT $batch
        """, cursor=cursor, head=CODE_HEAD_CHARS, batch=BATCH).data()
        if not rows:
            return
        for r in rows:
            yield r
            n += 1
            if limit and n >= limit:
                return
        cursor = rows[-1]["sha"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "code_index"))
    ap.add_argument("--limit", type=int, default=None,
                    help="smoke only; a limited index is NOT valid for a run")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))

    recs_p = out / "records.jsonl"
    t0 = time.time()
    postings: dict[str, list[int]] = defaultdict(list)
    tfs: dict[str, list[int]] = defaultdict(list)
    meta_entry, meta_sha, meta_level, meta_origin = [], [], [], []
    meta_lang, meta_kind, meta_len = [], [], []
    doclen = []
    n = 0
    with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s, \
            recs_p.open("w", encoding="utf-8") as fh:
        for r in fetch_all(s, args.limit):
            # R2 / the 313-node lesson: a level with no verification_report
            # behind it is 0 here, exactly as the graph arm reports it. The
            # flat arm must not become a fourth surface that can regress this.
            lvl = int(r["level"] or 0)
            if not r["has_report"]:
                lvl = 0
            rec = {"sha": r["sha"], "entry": r["entry"],
                   "signature": r["signature"], "language": r["language"],
                   "source_kind": r["source_kind"], "level": lvl,
                   "origin": r["origin"], "test_cases_n": r["test_cases_n"],
                   "code_len": r["code_len"], "code_head": r["code_head"]}
            fh.write(json.dumps(rec) + "\n")

            bag: dict[str, int] = defaultdict(int)
            for t in tokenize(r["entry"] or ""):
                bag[t] += ENTRY_WEIGHT
            for t in tokenize(r["signature"] or ""):
                bag[t] += 1
            for t in tokenize(r["origin"] or ""):
                bag[t] += 1
            for t in tokenize(r["code_head"] or ""):
                bag[t] += 1
            for t, c in bag.items():
                postings[t].append(n)
                tfs[t].append(min(c, 255))
            doclen.append(sum(bag.values()))

            meta_entry.append(r["entry"] or "")
            meta_sha.append(r["sha"])
            meta_level.append(lvl)
            meta_origin.append(r["origin"] or "")
            meta_lang.append(r["language"] or "")
            meta_kind.append(r["source_kind"] or "")
            meta_len.append(r["code_len"] or 0)
            n += 1
            if n % 20000 == 0:
                print(f"  {n} indexed ({time.time()-t0:.0f}s)", flush=True)
    driver.close()

    lex = {
        "postings": {t: (np.asarray(ids, dtype=np.int32),
                         np.asarray(tfs[t], dtype=np.uint8))
                     for t, ids in postings.items()},
        "doclen": np.asarray(doclen, dtype=np.int32),
        "entry": meta_entry, "sha": meta_sha,
        "level": np.asarray(meta_level, dtype=np.int8),
        "origin": meta_origin, "language": meta_lang,
        "source_kind": meta_kind,
        "code_len": np.asarray(meta_len, dtype=np.int32),
        "n_docs": n,
        "entry_weight": ENTRY_WEIGHT,
        "code_head_chars": CODE_HEAD_CHARS,
        "generic_tokens": sorted(GENERIC_METHOD_TOKENS),
    }
    lex_p = out / "lexicon.pkl"
    with lex_p.open("wb") as fh:
        pickle.dump(lex, fh, protocol=4)

    params = {"uri": os.environ["NEO4J_URI"], "n_docs": n,
              "code_head_chars": CODE_HEAD_CHARS,
              "entry_weight": ENTRY_WEIGHT,
              "indexed_fields": ["entry", "signature", "paper_attribution",
                                 f"code[:{CODE_HEAD_CHARS}]"],
              "traversals": "none -- :CodeSample node properties only",
              "vocab": len(postings), "limit": args.limit}
    # No file inputs: the input is the live graph, named in params. R1's
    # requirement is that the derivation be recorded, and for a graph read
    # that is the URI + the node count + the field list.
    provenance.write_sidecar(recs_p, inputs=[], params=params)
    provenance.write_sidecar(lex_p, inputs=[], params=params)
    print(f"indexed {n} CodeSamples, vocab {len(postings)}, "
          f"{time.time()-t0:.0f}s -> {out}")
    if args.limit:
        print("WARNING: --limit was set; this index is a smoke artifact, "
              "not valid for a benchmark run", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
