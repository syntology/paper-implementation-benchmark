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
Turn raw run transcripts into publishable ones by removing every retrieved
body, and prove that nothing survived.

WHY THIS EXISTS. The mechanism tables -- which key the agent queried with,
which retrieval route surfaced the sample it fetched, whether that sample was
the right one, how the ontology resolved each name -- are the part of this
benchmark that says *what worked*, and they are derived from transcripts.
Raw transcripts cannot ship: agents pulled 174 distinct code samples into them
in full, 22 of 29 harvested ones under no licence we can rely on, plus GitHub
file bodies, web pages, paper abstracts and OpenReview review text. Publishing
a table nobody else can regenerate is an assertion wearing a table's clothes,
so the choice was ship a redactor or cut the claim. This is the redactor.

WHAT IT KEEPS. Message order and roles, every tool call by name with its
*structural* arguments, and the structural fields of every tool result: shas,
entry names, `matched_by` routes, verification levels, counts, ratings,
statuses, error shapes. That is exactly the input
`analyze_code_only_mechanism.py` reads, so the tables re-derive from the
published tree with the analyzer unmodified.

WHAT IT REMOVES. Every string that could be, or could contain, something we
retrieved: source bodies, verification reports, test cases, fetched files,
fetched web pages, abstracts, review prose, the subject's own `run_python`
and `submit_solution` code (in the substitution arms those are in places close
derivatives of a fetched substitute), `stdout`/`stderr`, and every assistant
text block. Each becomes a fixed-shape placeholder:

    <redacted body sha256=<64 hex> bytes=<n> field=<path> origin=<id|->>

A placeholder is a *string* of bounded length, which matters: consumers that
test `isinstance(x, str) and len(x) > 40` to mean "this record carried source"
keep working, and no consumer has to be patched to read a redacted tree.

THE RULE IS DEFAULT-DENY. `KEEP_KEYS` is an allow-list of key names whose
values are known to be structural. Anything not on it is redacted, so a tool
that grows a new field leaks nothing until someone adds it deliberately. Kept
strings are additionally capped: over `KEEP_CAP` characters a value is
redacted even if its key is allow-listed, because an allow-listed name on an
unexpectedly long value is exactly how this kind of filter fails.

Exit 0 clean - 1 a verification finding - 4 nothing to redact.

    python3 tools/redact_transcripts.py --self-test
    python3 tools/redact_transcripts.py --source <working repo> --bench-dir <dir>
    python3 tools/redact_transcripts.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# Key names whose values are structure, not retrieved content. Default-deny:
# every other string in a tool result is redacted.
KEEP_KEYS = {
    # identity and ranking
    "code_sha256", "sha256", "entry", "language", "source_kind", "matched_by",
    "verification_level", "min_level", "origin_arxiv_id", "code_chars",
    "fetch_with", "retrieve_with", "total_ranked", "returned", "corpus",
    "total_matching", "total_count", "n_distinct_nodes", "n_repos",
    "matched_tokens", "of_tokens", "matched_distinctive", "of_distinctive",
    "limit", "start", "truncated", "total_chars", "returncode", "status",
    "node_type", "n_reviews", "resolved_via", "fallback",
    # bibliographic facts (citation, not licensed reuse)
    "arxiv_id", "paper_title", "title", "method", "year", "venue",
    "conference", "venue_confirmed", "trace_readiness", "id_or_title",
    "name", "type", "url", "html_url", "repo", "path", "ref", "directory",
    "owner", "provenance", "link_provenance", "review_provenance",
    "propose_confidence", "propose_provenance", "repo_provenance",
    "repo_url", "pwc_is_official", "pwc_mentioned_in_paper",
    "pwc_mentioned_in_github", "link_strength", "source_file",
    # graded review scalars (numbers, not the review's prose)
    "rating", "confidence", "soundness", "presentation", "contribution",
    "review_id",
    # provenance of the served artifact
    "generated_by", "cross_checked_by", "spec_review", "attribution",
    "test_cases_provenance", "env",
    # the agent's own query text, and our own notes about a result
    "query", "note", "verified_note", "hint", "authors_note", "error",
}

# Keys whose value is a *list of structural records* we walk into. Any other
# container is walked too -- containers are structure; only strings leak.
KEEP_CAP = 400          # an allow-listed string longer than this is redacted
QUERY_CAP = 1200        # agent-authored query text may run longer

AGENT_AUTHORED = {"query", "name", "id_or_title"}

PLACEHOLDER = re.compile(r"^<redacted body sha256=[0-9a-f]{64} bytes=\d+ "
                         r"field=[^ ]+ origin=[^>]*>$")


def _digest(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()


def _origin_of(parent: dict | None) -> str:
    if not isinstance(parent, dict):
        return "-"
    for k in ("origin_arxiv_id", "arxiv_id", "paper_attribution", "repo", "url"):
        v = parent.get(k)
        if isinstance(v, str) and v and not PLACEHOLDER.match(v):
            return v[:80]
    return "-"


def redact_value(s: str, field: str, parent: dict | None) -> str:
    return (f"<redacted body sha256={_digest(s)} bytes={len(s)} "
            f"field={field} origin={_origin_of(parent)}>")


def redact_obj(obj, path: str = "", parent: dict | None = None, stats=None):
    """Walk a parsed tool-result payload, redacting every non-allow-listed
    string. Containers are preserved so the shape a consumer walks is intact."""
    if isinstance(obj, dict):
        return {k: redact_obj(v, f"{path}.{k}" if path else k, obj, stats)
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(v, f"{path}[]", parent, stats) for v in obj]
    if isinstance(obj, str):
        leaf = path.split(".")[-1].replace("[]", "")
        cap = QUERY_CAP if leaf in AGENT_AUTHORED else KEEP_CAP
        if leaf in KEEP_KEYS and len(obj) <= cap:
            if stats is not None:
                stats["kept_strings"] += 1
            return obj
        if stats is not None:
            stats["redacted_strings"] += 1
            stats["redacted_bytes"] += len(obj)
        return redact_value(obj, path or "?", parent)
    return obj


# Tool-call arguments that are the agent's own generated code, not a query.
CODE_ARGS = {("run_python", "code"), ("submit_solution", "code")}


def redact_transcript(messages: list, stats: dict) -> list:
    out = []
    for msg in messages:
        blocks = []
        for b in msg.get("content") or []:
            if not isinstance(b, dict):
                continue
            if "cachePoint" in b:
                blocks.append({"cachePoint": b["cachePoint"]})
                continue
            if "text" in b:
                # Assistant reasoning and the task prompt. The prompt is ours
                # and is published in src/agent_harness.py; assistant text can
                # quote anything it just fetched, so all of it is redacted and
                # only its size survives.
                t = b["text"] or ""
                stats["redacted_strings"] += 1
                stats["redacted_bytes"] += len(t)
                blocks.append({"text": redact_value(t, "message.text", None)})
                continue
            if "toolUse" in b:
                tu = b["toolUse"]
                args = {}
                for k, v in (tu.get("input") or {}).items():
                    if (tu["name"], k) in CODE_ARGS and isinstance(v, str):
                        stats["redacted_strings"] += 1
                        stats["redacted_bytes"] += len(v)
                        args[k] = redact_value(v, f"{tu['name']}.{k}", None)
                    else:
                        args[k] = redact_obj(v, k, None, stats)
                blocks.append({"toolUse": {k: v for k, v in tu.items()
                                          if k != "input"} | {"input": args}})
                stats["tool_calls"] += 1
                continue
            if "toolResult" in b:
                tr = b["toolResult"]
                content = []
                for c in tr.get("content") or []:
                    if not isinstance(c, dict) or "text" not in c:
                        continue
                    txt = c["text"] or ""
                    try:
                        payload = json.loads(txt)
                    except ValueError:
                        # Not JSON: a raw body or a plain error string. There
                        # is no structure to keep, so none is kept.
                        stats["redacted_strings"] += 1
                        stats["redacted_bytes"] += len(txt)
                        content.append({"text": redact_value(
                            txt, "toolResult.nonjson", None)})
                        continue
                    content.append({"text": json.dumps(
                        redact_obj(payload, "", None, stats))})
                blocks.append({"toolResult": {k: v for k, v in tr.items()
                                              if k != "content"}
                               | {"content": content}})
                continue
        out.append({"role": msg.get("role"), "content": blocks})
    return out


# --- verification ----------------------------------------------------------

def verify(root: Path) -> list[str]:
    """A redacted tree is only trustworthy if it is CHECKED, not just produced.

    Every string in every redacted transcript must be either a placeholder, an
    allow-listed value within its cap, or short structural text. A finding
    names the file and the field."""
    findings = []
    n = 0
    for p in sorted(root.rglob("transcript.json")):
        n += 1
        doc = json.loads(p.read_text())
        for hit in _bad_strings(doc, ""):
            findings.append(f"{p.relative_to(root)}: {hit}")
    if not n:
        findings.append(f"no transcripts under {root}")
    return findings


def _bad_strings(obj, path):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _bad_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _bad_strings(v, f"{path}[]")
    elif isinstance(obj, str):
        leaf = path.split(".")[-1].replace("[]", "")
        if PLACEHOLDER.match(obj):
            return
        # A tool result rides as a JSON string inside the document; re-parse
        # and check its contents rather than its serialisation.
        if leaf == "text" and obj.startswith(("{", "[")):
            try:
                yield from _bad_strings(json.loads(obj), path + "<json>")
                return
            except ValueError:
                pass
        cap = QUERY_CAP if leaf in AGENT_AUTHORED else KEEP_CAP
        if len(obj) > cap:
            yield f"{path}: {len(obj)} chars, over cap {cap}"
        elif leaf not in KEEP_KEYS and leaf not in (
                "role", "toolUseId", "status", "cachePoint", "name", "text"):
            yield f"{path}: non-allow-listed key kept ({len(obj)} chars)"


# --- self-test -------------------------------------------------------------

SECRET_BODY = (
    "def harvested_secret_routine(x, y):\n"
    "    # THIS LINE IS THE CANARY 8f4c2a1b9e7d and must never survive\n"
    "    z = x @ y.T\n" + "    z = z + 1\n" * 30 + "    return z\n")


def self_test() -> int:
    """Plant a body in every place a body can ride and require that not one
    line of it survives. A redactor never observed failing is not a verified
    redactor -- the same standard tools/scan_secrets.py is held to."""
    canary = "8f4c2a1b9e7d"
    fake = [
        {"role": "user", "content": [{"text": "Implement " + SECRET_BODY}]},
        {"role": "assistant", "content": [
            {"text": "Here is what I found:\n" + SECRET_BODY},
            {"toolUse": {"toolUseId": "t1", "name": "code_search",
                         "input": {"query": "momentum update", "limit": 20}}},
            {"toolUse": {"toolUseId": "t2", "name": "run_python",
                         "input": {"code": SECRET_BODY}}}]},
        {"role": "user", "content": [
            {"toolResult": {"toolUseId": "t1", "status": "success", "content": [
                {"text": json.dumps({"query": "momentum update",
                                     "total_ranked": 385, "returned": 2,
                                     "results": [
                                         {"code_sha256": "a" * 64,
                                          "entry": "f", "matched_by": ["keyword"],
                                          "verification_level": 3,
                                          "origin_arxiv_id": "2007.06680"}],
                                     "unknown_new_field": SECRET_BODY})}]}},
            {"toolResult": {"toolUseId": "t2", "status": "error", "content": [
                {"text": SECRET_BODY}]}}]},
        {"role": "assistant", "content": [
            {"toolUse": {"toolUseId": "t3", "name": "code_get",
                         "input": {"code_sha256": "b" * 64}}}]},
        {"role": "user", "content": [
            {"toolResult": {"toolUseId": "t3", "content": [
                {"text": json.dumps({"samples": [
                    {"code_sha256": "b" * 64, "entry": "f",
                     "verification_level": 3, "source_kind": "harvested",
                     "origin_arxiv_id": "2007.06680",
                     "code": SECRET_BODY,
                     "verification_report": SECRET_BODY,
                     "test_cases": SECRET_BODY,
                     "signature": "def harvested_secret_routine(x, y):"}]})}]}}]},
    ]
    stats = _new_stats()
    red = redact_transcript(fake, stats)
    blob = json.dumps(red)
    problems = []
    if canary in blob:
        problems.append("CANARY SURVIVED in the redacted transcript")
    for line in SECRET_BODY.splitlines():
        if len(line.strip()) > 12 and line.strip() in blob:
            problems.append(f"body line survived: {line.strip()[:40]!r}")
    if "def harvested_secret_routine" in blob:
        problems.append("the signature line survived")
    findings = list(_bad_strings(red, ""))
    if findings:
        problems.append(f"verifier flags its own output: {findings[:3]}")

    # The structure the mechanism analyzer reads must still be there.
    payload = json.loads(red[2]["content"][0]["toolResult"]["content"][0]["text"])
    if payload["results"][0]["matched_by"] != ["keyword"]:
        problems.append("matched_by did not survive -- the tables would break")
    if payload.get("total_ranked") != 385:
        problems.append("ranking counts did not survive")
    if not PLACEHOLDER.match(payload["unknown_new_field"]):
        problems.append("DEFAULT-DENY FAILED: an unknown field was kept")
    samples = json.loads(
        red[4]["content"][0]["toolResult"]["content"][0]["text"])["samples"][0]
    if samples["verification_level"] != 3:
        problems.append("verification_level did not survive")
    if not (isinstance(samples["code"], str) and len(samples["code"]) > 40):
        problems.append("the `carried source` predicate broke: `code` must "
                        "remain a >40-char string so fetched_origins() counts it")

    # CODE_ARGS is defence in depth: `code` is not allow-listed, so a code
    # argument is already redacted by the default-deny rule. Testing it only
    # through that rule tests nothing about CODE_ARGS -- a mutation removing
    # it survived until this check existed. So the property is checked on its
    # own terms: with `code` allow-listed and SHORT enough to clear the cap,
    # the subject's own generated code must still not ride out.
    global KEEP_KEYS
    saved, KEEP_KEYS = KEEP_KEYS, KEEP_KEYS | {"code"}
    try:
        short = "def f(x):\n    return x + 1  # canary2 3e91aa\n"
        probe = redact_transcript([{"role": "assistant", "content": [
            {"toolUse": {"toolUseId": "p1", "name": "run_python",
                         "input": {"code": short}}},
            {"toolUse": {"toolUseId": "p2", "name": "submit_solution",
                         "input": {"code": short}}}]}], _new_stats())
        for blk in probe[0]["content"]:
            if not PLACEHOLDER.match(blk["toolUse"]["input"]["code"]):
                problems.append(
                    f"CODE_ARGS did not hold for {blk['toolUse']['name']}: the "
                    "subject's own code survived once `code` was allow-listed")
    finally:
        KEEP_KEYS = saved

    for label, ok in (("canary removed", "CANARY SURVIVED in the redacted transcript" not in problems),
                      ("subject-authored code redacted by name, not by cap",
                       not any(p.startswith("CODE_ARGS") for p in problems)),
                      ("body lines removed", not any(p.startswith("body line") for p in problems)),
                      ("unknown field denied by default",
                       "DEFAULT-DENY FAILED: an unknown field was kept" not in problems),
                      ("structure preserved", not any(
                          "did not survive" in p or "predicate broke" in p
                          for p in problems)),
                      ("verifier clean on own output",
                       not any(p.startswith("verifier flags") for p in problems))):
        print(f"  {'PASS' if ok else 'FAIL':4s}  {label}")
    print("\nredactor self-test: " + ("PASS" if not problems else "FAIL"))
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    return 1 if problems else 0


def _new_stats():
    return {"kept_strings": 0, "redacted_strings": 0, "redacted_bytes": 0,
            "tool_calls": 0}


RUN_DIRS = ["runs", "runs_v11", "runs_v12", "runs_v13", "runs_v14",
            "runs_v15", "runs_v16"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="working repo root (authors only)")
    ap.add_argument("--bench-dir", default=None,
                    help="benchmark directory inside --source; also read from "
                         "BENCH_INTERNAL_DIR")
    # Beside each run's meta.json, which is where the analyzers look.
    ap.add_argument("--out", default=str(REPO / "data" / "runs"))
    ap.add_argument("--verify", nargs="?", const=str(REPO / "data" / "runs"),
                    help="check an already-redacted tree and exit")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if args.verify:
        findings = verify(Path(args.verify))
        for f in findings[:40]:
            print(f"  {f}")
        print("\nredacted-transcript verify: "
              + ("CLEAN" if not findings else f"{len(findings)} FINDINGS"))
        return 1 if findings else 0

    if not args.source:
        print("--source is required to redact (authors only): the raw "
              "transcripts are not in this repository.", file=sys.stderr)
        return 4
    import os
    bench = args.bench_dir or os.environ.get("BENCH_INTERNAL_DIR")
    if not bench:
        print("set --bench-dir or BENCH_INTERNAL_DIR to the benchmark "
              "directory inside --source", file=sys.stderr)
        return 4
    src = Path(args.source).resolve() / bench
    out = Path(args.out)
    stats = _new_stats()
    stats["transcripts"] = 0
    for rd in RUN_DIRS:
        for p in sorted((src / rd).glob("*/*/transcript.json")):
            doc = json.loads(p.read_text())
            red = redact_transcript(doc, stats)
            d = out / rd / p.parent.parent.name / p.parent.name
            d.mkdir(parents=True, exist_ok=True)
            (d / "transcript.json").write_text(
                json.dumps(red, indent=1, sort_keys=True) + "\n")
            stats["transcripts"] += 1
    if not stats["transcripts"]:
        print(f"no transcripts under {src}", file=sys.stderr)
        return 4
    print(json.dumps(stats, indent=1))
    findings = verify(out)
    for f in findings[:40]:
        print(f"  {f}")
    print("\nredacted-transcript verify: "
          + ("CLEAN" if not findings else f"{len(findings)} FINDINGS"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
