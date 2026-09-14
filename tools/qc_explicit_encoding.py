#!/usr/bin/env python3
"""
Every text read and write in shipped code says which encoding it means.

WHY (2026-09-14, measured on a windows-latest CI leg, not argued).
`Path.read_text()` with no `encoding=` follows the locale: UTF-8 here, **cp1252
on Windows**. The leg reported `locale.getpreferredencoding='cp1252'
utf8_mode=0`, and `README.md` read that way differs from its UTF-8 content by
**20,463 characters**. `verify_claims` passed anyway, because every phrase it
asserts happens to be ASCII -- a gate going green on mangled text, which is
worse than a gate going red.

WHY A GATE AND NOT A GREP. The first version of this check was a line scan, and
it reported 8 sites that were already fixed: a multi-line call puts `encoding=`
on a later line, which a line-based reader cannot see. It also read every binary
`p.open("rb")` as a text call, because it looked for the mode in `args[1]` (the
builtin's position) when a Path method keeps it in `args[0]`. Both are defects
of the instrument rather than the code, and both are invisible to anything that
does not parse.

So this parses. A call is a finding when its function is `read_text`,
`write_text` or `open`, it has no `encoding=` keyword, and -- for `open` -- its
mode does not contain `b`, wherever that mode lives.

Exit 0 clean / 1 findings, per the project exit-code contract.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ROOTS = ("src", "tools")


def _mode(node: ast.Call) -> str:
    """The mode string, wherever this call keeps it."""
    idx = 0 if isinstance(node.func, ast.Attribute) else 1
    if len(node.args) > idx and isinstance(node.args[idx], ast.Constant):
        v = node.args[idx].value
        return v if isinstance(v, str) else ""
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return kw.value.value or ""
    return ""


def findings_for(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError) as e:
        return [f"{path.relative_to(REPO)}: unreadable -- {type(e).__name__}"]
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = (fn.attr if isinstance(fn, ast.Attribute)
                else fn.id if isinstance(fn, ast.Name) else None)
        if name not in ("read_text", "write_text", "open"):
            continue
        if any(kw.arg == "encoding" for kw in node.keywords):
            continue
        if name == "open":
            if "b" in _mode(node):
                continue
            if not isinstance(fn, ast.Attribute) and not node.args:
                continue          # open() with no args is not a file open
        out.append(f"{path.relative_to(REPO)}:{node.lineno} {name}() without encoding=")
    return out


def main() -> int:
    files = [f for r in ROOTS for f in sorted((REPO / r).rglob("*.py"))]
    findings = [f for p in files for f in findings_for(p)]
    for f in findings:
        print(f"  [ENCODING] {f}")
    print(f"explicit encoding: {len(files)} file(s) parsed, {len(findings)} finding(s)"
          + ("" if findings else " -- every text read and write names its encoding"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
