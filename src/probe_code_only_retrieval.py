#!/usr/bin/env python3
"""
Offline retrieval probe for the `code_only` arm
(PREREGISTRATION_CODE_ONLY.md, "Offline retrieval probe").

WHAT IT MEASURES, AND WHY BEFORE THE SWEEP. The live sweep measures an
agent's behaviour; this measures the arm's CEILING, with zero subject spend.
If `code_only` fails the sweep it matters enormously whether the index could
not surface the code (a retrieval fact) or the agent did not ask for it (a
behavioural fact), and after the sweep those two are hard to separate from
transcripts alone. So the ceiling is measured first and pre-registered.

THREE QUERY FORMS, because the prompt hands the subject three different keys
and they are not equally fair to a flat index:
  Q1  the entry function name           -- the key a code index is built for
  Q2  the method name                   -- the key the GRAPH's resolvers use
  Q3  method name + the first sentence  -- the natural-language form
Each is re-scored with `no_origin=True`, which drops the numeric tokens that
can only be reaching the denormalised `paper_attribution` field. That is
disclosed asymmetry 1's counterfactual: the result with and without the
origin-id route.

GROUND TRUTH IS RESOLVED GRAPH-SIDE, FOR ANALYSIS ONLY. The arm never sees
it. A sample counts as correct when it carries the task's origin arXiv id
AND the task's entry name -- that is the artifact that would pass the
referee. The set the graph actually serves (Paper->PROPOSES->Method->
HAS_REFERENCE_IMPL) is resolved too and reported as a cross-check, because a
disagreement between the two would mean the probe is scoring the wrong
target.

R1: output is provenance-stamped. Read-only (C3).

    ./venv/bin/python3 <BENCH>/probe_code_only_retrieval.py
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
sys.path.insert(0, str(HERE))

from neo4j import GraphDatabase  # noqa: E402

import provenance  # noqa: E402
import code_only_arm_tools as C  # noqa: E402

LIMIT = 50
KS = (1, 5, 15, 50)


def ground_truth(session, task) -> dict:
    """The sample(s) that would pass, plus what the graph serves, plus what
    the flat corpus holds for this paper at all."""
    aid, entry = task["arxiv_id"], task["entry"]
    correct = session.run("""
        MATCH (c:CodeSample)
        WHERE c.paper_attribution = $aid AND c.entry = $entry
        RETURN c.code_sha256 AS sha, c.verification_level AS lvl,
               c.verification_report IS NOT NULL AS backed
    """, aid=aid, entry=entry).data()
    served = session.run("""
        MATCH (p:Paper {arxiv_id: $aid})-[:PROPOSES]->(m:Method)-[:HAS_REFERENCE_IMPL]->(c:CodeSample)
        RETURN c.code_sha256 AS sha, m.name AS method, c.entry AS entry,
               c.verification_level AS lvl,
               c.verification_report IS NOT NULL AS backed
    """, aid=aid).data()
    any_code = session.run("""
        MATCH (c:CodeSample) WHERE c.paper_attribution = $aid
        RETURN count(c) AS n
    """, aid=aid).single()["n"]
    return {
        "correct_shas": [r["sha"] for r in correct],
        "correct_backed_level": [int(r["lvl"] or 0) if r["backed"] else 0
                                 for r in correct],
        "graph_served_shas": [r["sha"] for r in served],
        "graph_served_entries": sorted({r["entry"] for r in served}),
        "samples_for_this_paper_in_flat_corpus": any_code,
    }


def rank_of(res: dict, targets: set) -> tuple[int | None, bool]:
    for i, r in enumerate(res.get("results", [])):
        if r["code_sha256"] in targets:
            return i + 1, True
    in_facet = any(r["code_sha256"] in targets
                   for r in res.get("verified_matches", []))
    return None, in_facet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=str(REPO / "tasks" / "tasks_freeze.json"))
    ap.add_argument("--out", default=str(REPO / "data" / "probe_code_only_retrieval.json"))
    args = ap.parse_args()

    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))["tasks"]
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    rows = []
    ledger = provenance.ExclusionLedger()
    t0 = time.time()
    with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
        for t in tasks:
            gt = ground_truth(s, t)
            targets = set(gt["correct_shas"])
            row = {"task_id": t["task_id"], "stratum": t["stratum"],
                   "method": t["method"], "entry": t["entry"],
                   "arxiv_id": t["arxiv_id"], **gt}
            if not targets:
                # R3: a task with no reachable target is EXCLUDED from the
                # recall denominators and says so, rather than counting as a
                # retrieval miss the index could never have avoided.
                ledger.exclude("no_target_sample_in_flat_corpus")
                row["queries"] = {}
                rows.append(row)
                continue
            queries = {
                "Q1_entry": t["entry"],
                "Q2_method": t["method"],
                "Q3_method_plus_sentence": f"{t['method']}: {t['first_sentence']}",
            }
            row["queries"] = {}
            for qname, q in queries.items():
                cell = {}
                for variant, no_origin in (("with_origin", False),
                                           ("no_origin", True)):
                    res = C.code_search(q, limit=LIMIT, min_level=0,
                                        no_origin=no_origin)
                    rk, facet = rank_of(res, targets)
                    cell[variant] = {
                        "rank": rk, "in_verified_facet": facet,
                        "top1_entry": (res["results"][0]["entry"]
                                       if res["results"] else None),
                        "matched_by": (res["results"][rk - 1]["matched_by"]
                                       if rk else None),
                    }
                row["queries"][qname] = cell
            ledger.process()
            rows.append(row)
            print(f"  {t['task_id']:<22} "
                  + "  ".join(f"{k.split('_')[0]}={row['queries'][k]['with_origin']['rank']}"
                              for k in queries), flush=True)
    driver.close()

    # recall table -----------------------------------------------------------
    def recall(stratum, qname, variant):
        cell = [r for r in rows
                if r["stratum"] == stratum and r.get("queries")]
        out = {}
        for k in KS:
            hit = sum(1 for r in cell
                      if (r["queries"][qname][variant]["rank"] or 10 ** 9) <= k)
            out[f"recall@{k}"] = [hit, len(cell)]
        out["in_verified_facet"] = [
            sum(1 for r in cell
                if r["queries"][qname][variant]["in_verified_facet"]
                or (r["queries"][qname][variant]["rank"] or 10 ** 9) <= LIMIT),
            len(cell)]
        return out

    summary = {}
    for stratum in ("in_catalog", "off_catalog"):
        summary[stratum] = {
            q: {v: recall(stratum, q, v) for v in ("with_origin", "no_origin")}
            for q in ("Q1_entry", "Q2_method", "Q3_method_plus_sentence")}

    print("\n## Retrieval ceiling (rank of the correct sample in code_search)\n")
    for stratum, block in summary.items():
        print(f"[{stratum}]")
        for q, vv in block.items():
            for v, r in vv.items():
                print(f"  {q:<26} {v:<12} "
                      + "  ".join(f"@{k}={r[f'recall@{k}'][0]}/{r[f'recall@{k}'][1]}"
                                  for k in KS)
                      + f"  facet_or_top50={r['in_verified_facet'][0]}/{r['in_verified_facet'][1]}")
        print()

    provenance.write_json(Path(args.out),
                          {"rows": rows, "summary": summary,
                           "limit": LIMIT, "wall_s": round(time.time() - t0, 1)},
                          inputs=[Path(args.tasks),
                                  HERE / "code_index" / "lexicon.pkl"],
                          params=vars(args), exclusions=ledger, indent=1)
    print(f"wrote {args.out}")
    return ledger.enforce(accept=("no_target_sample_in_flat_corpus",))


if __name__ == "__main__":
    sys.exit(main() or 0)
