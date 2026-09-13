#!/usr/bin/env python3
"""
Pull all 118,400 :CodeSample embeddings so the `code_only` arm can search
them EXHAUSTIVELY (PREREGISTRATION_CODE_ONLY.md).

WHY LOCAL AND EXHAUSTIVE, not the server-side ANN index. Two reasons, and
the first is the decisive one:

1. The read credential cannot execute it. `db.index.vector.queryNodes` on
   `syntology_api_reader` returns
   `Neo.ClientError.Security.Forbidden ... roles [PUBLIC, reader]` -- the
   Aura RBAC state this project already knows about. The documented
   workaround is a role assignment, which is an admin write, and this
   session is read-only by contract. So the vector half either goes local
   or does not exist, and an arm with no semantic search would be a
   strawman.
2. Local brute force is STRONGER than the index it replaces. 485 MB of
   float32 is one numpy matmul per query (~50 ms), exact rather than
   approximate, and -- the part that matters for this benchmark -- it
   ranks the whole corpus even when the caller filters to the 3,125
   samples with a backed level >= 2. An ANN top-k over 118,400 would put
   most of those out of reach at any reasonable k.

Nothing here traverses a relationship or reads a :Method or :Paper node.
Read-only.

R1: the .npy gets a provenance sidecar naming the graph URI, the node
count, and the embedding model the vectors came from.

    ./venv/bin/python3 <BENCH>/build_code_vectors.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import numpy as np  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402

import provenance  # noqa: E402

BATCH = 1000
DIMS = 1024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "code_index"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    vec_p, sha_p = out / "all_vectors.npy", out / "all_shas.json"

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    shas, blocks, models = [], [], set()
    missing = 0
    t0, cursor = time.time(), ""
    with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
        while True:
            rows = s.run("""
                MATCH (c:CodeSample) WHERE c.code_sha256 > $cursor
                RETURN c.code_sha256 AS sha, c.embedding AS v,
                       c.embedding_model AS model
                ORDER BY c.code_sha256 LIMIT $batch
            """, cursor=cursor, batch=BATCH).data()
            if not rows:
                break
            buf = np.zeros((len(rows), DIMS), dtype=np.float32)
            for i, r in enumerate(rows):
                if r["v"] is None:
                    # R3d: an absent vector is booked, not silently dropped --
                    # a zero row can never be anyone's nearest neighbour, and
                    # the count is reported so "118,400 searched" stays true.
                    missing += 1
                else:
                    buf[i] = np.asarray(r["v"], dtype=np.float32)
                    models.add(r["model"])
                shas.append(r["sha"])
            blocks.append(buf)
            cursor = rows[-1]["sha"]
            if len(shas) % 20000 < BATCH:
                print(f"  {len(shas)} pulled ({time.time()-t0:.0f}s)", flush=True)
    driver.close()

    M = np.vstack(blocks)
    n = np.linalg.norm(M, axis=1, keepdims=True)
    n[n == 0] = 1.0
    M = (M / n).astype(np.float32)
    np.save(vec_p, M)
    sha_p.write_text(json.dumps(shas))
    params = {"uri": os.environ["NEO4J_URI"], "n": len(shas),
              "dims": DIMS, "embedding_models": sorted(models),
              "rows_without_embedding": missing,
              "normalized": True,
              "traversals": "none -- :CodeSample node properties only"}
    provenance.write_sidecar(vec_p, inputs=[], params=params)
    provenance.write_sidecar(sha_p, inputs=[], params=params)
    print(f"{len(shas)} vectors ({missing} rows had none) -> {vec_p} "
          f"({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
