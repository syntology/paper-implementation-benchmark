#!/usr/bin/env python3
"""
Referee for the graph-vs-search benchmark (PREREGISTRATION.md): run each
submitted solution.py against its task's paper-derived property suite in
the stage-13 sandbox. A run PASSES iff every property in the task's
recorded pass_both set passes. Solutions never saw these tests.

Usage:
    ./venv/bin/python3 <BENCH>/verify_solutions.py
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import provenance  # noqa: E402
from run_sandboxed import run_check  # noqa: E402
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent / "vendor"))
import corpus_files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=str(REPO / "tasks" / "tasks.json"))
    ap.add_argument("--runs", default=str(REPO / "runs"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    # DERIVE the output from --runs. The default was a fixed results.json, so
    # `verify_solutions.py --runs runs_v12` silently overwrote run 1's results
    # -- 96 runs across four arms replaced by 24 from one arm, and the only
    # reason it was recoverable is that the file happened to be tracked and the
    # change uncommitted. A flag that points the INPUT somewhere else while the
    # OUTPUT stays put is a trap, not a default.
    if args.out is None:
        runs_dir = Path(args.runs).name
        suffix = runs_dir[len("runs"):] if runs_dir.startswith("runs") else f"_{runs_dir}"
        args.out = str(HERE / f"results{suffix}.json")
        print(f"--out not given; writing to {args.out} (derived from --runs)",
              file=sys.stderr)


    tasks = {t["task_id"]: t
             for t in json.loads(Path(args.tasks).read_text())["tasks"]}
    runs_root = Path(args.runs)
    ledger = provenance.ExclusionLedger()
    rows = []
    for meta_p in corpus_files.iter_paper_files(runs_root, "*/*/meta.json"):
        run_dir = meta_p.parent
        arm = run_dir.name
        tid = run_dir.parent.name
        task = tasks.get(tid)
        if task is None:
            ledger.exclude("run_without_task")
            continue
        meta = json.loads(meta_p.read_text())
        sol = run_dir / "solution.py"
        row = {"task_id": tid, "arm": arm, "stratum": task["stratum"],
               "method": task["method"],
               "usage": meta.get("usage"), "turns": meta.get("turns"),
               "wall_s": meta.get("wall_s"),
               "syntology_calls": meta.get("syntology_calls"),
               "search_calls": meta.get("search_calls"),
               "stop_reason": meta.get("stop_reason")}
        if not sol.exists():
            row.update(passed=False, reason="no_submission")
            rows.append(row); ledger.process(); continue
        res = run_check(sol, task["entry"], REPO / task["property_tests"],
                        timeout=90)
        if not res.get("ok"):
            row.update(passed=False, reason=f"referee_{res.get('error')}",
                       detail=(res.get("stderr") or "")[-400:])
            rows.append(row); ledger.process(); continue
        got = {r["name"]: r for r in res.get("results", [])}
        # STRICT boolean check. The sandbox used to serialize np.bool_ as the
        # strings "True"/"False" (both truthy -- the 2026-08-31 referee-audit
        # finding), so `is True` guards against re-reading any stale runner.
        missing = [p for p in task["pass_both"]
                   if got.get(p, {}).get("passed") is not True]
        row.update(
            passed=not missing,
            properties_required=len(task["pass_both"]),
            properties_failed=missing,
            failure_details=[{ "name": p,
                               "detail": str(got.get(p, {}).get("detail"))[:300]}
                             for p in missing[:3]])
        rows.append(row); ledger.process()

    provenance.write_json(Path(args.out), {"runs": rows},
                          inputs=[Path(args.tasks)], params=vars(args),
                          exclusions=ledger, indent=2)
    n_pass = sum(1 for r in rows if r.get("passed"))
    print(f"verified {len(rows)} runs -> {args.out}  ({n_pass} passed)")


if __name__ == "__main__":
    main()
