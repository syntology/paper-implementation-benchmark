#!/usr/bin/env python3
"""
Analysis for the graph-vs-search benchmark (PREREGISTRATION.md): pass
rates by arm x stratum, the two pre-registered paired comparisons with
exact sign tests, cost/effort medians, tool-adoption, and the failure
taxonomy. Reads results.json (verify_solutions.py) + run metas.

Usage:
    ./venv/bin/python3 <BENCH>/analyze.py
"""
import json
import math
import statistics
import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import provenance  # noqa: E402

# The default is run 1 / v1.4's four arms. --arms overrides it, because the
# code_only ablation (PREREGISTRATION_CODE_ONLY.md) runs a different roster
# and a hardcoded list silently prints empty cells for arms that ran and
# omits the one under test.
ARMS = ["none", "search", "syntology", "both"]
# On-demand us-east-1 Sonnet 4.5 pricing per token (cache write 1.25x,
# cache read 0.1x input).
PRICE = {"inputTokens": 3e-6, "outputTokens": 15e-6,
         "cacheReadInputTokens": 0.3e-6, "cacheWriteInputTokens": 3.75e-6}


def sign_test_p(b: int, c: int) -> float:
    """Exact two-sided sign test on discordant pairs (b vs c)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def run_cost(usage: dict) -> float:
    return sum((usage.get(k) or 0) * p for k, p in PRICE.items())


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(REPO / "data" / "results.json"))
    ap.add_argument("--runs", default=str(REPO / "runs"))
    ap.add_argument("--out", default=None,
                    help="analysis json; default derived from --results")
    ap.add_argument("--arms", default=None,
                    help="comma-separated arm roster (default: the four of "
                         "run 1). Arms present in --results but absent here "
                         "would be silently dropped, so this defaults to the "
                         "arms the results file actually contains when given "
                         "as 'auto'.")
    ap.add_argument("--compare", default=None,
                    help="comma-separated 'a:b' paired comparisons to run "
                         "instead of the run-1 set")
    args = ap.parse_args()
    results_p, runs_root = Path(args.results), Path(args.runs)
    global ARMS
    # Derive the output from the input, the same lesson verify_solutions.py
    # learned the hard way: a fixed default beside a movable input overwrites
    # the wrong file.
    out_p = Path(args.out) if args.out else results_p.with_name(
        results_p.name.replace("results", "analysis"))
    res = json.loads(results_p.read_text(encoding="utf-8"))["runs"]
    if args.arms == "auto":
        ARMS = sorted({r["arm"] for r in res})
    elif args.arms:
        ARMS = args.arms.split(",")
    by = {(r["task_id"], r["arm"]): r for r in res}
    tasks = sorted({r["task_id"] for r in res})
    strata = {r["task_id"]: r["stratum"] for r in res}
    orphan = sorted({r["arm"] for r in res} - set(ARMS))
    if orphan:
        # R3: an arm that ran and is not in the roster is an exclusion, and it
        # is reported rather than silently dropped from every table below.
        print(f"NOTE: arms present in results but not analysed: {orphan} "
              f"(pass --arms auto to include them)\n")

    # pass rates ---------------------------------------------------------
    table = defaultdict(dict)
    for arm in ARMS:
        for st in ["in_catalog", "off_catalog"]:
            cell = [by[(t, arm)] for t in tasks
                    if strata[t] == st and (t, arm) in by]
            table[arm][st] = (sum(1 for r in cell if r["passed"]), len(cell))
        allc = [by[(t, arm)] for t in tasks if (t, arm) in by]
        table[arm]["all"] = (sum(1 for r in allc if r["passed"]), len(allc))

    print("## Pass rates (referee: full recorded pass_both property set)\n")
    print(f"{'arm':<11}{'in_catalog':>12}{'off_catalog':>13}{'overall':>10}")
    for arm in ARMS:
        row = table[arm]
        print(f"{arm:<11}"
              f"{row['in_catalog'][0]:>7}/{row['in_catalog'][1]:<4}"
              f"{row['off_catalog'][0]:>8}/{row['off_catalog'][1]:<4}"
              f"{row['all'][0]:>6}/{row['all'][1]:<3}")

    # paired comparisons -------------------------------------------------
    def paired(a1, a2, subset=None):
        b = c = 0
        for t in tasks:
            if subset and strata[t] != subset:
                continue
            r1, r2 = by.get((t, a1)), by.get((t, a2))
            if not r1 or not r2:
                continue
            if r1["passed"] and not r2["passed"]:
                b += 1
            elif r2["passed"] and not r1["passed"]:
                c += 1
        return b, c, sign_test_p(b, c)

    print("\n## Pre-registered paired comparisons (discordant tasks, exact sign test)\n")
    if args.compare:
        pairs = [tuple(p.split(":")) for p in args.compare.split(",")]
        comps = [(a, b, sub) for a, b in pairs
                 for sub in (None, "in_catalog", "off_catalog")]
    else:
        comps = [("both", "search", None), ("syntology", "search", None),
                 ("both", "search", "in_catalog"), ("syntology", "search", "in_catalog"),
                 ("both", "search", "off_catalog"), ("syntology", "search", "off_catalog"),
                 ("syntology", "none", None), ("search", "none", None),
                 ("both", "none", None)]
    comp_out = []
    for a1, a2, sub in comps:
        b, c, p = paired(a1, a2, sub)
        lbl = f"{a1} vs {a2}" + (f" [{sub}]" if sub else " [all]")
        print(f"{lbl:<38} +{b} / -{c}   p={p:.4f}")
        comp_out.append({"comparison": lbl, "wins": b, "losses": c, "p": p})

    # effort and cost ----------------------------------------------------
    print("\n## Effort per run (median)\n")
    # Reported per stratum as well as overall: the freeze's headline
    # efficiency numbers (6 turns vs 20) were in-catalog medians, and an
    # overall median silently mixes a covered task with an uncovered one.
    eff = {}
    for arm in ARMS:
        for st in ("in_catalog", "off_catalog", "ALL"):
            cell = [r for r in res if r["arm"] == arm and r.get("usage")
                    and (st == "ALL" or r["stratum"] == st)]
            if not cell:
                continue
            costs = [run_cost(r["usage"]) for r in cell]
            turns = [r.get("turns") or 0 for r in cell]
            walls = [r.get("wall_s") or 0 for r in cell]
            nosub = sum(1 for r in cell if r.get("reason") == "no_submission")
            eff[f"{arm}|{st}"] = {
                "n": len(cell),
                "median_cost": round(statistics.median(costs), 3),
                "total_cost": round(sum(costs), 2),
                "median_turns": statistics.median(turns),
                "median_wall_s": statistics.median(walls),
                "no_submission": nosub}
            e = eff[f"{arm}|{st}"]
            print(f"{arm:<11}{st:<13} n={e['n']:<3} ${e['median_cost']:<7} "
                  f"turns {e['median_turns']:<5} wall {e['median_wall_s']}s "
                  f"no-submit {nosub}  (total ${e['total_cost']})")

    # tool adoption ------------------------------------------------------
    print("\n## Code-fetch adoption (when offered)\n")
    # Each arm's flagship fetch is a different tool name; the question is the
    # same one in every arm -- did the agent actually pull served code -- so
    # the mapping lives here once instead of the caller knowing which arm
    # means which tool.
    FETCH = {"syntology": "syntology_get_reference_implementation",
             "both": "syntology_get_reference_implementation",
             "code_only": "code_get"}
    adoption = {}
    for arm in [a for a in ARMS if a in FETCH]:
        metas = []
        for t in tasks:
            mp = runs_root / t / arm / "meta.json"
            if mp.exists():
                metas.append(json.loads(mp.read_text(encoding="utf-8")))
        key = "code_only_calls" if arm == "code_only" else "syntology_calls"
        used = sum(1 for m in metas if m.get(key, 0) > 0)
        got_ref = sum(1 for m in metas
                      if any(c["tool"] == FETCH[arm]
                             for c in m.get("tool_calls", [])))
        adoption[arm] = {"runs": len(metas), "any_arm_tool_call": used,
                         "fetch_tool": FETCH[arm],
                         "called_fetch_tool": got_ref}
        print(f"{arm:<11} any arm-tool call: {used}/{len(metas)}   "
              f"{FETCH[arm]}: {got_ref}/{len(metas)}")

    # failure taxonomy ---------------------------------------------------
    print("\n## Failure taxonomy (non-passing runs)\n")
    tax = defaultdict(int)
    for r in res:
        if r["passed"]:
            continue
        reason = r.get("reason") or (
            f"properties_failed:{len(r.get('properties_failed') or [])}")
        tax[f"{r['arm']}|{reason.split(':')[0]}"] += 1
    for k in sorted(tax):
        print(f"  {k:<40} {tax[k]}")

    # per-task grid ------------------------------------------------------
    print("\n## Per-task grid (P=pass, f=fail, .=missing)\n")
    print(f"{'task':<22}{'strat':<13}" + "".join(f"{a:<11}" for a in ARMS))
    for t in tasks:
        cells = []
        for a in ARMS:
            r = by.get((t, a))
            cells.append("." if r is None else ("P" if r["passed"] else "f"))
        print(f"{t:<22}{strata[t]:<13}" + "".join(f"{c:<11}" for c in cells))

    provenance.write_json(out_p, {
        "pass_table": {a: {k: list(v) for k, v in row.items()}
                       for a, row in table.items()},
        "paired_comparisons": comp_out,
        "effort": eff,
        "adoption": adoption,
        "failure_taxonomy": dict(tax),
    }, inputs=[results_p], params=vars(args), indent=2)
    print(f"\nwrote {out_p}")


if __name__ == "__main__":
    main()
