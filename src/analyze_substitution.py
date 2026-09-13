#!/usr/bin/env python3
"""
Analysis for the substitution experiment (PREREGISTRATION_SUBSTITUTION.md).
Read-only (C3).

Everything here was fixed before the run:

  PRIMARY      binary referee pass, paired exact two-sided sign test.
  CO-PRIMARY   property fraction (required - failed)/required, 0 for a
               non-submission or referee crash, paired Wilcoxon signed-rank.
               Pre-committed as the usability measure BECAUSE a substitute is
               not pass/fail the way an exact reproduction is, and because it
               is where the power lives: it uses the pairs where both arms
               fail the binary and one is much closer than the other.
  SECONDARY    adoption, substitute provenance, turns/wall/cost, and the
               syntology_compose call count.
  AUDIT        every *_ho transcript is scanned for every held-out sha AND
               every held-out source verbatim. A hit invalidates that task,
               which is REPORTED as an invalidation, never silently dropped.

`sign_test_p`, `run_cost` and `PRICE` are imported from analyze.py rather
than re-typed, so the two reports cannot disagree about what a p-value or a
dollar is (R10).

    ./venv/bin/python3 <BENCH>/analyze_substitution.py \
        --results .../results_v16.json --runs .../runs_v16 \
        --holdout .../tasks/holdout_sets.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
sys.path.insert(0, str(HERE))

import provenance  # noqa: E402
from analyze import PRICE, run_cost, sign_test_p  # noqa: E402

ARMS = ["none", "syntology_ho", "code_only_ho"]


def frac(row) -> float:
    """Share of the task's pass_both properties this run satisfied."""
    req = row.get("properties_required")
    if not req:
        return 0.0
    return (req - len(row.get("properties_failed") or [])) / req


def wilcoxon(diffs):
    """Two-sided Wilcoxon signed-rank on the non-zero paired differences."""
    d = [x for x in diffs if x != 0]
    n = len(d)
    if n == 0:
        return {"n_nonzero": 0, "W": None, "p": 1.0, "z": None}
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        avg = (i + j + 2) / 2.0          # average rank over the tie block
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    w_pos = sum(r for r, x in zip(ranks, d) if x > 0)
    w_neg = sum(r for r, x in zip(ranks, d) if x < 0)
    W = min(w_pos, w_neg)
    try:
        from scipy.stats import wilcoxon as _w
        p = float(_w(d, alternative="two-sided",
                     zero_method="wilcox", method="exact"
                     if n <= 25 else "approx").pvalue)
    except Exception:                      # noqa: BLE001 -- normal fallback
        mu = n * (n + 1) / 4.0
        sd = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
        z = (W - mu) / sd if sd else 0.0
        p = math.erfc(abs(z) / math.sqrt(2))
    mu = n * (n + 1) / 4.0
    sd = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    return {"n_nonzero": n, "W_plus": w_pos, "W_minus": w_neg, "W": W,
            "z": round((W - mu) / sd, 3) if sd else None, "p": p}


def transcript_text(run_dir: Path) -> str:
    p = run_dir / "transcript.json"
    return p.read_text() if p.exists() else ""


def fetched_origins(run_dir: Path) -> list:
    """Origin arXiv ids of artifacts the run actually RECEIVED from its arm.

    Parsed out of the tool RESULTS, not the calls: a call that errored
    fetched nothing, and adoption measured on calls would count it.

    The transcript stores each tool result as a JSON *string* inside a JSON
    document, so its quotes are escaped. A scan of the raw file text for
    `"origin_arxiv_id": "` therefore finds nothing in the graph arm and
    everything in the flat arm (whose `attributed to arXiv:` carries no
    quotes) -- which read as an adoption collapse that was entirely an
    artifact of the scanner. Parse, then walk.
    """
    p = run_dir / "transcript.json"
    if not p.exists():
        return []
    out = []

    def _walk(o):
        if isinstance(o, dict):
            # Only a record that actually CARRIES SOURCE counts as an artifact
            # received. Both arms also return origin ids on pointer-shaped
            # records -- the graph arm's `fallback` names the target paper
            # itself -- and counting those scored a run that was handed nothing
            # but a repo URL as an adopted fetch, 6/6, under a hold-out where
            # the graph served no code at all.
            code = o.get("code")
            if isinstance(code, str) and len(code) > 40:
                v = o.get("origin_arxiv_id") or o.get("paper_attribution")
                out.append(v if isinstance(v, str) and v else "?")
            for x in o.values():
                _walk(x)
        elif isinstance(o, list):
            for x in o:
                _walk(x)

    for msg in json.loads(p.read_text()):
        for block in msg.get("content", []) if isinstance(msg, dict) else []:
            tr = block.get("toolResult") if isinstance(block, dict) else None
            if not tr:
                continue
            for c in tr.get("content", []):
                txt = c.get("text") or ""
                try:
                    _walk(json.loads(txt))
                except ValueError:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--holdout", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", default=str(REPO / "data" / "analysis_substitution.json"))
    args = ap.parse_args()

    res = json.loads(Path(args.results).read_text())["runs"]
    ho = json.loads(Path(args.holdout).read_text())["holdout"]
    tasks = {t["task_id"]: t
             for t in json.loads(Path(args.tasks).read_text())["tasks"]}
    runs_root = Path(args.runs)

    by = {(r["task_id"], r["arm"]): r for r in res}
    arms = [a for a in ARMS if any(k[1] == a for k in by)]
    tids = sorted({t for t, _ in by})

    # --- AUDIT: leak scan -----------------------------------------------
    from neo4j import GraphDatabase
    all_shas = sorted({s for v in ho.values() for s in v["shas"]})
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
        texts = {r["sha"]: r["code"] for r in s.run(
            "MATCH (c:CodeSample) WHERE c.code_sha256 IN $s "
            "RETURN c.code_sha256 AS sha, c.code AS code", s=all_shas).data()}
    driver.close()

    leaks = []
    for tid in tids:
        shas = set(ho.get(tid, {}).get("shas", []))
        for arm in arms:
            if not arm.endswith("_ho"):
                continue
            txt = transcript_text(runs_root / tid / arm)
            if not txt:
                continue
            hit_sha = [x for x in shas if x in txt]
            hit_src = [x for x in shas
                       if texts.get(x) and len(texts[x]) > 200
                       and json.dumps(texts[x])[1:-1] in txt]
            if hit_sha or hit_src:
                leaks.append({"task_id": tid, "arm": arm,
                              "sha_in_transcript": hit_sha,
                              "source_in_transcript": hit_src})

    invalid = {l["task_id"] for l in leaks}
    usable = [t for t in tids if t not in invalid]

    # --- primary + co-primary -------------------------------------------
    table, fracs = {}, {}
    for arm in arms:
        rows = [by[(t, arm)] for t in usable if (t, arm) in by]
        table[arm] = {
            "n": len(rows),
            "passed": sum(1 for r in rows if r.get("passed")),
            "mean_property_fraction": round(
                statistics.mean([frac(r) for r in rows]), 4) if rows else None,
            "no_submission": sum(1 for r in rows
                                 if r.get("reason") == "no_submission"),
        }
        fracs[arm] = {r["task_id"]: frac(r) for r in rows}

    def paired(a1, a2):
        b = c = 0
        disc = {"favours_" + a1: [], "favours_" + a2: []}
        for t in usable:
            r1, r2 = by.get((t, a1)), by.get((t, a2))
            if not r1 or not r2:
                continue
            if r1.get("passed") and not r2.get("passed"):
                b += 1
                disc["favours_" + a1].append(t)
            elif r2.get("passed") and not r1.get("passed"):
                c += 1
                disc["favours_" + a2].append(t)
        p = sign_test_p(b, c)
        n = len([t for t in usable if (t, a1) in by and (t, a2) in by])
        out = {"wins": b, "losses": c, "n_paired": n, "p": p,
               "discordant": disc}
        if b + c == 0 and n:
            # Rule of three: 0 discordant in n pairs caps the per-task
            # advantage at ~3/n with 95% confidence. NOT evidence of zero.
            out["rule_of_three_upper_bound_per_task"] = round(3.0 / n, 4)
        return out

    comparisons = {}
    for a1, a2 in [("syntology_ho", "code_only_ho"),
                   ("syntology_ho", "none"), ("code_only_ho", "none")]:
        if a1 not in arms or a2 not in arms:
            continue
        # PAIRED means paired: only tasks where BOTH arms have a run. Defaulting
        # a missing run to 0.0 scores an arm that did not run as a total failure
        # and inverts the sign of the difference -- on the partial dry run that
        # turned an arm leading the floor by +0.28 into trailing it by -0.30.
        both = [t for t in usable if (t, a1) in by and (t, a2) in by]
        comparisons[f"{a1} vs {a2}"] = paired(a1, a2)
        d = [fracs[a1][t] - fracs[a2][t] for t in both]
        comparisons[f"{a1} vs {a2}"]["wilcoxon_property_fraction"] = wilcoxon(d)
        comparisons[f"{a1} vs {a2}"]["n_paired_fraction"] = len(d)
        comparisons[f"{a1} vs {a2}"]["mean_fraction_delta"] = round(
            statistics.mean(d), 4) if d else None

    # --- effort, adoption, mechanism ------------------------------------
    effort, adoption = {}, {}
    for arm in arms:
        rows = [by[(t, arm)] for t in usable if (t, arm) in by]
        effort[arm] = {
            "median_turns": statistics.median([r["turns"] for r in rows]),
            "median_wall_s": statistics.median([r["wall_s"] for r in rows]),
            "median_cost_usd": round(statistics.median(
                [run_cost(r.get("usage") or {}) for r in rows]), 4),
            "total_cost_usd": round(sum(run_cost(r.get("usage") or {})
                                        for r in rows), 4),
        }
        calls, fetched, compose_calls, off_target = 0, 0, 0, []
        for t in usable:
            md = runs_root / t / arm / "meta.json"
            if not md.exists():
                continue
            m = json.loads(md.read_text())
            tc = m.get("tool_calls") or []
            calls += sum(1 for c in tc if c["tool"] not in
                         ("run_python", "submit_solution"))
            compose_calls += sum(1 for c in tc if c["tool"] == "syntology_compose")
            origins = fetched_origins(runs_root / t / arm)
            if origins:
                fetched += 1
                tgt = tasks[t]["arxiv_id"]
                off_target += [o for o in origins if o != tgt]
        adoption[arm] = {"arm_tool_calls": calls,
                         "runs_that_received_an_artifact": fetched,
                         "runs": len(rows),
                         "syntology_compose_calls": compose_calls,
                         "distinct_substitute_origins": len(set(off_target))}

    summary = {
        "arms": arms, "n_tasks_run": len(tids), "n_tasks_usable": len(usable),
        "invalidated_by_leak": sorted(invalid),
        "leaks": leaks,
        "table": table, "comparisons": comparisons,
        "effort": effort, "adoption": adoption,
        "total_spend_usd": round(sum(e["total_cost_usd"] for e in effort.values()), 4),
    }
    provenance.write_json(Path(args.out), summary,
                          inputs=[Path(args.results), Path(args.holdout),
                                  Path(args.tasks)],
                          params=vars(args), indent=2)

    print(f"\n## arms (n usable = {len(usable)} of {len(tids)}; "
          f"{len(invalid)} invalidated by leak)\n")
    for arm in arms:
        r = table[arm]
        print(f"  {arm:<14} {r['passed']:>3}/{r['n']:<3}  "
              f"mean property fraction {r['mean_property_fraction']}  "
              f"no-submission {r['no_submission']}")
    print("\n## paired\n")
    for k, v in comparisons.items():
        w = v["wilcoxon_property_fraction"]
        print(f"  {k:<30} +{v['wins']}/-{v['losses']}  sign p={v['p']:.4f}   "
              f"wilcoxon p={w['p']:.4f} (n_nonzero={w['n_nonzero']}, "
              f"dmean={v['mean_fraction_delta']})")
    print("\n## effort / adoption\n")
    for arm in arms:
        e, a = effort[arm], adoption[arm]
        print(f"  {arm:<14} turns {e['median_turns']:<4} "
              f"wall {e['median_wall_s']:<6} cost ${e['median_cost_usd']:<7} "
              f"total ${e['total_cost_usd']:<7} "
              f"fetched {a['runs_that_received_an_artifact']}/{a['runs']} "
              f"compose {a['syntology_compose_calls']}")
    print(f"\nTOTAL SPEND ${summary['total_spend_usd']}")
    print(f"-> {args.out}")
    if leaks:
        print(f"\n!! {len(leaks)} LEAK(S): {sorted(invalid)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
