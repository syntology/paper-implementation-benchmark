#!/usr/bin/env python3
"""
Compose semantics -- the ONE definition of what makes a typed edge.

Before this module the rules lived in five copies that had already
diverged: main.py's serving path checked role + dtype family + rank and
demoted hallucinated tensor roles on non-tensor outputs; the offline
lane (typed_composition_search.py, generality_score.py) checked role +
dtype family only. The rank check is measured, not stylistic -- of 5
failures when 31 decided pairs were executed shape-consistently, 2 were
pure rank mismatches -- so the offline copies were overcounting edges
against a rule production had already learned was wrong. Same story for
the non-tensor demotion (2 of the same 5 failures) and the backed-level
rule (313/396 CodeSamples once served as machine-verified on a
hardcoded 3). This module is those rules, verbatim from serving;
qc_compose_semantics.py holds it and main.py's copy in behavioral
lockstep until main.py can import it directly (main.py is under active
edit by another session, ACTIVE_WORK.md).

<INTERNAL>/scaling_fit.py carries its own copy
BY DESIGN -- its docstring pins the semantics to a commit as the
measurement's frozen method -- and is allowlisted in the QC scan.

Stdlib only. Callers own their graph sessions and their scoring.
"""
from __future__ import annotations

import json

# Roles that end a chain. A loss is what you optimise, so nothing
# consuming it is a gap in the graph. Serving reports terminality as
# EFFECTIVE rather than by role alone because the adapter table still
# carries loss -> gradients.
TERMINAL_ROLES = {"loss", "scalar_metric", "method_internal_output",
                  "unprobed", "error", "UNTYPED_OUT"}

# Python types that cannot be a tensor. A tensor role on one of these is
# a hallucination -- model_wrapper returns a model and Log is a class,
# both were typed with tensor roles, both failed the moment a consumer
# touched them. The fixture run records what the output actually IS, so
# demotion is a deterministic guard, not another model's opinion.
NON_TENSOR_TYPES = {"function", "method", "module", "type", "NoneType",
                    "builtin_function_or_method", "partial"}

# The hand-ratified deterministic framework ops (from
# schema_v2_prototype.py). Serving keeps its own copy for now
# (ACTIVE_WORK.md); the QC gate checks the two stay identical.
ADAPTERS = [
    ("loss", "gradients", "autograd", "d(loss)/d(params)"),
    ("logits", "probs", "softmax", "normalize over last axis"),
    ("probs", "log_probs", "log", "elementwise log"),
    ("logits", "log_probs", "log_softmax", "fused"),
    ("log_probs", "probs", "exp", "elementwise exp"),
    ("weight_matrix", "param_vector", "flatten", "reshape (out,in)->(P,)"),
    ("param_vector", "weight_matrix", "unflatten", "requires shape metadata"),
    ("gradients", "weight_matrix", "grad_as_matrix",
     "a gradient wrt a weight matrix is a matrix"),
    ("noise_prediction", "score_function", "score_from_eps", "score = -eps/sigma"),
    ("score_function", "noise_prediction", "eps_from_score", "inverse"),
]


def dtype_fam(dt):
    """int is its own family; everything else (float, None, 'other',
    'float(int-valued)') collapses to float. The collapse of 'other'
    into float is a known softness inherited from serving -- change it
    there first or not at all."""
    return "int" if dt == "int" else "float"


def unify(out, in_param):
    """Role equality, dtype family, AND rank.

    Rank is enforced only when BOTH sides recorded one: params carried
    `kind` but no ndim until backfilled, so a missing value means
    unknown, not incompatible -- refusing those would silently delete
    edges that were never tested."""
    if out.get("role") != in_param.get("role"):
        return False
    if dtype_fam(out.get("dtype", "float")) != dtype_fam(in_param.get("dtype", "float")):
        return False
    on, pn = out.get("shape_ndim"), in_param.get("ndim")
    if on is not None and pn is not None and on != pn:
        return False
    return True


def demote_non_tensor(out, fixture_out_type):
    """Return the output contract with hallucinated tensor roles demoted.

    Never mutates the input; returns a new dict when demoting."""
    if (fixture_out_type in NON_TENSOR_TYPES
            and out.get("role") not in (None, "UNTYPED_OUT")):
        out = dict(out)
        out["role_demoted_because"] = f"output is a {fixture_out_type}, not a tensor"
        out["role"] = "UNTYPED_OUT"
    return out


def effective_level(lvl, verification_report):
    """A verification_level with no report is self-reported and counts
    as 0. Writers refuse to store one; readers must not trust one."""
    return 0 if verification_report is None else int(lvl or 0)


def is_producer(out):
    """Can this output start a typed (non-adapter) edge?"""
    role = out.get("role")
    return role is not None and role not in TERMINAL_ROLES


def boundary_params(tensor_contract):
    """Boundary-tier params from a tensor_contract (JSON string or list).
    Raises ValueError/TypeError on garbage -- callers decide whether an
    unparseable contract is skipped, and must count it if so (R3)."""
    params = (json.loads(tensor_contract) if isinstance(tensor_contract, str)
              else (tensor_contract or []))
    return [p for p in params if p.get("tier") == "boundary"]


def parse_output(output_contract):
    """Output contract from JSON string or dict; {} for empty."""
    if isinstance(output_contract, str):
        return json.loads(output_contract) if output_contract else {}
    return output_contract or {}
