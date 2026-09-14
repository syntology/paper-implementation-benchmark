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
Validate every shipped artifact against `schemas/artifacts.schema.json`.

WHY. This repository is read by agents as well as by people, and a schema
nobody validates is a promise, not a contract -- it drifts the first time a
field is added and the drift is invisible until something downstream breaks.
So the schemas are checked against the actual published files on every push
(.github/workflows/ci.yml), which is what lets an agent rely on them without
reading the prose.

The schemas are also deliberately STRICT: `additionalProperties: false` on the
task, run-meta and result-row shapes. A new field is then a build failure, and
the person adding it has to decide whether it is part of the published
contract. That is the intended cost.

`jsonschema` is NOT in requirements.txt: nothing in the benchmark needs it, and
this is the only thing that does. Missing it is an ERROR here, not a skip --
a validator that quietly does nothing when its dependency is absent is exactly
the failure this repository keeps finding in other people's checks.

Exit 0 clean - 1 findings - 2 the validator itself could not run.

    pip install 'jsonschema>=4.18'
    python3 tools/validate_schemas.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("validate_schemas: jsonschema is not installed, so NOTHING was "
          "checked. This is a failure, not a skip.\n"
          "    pip install 'jsonschema>=4.18'", file=sys.stderr)
    sys.exit(2)


def validate(name: str, schema: dict, items: list[tuple[str, object]],
             findings: list[str]) -> None:
    """Validate every item against one $defs entry, reporting counts (R3)."""
    v = Draft202012Validator(schema)
    n_bad = 0
    for where, obj in items:
        for err in sorted(v.iter_errors(obj), key=lambda e: list(e.path)):
            path = "/".join(str(p) for p in err.path) or "<root>"
            findings.append(f"{name}: {where} [{path}] {err.message[:160]}")
            n_bad += 1
    print(f"  {'FAIL' if n_bad else 'PASS'}  {name:<12} "
          f"validated={len(items)} findings={n_bad}")


def main() -> int:
    schema_path = REPO / "schemas" / "artifacts.schema.json"
    root = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(root)          # the schema itself is valid
    print(f"schema validation: {schema_path.relative_to(REPO)} "
          f"(python {sys.version.split()[0]})")

    def sub(name: str) -> dict:
        # Each $defs entry is validated standalone, so it carries the root's
        # $defs with it for the one internal $ref (run_meta -> provenance).
        return {**root["$defs"][name], "$defs": root["$defs"]}

    findings: list[str] = []

    tasks = []
    for p in sorted((REPO / "tasks").glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        for i, row in enumerate(doc.get("tasks", [])):
            tasks.append((f"{p.name}[{i}]", row))
    validate("task", sub("task"), tasks, findings)

    metas = []
    for p in sorted((REPO / "data" / "runs").glob("*/*/*/meta.json")):
        metas.append((str(p.relative_to(REPO)), json.loads(p.read_text(encoding="utf-8"))))
    validate("run_meta", sub("run_meta"), metas, findings)

    rows = []
    for p in sorted((REPO / "data").glob("results*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        for i, row in enumerate(doc.get("runs", [])):
            rows.append((f"{p.name}[{i}]", row))
    validate("result_row", sub("result_row"), rows, findings)

    validate("manifest", sub("manifest"),
             [("MANIFEST.json", json.loads((REPO / "MANIFEST.json").read_text(encoding="utf-8")))],
             findings)

    # An empty run would "pass" every check above. These floors are the same
    # ratchet the CI workflow puts on verify_claims.py: a validator that
    # validated nothing must not report clean.
    for name, got, floor in (("tasks", len(tasks), 96),
                             ("run metas", len(metas), 478),
                             ("result rows", len(rows), 478)):
        if got < floor:
            findings.append(f"only {got} {name} found; the floor is {floor} "
                            f"-- did the artifacts move?")

    if findings:
        print(f"\n{len(findings)} finding(s):")
        for f in findings[:40]:
            print(f"  {f}")
        if len(findings) > 40:
            print(f"  ... {len(findings) - 40} more")
        print("\nschema validation: FINDINGS")
        return 1
    print("\nschema validation: CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
