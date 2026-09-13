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
Scan this repo for anything that must not be in a public tree.

A leaked key in a public repository is unrecoverable -- rotating it is damage
control, not a fix -- so this is a gate that refuses (STANDARDS.md R4), not a
report that someone reads. Run it before every publish and on every change.

SIX CLASSES, and what each one is actually looking for:

  KEY        credential shapes: AWS access key ids and secret-looking
             assignments, Neo4j/Aura passwords, GitHub PATs, Semantic Scholar
             keys, Bearer tokens, private-key PEM headers, JWTs, Slack/Stripe
             tokens, and `NAME=<20+ opaque chars>` assignments generally.
  HOST       internal hostnames and endpoints: *.neo4j.io / Aura instance ids,
             App Runner and ECR endpoints, Cloudflare account ids, private
             IPs, and localhost ports that name an internal service.
  PATH       absolute paths from a developer machine -- /Users/<name>/,
             /Volumes/<name>/, and this project's own working-copy root.
  EMAIL      addresses. A public role address is fine and is allowlisted by
             name; a personal one is not.
  INTERNAL   a name from the private repository's own directory layout.
             Not a credential, but not ours to publish either: a stamped
             provenance path whose machine-specific prefix has been redacted
             still names the internal stage directory it came from, and 3,015
             of those survived the first packaging pass. Two rules, and the
             difference is deliberate --
               SHAPE, always on: a numbered stage directory of the form
                 `<tree>/NN_<name>`, in either its slash spelling or the
                 `Path / "<tree>" / "NN_<name>"` spelling. Anyone can run it.
               EXACT, when the BENCH_INTERNAL_* variables are set: the actual
                 names, matched literally. This is the strict mode, it is the
                 one the publisher runs, and when the variables are absent the
                 scan says so rather than reporting a pass it did not earn.

  DOTENV     a .env, credentials file, private key, or keystore of any kind
             appearing anywhere in the tree.
  BIGCODE    a file that looks like a bulk third-party code corpus -- the
             licence hazard, checked here because it travels the same way a
             secret does: by being copied in without anyone rereading it.

Findings print with file, line and a masked excerpt. Exit 0 clean, 1 findings.

    ./venv/bin/python3 harness/tools/scan_secrets.py
    ./venv/bin/python3 harness/tools/scan_secrets.py --root some/other/tree
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent

# Addresses that are public by design. Anything else is a finding.
ALLOWED_EMAILS = {"media@syntology.ai"}

# Hostnames a public repo may legitimately name.
ALLOWED_HOSTS = {
    "api.semanticscholar.org", "api.github.com", "arxiv.org",
    "export.arxiv.org", "ar5iv.labs.arxiv.org", "raw.githubusercontent.com",
    "github.com", "syntology.ai", "www.syntology.ai", "huggingface.co",
    "docs.aws.amazon.com", "bedrock-runtime.us-east-1.amazonaws.com",
    "openreview.net", "api.openreview.net", "doi.org", "api.crossref.org",
}

RULES: list[tuple[str, str, re.Pattern]] = [
    ("KEY", "AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("KEY", "AWS secret access key", re.compile(
        r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}")),
    ("KEY", "GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("KEY", "Semantic Scholar key", re.compile(r"\bs2k-[A-Za-z0-9]{8,}\b")),
    ("KEY", "Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b")),
    ("KEY", "Stripe key", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("KEY", "private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("KEY", "JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("KEY", "Bearer literal", re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}=*")),
    ("KEY", "neo4j auth literal", re.compile(
        r"(?i)(neo4j_password|NEO4J_AUTH)\s*[=:]\s*['\"]?[^\s'\"{}$]{6,}")),
    ("KEY", "assigned opaque secret", re.compile(
        r"(?i)\b(?:password|passwd|secret|api_key|apikey|access_token|auth_token|"
        r"client_secret|private_token)\b\s*[=:]\s*['\"][^'\"\n${}<>]{12,}['\"]")),

    ("HOST", "Neo4j/Aura endpoint", re.compile(
        r"(?i)\b(?:neo4j|bolt)(?:\+s|\+ssc)?://[^\s'\"]+")),
    # Written against the shapes AWS actually emits, not the shape you would
    # guess: App Runner is <id>.<region>.awsapprunner.com and ECR is
    # <account>.dkr.ecr.<region>.amazonaws.com. The first draft of this rule
    # guessed `.apprunner.<region>.amazonaws.com` and the self-test caught it.
    ("HOST", "App Runner endpoint", re.compile(
        r"(?i)\b[a-z0-9-]+\.[a-z0-9-]+\.awsapprunner\.com\b")),
    ("HOST", "AWS service endpoint", re.compile(
        r"(?i)\b[a-z0-9.-]+\.(?:dkr\.ecr|elb|execute-api|rds|s3|lambda)\."
        r"[a-z0-9-]+\.amazonaws\.com\b")),
    ("HOST", "AWS account id in ARN", re.compile(r"\barn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:")),
    ("HOST", "private IPv4", re.compile(
        r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")),
    ("HOST", "localhost port", re.compile(r"\b(?:localhost|127\.0\.0\.1):\d{2,5}\b")),
    ("HOST", "cloudflare account id", re.compile(r"(?i)\bcloudflare[_-]?account[_-]?id\b")),

    ("PATH", "developer home path", re.compile(r"/Users/[A-Za-z0-9_.-]+/")),
    ("PATH", "external volume path", re.compile(r"/Volumes/[A-Za-z0-9_.-]+/")),
    ("PATH", "working-copy root", re.compile(r"(?i)synt" + r"ology-final/|synt" + r"ology-overhaul/")),  # noscan

    ("EMAIL", "email address", re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),

    # Shape of a numbered internal stage directory. Written as a shape rather
    # than as a list of names for the obvious reason: a gate that has to name
    # what it is hiding publishes it. Scoped by THIRD_PARTY_FIELDS below,
    # because a published transcript records the repository paths an agent
    # searched -- `infosec/50_google_neural` is somebody else's directory,   # noscan
    # and a gate that flags it teaches its reader to stop looking.
    ("INTERNAL", "internal stage directory (path form)", re.compile(
        r"\b[a-z][a-z0-9_]{2,}/[0-9]{2}_[a-z][a-z0-9_]{2,}\b")),
    ("INTERNAL", "internal stage directory (Path-joined form)", re.compile(
        r'"[a-z][a-z0-9_]{2,}"\s*/\s*"[0-9]{2}_[a-z][a-z0-9_]{2,}"')),
]


def exact_internal_rules() -> tuple[list, list[str]]:
    """Literal internal names, from the environment. Returns (rules, sources).

    An empty list is NOT a clean result and is never reported as one -- see
    `main`, which prints `EXACT: not configured` and leaves the operator in no
    doubt about which half of the class actually ran."""
    import os
    names, src = [], []
    for var in ("BENCH_INTERNAL_DIR", "BENCH_INTERNAL_REFIMPL_DIR",
                "BENCH_INTERNAL_AUDIT_DIR"):
        v = os.environ.get(var, "").strip().strip("/")
        if v:
            names.append(v)
            src.append(var)
            # the bare leaf, and the tree it sits in
            names += [part for part in v.split("/") if part]
    for pair in os.environ.get("BENCH_INTERNAL_NAMES", "").split(","):
        nm = pair.split("=", 1)[0].strip()
        if nm:
            names.append(nm)
            src.append("BENCH_INTERNAL_NAMES")
    rules = [("INTERNAL", f"internal name (exact, {len(set(names))} configured)",
              re.compile(r"\b" + re.escape(n) + r"\b"))
             for n in sorted(set(names), key=len, reverse=True)]
    return rules, sorted(set(src))

DOTENV_NAMES = re.compile(
    r"(?i)^(\.env(\..*)?|.*\.pem|.*\.p12|.*\.pfx|.*\.keystore|.*\.jks|"
    r"credentials(\.json)?|id_(rsa|ed25519|ecdsa)(\.pub)?|.*\.key)$")

# A line may opt out of scanning with a trailing marker. Exemptions are COUNTED
# and printed, so an exemption can never be a silent hole -- the only lines that
# carry one are this scanner's own pattern definitions and plants, and two
# redaction regexes in tools/assemble.py that have to spell the repo's name.
#
# The marker must END the line. It used to be matched anywhere, which meant a
# sentence that merely MENTIONED it -- in a docstring, or in ASSEMBLY_REPORT.md
# explaining the convention -- exempted its own line from every rule. Three
# lines were silently exempt that way, which is precisely the hole the counting
# was supposed to make impossible.
NOSCAN = re.compile(r"#\s*noscan\s*$")

# JSON fields in a published transcript whose value is a third-party or
# agent-authored name: a repo path, a fetched URL, a query the subject typed.
# The INTERNAL *shape* rule does not apply inside them. The INTERNAL *exact*
# rule still does -- an actual internal name has no business there either.
THIRD_PARTY_FIELDS = {
    "repo", "path", "url", "html_url", "query", "name", "id_or_title",
    "title", "paper_title", "method", "entry", "fetch_with", "retrieve_with",
    "attribution", "fragments", "source_file", "repo_url"}

# A tool result rides as an escaped JSON string on ONE line, so the enclosing
# field cannot be read off the line's indentation -- the first version of this
# scoping tried that and skipped nothing. Walk back to the nearest key token
# instead.
_KEY_TOK = re.compile(r'\\?"([A-Za-z_][A-Za-z0-9_]*)\\?"\s*:')


def _enclosing_field(prefix: str) -> str | None:
    keys = _KEY_TOK.findall(prefix)
    return keys[-1] if keys else None


def _in_placeholder(prefix: str) -> bool:
    """Inside a `<redacted body ... origin=...>` marker, whose `origin` names
    the third-party repository the removed body came from."""
    i = prefix.rfind("<redacted body ")
    return i != -1 and ">" not in prefix[i:]

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache"}
BINARY_SUFFIXES = {".npy", ".pkl", ".pyc", ".png", ".jpg", ".jpeg", ".gz",
                   ".zip", ".parquet", ".so", ".dylib"}

# A file this large that is mostly code is a corpus, not a source file.
BIGCODE_BYTES = 5_000_000


def _mask(s: str) -> str:
    s = s.strip()
    if len(s) <= 24:
        return s
    return f"{s[:12]}...{s[-6:]} ({len(s)} chars)"


def scan(root: Path, extra_rules: list = ()) -> tuple[list[dict], dict]:
    findings: list[dict] = []
    rules = RULES + list(extra_rules)
    stats = {"files": 0, "bytes": 0, "skipped_binary": 0, "noscan_lines": 0,
             "internal_shape_field_skips": 0}
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_dir():
            continue
        rel = str(p.relative_to(root))
        if DOTENV_NAMES.match(p.name):
            findings.append({"cls": "DOTENV", "rule": "credential-bearing filename",
                             "file": rel, "line": 0, "excerpt": p.name})
            continue
        if p.suffix.lower() in BINARY_SUFFIXES:
            stats["skipped_binary"] += 1
            continue
        size = p.stat().st_size
        stats["files"] += 1
        stats["bytes"] += size
        if size > BIGCODE_BYTES and p.suffix in {".jsonl", ".json", ".py", ".txt"}:
            findings.append({"cls": "BIGCODE", "rule": "bulk corpus-sized file",
                             "file": rel, "line": 0,
                             "excerpt": f"{size/1e6:.1f} MB"})
        try:
            text = p.read_text()
        except (UnicodeDecodeError, OSError):
            stats["skipped_binary"] += 1
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if NOSCAN.search(line):
                stats["noscan_lines"] += 1
                continue
            for cls, rule, pat in rules:
                shape_only = cls == "INTERNAL" and "exact" not in rule
                for m in pat.finditer(line):
                    hit = m.group(0)
                    if shape_only and (
                            _enclosing_field(line[:m.start()]) in THIRD_PARTY_FIELDS
                            or _in_placeholder(line[:m.start()])):
                        stats["internal_shape_field_skips"] += 1
                        continue
                    if cls == "EMAIL" and hit.lower() in ALLOWED_EMAILS:
                        continue
                    if cls == "HOST":
                        host = re.sub(r"^[a-z+]+://", "", hit, flags=re.I).split("/")[0]
                        if host.split(":")[0] in ALLOWED_HOSTS:
                            continue
                    findings.append({"cls": cls, "rule": rule, "file": rel,
                                     "line": i, "excerpt": _mask(hit)})
    return findings, stats


# Planted strings, one per class, used by --self-test. A scanner that has
# never been seen to FAIL is not a verified scanner: a clean report from a
# broken regex is indistinguishable from a clean tree.
SELF_TEST_PLANTS = {
    "KEY-aws": "AKIA" + "IOSFODNN7EXAMPLE",
    "KEY-github": "ghp_" + "0123456789abcdefghijklmnopqrstuvwxyz",
    "KEY-pem": "-----BEGIN RSA PRIVATE KEY-----",                     # noscan
    "KEY-assigned": 'password = "hunter2hunter2hunter2"',             # noscan
    "HOST-neo4j": "neo4j+s://" + "abcd1234.databases.neo4j.io",       # noscan
    "HOST-apprunner": "abc123.eu-west-1.awsapprunner.com/health",     # noscan
    "HOST-privateip": "10.0.3.17",                                    # noscan
    "PATH-home": "/Users/someone/Documents/thing",                    # noscan
    "EMAIL-personal": "someone@example.com",                          # noscan
    # The leak this class exists for: a provenance stamp whose machine prefix
    # HAS been redacted and whose internal directory name has not. It is
    # planted in exactly that shape, because that is the shape that shipped.
    "INTERNAL-stage": '"argv": ["<REPO>/pipeline/20_some_experiment/run.py"]',  # noscan
    "INTERNAL-pathjoin": 'ROOT = REPO / "pipeline" / "20_some_experiment"',     # noscan
}

# Planted only for the EXACT half of the INTERNAL class, and only when the
# BENCH_INTERNAL_* variables are set: without them there is no list of names
# to match, and the self-test says the half did not run instead of passing it.
EXACT_PLANT_FIELD = "attribution"      # an allow-listed third-party field...


def self_test() -> int:
    """Plant one instance of each class in a throwaway tree and require a hit."""
    import tempfile
    missed = []
    exact_rules, exact_srcs = exact_internal_rules()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name, plant in SELF_TEST_PLANTS.items():
            (root / f"{name}.txt").write_text(f"harmless line\n{plant}\nharmless\n")
        (root / ".env").write_text("NOTHING=1\n")
        # A line that MENTIONS the marker mid-sentence must not be exempt.
        (root / "mentions_marker.txt").write_text(
            "a line may opt out with a trailing # noscan marker, like so: "
            + "AKIA" + "IOSFODNN7EXAMPLE\n")
        (root / "clean.txt").write_text("nothing to see, media@syntology.ai is allowlisted\n")
        # A third-party repo path of the same SHAPE as an internal stage
        # directory, sitting where transcripts actually put one. The shape
        # rule must NOT fire on it -- a gate that cries wolf on every
        # published transcript is a gate nobody reads.
        (root / "thirdparty.txt").write_text(
            '  "text": "{\\"repo\\": \\"ep-infosec/50_google_neural-tangents\\", '  # noscan
            '\\"content\\": \\"<redacted body sha256=' + "0" * 64 +
            ' bytes=18000 field=content origin=ep-infosec/50_google_neural-tangents>'  # noscan
            '\\"}"\n')
        import os
        configured = any(os.environ.get(v) for v in (
            "BENCH_INTERNAL_DIR", "BENCH_INTERNAL_REFIMPL_DIR",
            "BENCH_INTERNAL_AUDIT_DIR", "BENCH_INTERNAL_NAMES"))
        if exact_rules:
            # The exact half is tested inside an allow-listed third-party
            # field, which is where the shape half deliberately looks away --
            # so a pass here proves the two halves are independent. Both the
            # FULL path and its BARE LEAF are planted: prose says "the
            # 20_whatever directory" as readily as it says the whole path, and
            # a rule that only knew the joined form would miss it.
            nm = os.environ.get("BENCH_INTERNAL_DIR", "").strip("/")
            (root / "exactname.txt").write_text(
                f'  "{EXACT_PLANT_FIELD}": "produced under {nm}/x.py"\n')
            (root / "exactleaf.txt").write_text(
                f'  "{EXACT_PLANT_FIELD}": "see {nm.split("/")[-1]} for the sweep"\n')
            extra_nm = os.environ.get("BENCH_INTERNAL_NAMES", "").split(",")[0]
            extra_nm = extra_nm.split("=", 1)[0].strip()
            if extra_nm:
                (root / "exactextra.txt").write_text(
                    f'  "{EXACT_PLANT_FIELD}": "resolved from {extra_nm}/x"\n')
        findings, _ = scan(root, exact_rules)
        hit_files = {f["file"] for f in findings}
        for name in SELF_TEST_PLANTS:
            if f"{name}.txt" not in hit_files:
                missed.append(name)
        if ".env" not in hit_files:
            missed.append("DOTENV-.env")
        if "clean.txt" in hit_files:
            missed.append("FALSE-POSITIVE-on-allowlisted-address")
        if "thirdparty.txt" in hit_files:
            missed.append("FALSE-POSITIVE-on-third-party-repo-path")
        if "mentions_marker.txt" not in hit_files:
            missed.append("NOSCAN-mentioned-mid-line-exempted-the-line")
        if exact_rules and "exactname.txt" not in hit_files:
            missed.append("INTERNAL-exact")
        if exact_rules and "exactleaf.txt" not in hit_files:
            missed.append("INTERNAL-exact-bare-leaf")
        if (root / "exactextra.txt").exists() and "exactextra.txt" not in hit_files:
            missed.append("INTERNAL-exact-extra-name")
        # Configured but no rules built is a silently disabled gate, which is
        # worse than an unconfigured one: it reports a pass it never ran.
        if configured and not exact_rules:
            missed.append("INTERNAL-exact-configured-but-no-rules-built")
    for name in SELF_TEST_PLANTS:
        print(f"  {'MISSED' if name in missed else 'caught':7s} {name}")
    print(f"  {'MISSED' if 'DOTENV-.env' in missed else 'caught':7s} DOTENV-.env")
    print(f"  {'MISSED' if 'FALSE-POSITIVE-on-third-party-repo-path' in missed else 'caught':7s}"
          f" INTERNAL-shape-does-not-fire-on-third-party-repo-path")
    print(f"  {'MISSED' if 'NOSCAN-mentioned-mid-line-exempted-the-line' in missed else 'caught':7s}"
          f" NOSCAN-must-END-the-line, not merely appear in it")
    if exact_rules:
        print(f"  {'MISSED' if 'INTERNAL-exact' in missed else 'caught':7s} "
              f"INTERNAL-exact (from {', '.join(exact_srcs)})")
        print(f"  {'MISSED' if 'INTERNAL-exact-bare-leaf' in missed else 'caught':7s} "
              f"INTERNAL-exact-bare-leaf")
        if "BENCH_INTERNAL_NAMES" in exact_srcs:
            print(f"  {'MISSED' if 'INTERNAL-exact-extra-name' in missed else 'caught':7s} "
                  f"INTERNAL-exact-extra-name (BENCH_INTERNAL_NAMES)")
    elif 'INTERNAL-exact-configured-but-no-rules-built' in missed:
        print("  MISSED  INTERNAL-exact -- BENCH_INTERNAL_* IS set but no "
              "exact rule was built")
    else:
        print("  SKIPPED INTERNAL-exact -- BENCH_INTERNAL_* not set, so the "
              "exact half did not run and is not reported as passing")
    print("\nself-test: " + ("PASS" if not missed else f"FAIL -- {missed}"))
    return 1 if missed else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the detector can fire: plant one string per "
                         "class and require a hit on each")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.root).resolve()
    exact_rules, exact_srcs = exact_internal_rules()
    findings, stats = scan(root, exact_rules)
    stats["internal_exact_names"] = len(exact_rules)
    stats["internal_exact_from"] = exact_srcs

    if args.json:
        print(json.dumps({"root": str(root), "stats": stats,
                          "findings": findings}, indent=1))
    else:
        print(f"scanned {stats['files']} text files "
              f"({stats['bytes']/1e6:.1f} MB), skipped {stats['skipped_binary']} binary, "
              f"{stats['noscan_lines']} line(s) exempted with `# noscan`")
        print("  INTERNAL exact rules: "
              + (f"{len(exact_rules)} name(s) from {', '.join(exact_srcs)}"
                 if exact_rules else
                 "NOT CONFIGURED -- shape rule only. Set BENCH_INTERNAL_DIR / "
                 "BENCH_INTERNAL_REFIMPL_DIR / BENCH_INTERNAL_AUDIT_DIR / "
                 "BENCH_INTERNAL_NAMES before publishing.")
              + f"; {stats['internal_shape_field_skips']} shape match(es) inside "
                "third-party fields were not counted")
        by_cls: dict[str, int] = {}
        for f in findings:
            by_cls[f["cls"]] = by_cls.get(f["cls"], 0) + 1
        for cls, _, _ in RULES:
            by_cls.setdefault(cls, 0)
        by_cls.setdefault("DOTENV", 0)
        by_cls.setdefault("BIGCODE", 0)
        for cls in sorted(by_cls):
            print(f"  {cls:8s} {by_cls[cls]}")
        for f in findings[:200]:
            print(f"    [{f['cls']}] {f['file']}:{f['line']} -- {f['rule']}: {f['excerpt']}")
        if len(findings) > 200:
            print(f"    ... {len(findings)-200} more")
    print("\nsecret scan: " + ("CLEAN" if not findings else f"{len(findings)} FINDINGS"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
