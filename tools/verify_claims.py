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
Re-derive every mechanically checkable claim in this repository from `data/`.

CLAIMS_TO_PREREG.md is a document, and a document drifts away from the numbers
it describes. This is the executable half: each check recomputes one published
figure from the published artifacts and fails if it has moved. It reads nothing
but `data/`, `tasks/` and `referees/`, needs no credentials, and costs nothing.

The transcript-derived figures used to be marked `[unverifiable-here]`, because
raw transcripts cannot be published. They are checked now: `data/runs/**/
transcript.json` carries each run REDACTED -- every retrieved body replaced by
a `<redacted body sha256=... bytes=...>` placeholder, structure intact -- and
`src/analyze_code_only_mechanism.py` re-derives `data/mechanism_v15.json` from
them byte for byte. The fidelity bracket is checked the same way, by
`tools/recompute_fidelity_bracket.py` against the audit rows in
`data/fidelity_audit/`.

What is still NOT checkable here is stated in each check's own output rather
than left to be discovered, so a reader can see exactly where trust is being
asked for.

Exit 0 all checks pass - 1 any mismatch.

    python3 tools/verify_claims.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

ok = 0
bad: list[str] = []
notes: list[str] = []


def check(name: str, got, want, unit=""):
    global ok
    if got == want:
        ok += 1
        print(f"  PASS  {name}: {got}{unit}")
    else:
        bad.append(f"{name}: got {got}, published {want}")
        print(f"  FAIL  {name}: got {got}{unit}, published {want}{unit}")


def unverifiable(name: str, where: str):
    notes.append(f"{name} -- rests on {where}")
    print(f"  [unverifiable-here]  {name} (rests on {where})")


def load(p: str):
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def pass_table(results_file: str, tasks_file: str | None = None):
    """arm -> (passed, total), recomputed from the referee's own output."""
    rows = load(results_file)["runs"]
    agg: dict[str, list[int]] = {}
    for r in rows:
        a = agg.setdefault(r["arm"], [0, 0])
        a[0] += 1 if r.get("passed") else 0
        a[1] += 1
    return {k: tuple(v) for k, v in agg.items()}


def paired(results_file: str, arm_a: str, arm_b: str):
    rows = load(results_file)["runs"]
    by: dict[str, dict[str, bool]] = {}
    for r in rows:
        by.setdefault(r["task_id"], {})[r["arm"]] = bool(r.get("passed"))
    wins = losses = 0
    for t, d in by.items():
        if arm_a in d and arm_b in d and d[arm_a] != d[arm_b]:
            if d[arm_a]:
                wins += 1
            else:
                losses += 1
    return wins, losses


# --- DOC-DRIFT GATE ------------------------------------------------------
# "The cited tool does not produce the cited number" has now been found twice
# by outside readers: once as a README sentence calling 83.8% a mutant-approval
# rate that `recompute_fidelity_bracket.py` never emitted, and once as ten
# separate citations of "67 checks / names 3" surviving in README, REPRODUCTION
# and llms.txt after this tool had grown to 71 and 4. Both were prose drifting
# away from a tool that had moved. A third correction is not the answer; a gate
# is.
#
# This deliberately does NOT increment the check count. A check that counts
# itself changes the number it is checking, and then the docs can never state a
# stable figure. It reads the final totals and fails the run on disagreement.
# Docs that describe the CURRENT state and must therefore track this tool.
# CONTRIBUTING.md was missing from this list and carried "67 checks" long after
# the tool reached 73 -- the gate cannot see a file it does not read, which is
# its whole failure mode.
#
# ASSEMBLY_REPORT.md is deliberately NOT here. It opens "Written at packaging
# time 2026-09-11; revised 2026-09-13" and its table records what each tool
# printed on that day. 67 / 3 was correct then. Rewriting it to match today
# would falsify a dated record to satisfy a gate, so the row is annotated as
# historical instead. A dated record and a current claim are different things
# and only one of them should drift.
_DOC_FILES = ("README.md", "REPRODUCTION.md", "llms.txt", "CONTRIBUTING.md")

_COUNT_PATTERNS = (
    r"#\s*(\d+)\s+checks\b",
    r"re-derives the (\d+) checkable numbers",
    r"(\d+) of them and names \d+ it cannot",
    r"from `data/` — (\d+) checks",
    # The quickstart's EXPECTED-OUTPUT line. The gate shipped without this
    # pattern and passed while README still promised "71 checks passed" over a
    # tool emitting 73 -- the gate reproducing, at once, the exact defect it
    # was written to prevent. Any sentence quoting the tool's summary counts.
    r"`?(\d+) checks passed",
)
_NOTES_PATTERNS = (
    r"names (\d+) it cannot",
    r"prints the (\w+) things that",
    r"The (\w+) it prints as \*not\* checkable",
)
_WORD = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _doc_drift(n_checks: int, n_notes: int) -> list[str]:
    """Every doc citation of this tool's own totals must match what it emits."""
    import re as _re
    problems = []
    for fname in _DOC_FILES:
        fp = REPO / fname
        if not fp.exists():
            continue
        text = fp.read_text(encoding="utf-8")
        for pat in _COUNT_PATTERNS:
            for m in _re.finditer(pat, text):
                if int(m.group(1)) != n_checks:
                    problems.append(f"{fname} cites {m.group(1)} checks; "
                                    f"this tool emits {n_checks}")
        for pat in _NOTES_PATTERNS:
            for m in _re.finditer(pat, text):
                raw = m.group(1)
                val = _WORD.get(raw.lower(), None)
                if val is None:
                    try:
                        val = int(raw)
                    except ValueError:
                        continue
                if val != n_notes:
                    problems.append(f"{fname} says {raw!r} unverifiable; "
                                    f"this tool prints {n_notes}")
    # The manifest's own summary must agree with its own file list, and the
    # README must agree with both. summary.files sat at 1,275 while files held
    # 1,277, and the README quoted the stale one next to the command that
    # prints the real one.
    try:
        import json as _json
        man = _json.loads((REPO / "MANIFEST.json").read_text(encoding="utf-8"))
        n_files = len(man["files"])
        summ = (man.get("summary") or {}).get("files")
        if summ is not None and summ != n_files:
            problems.append(f"MANIFEST.json summary.files={summ} but "
                            f"len(files)={n_files}")
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        for m in __import__("re").finditer(r"every one of its ([\d,]+) files", readme):
            if int(m.group(1).replace(",", "")) != n_files:
                problems.append(f"README cites {m.group(1)} manifest files; "
                                f"MANIFEST.json holds {n_files}")
    except Exception as e:                                          # noqa: BLE001
        problems.append(f"manifest cross-check could not run: {e}")
    return problems


def _run_spend(fn: str) -> float:
    """A run's subject spend: the sum of its own effort.*.total_cost fields.

    Published as prose only until 2026-09-16, when an outside reader added the
    shipped fields and got a cent more than the README on two of four runs
    (37.25 not 37.24, 17.41 not 17.40). The fields were already at cent
    precision and summed exactly, so it was not a rounding artifact -- the prose
    had simply been computed once, somewhere else, and never re-derived. Gated
    here for the two runs whose arms are all in one file; v15 is stratified and
    v16's arms are not carried in analysis_substitution.json, so the published
    total still rests partly on figures this tool cannot reach."""
    eff = load(fn).get("effort") or {}
    return round(sum(float(v["total_cost"]) for v in eff.values()
                     if isinstance(v, dict) and "total_cost" in v), 2)


def main() -> int:
    print("subject spend, re-derived from each run's own effort fields")
    check("run-1 subject spend", _run_spend("data/analysis.json"), 37.25, " USD")
    check("v14 subject spend", _run_spend("data/analysis_v14.json"), 17.41, " USD")

    print("v1.5 -- the code_only ablation (results_v15.json)")
    t = pass_table("data/results_v15.json")
    check("code_only passed", t["code_only"], (24, 24))
    check("syntology passed", t["syntology"], (24, 24))
    check("none (floor) passed", t["none"], (10, 24))
    check("code_only vs syntology discordant",
          paired("data/results_v15.json", "code_only", "syntology"), (0, 0))
    check("code_only vs none discordant",
          paired("data/results_v15.json", "code_only", "none"), (14, 0))

    print("\nv1.6 -- the substitution experiment (results_v16.json)")
    t = pass_table("data/results_v16.json")
    # The published primary is the pre-registered n=48; two extra runs exist on
    # a smoke task outside it, so the raw file carries 49 for the *_ho arms.
    # Recomputing the primary needs the same exclusion, stated not hidden.
    rows = load("data/results_v16.json")["runs"]
    primary = {r["task_id"] for r in rows if r["arm"] == "none"}
    prim = Counter()
    tot = Counter()
    for r in rows:
        if r["task_id"] in primary:
            tot[r["arm"]] += 1
            prim[r["arm"]] += 1 if r.get("passed") else 0
    check("none passed (primary 48)", (prim["none"], tot["none"]), (24, 48))
    check("syntology_ho passed (primary 48)",
          (prim["syntology_ho"], tot["syntology_ho"]), (24, 48))
    check("code_only_ho passed (primary 48)",
          (prim["code_only_ho"], tot["code_only_ho"]), (23, 48))
    check("raw file carries n=49 for the hold-out arms (the disclosed extra)",
          (t["syntology_ho"][1], t["code_only_ho"][1]), (49, 49))

    print("\nv1 freeze (results_v14.json)")
    t = pass_table("data/results_v14.json")
    check("syntology passed", t["syntology"], (21, 24))
    check("both passed", t["both"], (21, 24))
    check("search passed", t["search"], (11, 24))
    check("none passed", t["none"], (13, 24))
    check("syntology vs search discordant",
          paired("data/results_v14.json", "syntology", "search"), (10, 0))
    check("search runs that never submitted",
          sum(1 for r in load("data/results_v14.json")["runs"]
              if r["arm"] == "search" and r.get("reason") == "no_submission"), 11)

    print("\nrun 1, strict referee (results.json)")
    t = pass_table("data/results.json")
    check("none passed (the floor that broke prediction 3)", t["none"], (13, 24))
    check("search passed", t["search"], (14, 24))
    check("syntology passed", t["syntology"], (13, 24))
    check("both passed", t["both"], (14, 24))

    print("\nacross every published run (data/runs/**/meta.json)")
    calls = Counter()
    runs = Counter()
    for m in (REPO / "data" / "runs").rglob("meta.json"):
        d = json.loads(m.read_text(encoding="utf-8"))
        runs[d["arm"]] += 1
        for tc in d.get("tool_calls", []):
            calls[tc["tool"]] += 1
    check("syntology_compose calls, all versions, all arms",
          calls["syntology_compose"], 0)
    check("published run records", sum(runs.values()), 478)

    print("\nefficiency and adoption (RESULTS_SUMMARY.md)")
    eff = load("data/analysis_v14.json")["effort"]
    check("v1 freeze search median turns (the cap)", eff["search"]["median_turns"], 20.0)
    check("v1 freeze syntology median turns", eff["syntology"]["median_turns"], 6.0)
    eff = load("data/analysis_v15.json")["effort"]
    check("v1.5 code_only median turns", eff["code_only|ALL"]["median_turns"], 6.0)
    check("v1.5 syntology median cost", eff["syntology|ALL"]["median_cost"], 0.081)
    eff = load("data/analysis_substitution.json")["effort"]
    check("v1.6 code_only_ho median turns", eff["code_only_ho"]["median_turns"], 10)
    check("v1.6 code_only_ho median cost", eff["code_only_ho"]["median_cost_usd"], 0.1787)
    check("v1.6 none median cost", eff["none"]["median_cost_usd"], 0.0464)

    ad = load("data/analysis.json")["adoption"]
    check("run 1: `both` runs that fetched served code",
          ad["both"]["called_get_reference_implementation"], 0)
    check("run 1: `syntology` runs that fetched served code",
          ad["syntology"]["called_get_reference_implementation"], 11)
    ad = load("data/analysis_v14.json")["adoption"]
    check("v1 freeze: `both` runs that fetched served code",
          ad["both"]["called_get_reference_implementation"], 18)
    check("v1 freeze: `syntology` runs that fetched served code",
          ad["syntology"]["called_get_reference_implementation"], 19)

    def called(run_dir, tool, arm):
        n = 0
        for m in (REPO / "data" / "runs" / run_dir).rglob("meta.json"):
            d = json.loads(m.read_text(encoding="utf-8"))
            if d["arm"] == arm and any(tc["tool"] == tool
                                       for tc in d.get("tool_calls", [])):
                n += 1
        return n
    check("v1.5 syntology runs calling get_reference_implementation",
          called("runs_v15", "syntology_get_reference_implementation", "syntology"), 24)
    check("v1.5 code_only runs calling code_get",
          called("runs_v15", "code_get", "code_only"), 24)
    check("v1.6 syntology_ho runs calling get_reference_implementation",
          called("runs_v16", "syntology_get_reference_implementation", "syntology_ho"), 2)

    ns = Counter(r["arm"] for r in load("data/results.json")["runs"]
                 if r.get("reason") == "no_submission")
    check("run 1 no-submission by arm", dict(sorted(ns.items())),
          {"both": 5, "none": 2, "search": 8, "syntology": 7})

    print("\nthe hold-out (holdout_verification.json)")
    hv = load("data/holdout_verification.json")
    check("verification findings", hv["findings"], [])
    check("tasks verified", hv["n_tasks"], 72)
    check("thread cross-talk probes", len(hv["cross_talk"]), 2)
    check("tasks with a hold-out installed",
          len(load("tasks/holdout_sets.json")["holdout"]), 72)
    check("held-out shas", load("tasks/holdout_sets.json")["n_shas_total"], 372)

    print("\nthe task set")
    for tf, n in (("tasks/tasks.json", 24), ("tasks/tasks_freeze.json", 24),
                  ("tasks/tasks_substitution.json", 72)):
        check(f"{tf} tasks", len(load(tf)["tasks"]), n)
    missing = []
    for tf in ("tasks/tasks_freeze.json", "tasks/tasks_substitution.json"):
        for t in load(tf)["tasks"]:
            for k in ("property_tests", "impl_for_validation"):
                if not (REPO / t[k]).exists():
                    missing.append(f"{t['task_id']}:{k}")
    check("referee files present for every task", missing, [])

    # WHAT THE LICENCE ACTUALLY COVERS, counted from the files rather than
    # quoted. `NOTICE` and `LICENSE_QUESTION.md` said 96 suites and 192
    # implementations for two days; the tree holds 72 and 144. The 96 was a
    # count of task ROWS across two task files -- the freeze's 24 ids are a
    # subset of the substitution set's 72 -- and it walked from a tool's
    # output into a licence document without anyone re-deriving it. A number
    # in a LICENCE is the last place a denominator should be loose.
    n_tasks = len(load("referees/INDEX.json")["tasks"])
    check("referee task directories", n_tasks, 72)
    for name, n in (("property_tests.py", 72), ("impl_sonnet.py", 72),
                    ("impl_llama.py", 72)):
        check(f"referees/*/{name}", len(list(REPO.glob(f"referees/*/{name}"))), n)
    idx = load("referees/INDEX.json")["tasks"]
    check("distinct arXiv papers named by the task set",
          len({t["arxiv_id"] for t in idx.values()}), 72)
    check("distinct methods", len({t["method"] for t in idx.values()}), 72)
    for doc, phrases in (
            ("NOTICE", ["72\nproperty-test suites", "144 generated"]),
            ("LICENSE_QUESTION.md", ["72 property suites and the 144 generated"]),
            ("README.md", ["72 property suites", "144 generated implementations"])):
        text = (REPO / doc).read_text(encoding="utf-8")
        check(f"{doc} states the counts this tree actually holds",
              [p for p in phrases if p not in text], [])
    # Report C counts task ROWS, not files, and that is the distinction that
    # was lost. Both numbers are pinned so neither can move silently.
    rows = sum(len(load(f"tasks/{f}")["tasks"])
               for f in ("tasks_freeze.json", "tasks_substitution.json"))
    check("task rows behind corpus_license_report.py's report C", rows, 96)

    print("\nthe mechanism tables, re-derived from the published transcripts")
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "mech.json"
        r = subprocess.run(
            [sys.executable, str(REPO / "src" / "analyze_code_only_mechanism.py"),
             "--out", str(out)], capture_output=True, text=True)
        if r.returncode != 0:
            check("analyze_code_only_mechanism.py runs", r.stderr.strip()[-160:], "")
        else:
            a = load("data/mechanism_v15.json")
            b = json.loads(out.read_text(encoding="utf-8"))
            a.pop("_provenance", None)
            b.pop("_provenance", None)
            check("mechanism_v15.json re-derives from data/runs/**/transcript.json",
                  [k for k in a if a[k] != b.get(k)], [])
    mech = load("data/mechanism_v15.json")
    check("v1.5 flat-arm fetches that were the CORRECT sample",
          mech["fetch_correctness"], {"correct": 24})
    check("v1.5 retrieval routes of fetched samples",
          dict(sorted(mech["routes"].items())),
          {"entry_exact": 2, "keyword": 26, "origin_id": 8, "semantic": 26})
    check("v1.5 conditional: fetched machine-verified code -> passed",
          {k: (v["passed"], v["fetched_verified"])
           for k, v in sorted(mech["conditional"].items())},
          {"code_only": (24, 24), "syntology": (24, 24)})
    check("v1.5 fetches that DEPENDED on the origin arXiv id",
          len(mech["origin_id_dependence"]["only_route"]), 0)

    sys.path.insert(0, str(REPO / "src"))
    import analyze_substitution as SUB
    # SUBSTITUTE origins, so a fetch from the task's OWN paper does not count:
    # the published figure is `off_target`, and counting self-origins turns
    # 143 into 147. Mirrored here rather than approximated.
    sub_tasks = {x["task_id"]: x["arxiv_id"]
                 for x in load("tasks/tasks_substitution.json")["tasks"]}
    # TWO denominators, and they disagree on purpose. The published artifact
    # counts all 49 runs the arm produced; RESULTS_SUBSTITUTION.md's table
    # counts the PRE-REGISTERED 48, which excludes the smoke task the
    # deviations section discloses. 147 and 143 are the same measurement over
    # the two populations, and quoting either without its denominator is how a
    # number starts drifting. Both are checked.
    def origins_over(tids):
        out = set()
        for d in (REPO / "data" / "runs" / "runs_v16").glob("*/code_only_ho"):
            if d.parent.name not in tids:
                continue
            tgt = sub_tasks.get(d.parent.name)
            out |= {o for o in SUB.fetched_origins(d)
                    if o and o != "?" and o != tgt}
        return out
    all_tids = {d.parent.name for d in
                (REPO / "data" / "runs" / "runs_v16").glob("*/code_only_ho")}
    check("v1.6 distinct substitute origins, all 49 runs (analysis artifact)",
          len(origins_over(all_tids)),
          load("data/analysis_substitution.json")["adoption"]["code_only_ho"]
          ["distinct_substitute_origins"])
    check("v1.6 distinct substitute origins, pre-registered 48 "
          "(RESULTS_SUBSTITUTION.md)", len(origins_over(primary)), 143)
    check("v1.6 runs that received actual source, pre-registered 48",
          sum(1 for t in sorted(primary)
              if SUB.fetched_origins(REPO / "data" / "runs" / "runs_v16" / t
                                     / "code_only_ho")), 48)

    print("\nthe fidelity bracket, re-derived from data/fidelity_audit/")
    r = subprocess.run([sys.executable,
                        str(REPO / "tools" / "recompute_fidelity_bracket.py")],
                       capture_output=True, text=True)
    check("recompute_fidelity_bracket.py agrees with the published summary",
          r.returncode, 0)
    fa = json.loads((REPO / "data" / "fidelity_audit"
                     / "audit_summary.json").read_text(encoding="utf-8"))
    check("fidelity bracket, low end (DeepSeek)",
          fa["per_model"]["deepseek"]["rate"], 0.2905)
    check("fidelity bracket, high end (Mistral)",
          fa["per_model"]["mistral"]["rate"], 0.7965)
    check("the permissive instrument's Wilson LB is below the 0.80 bar",
          fa["per_model"]["mistral"]["wilson_lower_95"] < 0.80, True)

    print("\nnot checkable from this repository")
    unverifiable("whether any individual fidelity verdict is right",
                 "the served code and the paper body the adjudicators read, "
                 "neither of which is published here")
    unverifiable("that the 400 audited rows are an SRS of the 2,831-edge frame",
                 "the private graph the frame was drawn from; the frame sha256 "
                 "and seed are in data/fidelity_audit/audit_summary.json")
    unverifiable("what the subject models actually wrote and read",
                 "the raw transcripts, which carry fetched third-party source "
                 "and are not published; the redacted ones keep structure only")

    # --- GRAPH_STATE's overlap counts, now derivable rather than asserted ----
    # An outside reader found this page's most precise numbers were its least
    # checkable. The overlapping ledger entries are published, so the split can
    # be re-derived here. The tranche SIZE (+141,896) is a fact about the graph
    # rather than the ledger and stays unverifiable-here.
    try:
        lw = load("data/run_window_ledger.json")
        ents = lw["entries"]
        struct = sum(1 for e in ents if e.get("changed_counts"))
        check("GRAPH_STATE: writes overlapping the scored run", len(ents), 90)
        check("GRAPH_STATE: of those, changing node/edge counts", struct, 39)
        check("GRAPH_STATE: of those, property writes only", len(ents) - struct, 51)
        check("GRAPH_STATE: ledger header agrees with its own rows",
              [lw["total_overlapping"], lw["changed_node_or_edge_counts"],
               lw["property_writes_only"]],
              [len(ents), struct, len(ents) - struct])
    except Exception as e:                                       # noqa: BLE001
        bad.append(f"run-window ledger: {type(e).__name__}: {e}")
        print(f"  FAIL  run-window ledger unreadable: {type(e).__name__}: {e}")
    unverifiable("the +141,896 CITES tranche size",
                 "the private graph -- the ledger records that the write "
                 "happened and its delta, not the graph's state")

    for problem in _doc_drift(ok, len(notes)):
        bad.append(problem)
        print(f"  FAIL  doc drift: {problem}")

    print(f"\n{ok} checks passed, {len(bad)} failed, "
          f"{len(notes)} figures not checkable here")
    for b in bad:
        print(f"  FAILED: {b}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
