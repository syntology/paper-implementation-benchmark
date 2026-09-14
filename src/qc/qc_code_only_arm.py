#!/usr/bin/env python3
"""
QC gate for the `code_only` benchmark arm (PREREGISTRATION_CODE_ONLY.md).

WHY THIS EXISTS. The whole ablation rests on one claim: **that arm has the
CodeSamples and none of the graph.** If a `:Method` lookup or a
`HAS_REFERENCE_IMPL` traversal ever leaks into `code_only_arm_tools.py`, the
result stops meaning what the report says it means, and nothing about the
numbers would look wrong. A claim that load-bearing gets a check that
refuses, not a comment that asserts (R4).

Four checks, each naming what refuses on it:

  A. ARM PURITY -- no relationship pattern, no :Method, no :Paper, no
     import of syntology_arm_tools' serving functions in the arm module.
     Refuses: any re-run of the ablation.
  B. TOKENIZER PARITY -- build_code_index.tokenize and
     code_only_arm_tools._tokenize are two copies of one function (the
     builder imports neo4j at module scope, so the arm cannot import it).
     R10: the contract is asserted, not assumed. Refuses: an index build.
  C. ROW ALIGNMENT -- lexicon.pkl row i and all_vectors.npy row i must be
     the same sample. A misalignment returns the code of a DIFFERENT sample
     than the one that was ranked, silently. Refuses: an arm load.
  D. R2 -- no record in the flat index carries a level > 0 without a backed
     verification_report. The 313-node incident must not reappear on a
     fourth serving surface.

Exit 0 clean - 1 findings, per the project exit-code contract.

    ./venv/bin/python3 qc_code_only_arm.py
"""
from __future__ import annotations

import json
import pickle
import random
import re
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GW = REPO
ARM = GW / "code_only_arm_tools.py"
INDEX = Path(os.environ.get("CODE_ONLY_INDEX", REPO.parent / "code_index"))

# Patterns that would mean the arm reached into the graph. The relationship
# pattern is checked as `-[` / `]->` / `<-[` because a traversal cannot be
# written in Cypher without one.
FORBIDDEN = [
    (r"-\[", "relationship traversal"),
    (r"\]->", "relationship traversal"),
    (r"<-\[", "relationship traversal"),
    (r":Method\b", ":Method node"),
    (r":Paper\b", ":Paper node"),
    (r"\bHAS_REFERENCE_IMPL\b", "HAS_REFERENCE_IMPL"),
    (r"\bPROPOSES\b", "PROPOSES"),
    (r"\bCOMPOSED_OF\b", "COMPOSED_OF"),
    (r"\bCITES\b", "CITES"),
    (r"query_engine", "query_engine templates/linker (the graph serving path)"),
]


def _code_only(text: str) -> str:
    """Strip comments and docstrings before pattern-matching.

    The module's own docstring says it traverses nothing, and says it by
    naming the relationships it does not traverse. A check that matched the
    prose would fail on the file that documents the property it verifies.
    """
    import io
    import tokenize as tk
    out = []
    prev_type = None
    try:
        for tok in tk.generate_tokens(io.StringIO(text).readline):
            if tok.type == tk.COMMENT:
                continue
            if tok.type == tk.STRING and prev_type in (None, tk.INDENT,
                                                       tk.NEWLINE, tk.NL):
                continue          # docstring
            out.append(tok.string)
            if tok.type not in (tk.NL, tk.NEWLINE, tk.INDENT, tk.DEDENT):
                prev_type = tok.type
            else:
                prev_type = tok.type
    except tk.TokenError:
        return text
    return "\n".join(out)


def check_purity(findings):
    src = _code_only(ARM.read_text(encoding="utf-8"))
    for pat, what in FORBIDDEN:
        m = re.search(pat, src)
        if m:
            findings.append(
                f"[A] arm purity: {ARM.name} contains {what} ({m.group(0)!r}) "
                f"outside comments/docstrings. The code_only arm must reach "
                f"no graph structure; REFUSE any re-run of the ablation until "
                f"this is removed or the pre-registration is amended.")
    if "syntology_arm_tools" in src:
        findings.append(
            f"[A] arm purity: {ARM.name} imports syntology_arm_tools at "
            f"runtime. Only build_code_index.py may, and only for the shared "
            f"generic-token list.")


def check_tokenizer(findings):
    sys.path.insert(0, str(GW))
    sys.path.insert(0, str(GW / "vendor"))
    import importlib.util
    # Repo-relative literal on purpose. `GW / "build_code_index.py"` reads to
    # qc_reference_integrity as a ROOT-relative "build_code_index.py", which
    # does not exist there, so this check reported a broken reference in the
    # file whose whole job is to keep the arm honest. Spelling the path in
    # full makes the reference genuinely checkable (R8): move the builder and
    # this goes red, which is the point.
    spec = importlib.util.spec_from_file_location(
        "_bci", GW / "build_code_index.py")
    try:
        bci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bci)
    except Exception as e:                                  # noqa: BLE001
        findings.append(f"[B] tokenizer parity: cannot import "
                        f"build_code_index.py ({type(e).__name__}: {e})")
        return
    import code_only_arm_tools as arm
    probes = ["compute_chameleon_domain_weights", "FavorPlusAttention",
              "2505.24844", "def gp_lower_confidence_bound(mu, sigma, beta):",
              "IS-MBPG* momentum", "", "UOT-FM loss"]
    for p in probes:
        a, b = bci.tokenize(p), arm._tokenize(p)
        if a != b:
            findings.append(
                f"[B] tokenizer parity: build_code_index.tokenize and "
                f"code_only_arm_tools._tokenize disagree on {p!r}: {a} vs {b}. "
                f"The index and the query would be tokenised differently, so "
                f"REFUSE an index build until they match.")


def check_alignment(findings):
    lex_p, vec_p, sha_p = (INDEX / "lexicon.pkl", INDEX / "all_vectors.npy",
                           INDEX / "all_shas.json")
    if not lex_p.exists():
        findings.append(f"[PARTIAL] alignment: {lex_p} missing -- run "
                        f"build_code_index.py, or set CODE_ONLY_INDEX")
        return None
    with lex_p.open("rb") as fh:
        lex = pickle.load(fh)
    if not (vec_p.exists() and sha_p.exists()):
        findings.append(f"[C] alignment: {vec_p.name}/{sha_p.name} missing -- "
                        f"run build_code_vectors.py")
        return lex
    shas = json.loads(sha_p.read_text(encoding="utf-8"))
    if shas != lex["sha"]:
        findings.append(
            "[C] alignment: all_shas.json and lexicon.pkl disagree on row "
            "order. Every ranked hit would return a DIFFERENT sample's code. "
            "REFUSE an arm load; rebuild both.")
    import numpy as np
    M = np.load(vec_p, mmap_mode="r")
    if M.shape[0] != len(shas):
        findings.append(f"[C] alignment: all_vectors.npy has {M.shape[0]} rows "
                        f"and all_shas.json {len(shas)}")
    return lex


def check_r2(findings, lex, live=True):
    """R2 on the artifact AND against the live graph.

    Comparing counts is not enough and the mutation test proved it: flipping
    one record's level from 1 to 3 left the `level > 0` count identical and
    the first version of this check passed. So the whole level vector is
    compared element-wise, and the levels themselves are re-derived from the
    graph on a sample -- which is the only place the 313-node lesson can
    actually be tested, since records.jsonl does not carry `has_report`.
    """
    if lex is None:
        return
    recs = INDEX / "records.jsonl"
    if not recs.exists():
        findings.append(f"[D] R2: {recs} missing")
        return
    levels, shas, bad = [], [], 0
    with recs.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            levels.append(r["level"])
            shas.append(r["sha"])
            if r["level"] not in (0, 1, 2, 3):
                bad += 1
    if bad:
        findings.append(f"[D] R2: {bad} records carry a level outside 0-3")
    if len(levels) != lex["n_docs"]:
        findings.append(f"[D] records.jsonl has {len(levels)} rows, lexicon "
                        f"claims {lex['n_docs']}")
        return
    import numpy as np
    lvl = np.asarray(lex["level"])
    diff = np.flatnonzero(lvl != np.asarray(levels, dtype=lvl.dtype))
    if diff.size:
        findings.append(
            f"[D] R2: records.jsonl and lexicon.pkl disagree on the "
            f"verification level of {diff.size} sample(s), first at row "
            f"{int(diff[0])} ({shas[int(diff[0])]}): records says "
            f"{levels[int(diff[0])]}, lexicon says {int(lvl[diff[0]])}")
    if shas != lex["sha"]:
        findings.append("[D] records.jsonl and lexicon.pkl disagree on row order")
    print(f"    index: {len(levels)} records, {int((lvl > 0).sum())} with a "
          f"backed level > 0")

    if not live:
        return
    import os
    if not os.environ.get("NEO4J_URI"):
        findings.append("[D] R2: NEO4J_URI unset, so the level claims in the "
                        "index were not re-derived from the graph. Run with "
                        "the environment sourced, or --offline to declare "
                        "the structural pass sufficient.")
        return
    try:
        from neo4j import GraphDatabase
        drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
                                   auth=(os.environ["NEO4J_USER"],
                                         os.environ["NEO4J_PASSWORD"]))
        rnd = random.Random(20260910)
        levelled = [i for i in range(len(levels)) if levels[i] > 0]
        sample = ([shas[i] for i in rnd.sample(levelled, min(150, len(levelled)))]
                  + [shas[i] for i in rnd.sample(range(len(shas)), 150)])
        with drv.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as s:
            rows = s.run("""
                MATCH (c:CodeSample) WHERE c.code_sha256 IN $shas
                RETURN c.code_sha256 AS sha, c.verification_level AS lvl,
                       c.verification_report IS NOT NULL AS backed
            """, shas=sample).data()
        drv.close()
    except Exception as e:                                   # noqa: BLE001
        findings.append(f"[D] R2: could not re-derive levels from the graph "
                        f"({type(e).__name__}: {e}) -- this check gates the "
                        f"313-node lesson and a silent skip is what it exists "
                        f"to prevent")
        return
    pos = {sh: i for i, sh in enumerate(shas)}
    mism = unbacked = 0
    for r in rows:
        want = int(r["lvl"] or 0) if r["backed"] else 0
        if not r["backed"] and (r["lvl"] or 0) > 0:
            unbacked += 1
        got = levels[pos[r["sha"]]]
        if got != want:
            mism += 1
            if mism == 1:
                findings.append(
                    f"[D] R2: index serves {r['sha']} at level {got}; the "
                    f"graph node says {r['lvl']} with report={r['backed']}, "
                    f"so the honest level is {want}. REFUSE the arm until the "
                    f"index is rebuilt.")
    print(f"    R2 live re-derivation: {len(rows)} sampled, {mism} mismatched, "
          f"{unbacked} unbacked levels correctly zeroed")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true",
                    help="skip the live re-derivation of index levels from "
                         "the graph (structural checks only)")
    a = ap.parse_args()
    findings = []
    check_purity(findings)
    check_tokenizer(findings)
    lex = check_alignment(findings)
    check_r2(findings, lex, live=not a.offline)
    real = [f for f in findings if not f.startswith("[PARTIAL]")]
    if findings:
        print("qc_code_only_arm: "
              + ("FINDINGS" if real else "UNVERIFIED (exit 4) -- not a pass"))
        for f in findings:
            print("  " + f)
        return 1 if real else 4
    print("qc_code_only_arm: clean (arm purity, tokenizer parity, row "
          "alignment, R2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
