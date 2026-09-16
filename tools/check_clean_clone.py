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
Does a CLEAN CLONE of this repository compile, import, install and match its
own manifest? Four checks, no credentials, no network, a few seconds.

WHY THIS EXISTS. On 2026-09-13 a clean clone of this tree was found to be
broken in two ways at once: **13 of the 18 modules in `src/` raised
`ModuleNotFoundError`** -- the referee among them, and all four analyzers
REPRODUCTION.md tells a reader to run -- and `requirements.txt` omitted
`requests`, which is a module-level import in the harness's import chain, so
**no arm would start**, not even the credential-free floor. Both defects were
invisible for a month because every check had been run inside the working
repository, where the missing modules resolve and every package is already
installed. ASSEMBLY_REPORT.md 4.9 is the incident.

The two gates that caught it lived inside `tools/assemble.py`, which needs the
working repo AND its internal directory names -- so the person most likely to
hit the defect was the one person who could not run the check. They live here
now, and `assemble.py` calls THIS module rather than keeping a second copy
(one way to do it; two copies drift, and the copy nobody runs drifts first).

  COMPILE       every .py in the tree compiles under THIS interpreter. Catches
                syntax that is only valid on the version the repo was built on
                (3.14.6); it executes nothing.
  IMPORTS       every `src/**/*.py` imports with ONLY its own directory on
                sys.path -- which is exactly what `python3 src/analyze.py`
                gives it, and exactly what the working repo hid. The probe
                runs from an empty cwd, because `python -c` puts the caller's
                directory on sys.path and a reader standing in a directory
                that happens to hold a same-named module would otherwise get
                a pass this tree did not earn.
  REQUIREMENTS  every unguarded module-level third-party import under `src/`
                is declared in requirements.txt. An import inside a try/except
                or under `if __name__ == "__main__"` is an option, not a
                requirement, and is not demanded.
  MANIFEST      every file in the tree matches MANIFEST.json's sha256 and
                byte count, every recorded file is present, and nothing is
                present that MANIFEST.json does not record. `assemble.py
                --check` does this too but cannot run without the working
                repo; this half needs nothing but the clone. A mismatch that
                disappears when CRLF is read back as LF is named as a line-
                ending conversion rather than reported as 1,272 corrupt
                files -- `.gitattributes` prevents it, and this says so when
                a clone made without it arrives anyway.

Exit 0 clean - 1 findings, per the project exit-code contract.

`--self-test` plants one instance of each finding class in throwaway trees and
requires a hit on every one, plus a clean tree that must produce none. A gate
never observed failing is not a verified gate (the house rule that
tools/scan_secrets.py's self-test comes from -- it caught a rule that could
never have fired).

    python3 tools/check_clean_clone.py
    python3 tools/check_clean_clone.py --self-test
    python3 tools/check_clean_clone.py --root <other tree>
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import py_compile
import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# Mirrors .gitignore. A path skipped here is a path this gate does not speak
# for, so the counts below print how many were skipped rather than leaving the
# exclusion silent (STANDARDS.md R3).
SKIP_DIR_NAMES = {".git", "__pycache__", ".venv", "venv", "node_modules",
                  ".mypy_cache", ".pytest_cache"}
# Root-anchored, exactly as .gitignore writes them: `/runs/` is a fresh sweep's
# output, `/code_index/` is a flat index you built. `data/runs/` -- the
# published run metadata -- is NOT either of those and is checked.
SKIP_ROOT_PREFIXES = ("runs/", "code_index/")
SKIP_FILE_NAMES = {".DS_Store"}
SKIP_SUFFIXES = (".pyc",)


def _stdlib_names() -> set:
    """Every stdlib module name, on any interpreter this might be run by.

    `sys.stdlib_module_names` is 3.10+, and this gate is the thing that
    MEASURES the floor -- the `python-3-9-boundary` CI job runs it on 3.9
    precisely to find out what does and does not work there. A tool that
    crashes below the floor cannot report where the floor is.
    """
    names = getattr(sys, "stdlib_module_names", None)
    if names is not None:
        return set(names)
    import os
    import sysconfig
    out = set(sys.builtin_module_names)
    lib = sysconfig.get_path("stdlib")
    for entry in os.listdir(lib):
        if entry.endswith(".py"):
            out.add(entry[:-3])
        elif "." not in entry:
            out.add(entry)
    dynload = os.path.join(lib, "lib-dynload")
    if os.path.isdir(dynload):
        for entry in os.listdir(dynload):
            out.add(entry.split(".")[0])
    return out


def _walk(root: Path):
    """Every file this gate speaks for, plus the count it deliberately skips.

    `.git` is not counted as a skip: it is the clone's own plumbing, it is
    thousands of files, and reporting it would bury the skips that a reader
    should actually look at (a stray venv, a build output, a `.DS_Store`).
    """
    kept, skipped = [], 0
    for p in sorted(root.rglob("*")):
        if p.is_dir() or ".git" in p.relative_to(root).parts:
            continue
        rel = p.relative_to(root).as_posix()
        if (set(p.relative_to(root).parts) & SKIP_DIR_NAMES
                or rel.startswith(SKIP_ROOT_PREFIXES)
                or p.name in SKIP_FILE_NAMES
                or p.name.endswith(SKIP_SUFFIXES)):
            skipped += 1
            continue
        kept.append(p)
    return kept, skipped


# --- COMPILE ---------------------------------------------------------------

def check_compile(root: Path) -> tuple[list[str], dict]:
    findings: list[str] = []
    files = [p for p in _walk(root)[0] if p.suffix == ".py"]
    with tempfile.TemporaryDirectory() as td:
        for i, p in enumerate(files):
            # cfile into a temp dir: a gate that leaves __pycache__ behind in
            # the tree it is checking has changed the thing it measured.
            try:
                py_compile.compile(str(p), cfile=f"{td}/{i}.pyc", doraise=True)
            except py_compile.PyCompileError as e:
                msg = str(e).strip().splitlines()[-1]
                findings.append(f"does not compile on "
                                f"{sys.version_info.major}.{sys.version_info.minor}: "
                                f"{p.relative_to(root)} -- {msg[:120]}")
    return findings, {"examined": len(files), "findings": len(findings)}


# --- IMPORTS ---------------------------------------------------------------

# Stdlib modules that exist on POSIX and simply do not on Windows. Named
# explicitly rather than matched loosely: the point is to excuse a PLATFORM
# fact, never a missing dependency, and a short closed list is the difference.
_POSIX_ONLY = ("resource", "fcntl", "pwd", "grp", "termios", "posix", "syslog")


def _posix_only_stdlib(err: str) -> str | None:
    """The POSIX-only module named by a ModuleNotFoundError, or None."""
    if "ModuleNotFoundError" not in err:
        return None
    for name in _POSIX_ONLY:
        if f"No module named '{name}'" in err:
            return name
    return None


def _declared_requirements(root: Path) -> set[str]:
    """Distribution names declared in requirements.txt, lowercased.

    Parsed exactly the way check_requirements parses them, so the two checks
    cannot disagree about what "declared" means."""
    reqs = root / "requirements.txt"
    if not reqs.exists():
        return set()
    out = set()
    for line in reqs.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("-"):
            out.add(re.split(r"[<>=!\[]", line)[0].strip().lower())
    return out


# The import probe REPORTS ITS OWN FAILURE, structurally.
#
# Three rounds of external review found the same defect at three depths, each
# time because this gate asked "what does the last line of stderr say?" when the
# question was "why did the process fail?":
#
#   r2  `"ModuleNotFoundError" in err`      excused a SyntaxError
#   r3  substring anywhere                  excused `RuntimeError: ModuleNotFound...`
#   r4  anchored at line start              excused an atexit handler that PRINTS
#                                           `ModuleNotFoundError: No module named 'numpy'`
#                                           while the real failure was a RuntimeError
#
# Each fix made the text match stricter, and text can always be forged, because
# the module under test controls its own stderr. So this stops reading prose.
# The probe catches the exception itself and emits its TYPE, its MRO and its
# `.name` as JSON behind a sentinel, then calls os._exit -- which skips atexit
# handlers and any replaced excepthook, so nothing the module registered can
# append a line after ours. A module could print the sentinel during import, so
# the LAST sentinel line wins and ours is provably last.
#
# ONLY the script's own directory goes on the path, which is exactly what
# `python3 src/analyze.py` does. Adding vendor/ here made the gate pass a tree
# whose modules could not import -- the gate supplying the fix it was testing.
_PROBE_SENTINEL = "__CCC_IMPORT_PROBE__"
_PROBE_SRC = (
    "import sys, os, json, pathlib, importlib\n"
    "p = pathlib.Path(sys.argv[1])\n"
    "sys.path.insert(0, str(p.parent))\n"
    "try:\n"
    "    importlib.import_module(p.stem)\n"
    "except BaseException as e:\n"
    "    info = {'type': type(e).__name__,\n"
    "            'mro': [c.__name__ for c in type(e).__mro__],\n"
    "            'name': getattr(e, 'name', None),\n"
    "            'msg': str(e)[:300]}\n"
    "    sys.stderr.write('\\n" + _PROBE_SENTINEL + "' + json.dumps(info) + '\\n')\n"
    "    sys.stderr.flush()\n"
    "    os._exit(1)\n"
)


def _probe_verdict(stderr: str) -> dict | None:
    """The probe's own report of the exception, or None if it never spoke."""
    hit = None
    for line in stderr.splitlines():
        line = line.strip()
        if line.startswith(_PROBE_SENTINEL):
            hit = line[len(_PROBE_SENTINEL):]
    if hit is None:
        return None
    try:
        v = json.loads(hit)
        return v if isinstance(v, dict) else None
    except ValueError:
        return None

def _probe_summary(verdict: dict | None, raw_last: str) -> str:
    """One readable line for a report. The JSON envelope is the WIRE FORMAT and
    has no business in a finding a human reads."""
    if not verdict:
        return raw_last[:120]
    t = verdict.get("type") or "?"
    m = (verdict.get("msg") or "").strip()
    return f"{t}: {m}"[:120] if m else t


def _declared_missing_module(verdict: dict | None,
                             declared: set[str]) -> str | None:
    """The declared distribution a genuine ModuleNotFoundError names, else None.

    Takes the PROBE'S OWN REPORT, not a line of stderr. A missing declared
    dependency is an unprovisioned environment; everything else -- an undeclared
    module, a SyntaxError, a bad relative import, a RuntimeError, or a module
    that merely PRINTS something that looks like a ModuleNotFoundError -- is a
    finding, because none of those are fixed by installing anything.

    `mro` rather than `type`, so a subclass of ModuleNotFoundError is still
    recognised as one; `name` rather than a parse of the message, because
    ModuleNotFoundError carries the module name as an attribute and reading it
    from prose is what produced three rounds of findings."""
    if not verdict:
        return None
    if "ModuleNotFoundError" not in (verdict.get("mro") or []):
        return None
    name = verdict.get("name")
    if not isinstance(name, str) or not name:
        return None
    top = name.split(".")[0]
    return top if top.lower() in declared else None

def check_imports(root: Path, subdir: str = "src") -> tuple[list[str], dict]:
    """Import every shipped module the way a reader runs it: on its own path."""
    findings: list[str] = []
    unsupported: list[str] = []
    uninstalled: list[str] = []
    declared = _declared_requirements(root)
    mods = sorted((root / subdir).rglob("*.py"))
    # The probe runs with its cwd in an EMPTY directory. `python -c` prepends
    # the current working directory to sys.path, so without this the gate
    # answers a question about the caller's cwd rather than about the clone:
    # measured 2026-09-13, running this file's own --self-test from a
    # directory that happens to contain `provenance.py` flips the
    # IMPORTS-broken_import plant from `caught` to `MISSED`, because the
    # planted module resolves against the cwd. That is the SAME defect class
    # the gate exists to catch -- a module resolving to something that is not
    # in the clone -- so leaving it here would make this the one check that
    # can be silenced by where a reader happens to be standing.
    with tempfile.TemporaryDirectory() as neutral:
        for mod in mods:
            # Imported by NAME, on a path, not through a synthetic spec:
            # arxiv_client.py reassigns `sys.modules[__name__].__class__`, and
            # a module loaded under a made-up name fails there for reasons
            # that have nothing to do with this tree.
            r = subprocess.run(
                [sys.executable, "-c", _PROBE_SRC, str(mod)],
                capture_output=True, text=True, cwd=neutral)
            if r.returncode != 0:
                last = (r.stderr.strip().splitlines() or ["?"])[-1]
                verdict = _probe_verdict(r.stderr)
                posix_only = _posix_only_stdlib(last)
                if posix_only and os.name == "nt":
                    # A PLATFORM FACT, COUNTED, NOT A FINDING (2026-09-14).
                    # `resource` is POSIX-only stdlib and run_sandboxed.py uses
                    # it for RLIMIT_CPU and RLIMIT_AS -- the CPU and memory caps
                    # this benchmark puts around untrusted code. Five shipped
                    # modules therefore cannot import on Windows, and that is
                    # true, permanent and architectural: Windows has no rlimits,
                    # only Job Objects, which is a port and not a patch.
                    #
                    # Reporting it as a finding made the whole Windows leg red
                    # and hid the question the leg was added to answer -- can a
                    # Windows reader VERIFY THE CLAIMS, which needs no sandbox
                    # at all. So it is separated rather than suppressed: named
                    # every run, counted in its own bucket, and never silently
                    # dropped. Only on Windows, and only for stdlib modules that
                    # genuinely do not exist there -- a missing THIRD-PARTY
                    # module is still a finding, because that is a packaging
                    # defect rather than a platform one.
                    unsupported.append(f"{mod.relative_to(root)} -- needs "
                                       f"{posix_only!r}, POSIX-only stdlib")
                    continue
                if _declared_missing_module(verdict, declared):
                    # Declared in requirements.txt and simply absent from
                    # this interpreter. Named every run and counted in its
                    # own bucket, never silently dropped.
                    uninstalled.append(
                        f"{mod.relative_to(root)} -- "
                        f"{_probe_summary(verdict, last)}")
                    continue
                findings.append(f"shipped module does not import: "
                                f"{mod.relative_to(root)} -- "
                                f"{_probe_summary(verdict, last)}")
    for u in unsupported:
        print(f"          [platform] not importable on this OS: {u}")
    if uninstalled:
        print(f"          [env] ENVIRONMENT INCOMPLETE: {len(uninstalled)} shipped "
              f"module(s) need a dependency requirements.txt declares and this "
              f"interpreter lacks. Not a defect in the clone -- run "
              f"`pip install -r requirements.txt` and re-run to exercise them.")
        for u in uninstalled:
            print(f"          [env]   {u}")
    return findings, {"examined": len(mods), "findings": len(findings),
                      "platform_unsupported": len(unsupported),
                      "deps_not_installed": len(uninstalled)}


# --- REQUIREMENTS ----------------------------------------------------------

def check_requirements(root: Path, subdir: str = "src") -> tuple[list[str], dict]:
    """Is every unguarded third-party import actually declared?

    `requests` was a module-level import in the outbound gateway, which the
    harness imports unconditionally, and it was not in requirements.txt. A
    clean clone could install the stated requirements and still not start the
    `none` arm. The import check above does not catch it, because it runs in an
    interpreter that already has everything.
    """
    findings: list[str] = []
    declared = set()
    reqs = root / "requirements.txt"
    if reqs.exists():
        for line in reqs.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                declared.add(re.split(r"[<>=!\[]", line)[0].strip().lower())
    else:
        findings.append("no requirements.txt")
    mods = sorted((root / subdir).rglob("*.py"))
    shipped = {p.stem for p in mods} | {"query_engine"}
    stdlib = _stdlib_names()
    n_imports = 0
    unparsed = 0
    for mod in mods:
        try:
            tree = ast.parse(mod.read_text(encoding="utf-8"))
        except SyntaxError:
            # A file that will not parse has no import list to check, and it
            # is COMPILE's finding, not this one's -- reported here as a count
            # rather than swallowed, because COMPILE and this check are always
            # run together and exit 1 on it (STANDARDS.md R3).
            unparsed += 1
            continue
        # Guarded = inside a try/except (an optional dependency), or inside
        # `if __name__ == "__main__":` (a script-only import that never runs
        # when the module is imported). Neither is a requirement; treating one
        # as a requirement would push packages into requirements.txt that
        # nothing importing this tree needs.
        guarded = set()
        for node in ast.walk(tree):
            main_guard = (isinstance(node, ast.If)
                          and "__name__" in ast.dump(node.test))
            if isinstance(node, ast.Try) or main_guard:
                guarded |= {id(n) for n in ast.walk(node)}
        for node in ast.walk(tree):
            if id(node) in guarded:
                continue
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            n_imports += len(names)
            for n in names:
                if (n in stdlib or n in shipped or n.lower() in declared):
                    continue
                msg = (f"undeclared third-party import: {n} in "
                       f"{mod.relative_to(root)} is not in requirements.txt")
                if msg not in findings:
                    findings.append(msg)
    return findings, {"examined": len(mods), "imports": n_imports,
                      "declared": len(declared), "unparsed": unparsed,
                      "findings": len(findings)}


# --- MANIFEST --------------------------------------------------------------

def check_manifest(root: Path) -> tuple[list[str], dict]:
    """Is this clone byte-for-byte the tree MANIFEST.json describes?"""
    findings: list[str] = []
    man_p = root / "MANIFEST.json"
    if not man_p.exists():
        return ["no MANIFEST.json"], {"examined": 0, "findings": 1}
    recorded = json.loads(man_p.read_text(encoding="utf-8"))["files"]
    files, skipped = _walk(root)
    seen = set()
    eol = []                                # drift that is not content drift
    for p in files:
        rel = p.relative_to(root).as_posix()
        if rel == "MANIFEST.json":          # cannot record its own hash
            continue
        seen.add(rel)
        want = recorded.get(rel)
        if want is None:
            findings.append(f"in the tree but not in MANIFEST.json: {rel}")
            continue
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != want["sha256"]:
            # One kind of "drift" is not drift at all: git converted line
            # endings on checkout. Measured 2026-09-13 -- `git -c
            # core.autocrlf=true clone` (the Git-for-Windows installer
            # DEFAULT) rewrites every file in this tree to CRLF and this
            # check then reports all 1,272 of them as corruption, while the
            # repository itself works fine. Naming it is the difference
            # between a reader fixing their git config in ten seconds and a
            # reader concluding the download is broken. It is still a
            # finding -- the tree does not match the manifest -- it is just a
            # finding that says what to do.
            if (b"\r\n" in data
                    and hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
                    == want["sha256"]):
                eol.append(rel)
            else:
                findings.append(f"sha256 drift vs MANIFEST.json: {rel}")
        elif len(data) != want.get("bytes"):
            findings.append(f"byte count drift vs MANIFEST.json: {rel}")
    if eol:
        findings.append(
            f"line endings converted on checkout, not content drift: "
            f"{len(eol)} file(s) match MANIFEST.json exactly once CRLF is read "
            f"back as LF (e.g. {', '.join(sorted(eol)[:3])}). Your git rewrote "
            f"them -- core.autocrlf=true is the Git-for-Windows default. Fix: "
            f"`git config --global core.autocrlf false` and re-clone, or clone "
            f"with `git -c core.autocrlf=false clone`. The .gitattributes in "
            f"this repository pins eol=lf and prevents it; a clone that hits "
            f"this was made without it.")
    for rel in recorded:
        if rel not in seen and rel != "MANIFEST.json":
            findings.append(f"in MANIFEST.json but missing from the tree: {rel}")
    return findings, {"examined": len(seen), "recorded": len(recorded),
                      "skipped": skipped, "eol_converted": len(eol),
                      "findings": len(findings)}


CHECKS = [("COMPILE", check_compile), ("IMPORTS", check_imports),
          ("REQUIREMENTS", check_requirements), ("MANIFEST", check_manifest)]


def run(root: Path, quiet: bool = False) -> tuple[int, dict[str, list[str]]]:
    out: dict[str, list[str]] = {}
    for name, fn in CHECKS:
        findings, counts = fn(root)
        out[name] = findings
        if not quiet:
            detail = " ".join(f"{k}={v}" for k, v in counts.items())
            print(f"  {'FAIL' if findings else 'PASS'}  {name:<12} {detail}")
            for f in findings[:20]:
                print(f"          {f}")
            if len(findings) > 20:
                print(f"          ... {len(findings) - 20} more")
    return sum(len(v) for v in out.values()), out


# --- self-test -------------------------------------------------------------

def _plant(td: Path, *, broken_import=False, undeclared=False,
           syntax_error=False, extra_file=False, drift=False, missing=False,
           crlf=False):
    """A minimal tree of the same SHAPE as this repo, with one defect."""
    (td / "src").mkdir(parents=True)
    (td / "requirements.txt").write_text("numpy>=1.24\n", encoding="utf-8")
    (td / "src" / "ok.py").write_text("import json\nX = 1\n", encoding="utf-8")
    if broken_import:
        # The exact 2026-09-13 defect: a module resolving a shared module at
        # the working repo's root, which is not where this layout keeps it.
        (td / "src" / "broken.py").write_text(
            "import sys, pathlib\n"
            "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))\n"
            "import provenance  # lives at the WORKING repo's root, not here\n",
            encoding="utf-8")
    if undeclared:
        (td / "src" / "undeclared.py").write_text("import requests\n", encoding="utf-8")
    if syntax_error:
        (td / "src" / "broken_syntax.py").write_text("def f(:\n    pass\n", encoding="utf-8")
    files = {}
    for p in sorted(td.rglob("*")):
        if p.is_file():
            rel = p.relative_to(td).as_posix()
            files[rel] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                          "bytes": p.stat().st_size,
                          "source": "self-test", "rule": "authored"}
    if drift:
        (td / "src" / "ok.py").write_text("import json\nX = 2\n", encoding="utf-8")   # after hashing
    if crlf:
        # What `git -c core.autocrlf=true clone` does to every file in the
        # tree. Same content, different bytes, so the hash misses -- and the
        # gate has to say WHICH of those two things happened.
        for rel in ("src/ok.py", "requirements.txt"):
            f = td / rel
            f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
    if missing:
        files["src/never_written.py"] = {"sha256": "0" * 64, "bytes": 0,
                                         "source": "self-test", "rule": "authored"}
    if extra_file:
        (td / "src" / "unrecorded.py").write_text("Y = 1\n", encoding="utf-8")
    (td / "MANIFEST.json").write_text(
        json.dumps({"summary": {}, "files": files}, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")


def self_test() -> int:
    # (class, plant, substring the finding must contain -- or None for any).
    # The `crlf` plant carries one because catching it is not enough: the
    # whole point of that branch is the WORDING, and a CRLF checkout reported
    # as "sha256 drift" would pass a class-only assertion while leaving the
    # reader exactly as stuck as before.
    plants = [
        ("IMPORTS", {"broken_import": True}, None),
        ("REQUIREMENTS", {"undeclared": True}, None),
        ("COMPILE", {"syntax_error": True}, None),
        ("MANIFEST", {"drift": True}, "sha256 drift"),
        ("MANIFEST", {"extra_file": True}, None),
        ("MANIFEST", {"missing": True}, None),
        ("MANIFEST", {"crlf": True}, "line endings converted on checkout"),
    ]
    missed = []
    for want, kw, must in plants:
        with tempfile.TemporaryDirectory() as d:
            td = Path(d)
            _plant(td, **kw)
            _, out = run(td, quiet=True)
            label = f"{want}-{'+'.join(kw)}"
            if out[want] and (must is None
                              or any(must in f for f in out[want])):
                print(f"  caught  {label}")
            elif out[want]:
                print(f"  MISSED  {label} -- fired, but no finding said "
                      f"{must!r}: {out[want][:2]}")
                missed.append(label)
            else:
                print(f"  MISSED  {label}")
                missed.append(label)
            # A plant must fire its OWN class. A COMPILE plant that only shows
            # up as an IMPORTS failure has not proved the compile gate works.
    # The IMPORTS plant again, but run from a decoy working directory that
    # SUPPLIES the missing module. `python -c` puts cwd on sys.path, so until
    # 2026-09-13 this flipped the plant from `caught` to `MISSED` and the gate
    # quietly reported a clean tree because of a file that was never in it.
    import os
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as decoy:
        td = Path(d)
        _plant(td, broken_import=True)
        (Path(decoy) / "provenance.py").write_text("X = 1\n", encoding="utf-8")
        here = os.getcwd()
        try:
            os.chdir(decoy)
            _, out = run(td, quiet=True)
        finally:
            os.chdir(here)
        if out["IMPORTS"]:
            print("  caught  IMPORTS-broken_import from a decoy cwd "
                  "(the probe ignores the caller's directory)")
        else:
            print("  MISSED  IMPORTS-cwd-leak: a module in the CALLER's cwd "
                  "satisfied an import that is not in the tree")
            missed.append("IMPORTS-cwd-leak")

    with tempfile.TemporaryDirectory() as d:                 # negative control
        td = Path(d)
        _plant(td)
        n, out = run(td, quiet=True)
        if n:
            print(f"  MISSED  FALSE-POSITIVE-on-clean-tree: {out}")
            missed.append("FALSE-POSITIVE-on-clean-tree")
        else:
            print("  caught  clean tree stays clean (no false positive)")
    print(f"\nself-test: {'FAIL -- ' + ', '.join(missed) if missed else 'PASS'}")
    return 1 if missed else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--self-test", action="store_true",
                    help="plant one of each finding class and require a hit")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.root).resolve()
    print(f"clean-clone check: {root}  (python "
          f"{sys.version.split()[0]}, {sys.platform})")
    n, _ = run(root)
    print(f"\nclean-clone check: {'CLEAN' if not n else f'{n} FINDINGS'}")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
