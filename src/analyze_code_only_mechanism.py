#!/usr/bin/env python3
"""
Mechanism analysis for the v1.5 `code_only` ablation
(PREREGISTRATION_CODE_ONLY.md, "Metrics -> Mechanism").

A pass rate says the arm worked. It does not say WHAT worked, and for this
ablation that is the whole question. Three things have to be separated, and
only the transcripts can separate them:

  1. **Which key did the agent query with?** The prompt hands every arm the
     method name, the paper title, the arXiv id AND the entry function name.
     A flat code index looks very different depending on which one an agent
     reaches for -- the offline probe measured recall of 17/18 @1 from the
     entry name and 10/18 @15 from the method name alone.
  2. **Which retrieval route surfaced the code it actually fetched?**
     `matched_by` on each hit is recorded by the arm for exactly this:
     `entry_exact` / `keyword` / `semantic` / `origin_id`. Disclosed
     asymmetry 1 stands or falls on the `origin_id` tally.
  3. **Did it fetch the RIGHT sample?** Ground truth comes from the probe
     (`probe_code_only_retrieval.json`), resolved graph-side for analysis
     only.

The same three questions are answered for the `syntology` arm in its own
terms -- which tool resolved the method, and what name it was called with --
so the two arms' discovery paths can be compared rather than just their
scores.

R1: stamped. Read-only; no model spend.

    ./venv/bin/python3 <BENCH>/analyze_code_only_mechanism.py
"""
from __future__ import annotations

import argparse
import json
import re
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import provenance  # noqa: E402


def walk(transcript):
    """Yield (tool_name, input_dict, result_payload_or_None) in order."""
    pending = {}
    for msg in transcript:
        for block in msg.get("content", []) or []:
            tu = block.get("toolUse") if isinstance(block, dict) else None
            if tu:
                pending[tu["toolUseId"]] = (tu["name"], tu.get("input") or {})
            tr = block.get("toolResult") if isinstance(block, dict) else None
            if tr and tr["toolUseId"] in pending:
                name, args = pending.pop(tr["toolUseId"])
                txt = ""
                for c in tr.get("content", []) or []:
                    txt += c.get("text", "") if isinstance(c, dict) else ""
                yield name, args, txt
    for name, args in pending.values():
        yield name, args, None


def classify_query(q: str, task: dict) -> str:
    """Which of the four keys the prompt handed the agent did it use?"""
    ql = (q or "").lower()
    if re.search(r"\d{4}\.\d{4,5}", ql):
        return "arxiv_id"
    if task["entry"].lower() in ql:
        return "entry_name"
    if task["method"].lower() in ql and len(ql) > len(task["method"]) + 8:
        return "method_plus_description"
    if task["method"].lower() in ql:
        return "method_name"
    title = (task.get("paper_title") or "").lower()
    if title and title[:25] in ql:
        return "paper_title"
    return "description"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(REPO / "data" / "runs" / "runs_v15"))
    ap.add_argument("--tasks", default=str(REPO / "tasks" / "tasks_freeze.json"))
    ap.add_argument("--results", default=str(REPO / "data" / "results_v15.json"))
    ap.add_argument("--probe", default=str(REPO / "data" / "probe_code_only_retrieval.json"))
    ap.add_argument("--out", default=str(REPO / "data" / "mechanism_v15.json"))
    args = ap.parse_args()

    tasks = {t["task_id"]: t
             for t in json.loads(Path(args.tasks).read_text())["tasks"]}
    truth = {r["task_id"]: set(r["correct_shas"])
             for r in json.loads(Path(args.probe).read_text())["rows"]}
    passed = {}
    rp = Path(args.results)
    if rp.exists():
        for r in json.loads(rp.read_text())["runs"]:
            passed[(r["task_id"], r["arm"])] = r["passed"]

    rows = []
    q_kinds, routes, fetch_ok = Counter(), Counter(), Counter()
    syn_tools, syn_names, syn_resolution = Counter(), Counter(), Counter()
    for tid, task in tasks.items():
        for arm in ("code_only", "syntology"):
            tp = Path(args.runs) / tid / arm / "transcript.json"
            if not tp.exists():
                continue
            tr = json.loads(tp.read_text())
            row = {"task_id": tid, "arm": arm, "stratum": task["stratum"],
                   "passed": passed.get((tid, arm)),
                   "queries": [], "fetched": [], "route": None,
                   "fetched_correct": None}
            last_hits = {}          # sha -> matched_by, from the latest search
            for name, a, res in walk(tr):
                if name == "code_search":
                    q = a.get("query", "")
                    kind = classify_query(q, task)
                    row["queries"].append({"q": q, "kind": kind,
                                           "min_level": a.get("min_level")})
                    q_kinds[kind] += 1
                    if res:
                        try:
                            payload = json.loads(res)
                        except ValueError:
                            payload = {}
                        for h in (payload.get("results") or []) + \
                                 (payload.get("verified_matches") or []):
                            last_hits[h.get("code_sha256")] = h.get("matched_by")
                elif name == "code_get":
                    sha = a.get("code_sha256", "")
                    row["fetched"].append(sha)
                    row["route"] = last_hits.get(sha) or ["unranked_or_direct"]
                    for r_ in row["route"]:
                        routes[r_] += 1
                    # The freeze's conditional, in this arm's terms: "every
                    # run that fetched SERVED code passed" (66/66 cumulative).
                    # The level comes out of code_get's own response, so it is
                    # the level the agent was actually shown, not one looked
                    # up afterwards from a different artifact.
                    if res:
                        try:
                            got = json.loads(res)
                        except ValueError:
                            got = {}
                        for smp in got.get("samples") or []:
                            row.setdefault("fetched_levels", []).append(
                                smp.get("verification_level"))
                elif name.startswith("syntology_"):
                    syn_tools[name] += 1
                    if name == "syntology_get_reference_implementation":
                        syn_names[classify_query(a.get("name", ""), task)] += 1
                        row["queries"].append({"q": a.get("name", ""),
                                               "kind": classify_query(a.get("name", ""), task),
                                               "tool": name})
                        row["fetched"].append(a.get("name", ""))
                        # What the ONTOLOGY actually did on this call. An
                        # exact name hit means the Method vocabulary was a
                        # lookup table; a `resolved_via` means the near-match
                        # ladder earned its keep; an `error` means the name
                        # did not resolve at all. This is the graph's own
                        # discovery mechanism, measured the same way the flat
                        # arm's `matched_by` measures its.
                        if res:
                            try:
                                payload = json.loads(res)
                            except ValueError:
                                payload = {}
                            if payload.get("error"):
                                syn_resolution["error"] += 1
                                row.setdefault("syn_resolution", []).append("error")
                            elif payload.get("resolved_via"):
                                syn_resolution["token_fallback"] += 1
                                row.setdefault("syn_resolution", []).append(
                                    f"token_fallback->{payload['resolved_via']}")
                            elif payload.get("fallback"):
                                syn_resolution["fallback_tier"] += 1
                                row.setdefault("syn_resolution", []).append("fallback_tier")
                            elif payload.get("implementations"):
                                syn_resolution["exact_name"] += 1
                                row.setdefault("syn_resolution", []).append("exact_name")
            if arm == "code_only" and row["fetched"]:
                ok = any(s in truth.get(tid, set()) for s in row["fetched"])
                row["fetched_correct"] = ok
                fetch_ok[("correct" if ok else "wrong_sample")] += 1
            rows.append(row)

    print("## code_only: which key did the agent query with?\n")
    for k, n in q_kinds.most_common():
        print(f"  {k:<26} {n}")
    print("\n## code_only: retrieval route of the sample it fetched\n")
    for k, n in routes.most_common():
        print(f"  {k:<26} {n}")
    print("\n## code_only: was the fetched sample the correct one?\n")
    for k, n in fetch_ok.most_common():
        print(f"  {k:<26} {n}")

    # Disclosed asymmetry 1, answered directly. A route tagged `origin_id`
    # alongside `keyword`/`semantic` would have surfaced the same sample
    # without the denormalised arXiv id; a route tagged origin_id and NOTHING
    # else is a fetch that DEPENDED on it. Only the second number is a threat
    # to the finding, and reporting the first as if it were the second would
    # overstate the asymmetry as badly as ignoring it understates it.
    dep = [r for r in rows if r["arm"] == "code_only"
           and r["route"] and set(r["route"]) == {"origin_id"}]
    shared = [r for r in rows if r["arm"] == "code_only"
              and r["route"] and "origin_id" in r["route"]
              and set(r["route"]) != {"origin_id"}]
    print(f"\n## Asymmetry 1: fetches that DEPENDED on the origin arXiv id\n")
    print(f"  origin_id was the only route          {len(dep)}"
          + (f"  {[r['task_id'] for r in dep]}" if dep else ""))
    print(f"  origin_id shared with keyword/semantic {len(shared)}")

    # The conditional, in each arm's own terms.
    cond = {}
    for arm, pred in (("code_only",
                       lambda r: any((l or 0) >= 2 for l in r.get("fetched_levels") or [])),
                      ("syntology", lambda r: bool(r["fetched"]))):
        cell = [r for r in rows if r["arm"] == arm and pred(r)
                and r["passed"] is not None]
        cond[arm] = {"fetched_verified": len(cell),
                     "passed": sum(1 for r in cell if r["passed"]),
                     "failed_tasks": [r["task_id"] for r in cell if not r["passed"]]}
    print("\n## The conditional: fetched machine-verified code -> passed?\n")
    for arm, c in cond.items():
        print(f"  {arm:<11} {c['passed']}/{c['fetched_verified']}"
              + (f"   failures: {c['failed_tasks']}" if c["failed_tasks"] else ""))
    print("\n## syntology: tool calls\n")
    for k, n in syn_tools.most_common():
        print(f"  {k:<46} {n}")
    print("\n## syntology: what get_reference_implementation was called with\n")
    for k, n in syn_names.most_common():
        print(f"  {k:<26} {n}")
    print("\n## syntology: how the ONTOLOGY resolved that name\n")
    for k, n in syn_resolution.most_common():
        print(f"  {k:<26} {n}")

    # per-task discovery-path table
    print("\n## Per-task discovery path\n")
    print(f"{'task':<22}{'arm':<11}{'pass':<6}{'n_search':<10}{'route'}")
    for r in sorted(rows, key=lambda x: (x["task_id"], x["arm"])):
        print(f"{r['task_id']:<22}{r['arm']:<11}"
              f"{str(r['passed']):<6}{len(r['queries']):<10}"
              f"{','.join(r['route'] or []) if r['route'] else '-'}")

    provenance.write_json(Path(args.out), {
        "rows": rows,
        "query_kinds": dict(q_kinds), "routes": dict(routes),
        "fetch_correctness": dict(fetch_ok),
        "origin_id_dependence": {
            "only_route": [r["task_id"] for r in dep],
            "shared_route": [r["task_id"] for r in shared]},
        "conditional": cond,
        "syntology_tools": dict(syn_tools),
        "syntology_name_kinds": dict(syn_names),
        "syntology_resolution": dict(syn_resolution),
    }, inputs=[Path(args.tasks), Path(args.probe)], params=vars(args), indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
