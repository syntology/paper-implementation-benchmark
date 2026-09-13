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
Measure the licence position of everything this repo could have shipped, and
of everything it decided not to.

WHY THIS IS A SCRIPT AND NOT A PARAGRAPH. "Most of the corpus is fine" is the
kind of claim that gets written once and then never re-measured. The decision
to exclude the flat index and the raw transcripts rests on counts; the counts
have to be re-derivable, and they have to name the population they are over.

THREE REPORTS.

  A. CORPUS CENSUS. Every :CodeSample in the graph the `code_only` arm
     searched, by source_kind x upstream_license. This is the population the
     flat index indexes, so it is the population a published index would
     redistribute.

  B. FETCH CENSUS. The distinct samples an agent actually pulled the full
     source of, via `code_get`, across the runs whose transcripts a public
     repo might carry -- with each one's upstream licence and repo. This is
     the population raw transcripts would redistribute.

  C. TASK-SET CHECK. The reference implementation behind each benchmark task,
     with its source_kind. The task set is only publishable if none of them is
     harvested third-party code.

Read-only: NEO4J_USER is the read credential and nothing here writes (C3).
Exit 0 clean - 1 if the task set turns out to carry harvested code, which
would block publication outright.

    ./venv/bin/python3 harness/tools/corpus_license_report.py --source <repo>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE.parent
# The internal benchmark directory is supplied, never defaulted: a default here
# would republish the layout tools/assemble.py exists to redact, and
# tools/scan_secrets.py's INTERNAL class would refuse the tree.
GW = os.environ.get("BENCH_INTERNAL_DIR", "")

# SPDX ids under which redistributing a snippet inline, with attribution, is
# permitted. Mirrors backfill_harvest_licenses.PERMISSIVE_INLINE in the
# working repo; kept as a literal here so the published tree is readable
# without it, and asserted equal by --check-parity when that repo is present.
PERMISSIVE_INLINE = {"0BSD", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
                     "BSL-1.0", "CC0-1.0", "ISC", "MIT", "MIT-0",
                     "Unlicense", "Zlib"}

# Redistributable, but with obligations a benchmark repo should not inherit
# silently (source-availability, share-alike, attribution clauses).
COPYLEFT_OR_SHAREALIKE = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1",
                          "LGPL-3.0", "MPL-2.0", "CC-BY-SA-4.0", "CC-BY-4.0",
                          "EPL-2.0", "OSL-3.0"}


def _env(root: Path) -> dict:
    env = {}
    p = root / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            m = re.match(r"^([A-Z0-9_]+)=(.*)$", line.strip())
            if m:
                env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    for k in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def _bucket(lic: str) -> str:
    if lic in PERMISSIVE_INLINE:
        return "permissive_inline"
    if lic in COPYLEFT_OR_SHAREALIKE:
        return "copyleft_or_sharealike"
    if lic == "NONE":
        return "no_licence_declared"       # upstream repo has no LICENSE file
    if lic in ("<none>", "<unrecorded>", None, ""):
        return "unrecorded"               # we never asked, or the ask failed
    return "other_or_unknown_spdx"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(DEST.parent),
                    help="working repo root (for .env and the run trees)")
    ap.add_argument("--out", default=str(DEST / "data" / "corpus" / "license_census.json"))
    args = ap.parse_args()
    src = Path(args.source).resolve()
    env = _env(src)

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            env["NEO4J_URI"], auth=(env["NEO4J_USER"], env["NEO4J_PASSWORD"]),
            notifications_min_severity="OFF")
    except Exception as e:
        print(f"[PARTIAL] graph unreachable: {type(e).__name__}: {e}")
        print("license report: UNVERIFIED (exit 4) -- not a pass")
        return 4

    report: dict = {"note": __doc__.strip().splitlines()[1]}

    # --- A. corpus census --------------------------------------------------
    with driver.session(database=env.get("NEO4J_DATABASE", "neo4j")) as s:
        rows = [r.data() for r in s.run(
            "MATCH (c:CodeSample) RETURN coalesce(c.source_kind,'?') AS kind, "
            "coalesce(c.upstream_license,'<unrecorded>') AS lic, count(*) AS n")]
    census: dict = {}
    for r in rows:
        census.setdefault(r["kind"], {}).setdefault(_bucket(r["lic"]), {})
        census[r["kind"]][_bucket(r["lic"])][r["lic"]] = r["n"]
    totals = {k: sum(sum(d.values()) for d in v.values()) for k, v in census.items()}
    buckets = {k: {b: sum(d.values()) for b, d in v.items()} for k, v in census.items()}
    report["A_corpus_census"] = {"total": sum(totals.values()),
                                 "by_source_kind": totals,
                                 "buckets": buckets, "detail": census}

    # --- B. what the transcripts fetched ------------------------------------
    fetched: set[str] = set()
    # With the internal directory named, this reads the RAW transcripts. With
    # it unset it reads the published redacted ones, which keep every
    # `code_get` argument -- so the population this census is over is the same
    # either way, and a reader can re-run report B without the working repo.
    tr_roots = ([src / GW / d for d in ("runs_v15", "runs_v16")] if GW
                else [DEST / "data" / "runs" / d for d in ("runs_v15", "runs_v16")])
    for root in tr_roots:
        for tr in root.glob("*/*/transcript.json"):
            try:
                msgs = json.loads(tr.read_text())
            except Exception:
                continue
            for m in msgs:
                for b in (m.get("content") or []):
                    tu = b.get("toolUse") if isinstance(b, dict) else None
                    if tu and tu.get("name") == "code_get":
                        v = (tu.get("input") or {}).get("code_sha256")
                        if v:
                            fetched.add(v)
    fetch_rows = []
    if fetched:
        with driver.session(database=env.get("NEO4J_DATABASE", "neo4j")) as s:
            fetch_rows = [r.data() for r in s.run(
                "MATCH (c:CodeSample) WHERE c.code_sha256 IN $shas "
                "RETURN c.code_sha256 AS sha, coalesce(c.source_kind,'?') AS kind, "
                "coalesce(c.upstream_license,'<unrecorded>') AS lic, "
                "c.generated_by AS repo", shas=sorted(fetched))]
    harvested = [r for r in fetch_rows if r["kind"] == "harvested"]
    report["B_transcript_fetch_census"] = {
        "distinct_code_get_targets": len(fetched),
        "resolved_in_graph": len(fetch_rows),
        "by_source_kind": dict(Counter(r["kind"] for r in fetch_rows)),
        "harvested_by_bucket": dict(Counter(_bucket(r["lic"]) for r in harvested)),
        "harvested_detail": sorted(
            [{"sha": r["sha"], "license": r["lic"], "repo": r["repo"]}
             for r in harvested], key=lambda x: (x["license"], x["repo"] or "")),
    }

    # --- C. the task set's own reference implementations --------------------
    task_kinds = Counter()
    task_detail = []
    for tf in ("tasks_freeze.json", "tasks_substitution.json"):
        tasks_dir = (src / GW / "tasks") if GW else (DEST / "tasks")
        doc = json.loads((tasks_dir / tf).read_text())
        for t in doc["tasks"]:
            impl = t.get("impl_for_validation") or ""
            kind = ("generated_by_us" if impl.endswith("impl_sonnet.py")
                    or impl.endswith("impl_llama.py") else "OTHER")
            task_kinds[kind] += 1
            if kind == "OTHER":
                task_detail.append({"task_id": t["task_id"], "impl": impl})
    report["C_task_set_check"] = {"by_kind": dict(task_kinds),
                                  "non_generated": task_detail}

    driver.close()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")

    a = report["A_corpus_census"]
    h = a["buckets"].get("harvested", {})
    ht = a["by_source_kind"].get("harvested", 0)
    unpub = h.get("no_licence_declared", 0) + h.get("unrecorded", 0)
    print(f"A. corpus: {a['total']} CodeSamples; harvested {ht}, "
          f"of which {unpub} ({100*unpub/max(ht,1):.1f}%) carry no licence we can rely on")
    print(f"   permissive-inline {h.get('permissive_inline',0)} - "
          f"copyleft/share-alike {h.get('copyleft_or_sharealike',0)}")
    b = report["B_transcript_fetch_census"]
    print(f"B. transcripts fetched {b['distinct_code_get_targets']} distinct samples; "
          f"{len(harvested)} harvested, buckets {b['harvested_by_bucket']}")
    print(f"C. task set reference implementations: {dict(task_kinds)}")
    print(f"\nwrote {out}")
    if task_detail:
        print("\nTASK SET CARRIES NON-GENERATED CODE -- publication blocked", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
