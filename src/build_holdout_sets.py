#!/usr/bin/env python3
"""
Build the per-task hold-out sets for the substitution experiment
(PREREGISTRATION_SUBSTITUTION.md). Read-only (C3).

WHAT A HOLD-OUT HAS TO REMOVE. The experiment asks what each arm offers when
the exact answer is not in the corpus. That is only the question being asked
if "the exact answer" is gone in every form it exists in, so the set is built
from four rules and their union is what both arms enforce:

  H1  paper_attribution == the task's origin arXiv id.
      The generated reference implementation AND every file harvested from
      that paper's own repository. Removing only the served sample would
      leave the paper's own source code one query away, and an arm that
      retrieved it would have found the answer, not a substitute.
  H2  reachable as (:Method {name_lower: the task's method})-[:HAS_REFERENCE_IMPL]->
      Whatever the graph would serve for that method name, including samples
      attributed elsewhere.
  H3  reachable as (:Paper {arxiv_id})-[:PROPOSES]->(:Method)-[:HAS_REFERENCE_IMPL]->
      The serving path the v1.5 run measured, spelled out rather than assumed
      to be a subset of H1 and H2.
  H4  entry name equal to the task's entry, normalised.
      The prompt hands the subject the exact entry function name because the
      referee calls it, and the flat index pins exact entry matches above
      everything else. A same-named sample from another paper is the answer
      arriving by a different sha, so it goes too. (This is the ONE rule that
      can remove genuinely unrelated code -- 386 of 1,179 served entry names
      collide -- and it removed 4 samples in 24 tasks, which is the price of
      not arguing case by case about which collision was really a substitute.)

WHAT IT DELIBERATELY DOES NOT REMOVE: everything else. Other papers' code,
other methods, near-duplicates of the same routine written for a different
paper. Those ARE the substitutes, and the experiment is about whether either
arm can find them.

    ./venv/bin/python3 <BENCH>/build_holdout_sets.py \
        --tasks .../tasks/tasks_substitution.json --out .../tasks/holdout_sets.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
sys.path.insert(0, str(HERE))

import provenance  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402

# H4 is computed from the ARM'S OWN entry index, not from a second copy of
# the normalisation rule and not from Cypher. Two reasons, one practical and
# one about correctness: there is no `entry_lower` twin on :CodeSample, and
# `toLower(c.entry)` in a predicate is the title-scan latency incident; and
# more importantly, a hold-out derived from the same table the arm pins
# exact-entry matches on cannot disagree with what the arm blocks. R10 by
# construction rather than by assertion.
import code_only_arm_tools as _flat  # noqa: E402


def build(session, task: dict) -> dict:
    aid, entry, method = task["arxiv_id"], task["entry"], task["method"]
    h1 = session.run(
        "MATCH (c:CodeSample) WHERE c.paper_attribution = $aid "
        "RETURN collect(DISTINCT c.code_sha256) AS shas", aid=aid).single()["shas"]
    h2 = session.run(
        "MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(c:CodeSample) "
        "WHERE m.name_lower = toLower($n) "
        "RETURN collect(DISTINCT c.code_sha256) AS shas", n=method).single()["shas"]
    h3 = session.run(
        "MATCH (p:Paper {arxiv_id: $aid})-[:PROPOSES]->(:Method)"
        "-[:HAS_REFERENCE_IMPL]->(c:CodeSample) "
        "RETURN collect(DISTINCT c.code_sha256) AS shas", aid=aid).single()["shas"]
    lex = _flat._load_index()
    h4 = [lex["sha"][i] for i in _flat._entry_exact.get(_flat._norm(entry), [])]

    served = session.run(
        "MATCH (p:Paper {arxiv_id: $aid})-[:PROPOSES]->(m:Method)"
        "-[:HAS_REFERENCE_IMPL]->(c:CodeSample) "
        "WHERE c.verification_report IS NOT NULL "
        "RETURN c.code_sha256 AS sha, c.entry AS entry, m.name AS method, "
        "       c.verification_level AS lvl ORDER BY c.verification_level DESC",
        aid=aid).data()
    union = sorted(set(h1) | set(h2) | set(h3) | set(h4))
    return {
        "task_id": task["task_id"], "arxiv_id": aid, "method": method,
        "entry": entry, "entry_norm": _flat._norm(entry),
        "shas": union,
        "by_rule": {"H1_paper_attribution": sorted(set(h1)),
                    "H2_method_impl": sorted(set(h2)),
                    "H3_paper_proposes_impl": sorted(set(h3)),
                    "H4_same_entry_name": sorted(set(h4))},
        "served_by_graph": served,
        "served_sha_in_holdout": all(r["sha"] in set(union) for r in served),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))["tasks"]
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    ledger = provenance.ExclusionLedger()
    out = {}
    with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
        for t in tasks:
            rec = build(s, t)
            if not rec["shas"]:
                # A task whose answer is not in the corpus cannot be held out,
                # and running it as a hold-out arm would silently measure the
                # ordinary condition. Excluded and counted (R3), never quietly
                # passed through.
                ledger.exclude("nothing_to_hold_out")
                print(f"  [excluded] {t['task_id']}: nothing to hold out")
                continue
            if not rec["served_by_graph"]:
                ledger.exclude("graph_serves_nothing")
                print(f"  [excluded] {t['task_id']}: graph serves no backed sample")
                continue
            ledger.process()
            out[t["task_id"]] = rec
            print(f"  {t['task_id']:>20}  {len(rec['shas']):>3} shas  "
                  f"(H1={len(rec['by_rule']['H1_paper_attribution'])} "
                  f"H2={len(rec['by_rule']['H2_method_impl'])} "
                  f"H3={len(rec['by_rule']['H3_paper_proposes_impl'])} "
                  f"H4={len(rec['by_rule']['H4_same_entry_name'])})")
    driver.close()

    provenance.write_json(
        Path(args.out),
        {"holdout": out,
         "n_tasks": len(out),
         "n_shas_total": sum(len(v["shas"]) for v in out.values()),
         "rules": ["H1 paper_attribution", "H2 method HAS_REFERENCE_IMPL",
                   "H3 paper PROPOSES method HAS_REFERENCE_IMPL",
                   "H4 same entry name (normalised)"]},
        inputs=[Path(args.tasks)], params=vars(args), exclusions=ledger, indent=2)
    print(f"\nwrote {len(out)} hold-out sets -> {args.out}")
    ledger.enforce(accept=())


if __name__ == "__main__":
    main()
