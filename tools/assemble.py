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
Assemble `harness/` -- the public benchmark repo -- from the working repo.

This script IS the packaging record (STANDARDS.md R1): every file in the
published tree got here by one of the rules below, and MANIFEST.json carries
the sha256 of each one plus the source it came from. Re-running it is how you
check that the published tree still matches the internal artifacts.

Three kinds of rule, and the difference matters for how the repo reads:

  VERBATIM   copied byte-for-byte. Pre-registrations, results documents, the
             harness, the arms, the referee. Nothing that produced a number
             may be edited on the way out.

  REDACTED   copied with a listed, mechanical substitution -- only ever an
             absolute path from the machine that ran the sweeps, counted and
             reported in the summary this prints.

  PATCHED    a small, enumerated set of path and interpreter rules applied to
             src/*.py so the published tree can actually be imported and run.
             Every rule, with its before/after, lands in
             src/PORTABILITY_PATCHES.md. None of them changes behaviour.

  DERIVED    built from internal artifacts: the per-task referee tree, the
             referee index, the patch record.

  REDACTED-TRANSCRIPT
             every run's transcript with each retrieved body replaced by a
             `<redacted body sha256=... bytes=...>` placeholder, so the
             mechanism tables re-derive here. tools/redact_transcripts.py
             does the work and verifies its own output.

  QUOTATIONS-REMOVED
             the fidelity audit's per-row verdicts with the adjudicators'
             verbatim paper quotes dropped.

  AUTHORED   written directly in the published repo -- the prose and the
             tools. Hashed but not copied from anywhere.

WHAT IS DELIBERATELY NOT COPIED, and why, is in ASSEMBLY_REPORT.md. The short
version: the 118,400-row flat index (71% of its harvested rows carry no
upstream licence) and every raw transcript (they contain fetched third-party
source, 22 of 29 harvested samples under no licence at all).

The internal directory names this assembles FROM are arguments, not constants:
see INTERNAL_REDACTIONS for why a default would be the leak.

    ./venv/bin/python3 harness/tools/assemble.py --source . \
        --bench-dir <dir> --refimpl-dir <dir> --audit-dir <dir> [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE.parent
sys.path.insert(0, str(HERE))

# The internal layout this tree was assembled FROM is supplied at run time and
# has no default here, because a default is the leak. See INTERNAL_REDACTIONS.
GW = ""
STAGE13 = ""
AUDIT = ""

# The one machine-specific string that appears inside stamped artifacts.
# Everything replaced here is a filesystem path, never a value.
PATH_REDACTIONS = [
    (re.compile(r"/Users/[A-Za-z0-9_.-]+/Documents/synt" + "ology-final"), "<REPO>"),  # noscan
    (re.compile(r"/Volumes/[A-Za-z0-9_.-]+/synt" + "ology-final"), "<ARCHIVE_VOLUME>"),  # noscan
    (re.compile(r"/private/var/folders/[^\s'\"]+"), "<TMPDIR>"),
    (re.compile(r"/var/folders/[^\s'\"]+"), "<TMPDIR>"),
    (re.compile(r"/Users/[A-Za-z0-9_.-]+/"), "<HOME>/"),
]

# INTERNAL DIRECTORY NAMES ARE A SEPARATE LEAK FROM ABSOLUTE PATHS, and the
# first version of this assembler fixed only the second. Rewriting
# `/Users/<name>/Documents/<repo>/<tree>/<NN_stage_name>` to
# `<REPO>/<tree>/<NN_stage_name>` hides the machine and publishes the layout:
# the numbering scheme, the sibling stages, what each one is called. 3,015
# occurrences survived that way across 529 files, in
# provenance stamps, sweep scripts, the portability patch record and
# `referees/INDEX.json`'s `internal_source`.
#
# They are replaced with STABLE ALIASES rather than deleted, because the reason
# they were kept is real: a reader tracing a published file back to the
# artifact it came from needs to see that two files came from two *different*
# internal origins, and which. `<BENCH>` and `<REFIMPL>` carry exactly that and
# nothing else. Any other numbered stage directory becomes `<INTERNAL>`.
#
# Gated by tools/scan_secrets.py's INTERNAL class, which fails the publish if
# one of these ever reappears; its --self-test plants one and requires the hit.
def internal_redactions(bench: str, stage13: str,
                        extra: list[tuple[str, str]] = ()) -> list[tuple[re.Pattern, str]]:
    tree = bench.split("/")[0]                      # the internal parent tree
    return [(re.compile(r"\b" + re.escape(name) + r"\b"), alias)
            for name, alias in extra] + [
        (re.compile(re.escape(bench)), "<BENCH>"),
        (re.compile(re.escape(stage13)), "<REFIMPL>"),
        # `REPO / "<tree>" / "<stage>"` -- the same name, path-joined in
        # Python source, which no slash-shaped rule would ever have matched.
        (re.compile(r'"' + re.escape(tree) + r'"\s*/\s*"'
                    + re.escape(bench.split("/", 1)[1]) + r'"'), '"<BENCH>"'),
        (re.compile(r'"' + re.escape(tree) + r'"\s*/\s*"'
                    + re.escape(stage13.split("/", 1)[1]) + r'"'), '"<REFIMPL>"'),
        (re.compile(r'"' + re.escape(tree) + r'"\s*/\s*"\d+_[A-Za-z0-9_.-]+"'),
         '"<INTERNAL>"'),
        (re.compile(r"\b" + re.escape(tree) + r"/\d+_[A-Za-z0-9_.-]+"), "<INTERNAL>"),
        (re.compile(r"\b" + re.escape(tree) + r"/"), "<INTERNAL>/"),
    ]


INTERNAL_REDACTIONS: list[tuple[re.Pattern, str]] = []

# --- what ships ------------------------------------------------------------

# (path inside the internal benchmark directory, destination) -- verbatim.
DOCS = [
    ("PREREGISTRATION.md", "prereg/PREREGISTRATION.md"),
    ("PREREGISTRATION_CODE_ONLY.md", "prereg/PREREGISTRATION_CODE_ONLY.md"),
    ("PREREGISTRATION_SUBSTITUTION.md", "prereg/PREREGISTRATION_SUBSTITUTION.md"),
    ("FREEZE_RUN.md", "prereg/FREEZE_RUN.md"),
    ("ABLATION_V11.md", "prereg/ABLATION_V11.md"),
    ("ABLATION_V12.md", "prereg/ABLATION_V12.md"),
    ("ABLATION_V13.md", "prereg/ABLATION_V13.md"),
    ("RESULTS.md", "results/RESULTS.md"),
    ("RESULTS_CODE_ONLY.md", "results/RESULTS_CODE_ONLY.md"),
    ("RESULTS_SUBSTITUTION.md", "results/RESULTS_SUBSTITUTION.md"),
]

# The reference-implementation fidelity audit. Its bracket is the reason
# nothing in this repository carries a correctness claim, and it used to ship
# as a sentence citing an internal document -- an asserted number in a
# benchmark repo, which is the one thing this repo exists to refuse. What
# ships now is the pre-registration, the adjudicator-level summary, and the
# per-row verdicts with every paper quotation removed, so
# tools/recompute_fidelity_bracket.py can re-derive 0.29-0.80 from published
# rows. (path inside the internal audit directory, destination.)
AUDIT_DOCS = [
    ("PREREGISTRATION.md", "data/fidelity_audit/PREREGISTRATION.md"),
]
AUDIT_JSON = [
    ("audit_audit.json", "data/fidelity_audit/audit_summary.json"),
    ("audit_validate.json", "data/fidelity_audit/validate_summary.json"),
    ("audit_mutate.json", "data/fidelity_audit/mutate_summary.json"),
]
AUDIT_ROWS = [
    ("rows_audit.jsonl", "data/fidelity_audit/rows_audit.jsonl"),
    ("rows_validate.jsonl", "data/fidelity_audit/rows_validate.jsonl"),
    ("rows_mutate.jsonl", "data/fidelity_audit/rows_mutate.jsonl"),
]

# Row fields that quote the PAPER rather than describe the code. The
# adjudicators were asked for an evidence quote and they returned verbatim
# body text; that is third-party prose and it does not ship. Everything the
# bracket is computed from -- verdict, failure mode, is_defining, the gold
# labels, the mutation rule -- does.
AUDIT_ROW_DROP = {"evidence_quote", "spec_text_withheld", "review_note_withheld",
                  "gold_note"}
AUDIT_ROW_CAP = 600      # `why` is the adjudicator's own prose; capped, not dropped

# The harness itself. Verbatim: these files produced the numbers.
SRC = [
    "agent_harness.py",
    "benchmark_holdout.py",
    "code_only_arm_tools.py",
    "search_arm_tools.py",
    "syntology_arm_tools.py",
    "verify_solutions.py",
    "verify_holdout.py",
    "analyze.py",
    "analyze_code_only_mechanism.py",
    "analyze_substitution.py",
    "compare_runs.py",
    "build_task_set.py",
    "build_task_set_substitution.py",
    "build_code_index.py",
    "build_code_vectors.py",
    "build_holdout_sets.py",
    "probe_code_only_retrieval.py",
    "probe_substitution.py",
]

SWEEPS = ["run_freeze_sweep.sh", "run_codeonly_sweep.sh", "run_substitution_sweep.sh"]

# Modules the harness imports from the working repo's root. Copied so the
# published tree can be read and (for the runnable arms) executed without the
# rest of the stack. `query_engine` is NOT here -- see ASSEMBLY_REPORT.md.
VENDOR = [
    ("provenance.py", "provenance.py"),
    ("bedrock_client.py", "bedrock_client.py"),
    ("corpus_files.py", "corpus_files.py"),
    ("compose_semantics.py", "compose_semantics.py"),
    ("api_gateway.py", "api_gateway.py"),
    ("arxiv_client.py", "arxiv_client.py"),
    ("source_availability.py", "source_availability.py"),
    ("s2_backoff.py", "s2_backoff.py"),
    ("s2_api_key.py", "s2_api_key.py"),
    ("@REFIMPL@/run_sandboxed.py", "run_sandboxed.py"),
]

# The mechanical gate that proves the `code_only` arm traverses nothing.
GATES = [("qc_code_only_arm.py", "qc/qc_code_only_arm.py")]

TASKS = ["tasks.json", "tasks_freeze.json", "tasks_substitution.json",
         "holdout_sets.json"]

# Referee outcomes and analyses. Each is checked content-free before shipping
# (no string longer than CONTENT_CAP outside its provenance block) and is
# REFUSED rather than trimmed if it fails -- see `_longest_string`.
DATA = [
    "results.json", "results_v11.json", "results_v12.json", "results_v13.json",
    "results_v14.json", "results_v15.json", "results_v16.json",
    "analysis.json", "analysis_v14.json", "analysis_v15.json",
    "analysis_substitution.json",
    "compare_run1_v14.json", "compare_v14_v15.json",
    "mechanism_v15.json",
    "probe_code_only_retrieval.json", "probe_substitution.json",
    "holdout_verification.json",
]

# Longest string a shipped result file may carry outside `_provenance`.
# Nothing in these files is retrieved content: the only long strings are the
# referee's own failure `detail` (truncated to 300 by verify_solutions.py) and
# one 400-char Python traceback. A code body would blow straight past this.
CONTENT_CAP = 500

RUN_DIRS = ["runs", "runs_v11", "runs_v12", "runs_v13", "runs_v14",
            "runs_v15", "runs_v16"]

QUERY_ENGINE_STUB = '''"""
`query_engine` -- a stand-in, not the real thing.

`syntology_arm_tools.py` imports `linker` and `templates` from this package at
module load, and `agent_harness.py` imports that module unconditionally. In
Syntology's working repo those are the production paper-resolution and Cypher
template modules; they are NOT published, because they are the live serving
path of a private system rather than part of this benchmark.

This stand-in exists so that the arms which DO run outside Syntology -- `none`,
`code_only`, and `search` with your own API keys -- can import the harness and
start. Any actual use of the graph arm's paper tools raises with a sentence
that says why, rather than an ImportError three frames deep or, worse, a
quietly wrong answer.

If you have the real package, put it ahead of `src/vendor/` on `PYTHONPATH`
and it takes precedence; nothing here has to be removed.

What this means for reproduction: the `syntology` and `syntology_ho` arms
cannot be re-run outside Syntology at all. The graph they read is private, and
publishing a snapshot of it is a separate decision from publishing this
benchmark. Their per-run structure, referee outcomes and analyses are in
`data/`, so their NUMBERS are auditable even though their RUNS are not
repeatable. See REPRODUCTION.md.
"""


class _Unavailable:
    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        raise NotImplementedError(
            f"query_engine.{self._name}.{attr} is not available: the Syntology "
            f"graph arm reads a private Neo4j graph through production serving "
            f"code that is not published with this benchmark. The `none`, "
            f"`code_only` and `search` arms do not need it. See REPRODUCTION.md."
        )


linker = _Unavailable("linker")
templates = _Unavailable("templates")
'''


# --- portability patches ---------------------------------------------------
#
# The harness was written to run from inside the working repo: the shared
# modules sit at the repo root, the referee property suites sit under
# an internal stage directory, and the subject interpreter is
# ./venv/bin/python3. In the published tree none of those paths exist, so the
# `none` arm -- the one arm that needs no credentials at all -- would die at
# import for every outsider. That is precisely the "harness that silently
# fails for everyone else" this repo must not be.
#
# So a SMALL, ENUMERATED patch set is applied on the way out. Every rule is
# listed here, written into src/PORTABILITY_PATCHES.md with its before/after,
# and counted; a rule that stops matching is reported rather than skipped.
# None of them changes behaviour: each one either resolves a path differently
# in the published layout, or reads an environment variable whose default is
# what the internal run used.
# Fixes that live in the PUBLISHED copy of a file and NOT yet in the internal
# source it is copied from. Every entry here makes a non-`--check` run of this
# assembler refuse outright (see main), because re-assembling would regenerate
# the file from `<BENCH>/` and quietly undo the fix. This is not a place to
# park work: an entry is an obligation on the next person with the working
# repo, and it is cleared by mirroring the change, not by deleting the line.
# Entries here BLOCK a non---check assemble run: the published tree carries a
# fix the internal source does not, so regenerating would silently revert it.
# Cleared 2026-09-13 -- src/verify_solutions.py's refusal fix was ported into
# `<BENCH>/verify_solutions.py`, verified there (exit 3 on a bad runs tree,
# exit 0 with --allow-partial). Written with the placeholder, not the real
# directory: the original of this comment spelled the internal name out and
# scan_secrets caught it as an INTERNAL finding on 2026-09-14. A file whose
# whole argument is that "a default is the leak" cannot name the directory in
# its own changelog.
UNMIRRORED_FIXES: dict[str, str] = {}

PORTABILITY_PATCHES: list[tuple[str, str, str]] = [
    # FIRST, and it is why: every module in src/ resolves the shared modules
    # at the working repo's ROOT, which in this layout holds no Python at all.
    # Without this rule `import provenance` raises for 13 of the 18 shipped
    # modules -- including all four analyzers REPRODUCTION.md tells a reader to
    # run -- and the failure only shows up when something actually imports
    # them, which packaging never did.
    ("sys.path.insert(0, str(REPO))",
     "sys.path.insert(0, str(REPO))\n"
     'sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))',
     "the shared modules the harness imports from the working repo's root are "
     "vendored into src/vendor/ here, so that directory goes on the path"),
    ('sys.path.insert(0, str(REPO / "@REFIMPL_PARTS@"))\n',
     '',
     "run_sandboxed.py (the referee's executor) is vendored into src/vendor/, "
     "which the rule above already put on the path, so this line is dropped"),
    ("REPO = HERE.parents[1]",
     'REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))',
     "the repo root is one level above src/ here, two levels above "
     "the benchmark directory internally; BENCH_REPO_ROOT overrides either way"),
    ("REPO = Path(__file__).resolve().parents[2]",
     'REPO = Path(os.environ.get("BENCH_REPO_ROOT",\n'
     '                           Path(__file__).resolve().parents[1]))',
     "same, for the two arm modules that resolve the root inline"),

    ('_sys.path.insert(0, str(_P(__file__).resolve().parents[2]))',
     '_sys.path.insert(0, str(_P(__file__).resolve().parent / "vendor"))',
     "corpus_files.py is vendored; the original inserted a directory ABOVE "
     "the repo root onto sys.path, which is worth not shipping"),
    ('[str(REPO / "venv" / "bin" / "python3"), "-I", str(script)],',
     '[os.environ.get("BENCH_PYTHON", sys.executable), "-I", str(script)],',
     "the subject's run_python tool must use the reader's interpreter; "
     "BENCH_PYTHON pins a different one"),
    ("HERE / args.a", "REPO / args.a",
     "compare_runs.py resolves a relative --a/--b against the directory it "
     "lives in, which internally held the result files and here is src/"),
    ("HERE / args.b", "REPO / args.b",
     "same for --b"),
    ('default=str(HERE / "tasks"', 'default=str(REPO / "tasks"',
     "task sets live at <repo>/tasks/ in the published layout"),
    ('default=str(HERE / "runs")', 'default=str(REPO / "runs")',
     "a fresh run tree belongs at the repo root, beside data/runs/ rather "
     "than inside src/"),
    ('default=str(HERE / "runs_v15")', 'default=str(REPO / "data" / "runs" / "runs_v15")',
     "the published run metadata lives under data/runs/"),
    # The arm-purity gate lives at src/qc/ here, so its two-level path into
    # the working repo has to become a one-level path into src/.
    ('REPO = Path(__file__).resolve().parent\n'
     'GW = REPO / "@BENCH_PARTS@"',
     'REPO = Path(__file__).resolve().parents[1]\n'
     'GW = REPO',
     "the arm-purity gate reads the arm module and the index from src/"),
    ('    sys.path.insert(0, str(GW))',
     '    sys.path.insert(0, str(GW))\n    sys.path.insert(0, str(GW / "vendor"))',
     "the gate's tokenizer-parity check needs the vendored modules on the path"),
    ('"_bci", REPO / "@BENCH@/build_code_index.py")',
     '"_bci", GW / "build_code_index.py")',
     "the gate's tokenizer-parity check loads the index builder from src/"),
    ('INDEX = GW / "code_index"',
     'INDEX = Path(os.environ.get("CODE_ONLY_INDEX", REPO.parent / "code_index"))',
     "the gate looks for the index where the arm does, not beside the arm"),
    ('INDEX_DIR = Path(os.environ.get("CODE_ONLY_INDEX", HERE / "code_index"))',
     'INDEX_DIR = Path(os.environ.get("CODE_ONLY_INDEX", REPO / "code_index"))',
     "the flat index is not shipped; the default points where you would "
     "build one, and CODE_ONLY_INDEX overrides it"),
    # The published tree has no index -- it is not redistributable -- so the
    # gate's checks C and D have no input. The original calls that a FINDING,
    # which would make this gate exit 1 for every reader and teach them to
    # ignore it. The repo's exit-code contract already has a code for "could
    # not verify": 4, used the same way by qc_license_gate.py. This changes no
    # verdict about the arm; check A, the one the ablation rests on, still
    # refuses on its own.
    ('findings.append(f"[C] alignment: {lex_p} missing -- run build_code_index.py")',
     'findings.append(f"[PARTIAL] alignment: {lex_p} missing -- run "\n'
     '                        f"build_code_index.py, or set CODE_ONLY_INDEX")',
     "a missing index reports as a partial, not as a finding"),
    ('    if findings:\n'
     '        print("qc_code_only_arm: FINDINGS")\n'
     '        for f in findings:\n'
     '            print("  " + f)\n'
     '        return 1',
     '    real = [f for f in findings if not f.startswith("[PARTIAL]")]\n'
     '    if findings:\n'
     '        print("qc_code_only_arm: "\n'
     '              + ("FINDINGS" if real else "UNVERIFIED (exit 4) -- not a pass"))\n'
     '        for f in findings:\n'
     '            print("  " + f)\n'
     '        return 1 if real else 4',
     "and the exit code follows the contract: 1 only when a check actually "
     "failed, 4 when one could not run"),
]

# Result/probe/analysis defaults: `HERE / "<name>.json"` -> `REPO / "data"`.
_DATA_DEFAULT = re.compile(r'default=str\(HERE / "([A-Za-z0-9_]+\.json)"\)')
_DATA_DEFAULT_SUB = r'default=str(REPO / "data" / "\1")'

# A MODULE-LEVEL `import os`. Deliberately not matching an indented local
# import (qc_code_only_arm.py has one inside a function): a local import does
# not put `os` in module scope, and the rules below read the environment at
# module level. Getting this wrong the other way produced a NameError at import
# on the first try, which is why the test below runs every shipped module.
_HAS_OS = re.compile(r"^import os\b", re.M)


def _patch(text: str) -> tuple[str, list[str]]:
    applied = []
    introduced_env = False
    for old, new, why in PORTABILITY_PATCHES:
        if old in text:
            text = text.replace(old, new)
            applied.append(why)
            introduced_env = introduced_env or "os.environ.get" in new
    text, n = _DATA_DEFAULT.subn(_DATA_DEFAULT_SUB, text)
    if n:
        applied.append("result/probe/analysis defaults point at data/")
    # Only when a rule above actually introduced a module-level `os.environ`
    # read into a file that has no `import os` to reach.
    if introduced_env and not _HAS_OS.search(text):
        text = text.replace("import sys\n", "import os\nimport sys\n", 1)
        applied.append("added `import os` for the env-var default above")
    return text, applied


def _redact(text: str) -> tuple[str, int]:
    """Machine paths first, then internal directory names.

    Order matters and is the bug that was here: an absolute path is rewritten
    to `<REPO>/<internal dir>`, so a rule that only ever looked for absolute
    paths reported success while the directory names walked out the door
    inside the very string it had just shortened."""
    n = 0
    for pat, sub in PATH_REDACTIONS + INTERNAL_REDACTIONS:
        text, k = pat.subn(sub, text)
        n += k
    return text, n


def _emit_transcript(run_dir: Path, rd: str, emit, redactions, problems, src: Path):
    """Ship each run's transcript, redacted, BESIDE its meta.json.

    Two things follow from putting it there rather than in a tree of its own:
    `analyze_code_only_mechanism.py` finds it with no flags, so the mechanism
    tables regenerate from the command REPRODUCTION.md already documents; and
    a run's structure and its evidence cannot drift apart into two places.

    The redaction and its verification live in tools/redact_transcripts.py --
    one module, self-tested, so there is a single answer to "what came out"."""
    import redact_transcripts as rt          # tools/ is on sys.path via HERE
    p = run_dir / "transcript.json"
    if not p.exists():
        return
    stats = rt._new_stats()
    red = rt.redact_transcript(json.loads(p.read_text(encoding="utf-8")), stats)
    findings = list(rt._bad_strings(red, ""))
    if findings:
        problems.append(f"redacted transcript not clean: {p} -- {findings[:2]}")
        return
    text, n = _redact(json.dumps(red, indent=1, sort_keys=True) + "\n")
    if n:
        redactions.append((str(p), n))
    rel = (f"data/runs/{rd}/{run_dir.parent.name}/{run_dir.name}/transcript.json")
    emit(rel, text.encode(), str(p.relative_to(src)), "redacted-transcript")


def _expand(s: str, bench: str, stage13: str) -> str:
    """Put the real internal names back into a match pattern at run time.

    The patch table has to match the working repo's source exactly, so it needs
    the real directory names -- and this file is published, so it may not carry
    them. The names arrive on the command line and are substituted here;
    `_PARTS` is the `Path / "a" / "b"` spelling the same name takes in Python
    source, which is how it escaped the first redactor."""
    return (s.replace("@BENCH_PARTS@", bench.replace("/", '" / "'))
             .replace("@REFIMPL_PARTS@", stage13.replace("/", '" / "'))
             .replace("@BENCH@", bench)
             .replace("@REFIMPL@", stage13))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _longest_string(obj, cap=CONTENT_CAP):
    """Largest string anywhere in a JSON document, EXCLUDING the `_provenance`
    subtree. Guards the promise that shipped result files carry no code bodies
    and no fetched third-party text.

    `_provenance` is exempt because it is ours by construction -- the argv of
    the command that produced the file, including a long `--only` task list and
    the R7 `--intent` sentence. Paths inside it are still redacted; what it can
    never hold is retrieved content, because provenance.py writes only argv,
    input paths and hashes.
    """
    worst = 0
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            stack.extend(v for k, v in o.items() if k != "_provenance")
        elif isinstance(o, list):
            stack.extend(o)
        elif isinstance(o, str):
            worst = max(worst, len(o))
    return worst


def main() -> int:
    global GW, STAGE13, AUDIT, INTERNAL_REDACTIONS, PORTABILITY_PATCHES
    import os
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(DEST.parent),
                    help="working repo root")
    ap.add_argument("--bench-dir", default=os.environ.get("BENCH_INTERNAL_DIR"),
                    help="the benchmark directory inside --source. No default: "
                         "publishing one would put the internal layout back in "
                         "this file. Also read from BENCH_INTERNAL_DIR.")
    ap.add_argument("--refimpl-dir",
                    default=os.environ.get("BENCH_INTERNAL_REFIMPL_DIR"),
                    help="the reference-implementation stage directory inside "
                         "--source; also BENCH_INTERNAL_REFIMPL_DIR")
    ap.add_argument("--audit-dir", default=os.environ.get("BENCH_INTERNAL_AUDIT_DIR"),
                    help="the fidelity-audit directory inside --source; also "
                         "BENCH_INTERNAL_AUDIT_DIR")
    ap.add_argument("--internal-name", action="append", default=[],
                    metavar="NAME=ALIAS",
                    help="any other internal directory name to rewrite, e.g. "
                         "the corpus tree a vendored module resolves. "
                         "Repeatable; also BENCH_INTERNAL_NAMES as a "
                         "comma-separated list of NAME=ALIAS.")
    ap.add_argument("--check", action="store_true",
                    help="verify the published tree matches MANIFEST.json and "
                         "the sources; write nothing")
    args = ap.parse_args()
    src = Path(args.source).resolve()
    if not (args.bench_dir and args.refimpl_dir and args.audit_dir):
        print("this assembler needs the internal directory names supplied: "
              "--bench-dir, --refimpl-dir and --audit-dir (or the matching "
              "BENCH_INTERNAL_*_DIR variables). They are deliberately absent "
              "from this file -- see INTERNAL_REDACTIONS. Only someone with "
              "the working repo can run it, and they know the names.",
              file=sys.stderr)
        return 2
    GW, STAGE13, AUDIT = (args.bench_dir.rstrip("/"),
                          args.refimpl_dir.rstrip("/"),
                          args.audit_dir.rstrip("/"))
    extra = [tuple(x.split("=", 1)) for x in
             (args.internal_name
              + [y for y in os.environ.get("BENCH_INTERNAL_NAMES", "").split(",") if y])]
    bad = [x for x in extra if len(x) != 2 or not all(x)]
    if bad:
        print(f"--internal-name wants NAME=ALIAS, got {bad}", file=sys.stderr)
        return 2
    INTERNAL_REDACTIONS = internal_redactions(GW, STAGE13, extra) + [
        (re.compile(re.escape(AUDIT)), "<AUDIT>")]
    PORTABILITY_PATCHES = [
        (_expand(o, GW, STAGE13), _expand(n, GW, STAGE13),
         _expand(w, GW, STAGE13))
        for o, n, w in PORTABILITY_PATCHES]
    if not (src / GW).is_dir():
        print(f"no {GW} under {src}", file=sys.stderr)
        return 2

    # A fix made in the PUBLISHED copy of a file this assembler regenerates is
    # a fix with a countdown on it: the next non-check run rewrites that file
    # from the internal source and the change is gone, with no diff, no
    # warning, and a green manifest afterwards because the manifest is
    # rewritten in the same pass. (Standing lesson: fix the source, not just
    # the copy -- a copy-only correction is undone by the next load.) So the
    # revert is refused BEFORE anything is written rather than reported after,
    # and clearing an entry is a deliberate act by whoever mirrored it.
    if UNMIRRORED_FIXES and not args.check:
        print("REFUSING to re-assemble: the published tree carries "
              f"{len(UNMIRRORED_FIXES)} fix(es) that are not in the internal "
              "source this would regenerate them from, so running would "
              "silently revert them:", file=sys.stderr)
        for rel, why in sorted(UNMIRRORED_FIXES.items()):
            print(f"  {rel}\n      {why}", file=sys.stderr)
        print("Mirror each into its internal source, then delete its entry "
              "from UNMIRRORED_FIXES in this file. `--check` still works and "
              "is unaffected.", file=sys.stderr)
        return 2

    manifest: dict[str, dict] = {}
    redactions: list[tuple[str, int]] = []
    problems: list[str] = []

    def emit(rel_dest: str, data: bytes, origin: str, rule: str):
        out = DEST / rel_dest
        if not args.check:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
        elif not out.exists() or out.read_bytes() != data:
            problems.append(f"drift: {rel_dest}")
        # The manifest's `source` is itself published text, and it is where
        # the internal layout was most visibly still on show.
        manifest[rel_dest] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "source": _redact(origin)[0], "rule": rule}

    patched: dict[str, list[str]] = {}
    rules_fired: set[str] = set()

    def copy_text(rel_src: str, rel_dest: str, rule="verbatim", portable=False):
        p = src / rel_src
        if not p.exists():
            problems.append(f"missing source: {rel_src}")
            return
        text = p.read_text(encoding="utf-8")
        # PATCH BEFORE REDACT. The patch table matches real source lines, and
        # redaction rewrites the internal directory names those lines contain
        # -- so redacting first silently stops three rules from matching and
        # ships a tree whose referee cannot import. That happened: every
        # module in src/ raised ModuleNotFoundError until this order was
        # fixed, and the assembler reported no problems because 18 other files
        # were still patched by other rules. `unmatched_patch_rules` below is
        # the gate that would have caught it.
        if portable:
            text, applied = _patch(text)
            if applied:
                patched[rel_dest] = applied
                rule = "portability-patched"
                for w in applied:
                    rules_fired.add(w)
        text, n = _redact(text)
        if n:
            redactions.append((rel_dest, n))
            if rule == "verbatim":
                rule = "redacted-paths"
        emit(rel_dest, text.encode(), rel_src, rule)

    for s, d in DOCS:
        copy_text(f"{GW}/{s}", d)
    for f in SRC:
        copy_text(f"{GW}/{f}", f"src/{f}", portable=True)
    for f in SWEEPS:
        copy_text(f"{GW}/{f}", f"src/sweeps/{f}")
    for s, d in VENDOR:
        copy_text(_expand(s, GW, STAGE13), f"src/vendor/{d}")
    for s, d in GATES:
        copy_text(s, f"src/{d}", portable=True)
    for f in TASKS:
        p = src / GW / "tasks" / f
        if not p.exists():
            problems.append(f"missing task file: {f}")
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        # Point each task at the referee tree THIS repo ships, so the referee
        # resolves without an outsider knowing anything about the internal
        # layout. The internal path stays recoverable from
        # referees/INDEX.json's `internal_source`.
        for t in doc.get("tasks", []):
            tid = t["task_id"]
            if t.get("property_tests"):
                t["property_tests"] = f"referees/{tid}/property_tests.py"
            if t.get("impl_for_validation"):
                t["impl_for_validation"] = f"referees/{tid}/impl_sonnet.py"
        text, n = _redact(json.dumps(doc, indent=1) + "\n")
        if n:
            redactions.append((f"tasks/{f}", n))
        emit(f"tasks/{f}", text.encode(), f"{GW}/tasks/{f}", "path-rewritten")

    for f in DATA:
        p = src / GW / f
        if not p.exists():
            problems.append(f"missing data: {f}")
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        worst = _longest_string(doc)
        if worst > CONTENT_CAP:
            problems.append(f"NOT content-free, refusing to ship: {f} "
                            f"(longest string {worst} chars)")
            continue
        copy_text(f"{GW}/{f}", f"data/{f}")

    # --- the reference-implementation fidelity audit -----------------------
    # README.md's "no correctness claim" rests on this audit's 0.29-0.80
    # bracket. It used to ship as a sentence, which in a repository built to
    # refuse asserted numbers is the worst line in the tree. The rows ship
    # instead, minus every paper quotation; the bracket is then recomputable
    # by tools/recompute_fidelity_bracket.py.
    for s, d in AUDIT_DOCS:
        copy_text(f"{AUDIT}/{s}", d)
    for s, d in AUDIT_JSON:
        p = src / AUDIT / s
        if not p.exists():
            problems.append(f"missing audit summary: {s}")
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        text, n = _redact(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        if n:
            redactions.append((d, n))
        emit(d, text.encode(), f"{AUDIT}/{s}", "redacted-paths")
    n_audit_rows = 0
    for s, d in AUDIT_ROWS:
        p = src / AUDIT / s
        if not p.exists():
            problems.append(f"missing audit rows: {s}")
            continue
        out_lines, dropped = [], 0
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for k in AUDIT_ROW_DROP:
                if k in row:
                    row[k] = None
                    dropped += 1
            over = [k for k, v in row.items()
                    if isinstance(v, str) and len(v) > AUDIT_ROW_CAP]
            if over:
                problems.append(f"audit row field over cap in {s}: {over[:3]}")
            out_lines.append(json.dumps(row, sort_keys=True))
            n_audit_rows += 1
        text, n = _redact("\n".join(out_lines) + "\n")
        if n:
            redactions.append((d, n))
        emit(d, text.encode(), f"{AUDIT}/{s}", "quotations-removed")

    # --- referees: one directory per task, named by task_id ----------------
    referee_index = {}
    seen_files: dict[str, str] = {}
    for tf in ("tasks_freeze.json", "tasks_substitution.json", "tasks.json"):
        doc = json.loads((src / GW / "tasks" / tf).read_text(encoding="utf-8"))
        for t in doc["tasks"]:
            tid = t["task_id"]
            if tid in referee_index:
                continue
            entry = {"task_id": tid, "arxiv_id": t["arxiv_id"],
                     "method": t["method"], "paper_title": t.get("paper_title"),
                     "entry": t["entry"], "signature": t["signature"],
                     "pass_both": t["pass_both"],
                     "suspect_tests": t.get("suspect_tests", []),
                     "files": {}}
            # Two LLM-drafted implementations per task, named by their
            # generator because the distinction is load-bearing: the SONNET
            # one is what revalidated the referee, and the LLAMA one is what
            # the graph actually served to the `syntology` arm. They are not
            # the same file (measured: median similarity ~0.35), and calling
            # either "the reference implementation" would blur which artifact
            # a number is about.
            for key, name in (("property_tests", "property_tests.py"),
                              ("impl_for_validation", "impl_sonnet.py"),
                              ("__sibling_llama__", "impl_llama.py")):
                rel = t.get(key)
                if key == "__sibling_llama__":
                    base = t.get("impl_for_validation")
                    rel = str(Path(base).parent / "impl_llama.py") if base else None
                if not rel:
                    continue
                p = src / rel
                if not p.exists():
                    problems.append(f"missing referee file {rel} for {tid}")
                    continue
                text, n = _redact(p.read_text(encoding="utf-8"))
                if n:
                    redactions.append((f"referees/{tid}/{name}", n))
                dest = f"referees/{tid}/{name}"
                emit(dest, text.encode(), rel, "verbatim")
                entry["files"][name] = {"path": dest,
                                        "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                        "internal_source": rel}
                seen_files[dest] = rel
            referee_index[tid] = entry
    # `internal_source` is the traceability field ASSEMBLY_REPORT.md flagged as
    # the place the internal layout stayed visible. It goes through _redact
    # like everything else now, so it names `<REFIMPL>/...` -- still a distinct,
    # stable origin per file, no longer the internal directory's name.
    index_text, n_idx = _redact(
         (json.dumps({"note": "Referee = property_tests.py, an LLM-drafted "
                              "paper-derived property suite. impl_sonnet.py is the "
                              "implementation used only to revalidate that the suite "
                              "is satisfiable. impl_llama.py is the artifact the "
                              "graph served to the `syntology` arm. NONE of the three "
                              "carries a correctness claim, none is the paper "
                              "authors' code, and passing the suite does not "
                              "establish fidelity to the paper -- see "
                              "README.md, 'What is NOT claimed'.",
                      "n_tasks": len(referee_index),
                      "tasks": referee_index}, indent=1) + "\n"))
    if n_idx:
        redactions.append(("referees/INDEX.json", n_idx))
    emit("referees/INDEX.json", index_text.encode(),
         "derived from tasks/*.json + " + STAGE13, "derived")

    # --- run metadata: structure only, never content -----------------------
    n_metas = 0
    for rd in RUN_DIRS:
        root = src / GW / rd
        if not root.is_dir():
            continue
        for meta in sorted(root.glob("*/*/meta.json")):
            doc = json.loads(meta.read_text(encoding="utf-8"))
            worst = _longest_string(doc)
            # holdout_shas are 64-char hashes; nothing else may be long.
            if worst > CONTENT_CAP:
                problems.append(f"run meta not content-free: {meta}")
                continue
            text, n = _redact(json.dumps(doc, indent=1, sort_keys=True) + "\n")
            if n:
                redactions.append((str(meta), n))
            _emit_transcript(meta.parent, rd, emit, redactions, problems, src)
            rel = f"data/runs/{rd}/{meta.parent.parent.name}/{meta.parent.name}/meta.json"
            emit(rel, text.encode(), str(meta.relative_to(src)), "redacted-paths")
            n_metas += 1

    # --- the query_engine stand-in ----------------------------------------
    # syntology_arm_tools.py does `from query_engine import linker, templates`
    # at import time, and agent_harness imports that module unconditionally --
    # so without something by this name, the `none` arm cannot start. The real
    # query_engine is Syntology's production serving package and is not
    # published. This stand-in lets every other arm import and run, and makes
    # the graph arm fail with a sentence instead of a traceback.
    emit("src/vendor/query_engine/__init__.py", QUERY_ENGINE_STUB.encode(),
         "written by tools/assemble.py", "stub")

    # --- the patch record --------------------------------------------------
    lines = [
        "# Portability patches",
        "",
        "`tools/assemble.py` applies the rules below to `src/*.py` on the way",
        "out of the working repo. They exist for one reason: the harness was",
        "written to run from inside that repo, and without them the `none`",
        "arm -- the one arm needing no credentials at all -- dies at import",
        "for every reader of this repository.",
        "",
        "**None of them changes what any arm does.** Each either resolves a",
        "path for the published layout or reads an environment variable whose",
        "default reproduces the internal behaviour. Everything else in `src/`",
        "is byte-identical to the code that produced the numbers; `MANIFEST.json`",
        "marks a patched file `portability-patched` and an untouched one",
        "`verbatim`.",
        "",
        "## Rules",
        "",
    ]
    for old, new, why in PORTABILITY_PATCHES:
        lines += [f"- **{why}**", "", "  ```diff",
                  *[f"  - {l}" for l in old.splitlines()],
                  *[f"  + {l}" for l in new.splitlines()],
                  "  ```", ""]
    lines += ["- **result/probe/analysis output defaults point at `data/`**", "",
              "  ```diff", '  - default=str(HERE / "<name>.json")',
              '  + default=str(REPO / "data" / "<name>.json")', "  ```", "",
              "- **`import os` added** where a rule above introduced its first use.",
              "", "## Where each rule landed", ""]
    for f in sorted(patched):
        lines.append(f"- `{f}`")
        for w in patched[f]:
            lines.append(f"  - {w}")
    lines += ["", "## Not patched, and therefore still true of this tree", "",
              "- `tasks/*.json` had `property_tests` / `impl_for_validation` "
              "repointed at `referees/<task_id>/` (marked `path-rewritten`). "
              "The internal path of every referee file is preserved in "
              "`referees/INDEX.json` under `internal_source`.",
              "- `src/vendor/query_engine/` is a **stand-in**, not the real "
              "package. See its docstring.",
              "- `src/sweeps/*.sh` are copied verbatim and will NOT run here: "
              "they `cd` to a working-repo layout, `source .env`, and call "
              "`joblog.sh`. They are shipped as the record of how each sweep "
              "was actually launched, not as an entry point.", ""]
    # The patch table quotes real source lines, which is where the internal
    # names ride into this document; it is redacted like every other artifact.
    patch_md, n_pm = _redact("\n".join(lines))
    if n_pm:
        redactions.append(("src/PORTABILITY_PATCHES.md", n_pm))
    emit("src/PORTABILITY_PATCHES.md", patch_md.encode(),
         "written by tools/assemble.py", "derived")

    # --- files authored directly in this repo ------------------------------
    # The prose and the tools were written here, not copied from anywhere, so
    # they have no `source` to trace. They are still hashed, because
    # MANIFEST.json claims to describe EVERY file and a manifest with holes in
    # it teaches a reader to stop trusting it.
    for p in sorted(DEST.rglob("*")):
        if p.is_dir() or ".git" in p.parts or "__pycache__" in p.parts:
            continue
        rel = str(p.relative_to(DEST))
        if rel in manifest or rel == "MANIFEST.json":
            continue
        manifest[rel] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                         "bytes": p.stat().st_size,
                         "source": "authored in this repository",
                         "rule": "authored"}

    # --- does the tree it just wrote compile, import, and declare its deps? --
    # The docstring above has always claimed "the test below runs every shipped
    # module". It did not exist, and 13 of the 18 modules in src/ raised
    # ModuleNotFoundError in the published tree for a month -- including every
    # analyzer REPRODUCTION.md tells a reader to run. A packaging step that
    # cannot answer "does this import" has not finished.
    #
    # These three gates USED to be written out here. They are in
    # tools/check_clean_clone.py now, and this calls them, because the person
    # most likely to hit the defect is the one person who cannot run this
    # assembler: it needs the working repo and the internal directory names.
    # Two copies drift, and the copy nobody runs drifts first.
    if not args.check:
        import check_clean_clone as ccc
        for name, fn in (("compile", ccc.check_compile),
                         ("import", ccc.check_imports),
                         ("requirements", ccc.check_requirements)):
            found, counts = fn(DEST) if name == "compile" else fn(DEST, "src")
            print(f"  {name}: " + " ".join(f"{k}={v}" for k, v in counts.items()))
            problems.extend(found)

    # A portability rule that matches nothing is either dead or -- the case
    # that actually happened -- a rule the redactor got to first. Either way it
    # is a finding, not a shrug.
    unmatched = [why for _, _, why in PORTABILITY_PATCHES if why not in rules_fired]
    for why in unmatched:
        problems.append(f"portability rule matched no file: {why}")

    total_redactions = sum(n for _, n in redactions)
    summary = {
        "files": len(manifest),
        "run_metas": n_metas,
        "redacted_transcripts": sum(
            1 for k in manifest if k.endswith("/transcript.json")),
        "audit_rows": n_audit_rows,
        "referee_tasks": len(referee_index),
        "path_redactions": total_redactions,
        "portability_patched_files": len(patched),
        "unmatched_patch_rules": len(unmatched),
        "problems": problems,
    }
    man_p = DEST / "MANIFEST.json"
    if args.check:
        # Compare against the RECORDED manifest, not against a freshly
        # recomputed one. Re-deriving both sides would make this check pass by
        # construction -- the exact defect STANDARDS.md R4 is about.
        if not man_p.exists():
            problems.append("no MANIFEST.json to check against")
        else:
            recorded = json.loads(man_p.read_text(encoding="utf-8"))["files"]
            for rel, got in manifest.items():
                want = recorded.get(rel)
                if want is None:
                    problems.append(f"not in MANIFEST.json: {rel}")
                elif want["sha256"] != got["sha256"]:
                    problems.append(f"sha256 drift vs MANIFEST.json: {rel}")
            for rel in recorded:
                if rel not in manifest:
                    problems.append(f"in MANIFEST.json but missing from tree: {rel}")
            summary["manifest_entries_checked"] = len(recorded)
    else:
        man = {"note": "Every file in this repo and where it came from. "
                       "Regenerate with tools/assemble.py; verify with "
                       "tools/assemble.py --check, which compares against THIS "
                       "file rather than recomputing both sides.",
               "summary": summary, "files": manifest}
        man_p.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=1))
    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems[:40]:
            print(f"  {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
