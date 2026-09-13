#!/usr/bin/env python3
"""
Build the stratified task set for the graph-vs-search benchmark
(PREREGISTRATION.md). Two strata:

  in_catalog   V3-granted in v3_results.jsonl AND served by the live
               graph at V3 (HAS_REFERENCE_IMPL, report-backed level 3).
  off_catalog  V3-granted in v3_results.jsonl but NOT served at level
               >= 2 -- the graph can offer at most fallback tiers.

Every candidate's referee is REVALIDATED today: the recorded impl must
still pass its full pass_both property set in the current sandbox before
the task is admitted. Failures are excluded and counted (R3).

Usage:
    ./venv/bin/python3 <BENCH>/build_task_set.py \
        --per-stratum 12 --out <BENCH>/tasks/tasks.json
"""
import argparse
import ast
import json
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import provenance  # noqa: E402
from run_sandboxed import run_check  # noqa: E402

BATCH = REPO / "<REFIMPL>" / "batch_runs"
V3_RESULTS = BATCH / "v3_results.jsonl"
SEED = 20260831


def _first_sentence(spec_text: str) -> str:
    para = spec_text.strip().split("\n\n")[0]
    m = re.match(r"(.+?\.)(\s|$)", para, re.S)
    s = (m.group(1) if m else para).strip()
    return re.sub(r"\s+", " ", s)[:280]


def _served_levels():
    """Method-name -> best report-backed served level, from the live graph."""
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
        rows = s.run("""
            MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
            RETURN toLower(m.name) AS name,
                   max(CASE WHEN cs.verification_report IS NOT NULL
                            THEN cs.verification_level ELSE 0 END) AS lvl
        """).data()
        titles = s.run("""
            MATCH (p:Paper) WHERE p.arxiv_id IS NOT NULL
            RETURN p.arxiv_id AS aid, p.title AS title
        """).data()
    driver.close()
    return ({r["name"]: int(r["lvl"] or 0) for r in rows},
            {t["aid"]: t["title"] for t in titles})


def _candidate(rec, batch_dir: Path):
    spec_p = batch_dir / "spec.json"
    tests_p = batch_dir / "property_tests.py"
    impl_p = batch_dir / "impl_sonnet.py"
    alt_p = batch_dir / "impl_llama.py"
    if not (spec_p.exists() and tests_p.exists()):
        return None, "missing_files"
    try:
        spec = json.loads(spec_p.read_text())
    except ValueError:
        return None, "spec_unreadable"
    entry, sig = spec.get("entry_name"), spec.get("signature")
    if not entry or not sig or not spec.get("spec_text"):
        return None, "spec_incomplete"
    pass_both = rec["pass_both"]
    if isinstance(pass_both, str):
        pass_both = ast.literal_eval(pass_both)
    suspect = rec.get("suspect_tests") or []
    if isinstance(suspect, str):
        suspect = ast.literal_eval(suspect)
    if len(pass_both) < 2:
        return None, "too_few_properties"
    impl = impl_p if impl_p.exists() else alt_p
    if not impl.exists():
        return None, "missing_files"
    return {"entry": entry, "signature": sig,
            "first_sentence": _first_sentence(spec["spec_text"]),
            "pass_both": pass_both, "suspect_tests": suspect,
            "impl_for_validation": str(impl.relative_to(REPO)),
            "property_tests": str(tests_p.relative_to(REPO))}, None


def _revalidate(cand) -> tuple[bool, str]:
    res = run_check(REPO / cand["impl_for_validation"], cand["entry"],
                    REPO / cand["property_tests"], timeout=60)
    if not res.get("ok"):
        return False, f"referee_crashed:{res.get('error')}"
    passed = {r["name"] for r in res.get("results", [])
              if r.get("passed") is True}
    missing = [p for p in cand["pass_both"] if p not in passed]
    if missing:
        return False, f"referee_regressed:{missing[:3]}"
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-stratum", type=int, default=12)
    ap.add_argument("--out", default=str(REPO / "tasks" / "tasks.json"))
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(V3_RESULTS)]
    v3 = [r for r in recs if r.get("v3") == "V3"]
    served, titles = _served_levels()

    ledger = provenance.ExclusionLedger()
    strata = {"in_catalog": [], "off_catalog": []}
    for r in v3:
        name = (r.get("method") or "").lower()
        if not name:
            ledger.exclude("no_method_name")
            continue
        lvl = served.get(name, -1)
        if lvl >= 3:
            strata["in_catalog"].append(r)
        elif lvl >= 2:
            ledger.exclude("served_v2_neither_stratum")
        else:
            strata["off_catalog"].append(r)

    rng = random.Random(SEED)
    tasks, validated = [], 0
    for stratum, pool in strata.items():
        rng.shuffle(pool)
        picked = 0
        for r in pool:
            if picked >= args.per_stratum:
                break
            batch_dir = BATCH / r["arxiv_id"]
            cand, why = _candidate(r, batch_dir)
            if cand is None:
                ledger.exclude(why)
                continue
            ok, why = _revalidate(cand)
            validated += 1
            if not ok:
                ledger.exclude(why.split(":")[0])
                print(f"  [excluded] {r['method']} ({r['arxiv_id']}): {why}")
                continue
            ledger.process()
            picked += 1
            tasks.append({
                "task_id": f"{stratum[:3]}_{r['arxiv_id']}",
                "stratum": stratum,
                "method": r["method"],
                "arxiv_id": r["arxiv_id"],
                "paper_title": titles.get(r["arxiv_id"]),
                "served_level": served.get((r["method"] or "").lower(), -1),
                **cand,
            })
            print(f"  [task] {stratum}: {r['method']} ({r['arxiv_id']}) "
                  f"props={len(cand['pass_both'])}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    provenance.write_json(out, {
        "seed": SEED,
        "pool_sizes": {k: len(v) for k, v in strata.items()},
        "referees_revalidated_today": validated,
        "tasks": tasks,
    }, inputs=[V3_RESULTS], params=vars(args), exclusions=ledger, indent=2)
    print(f"\nwrote {len(tasks)} tasks -> {out}")
    print(f"pools: { {k: len(v) for k, v in strata.items()} }")


if __name__ == "__main__":
    main()
