#!/usr/bin/env python3
"""Recompute MANIFEST entries for AUTHORED files that have legitimately changed.

WHY THIS EXISTS. Editing an authored file in this repository and forgetting to
update its manifest entry publishes a tree that fails its own
`check_clean_clone`. That happened twice on 2026-09-16 within an hour: first
when GRAPH_STATE.md was corrected, then again while fixing the findings an
outside reader raised about the first one. A discipline that fails twice in an
hour should be a command.

DELIBERATELY NARROW. It refreshes only entries whose `rule` is `authored` --
files this repository is the source of. A `verbatim` or `portability-patched`
file drifting means the MIRROR is stale, which is a different problem that
refreshing the hash would hide rather than fix; those are reported and left
alone.

    python3 tools/refresh_manifest.py --check   # what drifted, change nothing
    python3 tools/refresh_manifest.py --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--add", action="append", default=[],
                    help="record a NEW authored file. Deliberately explicit: a "
                         "sweep that auto-added anything untracked would quietly "
                         "publish whatever happened to be sitting in the tree.")
    a = ap.parse_args()
    if not (a.apply or a.check):
        ap.error("choose --check or --apply")

    mp = ROOT / "MANIFEST.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    files = m["files"]
    authored, foreign, missing = [], [], []
    for rel, e in files.items():
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
            continue
        b = p.read_bytes()
        if hashlib.sha256(b).hexdigest() == e.get("sha256"):
            continue
        (authored if e.get("rule") == "authored" else foreign).append((rel, e, b))

    for rel in a.add:
        rel = str(Path(rel).as_posix()).lstrip("./")
        p2 = ROOT / rel
        if not p2.exists():
            print(f"  cannot add {rel}: not in the tree")
            continue
        if rel in files:
            print(f"  {rel} is already recorded")
            continue
        b2 = p2.read_bytes()
        files[rel] = {"bytes": len(b2), "rule": "authored",
                      "sha256": hashlib.sha256(b2).hexdigest(),
                      "source": "authored in this repository"}
        print(f"  ADDED     {rel}")
        if not a.apply:
            print("    (not written -- pass --apply)")

    for rel in missing:
        print(f"  MISSING   {rel}")
    for rel, _, _ in foreign:
        print(f"  DRIFTED   {rel}  (rule={files[rel].get('rule')}) -- NOT refreshed: a "
              f"non-authored file drifting means the mirror is stale, and "
              f"rewriting its hash would hide that")
    for rel, _, _ in authored:
        print(f"  authored  {rel}  -> recompute")

    if not (authored or foreign or missing or a.add):
        print("  manifest matches the tree")
        return 0
    if not a.apply:
        print(f"\n  {len(authored)} authored file(s) would be refreshed. "
              f"--apply to write.")
        return 1 if (foreign or missing) else 0

    for rel, e, b in authored:
        e["sha256"] = hashlib.sha256(b).hexdigest()
        e["bytes"] = len(b)
    # summary.files is DERIVED, never carried forward. It was written once and
    # never maintained, so it drifted to 1,275 while files held 1,277 -- and the
    # README quoted the stale one, next to the very one-liner that prints the
    # real one. An external reviewer found the contradiction by running the
    # command the README told them to run. A summary that is not recomputed
    # where it is written is a stale number waiting to be cited.
    if isinstance(m.get("summary"), dict):
        before = m["summary"].get("files")
        m["summary"]["files"] = len(m["files"])
        if before != m["summary"]["files"]:
            print(f"  summary.files corrected {before} -> {m['summary']['files']}")
    mp.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print(f"\n  refreshed {len(authored)} authored entr(ies)")
    return 1 if (foreign or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
