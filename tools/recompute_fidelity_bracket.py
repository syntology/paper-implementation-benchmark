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
Re-derive the 0.29-0.80 reference-implementation fidelity bracket from the
published rows, and check it against the published summary.

WHY THIS EXISTS. README.md's most important sentence -- *no implementation in
this repository carries a correctness claim* -- rests on that bracket, and the
bracket used to ship as a citation to an internal audit nobody outside
Syntology could see. An asserted number in a benchmark repository is the exact
thing this repository exists to refuse, and it is worse when the number is the
load-bearing one. So the audit's per-row verdicts ship (minus the adjudicators'
verbatim paper quotations, which are not ours to publish), and this recomputes
every headline figure from them.

WHAT IT RECOMPUTES, from `data/fidelity_audit/`:

  the bracket     each adjudicator family's correct-rate and Wilson 95% lower
                  bound over its own adjudicable rows; the strict reading that
                  additionally requires `is_defining`; and the conservative
                  floor where a row counts correct only if BOTH families say so
  the instrument  sensitivity and specificity of each adjudicator against the
                  22 gold-labelled validation rows -- the finding that neither
                  adjudicator earned the right to score
  the mutants     the paired flip rate: of the originals a family called
                  CORRECT, how many of their deterministically mutated twins it
                  then called INCORRECT

WHAT IT CANNOT CHECK, and says so rather than letting it pass as checked: the
adjudicators read the served code and the paper body, and neither is in this
repository. You can verify that the published verdicts produce the published
bracket. You cannot verify that the verdicts are right -- and the audit's own
primary finding is that on its own evidence they largely are not.

Exit 0 all checks agree - 1 any mismatch - 4 the audit artifacts are absent.

    python3 tools/recompute_fidelity_bracket.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
AUDIT = REPO / "data" / "fidelity_audit"

ok = 0
bad: list[str] = []
notes: list[str] = []


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    """Wilson score interval, lower bound; z=1.96 -> 95% two-sided. The same
    formula the audit used, restated here so this tool depends on nothing."""
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return max(0.0, (c - m) / d)


def check(name: str, got, want):
    global ok
    if got == want:
        ok += 1
        print(f"  PASS  {name}: {got}")
    else:
        bad.append(f"{name}: recomputed {got}, published {want}")
        print(f"  FAIL  {name}: recomputed {got}, published {want}")


def rows(name: str) -> list[dict]:
    p = AUDIT / name
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def by_model(rs: list[dict]) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for r in rs:
        out[r["model"]].append(r)
    return out


def main() -> int:
    if not AUDIT.is_dir():
        print(f"no audit artifacts at {AUDIT}", file=sys.stderr)
        return 4
    summary = json.loads((AUDIT / "audit_summary.json").read_text(encoding="utf-8"))
    val_sum = json.loads((AUDIT / "validate_summary.json").read_text(encoding="utf-8"))
    mut_sum = json.loads((AUDIT / "mutate_summary.json").read_text(encoding="utf-8"))

    print("the frame and the draw")
    check("frame size (HAS_REFERENCE_IMPL edges)",
          summary["sampling"]["frame_size"], 2831)
    check("n drawn", summary["sampling"]["n_drawn"], 400)
    audit_rows = rows("rows_audit.jsonl")
    per_model = by_model(audit_rows)
    check("audit rows published", len(audit_rows),
          sum(m["n_rows"] for m in summary["per_model"].values()))

    print("\nthe bracket -- each family's rate over its own adjudicable rows")
    for m, rs in sorted(per_model.items()):
        pub = summary["per_model"][m]
        counts = Counter(r["verdict"] for r in rs)
        n = counts["CORRECT"] + counts["INCORRECT"]
        check(f"{m}: adjudicable", n, pub["n_adjudicable"])
        check(f"{m}: correct", counts["CORRECT"], pub["n_correct"])
        check(f"{m}: rate", round(counts["CORRECT"] / n, 4), pub["rate"])
        check(f"{m}: Wilson lower 95%",
              round(wilson_lower(counts["CORRECT"], n), 4), pub["wilson_lower_95"])
        strict = sum(1 for r in rs
                     if r["verdict"] == "CORRECT" and _truthy(r.get("is_defining")))
        check(f"{m}: strict (is_defining) correct", strict,
              pub["strict_defining_correct"])
        check(f"{m}: strict rate", round(strict / n, 4), pub["strict_rate"])
        modes = Counter(r.get("failure_mode") or "(unlabelled)"
                        for r in rs if r["verdict"] == "INCORRECT")
        check(f"{m}: failure modes", dict(sorted(modes.items())),
              dict(sorted(pub["failure_modes"].items())))

    print("\nthe conservative floor -- correct only when BOTH families agree")
    verdicts: dict[str, dict[str, str]] = defaultdict(dict)
    for r in audit_rows:
        verdicts[r["key"]][r["model"]] = r["verdict"]
    fams = sorted(per_model)
    decided = [k for k, v in verdicts.items()
               if all(v.get(f) in ("CORRECT", "INCORRECT") for f in fams)]
    both_ok = sum(1 for k in decided
                  if all(verdicts[k][f] == "CORRECT" for f in fams))
    pair = summary.get("agreement_all_pairs", {})
    pub_pair = next(iter(pair.values())) if pair else {}
    check("both families decided", len(decided), pub_pair.get("n_both_decided"))
    check("both say CORRECT", both_ok, pub_pair.get("both_say_correct"))
    check("conservative floor rate", round(both_ok / len(decided), 4),
          pub_pair.get("conservative_floor_rate"))

    print("\nthe headline bracket, as README.md states it")
    lo = min(summary["per_model"][m]["rate"] for m in per_model)
    hi = max(summary["per_model"][m]["rate"] for m in per_model)
    check("bracket, rounded to 2 dp", (round(lo, 2), round(hi, 2)), (0.29, 0.80))

    print("\nthe instrument -- did either adjudicator earn the right to score?")
    val_rows = rows("rows_validate.jsonl")
    for m, rs in sorted(by_model(val_rows).items()):
        pub = val_sum["instrument_validation"][m]
        neg = [r for r in rs if r["gold_label"] == 0]
        pos = [r for r in rs if r["gold_label"] == 1]
        caught = [r for r in neg if r["verdict"] == "INCORRECT"]
        kept = [r for r in pos if r["verdict"] == "CORRECT"]
        check(f"{m}: negatives caught", (len(caught), len(neg)),
              (pub["negatives_caught"], pub["n_negatives"]))
        check(f"{m}: sensitivity", round(len(caught) / len(neg), 4),
              pub["sensitivity"])
        check(f"{m}: positives kept", (len(kept), len(pos)),
              (pub["positives_kept"], pub["n_positives"]))
        check(f"{m}: specificity", round(len(kept) / len(pos), 4),
              pub["specificity"])
        check(f"{m}: clears both bars",
              round(len(caught) / len(neg), 4) >= val_sum["bars"]["sensitivity"]
              and round(len(kept) / len(pos), 4) >= val_sum["bars"]["specificity"],
              pub["clears_all_bars"])

    print("\nthe second channel -- deterministic AST mutants, paired")
    mut_rows = rows("rows_mutate.jsonl")
    for m, rs in sorted(by_model(mut_rows).items()):
        pub = mut_sum["mutation_validation"][m]
        got = {r["key"]: r for r in rs}
        pairs = [(got[k[:-5]], got[k]) for k in got
                 if k.endswith("||MUT") and k[:-5] in got]
        orig_correct = [(o, mu) for o, mu in pairs if o["verdict"] == "CORRECT"]
        flips = [1 for o, mu in orig_correct if mu["verdict"] == "INCORRECT"]
        check(f"{m}: pairs", len(pairs), pub["n_pairs"])
        check(f"{m}: originals called CORRECT", len(orig_correct),
              pub["originals_called_correct"])
        check(f"{m}: paired flips", len(flips), pub["paired_flips"])
        check(f"{m}: paired flip rate",
              round(len(flips) / len(orig_correct), 4), pub["paired_flip_rate"])
        check(f"{m}: clears the flip bar",
              round(len(flips) / len(orig_correct), 4) >= pub["bar"],
              pub["clears_bar"])

    print("\nnot checkable from this repository")
    for name, why in (
        ("whether any individual verdict is CORRECT",
         "the adjudicators read the served code and the paper body; neither "
         "is published here, and the audit's own finding is that the verdicts "
         "are unreliable in the permissive direction"),
        ("the frame itself -- that these 400 rows are an SRS of 2,831 edges",
         "the frame is the private graph; its sha256 and seed are recorded in "
         "audit_summary.json['sampling'] and can only be re-derived against it"),
    ):
        notes.append(name)
        print(f"  [unverifiable-here]  {name}\n        ({why})")

    print(f"\n{ok} checks passed, {len(bad)} failed, "
          f"{len(notes)} things not checkable here")
    for b in bad:
        print(f"  FAILED: {b}", file=sys.stderr)
    return 1 if bad else 0


def _truthy(v):
    return v is True or (isinstance(v, str) and v.lower() == "true")


if __name__ == "__main__":
    sys.exit(main())
