#!/usr/bin/env python3
"""
Enlarge the benchmark task set for the substitution experiment
(PREREGISTRATION_SUBSTITUTION.md). Read-only (C3).

WHY NEW TASKS AT ALL. The v1.5 result is a ceiling tie at n=24 and its own
power table says more tasks *of that shape* cannot rank the arms. Holding the
answer out changes the shape -- both arms drop off the ceiling -- but a
paired sign test still needs discordant pairs, and at n=24 it needs six of
them all pointing one way. So n goes up before the run rather than being
apologised for after it.

ADMISSION RULE, and it is stricter than the original builder's. A task is
admitted only when, WITHOUT the hold-out, both arms would have found the
exact answer:

  1. `v3_results.jsonl` granted it V3 (paper-derived property tests pass on
     two independently generated implementations), and the recorded impl
     still passes its full `pass_both` set in today's sandbox -- the same
     revalidation `build_task_set.py` does, reused from it rather than
     re-typed.
  2. The GRAPH serves a report-backed level >= 2 CodeSample for the method.
  3. The FLAT INDEX holds a sample carrying that paper's arXiv id and that
     entry name.

Without 2 and 3 the hold-out would be removing nothing from one of the arms,
and a task where one arm never had the answer cannot measure what either arm
does when the answer is taken away.

Tasks already in `tasks_freeze.json` are excluded here and re-attached by
`--carry-forward`, so the 24 that v1.5 measured at ceiling stay in the set
and stay paired with it.

    ./venv/bin/python3 <BENCH>/build_task_set_substitution.py \
        --n-new 24 --out .../tasks/tasks_substitution.json
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
sys.path.insert(0, str(HERE))

import provenance  # noqa: E402
import code_only_arm_tools as _flat  # noqa: E402
from build_task_set import BATCH, V3_RESULTS, _candidate, _revalidate  # noqa: E402

SEED = 20260910


def _graph_facts(methods, aids):
    """Served level per method name, and (aid, entry) pairs the graph holds."""
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
        served = s.run("""
            MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
            WHERE m.name_lower IN $names
            RETURN m.name_lower AS name,
                   max(CASE WHEN cs.verification_report IS NOT NULL
                            THEN cs.verification_level ELSE 0 END) AS lvl
        """, names=[m.lower() for m in methods]).data()
        titles = s.run("""
            MATCH (p:Paper) WHERE p.arxiv_id IN $aids
            RETURN p.arxiv_id AS aid, p.title AS title
        """, aids=list(aids)).data()
    driver.close()
    return ({r["name"]: int(r["lvl"] or 0) for r in served},
            {t["aid"]: t["title"] for t in titles})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-new", type=int, default=24)
    ap.add_argument("--carry-forward",
                    default=str(REPO / "tasks" / "tasks_freeze.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    carried = json.loads(Path(args.carry_forward).read_text(encoding="utf-8"))["tasks"]
    seen_aids = {t["arxiv_id"] for t in carried}

    recs = [json.loads(l) for l in open(V3_RESULTS, encoding="utf-8")]
    pool = [r for r in recs
            if r.get("v3") == "V3" and r.get("method")
            and r.get("arxiv_id") not in seen_aids]

    ledger = provenance.ExclusionLedger()
    # The flat index's (origin, entry) table, built once: condition 3 is a
    # membership test against exactly what the arm can rank.
    lex = _flat._load_index()
    flat_pairs = {(lex["origin"][i], lex["entry"][i]) for i in range(lex["n_docs"])}

    served, titles = _graph_facts({r["method"] for r in pool},
                                  {r["arxiv_id"] for r in pool})

    rng = random.Random(args.seed)
    rng.shuffle(pool)

    new_tasks, screened, revalidated = [], 0, 0
    for r in pool:
        if len(new_tasks) >= args.n_new:
            break
        screened += 1
        if served.get((r["method"] or "").lower(), -1) < 2:
            ledger.exclude("graph_serves_below_v2")
            continue
        cand, why = _candidate(r, BATCH / r["arxiv_id"])
        if cand is None:
            ledger.exclude(why)
            continue
        if (r["arxiv_id"], cand["entry"]) not in flat_pairs:
            ledger.exclude("flat_index_lacks_the_answer")
            continue
        ok, why = _revalidate(cand)
        revalidated += 1
        if not ok:
            ledger.exclude(why.split(":")[0])
            continue
        ledger.process()
        new_tasks.append({
            "task_id": f"sub_{r['arxiv_id']}",
            "stratum": "substitution_new",
            "method": r["method"],
            "arxiv_id": r["arxiv_id"],
            "paper_title": titles.get(r["arxiv_id"]),
            "served_level": served.get((r["method"] or "").lower(), -1),
            **cand,
        })
        print(f"  [task] {r['method'][:38]:<38} {r['arxiv_id']}  "
              f"props={len(cand['pass_both'])}")

    tasks = [dict(t, stratum_v15=t["stratum"]) for t in carried] + new_tasks
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    provenance.write_json(out, {
        "seed": args.seed,
        "n_carried_forward": len(carried),
        "n_new": len(new_tasks),
        "pool_after_exclusions": len(pool),
        "candidates_screened": screened,
        "referees_revalidated_today": revalidated,
        "admission_rule": ["v3_granted_and_revalidates",
                           "graph_serves_backed_level_ge_2",
                           "flat_index_holds_origin_plus_entry"],
        "tasks": tasks,
    }, inputs=[V3_RESULTS, Path(args.carry_forward)], params=vars(args),
        exclusions=ledger, indent=2)
    print(f"\nwrote {len(tasks)} tasks ({len(carried)} carried + "
          f"{len(new_tasks)} new) -> {out}")
    # Screening exclusions ARE this script's purpose: it walks a 1,911-record
    # pool to find n admissible tasks, so every rejection is a decision it was
    # asked to make. They are still counted and printed.
    ledger.enforce(accept=("graph_serves_below_v2", "flat_index_lacks_the_answer",
                           "missing_files", "spec_unreadable", "spec_incomplete",
                           "too_few_properties", "referee_crashed",
                           "referee_regressed"))


if __name__ == "__main__":
    main()
