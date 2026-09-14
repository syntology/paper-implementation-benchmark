#!/usr/bin/env python3
"""
Offline substitution probe (PREREGISTRATION_SUBSTITUTION.md). Zero subject
spend, run before the sweep. Read-only (C3).

WHAT IT MEASURES, AND WHY BEFORE THE SWEEP. The sweep measures an agent's
behaviour. This measures what each arm HAS to offer once the answer is held
out, independent of whether an agent asks for it. If both arms score badly in
the sweep it matters enormously whether neither surface held a substitute (a
corpus fact) or the agents did not use the one that was there (a behavioural
fact), and after the sweep those are hard to separate from transcripts.

FOUR THINGS, per task, all under the task's own hold-out:

  1. FLAT -- what `code_search` ranks in place of the answer, for the three
     query forms the v1.5 probe used. Non-empty? What is at rank 1?
  2. GRAPH -- what `get_reference_implementation` degrades to (which
     fallback tier), and whether `list_reference_implementations` still
     offers a near match for the method name.
  3. THE COMPOSE COUNTERFACTUAL -- `compose` on the target entry with the
     hold-out OFF. The hold-out makes the graph's one proximity tool
     inoperable (it resolves its subject from the universe it also draws
     partners from), which is disclosed as a cost in the pre-registration
     rather than excepted away. This is how that cost is priced: what
     compose WOULD have offered. If those partners are good and the tool
     could not be invoked, the finding is that the graph's proximity tool
     keys on the artifact you do not have -- a serving-design defect, and a
     more useful result than a relaxed hold-out.
  4. OVERLAP -- does the flat index's top substitute appear among the
     partners compose would have named? That asks whether the two arms'
     notions of "nearby" even coincide.

    ./venv/bin/python3 <BENCH>/probe_substitution.py \
        --tasks .../tasks/tasks_substitution.json --holdout .../tasks/holdout_sets.json
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

import provenance  # noqa: E402
import benchmark_holdout as HO  # noqa: E402
import code_only_arm_tools as FLAT  # noqa: E402
import syntology_arm_tools as GRAPH  # noqa: E402

TOP = 5


def flat_head(resp):
    return [{"entry": r["entry"], "origin": r["origin_arxiv_id"],
             "level": r["verification_level"], "matched_by": r["matched_by"]}
            for r in resp.get("results", [])[:TOP]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--holdout", required=True)
    ap.add_argument("--out", default=str(REPO / "data" / "probe_substitution.json"))
    args = ap.parse_args()

    tasks = {t["task_id"]: t
             for t in json.loads(Path(args.tasks).read_text(encoding="utf-8"))["tasks"]}
    ho = json.loads(Path(args.holdout).read_text(encoding="utf-8"))["holdout"]

    rows = []
    t0 = time.time()
    for tid, rec in ho.items():
        task = tasks[tid]
        shas = set(rec["shas"])
        row = {"task_id": tid, "method": task["method"], "entry": task["entry"],
               "arxiv_id": task["arxiv_id"]}

        # 3 -- compose counterfactual FIRST, with the hold-out off.
        HO.clear_holdout()
        try:
            c = GRAPH.compose(task["entry"], direction="downstream", min_level=2)
            row["compose_counterfactual"] = {
                "resolved": True, "total": c["total"], "typed": c["typed"],
                "adapter": c["adapter"],
                "effectively_terminal": c["effectively_terminal"],
                "partners": [{"entry": p["entry"], "method": p["method"],
                              "paper": p["paper"], "tier": p["tier"],
                              "level": p["verification_level"]}
                             for p in c["partners"][:TOP]]}
        except ValueError as e:
            row["compose_counterfactual"] = {"resolved": False,
                                             "why": str(e)[:120]}

        # 1 + 2 -- both arms, hold-out ON
        HO.set_holdout(shas)
        row["flat"] = {}
        for label, q in (("Q1_entry", task["entry"]),
                         ("Q2_method", task["method"]),
                         ("Q3_method_plus_sentence",
                          f"{task['method']} {task['first_sentence']}")):
            r = FLAT.code_search(q, limit=TOP)
            row["flat"][label] = {"total_ranked": r["total_ranked"],
                                  "returned": r["returned"],
                                  "head": flat_head(r),
                                  "n_verified_facet": len(r.get("verified_matches", []))}
        g = {}
        try:
            r = GRAPH.get_reference_implementation(task["method"], min_level=2)
            g["outcome"] = ("served" if r.get("implementations")
                            else f"fallback:{(r.get('fallback') or {}).get('tier')}")
            g["resolved_via"] = r.get("resolved_via")
        except ValueError as e:
            g["outcome"] = "raised"
            g["message"] = str(e)[:200]
        lr = GRAPH.list_reference_implementations(query=task["method"], limit=TOP)
        g["list_total_matching"] = lr["total_matching"]
        g["list_head"] = [{"method": i["method"], "origin": i["origin_arxiv_id"],
                           "level": i["verification_level"]}
                          for i in lr.get("implementations", [])[:TOP]]
        g["near_matches"] = [{"method": i["method"], "origin": i["origin_arxiv_id"]}
                             for i in lr.get("near_matches", [])[:TOP]]
        row["graph"] = g

        # 4 -- overlap between the two arms' notions of "nearby"
        cc = row.get("compose_counterfactual") or {}
        partner_entries = {p["entry"] for p in cc.get("partners", [])}
        flat_entries = {h["entry"] for lab in row["flat"]
                        for h in row["flat"][lab]["head"]}
        row["overlap_flat_top_in_compose_partners"] = sorted(
            partner_entries & flat_entries)

        HO.clear_holdout()
        rows.append(row)
        print(f"  {tid:>22}  flat_top={row['flat']['Q3_method_plus_sentence']['head'][:1]}"
              f"  graph={g['outcome']}  compose={cc.get('total', cc.get('resolved'))}")

    n = len(rows)
    summary = {
        "n_tasks": n,
        "flat_nonempty_Q3": sum(1 for r in rows
                                if r["flat"]["Q3_method_plus_sentence"]["returned"]),
        "graph_served_anyway": sum(1 for r in rows
                                   if r["graph"]["outcome"] == "served"),
        "graph_fallback": sum(1 for r in rows
                              if str(r["graph"]["outcome"]).startswith("fallback")),
        "graph_raised": sum(1 for r in rows if r["graph"]["outcome"] == "raised"),
        "list_total_matching_zero": sum(1 for r in rows
                                        if r["graph"]["list_total_matching"] == 0),
        "list_offered_near_matches": sum(1 for r in rows if r["graph"]["near_matches"]),
        "compose_would_have_resolved": sum(
            1 for r in rows if r["compose_counterfactual"].get("resolved")),
        "compose_typed_partners_median": sorted(
            r["compose_counterfactual"].get("typed", 0) for r in rows)[n // 2] if n else 0,
        "tasks_with_overlap": sum(1 for r in rows
                                  if r["overlap_flat_top_in_compose_partners"]),
    }
    provenance.write_json(Path(args.out),
                          {"rows": rows, "summary": summary, "top": TOP,
                           "wall_s": round(time.time() - t0, 1)},
                          inputs=[Path(args.tasks), Path(args.holdout)],
                          params=vars(args), indent=2)
    print("\n" + json.dumps(summary, indent=1))
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
