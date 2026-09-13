#!/usr/bin/env python3
# Copyright 2026 Syntology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Prove the referee runs in THIS tree, offline, for zero spend.

The referee is the part of this benchmark an outsider most needs to be able to
run: it is deterministic, local, needs no credentials, and it is what every
number in `results/` was scored by. So it gets a smoke test that a reader can
run before touching an API key.

WHAT IT DOES. For each task named on the command line (default: three, one per
task set), it builds a throwaway run tree that looks exactly like a real sweep's
output -- `runs/<task_id>/<arm>/solution.py` plus a minimal `meta.json` -- with
the task's own `impl_sonnet.py` as the submission, then runs
`src/verify_solutions.py` over it and checks the referee marked it passed.

WHAT A PASS MEANS, and what it does not. It means the task file, the referee
tree, the sandbox runner and the strict-boolean scoring all resolve and work
here. `impl_sonnet.py` is the implementation that was used to revalidate that
each property suite is satisfiable, so it passing is the expected outcome, not
evidence about anyone's agent -- and not evidence that the implementation is
faithful to its paper (see README.md, "What is NOT claimed").

A FAILURE IS INFORMATIVE EITHER WAY: either this tree is broken, or a property
suite has stopped being satisfiable in your Python/numpy, which is exactly the
drift a reproduction attempt needs to know about before it spends anything.

Exit 0 all passed - 1 any task failed - 4 could not run at all.

    python3 tools/smoke_referee.py
    python3 tools/smoke_referee.py --tasks in__2505.24844,sub_2202.08836
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

DEFAULT_TASKS = ["in__2505.24844", "off_2210.17323", "sub_2202.08836"]
TASK_FILES = {"tasks/tasks_freeze.json": ("in__", "off_"),
              "tasks/tasks_substitution.json": ("sub_", "in__", "off_")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=",".join(DEFAULT_TASKS))
    ap.add_argument("--keep", action="store_true", help="keep the temp tree")
    args = ap.parse_args()
    want = [t for t in args.tasks.split(",") if t]

    # Find each task in whichever task file holds it.
    located: dict[str, tuple[str, dict]] = {}
    for tf in TASK_FILES:
        p = REPO / tf
        if not p.exists():
            continue
        for t in json.loads(p.read_text())["tasks"]:
            if t["task_id"] in want and t["task_id"] not in located:
                located[t["task_id"]] = (tf, t)
    missing = [t for t in want if t not in located]
    if missing:
        print(f"no such task(s): {missing}", file=sys.stderr)
        return 4

    tmp = Path(tempfile.mkdtemp(prefix="syntology-referee-smoke-"))
    failures = []
    try:
        by_file: dict[str, list[str]] = {}
        for tid, (tf, t) in located.items():
            impl = REPO / t["impl_for_validation"]
            if not impl.exists():
                print(f"{tid}: missing {impl}", file=sys.stderr)
                return 4
            d = tmp / "runs" / tid / "smoke"
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy(impl, d / "solution.py")
            (d / "meta.json").write_text(json.dumps(
                {"task_id": tid, "arm": "smoke", "submitted": True,
                 "turns": 0, "wall_s": 0.0, "stop_reason": "smoke",
                 "usage": {}}, indent=1))
            by_file.setdefault(tf, []).append(tid)

        for tf, tids in by_file.items():
            out = tmp / f"results_{Path(tf).stem}.json"
            cmd = [sys.executable, str(REPO / "src" / "verify_solutions.py"),
                   "--tasks", str(REPO / tf), "--runs", str(tmp / "runs"),
                   "--out", str(out)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"verify_solutions failed for {tf}:\n{r.stderr[-2000:]}",
                      file=sys.stderr)
                return 4
            rows = {x["task_id"]: x for x in json.loads(out.read_text())["runs"]}
            for tid in tids:
                row = rows.get(tid)
                ok = bool(row and row.get("passed"))
                detail = "" if ok else f" -- {row.get('reason') or row.get('properties_failed')}"
                print(f"  {'PASS' if ok else 'FAIL'}  {tid}"
                      f"  ({row.get('properties_required') if row else '?'} properties){detail}")
                if not ok:
                    failures.append(tid)
    finally:
        if args.keep:
            print(f"\ntemp tree kept at {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    print("\nreferee smoke: " + ("PASS" if not failures else f"FAIL {failures}"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
