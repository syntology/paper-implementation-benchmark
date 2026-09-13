#!/usr/bin/env python3
"""
Cross-run paired comparison for the graph-vs-search benchmark: the SAME
tasks under two serving states (e.g. run 1 @0387438 vs the v1 freeze
@bc87485a). analyze.py pairs arm-vs-arm within one run; this pairs
run-vs-run within one arm, per task, which is the question a freeze
answers: what did the changes buy?

Per arm, per today's stratum: pass counts A vs B, discordant tasks
(+ gained / - lost) with an exact two-sided sign test, adoption of
get_reference_implementation, median cost and wall, and the
fetched-served-code conditional pooled across both runs.

Usage:
    ./venv/bin/python3 <BENCH>/compare_runs.py \
        --a results.json --a-runs runs --b results_v14.json --b-runs runs_v14 \
        --tasks tasks/tasks_freeze.json [--out compare_run1_v14.json]
"""
import argparse
import json
import statistics as st
import os
import sys
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import provenance  # noqa: E402
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent / "vendor"))
import corpus_files

PRICE = {"inputTokens": 3e-6, "outputTokens": 15e-6,
         "cacheReadInputTokens": 0.3e-6, "cacheWriteInputTokens": 3.75e-6}
ARMS = ["none", "search", "syntology", "both"]


def sign_test(pos, neg):
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def load(results, runs):
    res = {(r["task_id"], r["arm"]): r for r in json.loads(Path(results).read_text())["runs"]}
    metas = {}
    for mp in corpus_files.iter_paper_files(runs, "*/*/meta.json"):
        m = json.loads(mp.read_text())
        metas[(m["task_id"], m["arm"])] = m
    return res, metas


def fetched(meta):
    return any(c["tool"] == "syntology_get_reference_implementation"
               for c in (meta or {}).get("tool_calls", []))


def cost(meta):
    return sum((meta.get("usage", {}).get(k) or 0) * v for k, v in PRICE.items())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--a-runs", required=True)
    ap.add_argument("--b", required=True); ap.add_argument("--b-runs", required=True)
    ap.add_argument("--tasks", default=str(REPO / "tasks" / "tasks_freeze.json"))
    ap.add_argument("--label-a", default="A"); ap.add_argument("--label-b", default="B")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    A, Am = load(REPO / args.a if not Path(args.a).is_absolute() else args.a,
                 REPO / args.a_runs if not Path(args.a_runs).is_absolute() else args.a_runs)
    B, Bm = load(REPO / args.b if not Path(args.b).is_absolute() else args.b,
                 REPO / args.b_runs if not Path(args.b_runs).is_absolute() else args.b_runs)
    tasks = json.loads(Path(args.tasks).read_text())["tasks"]
    strata = {t["task_id"]: t["stratum"] for t in tasks}
    out = {"arms": {}, "conditional": {}}

    print(f"\n## {args.label_a} -> {args.label_b}, paired per task (strata = today's)\n")
    print(f"{'arm':<10}{'stratum':<13}{'n':>3}{'pass A':>8}{'pass B':>8}{'+/-':>8}{'p':>8}"
          f"{'fetch A':>9}{'fetch B':>9}{'$med A':>9}{'$med B':>9}{'wall A':>8}{'wall B':>8}")
    for arm in ARMS:
        for stratum in ["in_catalog", "off_catalog", "ALL"]:
            tids = [t for t in strata if stratum == "ALL" or strata[t] == stratum]
            pairs = [t for t in tids if (t, arm) in A and (t, arm) in B]
            if not pairs:
                continue
            pa = sum(1 for t in pairs if A[(t, arm)]["passed"])
            pb = sum(1 for t in pairs if B[(t, arm)]["passed"])
            gained = sum(1 for t in pairs if B[(t, arm)]["passed"] and not A[(t, arm)]["passed"])
            lost = sum(1 for t in pairs if A[(t, arm)]["passed"] and not B[(t, arm)]["passed"])
            p = sign_test(gained, lost)
            fa = sum(1 for t in pairs if fetched(Am.get((t, arm))))
            fb = sum(1 for t in pairs if fetched(Bm.get((t, arm))))
            ca = st.median([cost(Am[(t, arm)]) for t in pairs if (t, arm) in Am] or [0])
            cb = st.median([cost(Bm[(t, arm)]) for t in pairs if (t, arm) in Bm] or [0])
            wa = st.median([Am[(t, arm)].get("wall_s", 0) for t in pairs if (t, arm) in Am] or [0])
            wb = st.median([Bm[(t, arm)].get("wall_s", 0) for t in pairs if (t, arm) in Bm] or [0])
            print(f"{arm:<10}{stratum:<13}{len(pairs):>3}{pa:>8}{pb:>8}{f'+{gained}/-{lost}':>8}"
                  f"{p:>8.3f}{fa:>9}{fb:>9}{ca:>9.3f}{cb:>9.3f}{wa:>8.0f}{wb:>8.0f}")
            out["arms"][f"{arm}|{stratum}"] = {
                "n": len(pairs), "pass_a": pa, "pass_b": pb, "gained": gained, "lost": lost,
                "sign_p": p, "fetch_a": fa, "fetch_b": fb, "cost_med_a": ca, "cost_med_b": cb,
                "wall_med_a": wa, "wall_med_b": wb}

    # the conditional, pooled
    for label, R, M in [(args.label_a, A, Am), (args.label_b, B, Bm)]:
        f = [(k, R[k]["passed"]) for k, m in M.items() if fetched(m) and k in R]
        out["conditional"][label] = {"fetched": len(f), "passed": sum(1 for _, p in f if p)}
        print(f"\nconditional [{label}]: fetched served code {len(f)} -> passed "
              f"{sum(1 for _, p in f if p)}")

    out_p = Path(args.out) if args.out else HERE / f"compare_{args.label_a}_{args.label_b}.json"
    provenance.write_json(out_p, out, inputs=[Path(args.a), Path(args.b), Path(args.tasks)]
                          if Path(args.a).is_absolute() else
                          [REPO / args.a, REPO / args.b, Path(args.tasks)],
                          params=vars(args), indent=2)
    print(f"\nwrote {out_p}")


if __name__ == "__main__":
    main()
