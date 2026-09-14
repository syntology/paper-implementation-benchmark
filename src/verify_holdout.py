#!/usr/bin/env python3
"""
Prove the hold-out is real, on BOTH arms, before any subject token is spent
(PREREGISTRATION_SUBSTITUTION.md, "Exclusion verification"). Read-only (C3).

An arm that can still reach the held-out sample makes the whole experiment
meaningless, and nothing about the resulting numbers would look wrong. So
the exclusion is a check that refuses (R4), not a claim in a document.

SIX CHECKS.

  P  PARITY. With no hold-out installed, both arms return exactly what they
     returned for v1.5: the graph serves the same sample for every task, and
     the flat index ranks the correct sha where `probe_code_only_retrieval.json`
     recorded it. This is what licenses reusing v1.5 as the no-hold-out
     condition instead of paying to re-run it.
  C  CAPABILITY (the test of the test). With the hold-out OFF, every query in
     the battery must actually REACH the held-out sample. An "it is absent"
     assertion from a query that could never have found it proves nothing.
  F  FLAT EXCLUSION. With the hold-out ON, no held-out sha appears anywhere
     in a `code_search` response for any battery query -- ranked list,
     verified facet, or pin -- and `code_get` refuses every held-out sha with
     the same error an unknown sha gets.
  G  GRAPH EXCLUSION. With the hold-out ON, no graph tool returns the held-out
     CODE. Checked on the code TEXT, not on a sha, because the graph tools do
     not return shas: the held-out sources are fetched once, analysis-side,
     and any response containing one verbatim is a leak.
  T  THREAD CROSS-TALK. Two threads, two different hold-outs, concurrent
     searches: each must see only its own exclusions. The harness runs
     `--workers 2` in one process over module-global caches, so this is the
     failure that would corrupt results while looking normal.
  X  INDEX COVERAGE. Every held-out sha must exist in the flat index, or
     "removed from the flat index" is a claim about rows that were never
     there.

Exit 0 clean - 1 findings, per the project exit-code contract.

    ./venv/bin/python3 <BENCH>/verify_holdout.py \
        --tasks .../tasks/tasks_substitution.json --holdout .../tasks/holdout_sets.json
"""
from __future__ import annotations

import argparse
import concurrent.futures
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
import benchmark_holdout as HO  # noqa: E402
import code_only_arm_tools as FLAT  # noqa: E402
import syntology_arm_tools as GRAPH  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402

TOPK = 50


def battery(task):
    """The three query forms the v1.5 probe used, plus the signature.

    They are the keys the prompt actually hands the subject, which is what
    makes them the adversarial set: if anything can pull the answer back out
    of a held-out arm, it is one of these.
    """
    return [("entry", task["entry"]),
            ("method", task["method"]),
            ("method_plus_sentence",
             f"{task['method']} {task['first_sentence']}"),
            ("signature", task["signature"])]


def _flat_shas(resp):
    out = [r["code_sha256"] for r in resp.get("results", [])]
    out += [r["code_sha256"] for r in resp.get("verified_matches", [])]
    return out


def _texts_of(session, shas):
    rows = session.run(
        "MATCH (c:CodeSample) WHERE c.code_sha256 IN $s "
        "RETURN c.code_sha256 AS sha, c.code AS code", s=list(shas)).data()
    return {r["sha"]: r["code"] for r in rows if r["code"]}


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk_strings(v)


def _graph_leak(resp, texts):
    """Any held-out source appearing verbatim in a graph-tool response."""
    blob = "\n".join(_walk_strings(resp))
    return [sha for sha, code in texts.items()
            if code and len(code) > 80 and code in blob]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--holdout", required=True)
    ap.add_argument("--probe", default=str(REPO / "data" / "probe_code_only_retrieval.json"))
    ap.add_argument("--out", default=str(REPO / "data" / "holdout_verification.json"))
    args = ap.parse_args()

    tasks = {t["task_id"]: t
             for t in json.loads(Path(args.tasks).read_text(encoding="utf-8"))["tasks"]}
    ho = json.loads(Path(args.holdout).read_text(encoding="utf-8"))["holdout"]
    probe = {}
    p = Path(args.probe)
    if p.exists():
        for row in json.loads(p.read_text(encoding="utf-8")).get("rows", []):
            probe[row.get("task_id")] = row

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    session = driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j"))

    lex = FLAT._load_index()
    index_shas = set(lex["sha"])

    findings, rows = [], []
    for tid, rec in ho.items():
        task = tasks[tid]
        shas = set(rec["shas"])
        texts = _texts_of(session, shas)
        row = {"task_id": tid, "n_holdout": len(shas),
               "n_holdout_in_flat_index": len(shas & index_shas),
               "capability": {}, "flat_excluded": {}, "graph": {}}

        # X -- index coverage
        missing = shas - index_shas
        if missing:
            findings.append(f"[X] {tid}: {len(missing)} held-out sha(s) are not "
                            f"rows in the flat index, so removing them from it "
                            f"removes nothing: {sorted(missing)[:3]}")

        # C -- capability, hold-out OFF
        HO.clear_holdout()
        reachable = False
        for label, q in battery(task):
            got = _flat_shas(FLAT.code_search(q, limit=TOPK))
            hit = [s for s in got if s in shas]
            row["capability"][label] = {"n_hits": len(hit),
                                        "rank": (got.index(hit[0]) + 1) if hit else None}
            reachable = reachable or bool(hit)
        served_open = GRAPH.get_reference_implementation(task["method"], min_level=0)
        row["capability"]["graph_serves"] = bool(served_open.get("implementations"))
        if not reachable:
            findings.append(f"[C] {tid}: with the hold-out OFF, no battery query "
                            f"reached the held-out sample in the top {TOPK}. An "
                            f"absence result for this task would be vacuous.")
        if not row["capability"]["graph_serves"]:
            findings.append(f"[C] {tid}: with the hold-out OFF the graph arm "
                            f"serves nothing for '{task['method']}'; the graph "
                            f"side of the hold-out removes nothing.")

        # P -- parity against the v1.5 probe (flat side), where recorded
        pr = probe.get(tid)
        if pr:
            want = ((pr.get("queries") or {}).get("Q1_entry")
                    or {}).get("with_origin", {}).get("rank")
            # Compare the rank of the sha the PROBE scored, not of "the first
            # held-out sha". The hold-out is wider than the probe's target --
            # H4 removes same-named samples from other papers -- so the first
            # held-out row can legitimately outrank the probe's own target
            # and read as a parity break that is really a definition mismatch.
            # (Found on off_2306.12360, which holds four same-entry samples.)
            correct = set(pr.get("correct_shas") or [])
            if want and correct:
                got = _flat_shas(FLAT.code_search(task["entry"], limit=TOPK))
                hit = [i + 1 for i, s in enumerate(got) if s in correct]
                if hit and hit[0] != want:
                    findings.append(
                        f"[P] {tid}: entry-name rank of the probe's own target "
                        f"moved {want} -> {hit[0]} with no hold-out installed; "
                        f"the arm is no longer the one v1.5 measured.")

        # F -- flat exclusion, hold-out ON
        HO.set_holdout(shas)
        for label, q in battery(task):
            got = _flat_shas(FLAT.code_search(q, limit=TOPK))
            leak = [s for s in got if s in shas]
            row["flat_excluded"][label] = {"leaked": leak, "n_returned": len(got)}
            if leak:
                findings.append(f"[F] {tid}/{label}: code_search returned "
                                f"held-out sha(s) {leak}")
        blocked_ok, blocked_bad = 0, []
        for s in shas:
            try:
                FLAT.code_get(s)
                blocked_bad.append(s)
            except ValueError:
                blocked_ok += 1
        row["code_get_refused"] = blocked_ok
        if blocked_bad:
            findings.append(f"[F] {tid}: code_get served held-out sha(s) "
                            f"{blocked_bad[:3]}")
        try:
            by_name = FLAT.code_get(task["entry"])
            leak = [s["code_sha256"] for s in by_name.get("samples", [])
                    if s["code_sha256"] in shas]
            if leak:
                findings.append(f"[F] {tid}: code_get by ENTRY NAME served "
                                f"held-out sha(s) {leak}")
            row["code_get_by_entry"] = "returned_other_samples"
        except ValueError:
            row["code_get_by_entry"] = "refused"

        # G -- graph exclusion, hold-out ON
        g = {}
        try:
            r = GRAPH.get_reference_implementation(task["method"], min_level=0)
            g["get_reference_implementation"] = (
                "fallback" if not r.get("implementations") else "served")
            leak = _graph_leak(r, texts)
            if leak:
                findings.append(f"[G] {tid}: get_reference_implementation "
                                f"returned held-out source {leak}")
        except ValueError as e:
            g["get_reference_implementation"] = f"raised: {str(e)[:60]}"
        r = GRAPH.list_reference_implementations(query=task["method"], limit=50)
        listed = [i for i in r.get("implementations", [])
                  if (i.get("method") or "").lower() == task["method"].lower()]
        g["listed_target_method"] = len(listed)
        if listed:
            findings.append(f"[G] {tid}: list_reference_implementations still "
                            f"lists '{task['method']}' as having an implementation")
        try:
            r = GRAPH.get_code_for_paper(task["arxiv_id"])
            g["get_code_for_paper_vri"] = len(
                r.get("verified_reference_implementations", []))
            if g["get_code_for_paper_vri"]:
                findings.append(f"[G] {tid}: get_code_for_paper still advertises "
                                f"{g['get_code_for_paper_vri']} verified impl(s)")
            leak = _graph_leak(r, texts)
            if leak:
                findings.append(f"[G] {tid}: get_code_for_paper leaked source {leak}")
        except ValueError as e:
            g["get_code_for_paper_vri"] = f"raised: {str(e)[:60]}"
        # compose RESOLVING is not by itself a leak, and the first version of
        # this check said it was. Its third resolution tier is a substring
        # match, so with the exact subject held out it lands on a DIFFERENT,
        # non-held-out routine from a different paper -- `ppo_clip_objective`
        # resolved to `ppo_clip_objective_gradient_step` (2110.02544). That is
        # the proximity behaviour this experiment exists to measure, not a
        # breach. What would be a breach is resolving to the held-out artifact
        # itself, so the check now tests the resolved (entry, origin) pair
        # against the hold-out by sha.
        by_pair = {(lex["origin"][i], lex["entry"][i]): lex["sha"][i]
                   for i in range(lex["n_docs"])}
        try:
            r = GRAPH.compose(task["entry"])
            rt = r.get("resolved_to") or {}
            sha = by_pair.get((rt.get("paper"), rt.get("entry")))
            g["compose"] = {"resolved_to_entry": rt.get("entry"),
                            "resolved_to_paper": rt.get("paper"),
                            "is_the_target": rt.get("entry") == task["entry"]
                            and rt.get("paper") == task["arxiv_id"],
                            "typed": r.get("typed"), "adapter": r.get("adapter")}
            if sha in shas or g["compose"]["is_the_target"]:
                findings.append(f"[G] {tid}: compose resolved to the HELD-OUT "
                                f"artifact ({rt.get('entry')} / {rt.get('paper')})")
            leak = _graph_leak(r, texts)
            if leak:
                findings.append(f"[G] {tid}: compose leaked held-out source {leak}")
        except ValueError:
            g["compose"] = "unresolvable"
        row["graph"] = g
        HO.clear_holdout()
        rows.append(row)
        print(f"  {tid:>22}  holdout={len(shas):>3}  "
              f"reachable_without={reachable}  graph={g.get('get_reference_implementation')}")

    # T -- thread cross-talk
    def _probe_thread(pair):
        tid, other = pair
        HO.set_holdout(set(ho[tid]["shas"]))
        got = set(_flat_shas(FLAT.code_search(tasks[tid]["entry"], limit=TOPK)))
        mine = got & set(ho[tid]["shas"])
        theirs = got & set(ho[other]["shas"])
        HO.clear_holdout()
        return tid, sorted(mine), sorted(theirs)

    ids = list(ho)
    cross = []
    if len(ids) >= 2:
        pairs = [(ids[0], ids[1]), (ids[1], ids[0])]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            for tid, mine, theirs in ex.map(_probe_thread, pairs):
                cross.append({"task_id": tid, "own_holdout_leaked": mine,
                              "other_holdout_suppressed": theirs})
                if mine:
                    findings.append(f"[T] {tid}: own hold-out leaked under "
                                    f"concurrency: {mine}")
        # The positive half of the same check: with no hold-out at all, the
        # entry query for ids[0] DOES surface its own sample. Without this,
        # "no leak" could just mean the query returns nothing either way.
        HO.clear_holdout()
        base = set(_flat_shas(FLAT.code_search(tasks[ids[0]]["entry"], limit=TOPK)))
        if not (base & set(ho[ids[0]]["shas"])):
            findings.append("[T] cross-talk check is vacuous: the control query "
                            "does not reach its own sample even unheld")

    session.close()
    driver.close()

    provenance.write_json(Path(args.out), {
        "n_tasks": len(rows), "findings": findings, "tasks": rows,
        "cross_talk": cross, "topk": TOPK,
    }, inputs=[Path(args.tasks), Path(args.holdout)], params=vars(args), indent=2)
    print(f"\n{len(findings)} finding(s) -> {args.out}")
    for f in findings[:20]:
        print("  " + f)
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
