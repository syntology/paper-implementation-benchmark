#!/usr/bin/env python3
"""
Read-only replica of the live Syntology MCP serving surface, for the
graph-vs-search benchmark (see PREREGISTRATION.md).

WHY A REPLICA AND NOT AN IMPORT: main.py is under active edit by a
concurrent session (ACTIVE_WORK.md) and importing it builds the whole
FastAPI/MCP app, which needs Cloudflare env vars this benchmark should
not depend on. The paper-lookup tools therefore go through
query_engine.templates/linker exactly as main.py does, and the four
code-lane functions below are lifted verbatim from main.py@bc87485a
(2026-09-02, the v1-freeze re-lift by ast extraction; earlier pins in
order: 0387438, c70c1ea, cbc9a69). If serving changes in main.py,
re-lift before re-running the benchmark -- the benchmark's validity
depends on this file matching what production serves.

TWO PROVENANCE MECHANISMS, NOT ONE (corrected 2026-09-01). The resolver
functions are COPY-backed: pinned lifts, deliberately frozen, because
the run set measures one tool version and a copy that silently follows
main.py would mix versions into results_v13.json without saying so.
Those are exercised -- 136 calls across v1.1/v1.2/v1.3 -- and must be
re-lifted deliberately, never incidentally.

The compose tables and predicates are IMPORT-backed, from the root
compose_semantics module, and parity-gated by qc_compose_semantics.py.
That is stronger than a frozen copy for code nothing pins a result to:
a copy drifts the moment main.py moves and nobody notices, while a gate
fails loudly. syntology_compose was called ZERO times across every
benchmark run, so no result depends on those tables at all.

Read-only discipline: connects with NEO4J_USER (the read credential),
and nothing here writes.
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(os.environ.get("BENCH_REPO_ROOT",
                           Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from query_engine import linker, templates  # noqa: E402

# The substitution experiment's hold-out (PREREGISTRATION_SUBSTITUTION.md).
# A no-op unless a hold-out is installed on this thread, so every earlier run
# of this file is unaffected; the parity check in verify_holdout.py asserts
# that. Both arms consult the SAME set, which is the only thing that makes
# "unreachable to both" a claim rather than an assertion.
import benchmark_holdout  # noqa: E402

_driver = None


def _get_session():
    global _driver
    if _driver is None:
        from neo4j import GraphDatabase
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    return _driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j"))


def _resolve_or_raise(session, mention: str):
    link = linker.resolve(session, mention)
    if link.status == "not_found":
        raise ValueError(f"couldn't resolve '{mention}' to a paper in the graph")
    if link.status == "ambiguous":
        titles = [c.get("title") for c in link.candidates]
        raise ValueError(f"'{mention}' matches multiple papers: {titles}")
    return link


# --- paper-lane tools (delegate to query_engine.templates, as main.py does) --





def get_code_for_method(name: str) -> dict:
    with _get_session() as session:
        result = templates.t9_code_for_method(session, name)
        if result is None:
            raise ValueError(f"no method or dataset found matching '{name}'")
        return result


# --- code-lane tools (lifted verbatim from main.py@bc87485a; see header) -----

def _best_available_for_method(session, name: str) -> dict | None:
    """What we CAN offer when no verified implementation exists.

    98.4% of Methods (42,494 of 43,182) have no CodeSample, and every tool here
    answered that by raising -- the caller got an error and nothing else. But
    those methods are not empty: all 42,494 have a paper, 22,567 have a KNOWN
    repository link that simply has not been harvested yet, and a growing subset
    resolves to a Task with recommended open-source models. Throwing that away
    is a choice, not a limitation.

    Returns the best rung with an explicit `tier`, so a caller is never told
    'verified' about something that is not. Rungs, most to least actionable:
      repo_known    we know where the implementation lives, unharvested
      task_routable no code, but the task has open-source models that do it
      paper_only    the paper, always available
    """
    rec = session.run("""
        MATCH (m:Method) WHERE m.name_lower = toLower($name)
        OPTIONAL MATCH (p:Paper)-[:PROPOSES]->(m)
        OPTIONAL MATCH (p)-[:IMPLEMENTED_BY]->(r:CodeRepo)
        OPTIONAL MATCH (m)-[at:ADDRESSES_TASK]->(t:Task)
        RETURN m.name AS method, m.origin_arxiv_id AS origin,
               p.title AS title, p.arxiv_id AS arxiv_id,
               collect(DISTINCT r.owner + '/' + r.repo)[..5] AS repos,
               collect(DISTINCT {task: t.id, label: t.label,
                                 similarity: at.similarity})[..3] AS tasks
        LIMIT 1
    """, name=name).single()
    if rec is None or rec["method"] is None:
        return None
    repos = [x for x in (rec["repos"] or []) if x and "/" in x]
    tasks = [x for x in (rec["tasks"] or []) if x and x.get("task")]
    out = {"method": rec["method"], "origin_arxiv_id": rec["origin"],
           "paper_title": rec["title"], "paper_arxiv_id": rec["arxiv_id"],
           "verified_implementation": False}
    if repos:
        out["tier"] = "repo_known"
        out["repositories"] = repos
        out["what_this_means"] = (
            "No verified implementation has been produced for this method yet, but "
            "its paper declares these repositories. They are UNVERIFIED by "
            "Syntology -- nothing here has been executed or type-checked.")
    elif tasks:
        out["tier"] = "task_routable"
        out["tasks"] = tasks
        out["what_this_means"] = (
            "No implementation and no declared repository. This method resolves to "
            "the task(s) below, for which mature open-source models exist on public "
            "hubs -- a working route to the outcome, not to this specific method.")
    else:
        out["tier"] = "paper_only"
        out["what_this_means"] = (
            "Only the paper is available for this method: no verified "
            "implementation, no declared repository, no task resolution.")
    if tasks and out["tier"] != "task_routable":
        out["tasks"] = tasks
    return out






# Compose semantics come from the shared module -- the same rules the
# serving copy is parity-gated against (qc_compose_semantics.py), so the
# "re-lift before re-running" caveat above no longer applies to these
# tables/predicates, only to the compose() function body itself.
from compose_semantics import (ADAPTERS as _COMPOSE_ADAPTERS,  # noqa: E402
                               TERMINAL_ROLES as _COMPOSE_TERMINAL,
                               NON_TENSOR_TYPES as _NON_TENSOR,
                               dtype_fam as _dtype_fam,
                               unify as _unify)


def compose(name: str, direction: str = "downstream", min_level: int = 2,
            limit: int = 25) -> dict:
    q = """
        MATCH (cs:CodeSample) WHERE cs.tensor_contract IS NOT NULL
        OPTIONAL MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(cs)
        RETURN cs.entry AS entry, cs.tensor_contract AS tc, cs.output_contract AS oc,
               cs.verification_level AS lvl, cs.verification_report AS vr,
               cs.paper_attribution AS paper, m.name AS method,
               coalesce(cs.source_kind, 'generated') AS source_kind,
               cs.shape_contract AS shape, cs.dependencies AS deps,
               cs.fixture_out_type AS fixture_out_type, cs.code_sha256 AS sha
    """
    with _get_session() as session:
        rows = session.run(q).data()
    # compose's universe is both the subject pool and the partner pool. A
    # held-out sample must be neither: not offerable as a partner, and not
    # resolvable as the subject -- which costs the graph arm the ability to
    # ask "what composes with the thing I cannot have", and is disclosed as a
    # cost in PREREGISTRATION_SUBSTITUTION.md rather than quietly excepted.
    rows = [r for r in rows if not benchmark_holdout.blocks(r.get("sha"))]

    def lvl_of(r):
        return 0 if r.get("vr") is None else int(r.get("lvl") or 0)

    universe = []
    for r in rows:
        try:
            params = json.loads(r["tc"]) if r["tc"] else []
            out = json.loads(r["oc"]) if r["oc"] else {}
        except (ValueError, TypeError):
            continue
        ot = r.get("fixture_out_type")
        if ot in _NON_TENSOR and out.get("role") not in (None, "UNTYPED_OUT"):
            out = dict(out)
            out["role"] = "UNTYPED_OUT"
            out["role_demoted_because"] = f"output is a {ot}, not a tensor"
        universe.append({**r, "params": [p for p in params
                                         if p.get("tier") == "boundary"],
                         "out": out, "lvl": lvl_of(r)})

    want = name.lower()
    subj = ([u for u in universe if (u["entry"] or "").lower() == want]
            or [u for u in universe if (u["method"] or "").lower() == want]
            or [u for u in universe if want in (u["entry"] or "").lower()])
    if not subj:
        raise ValueError(f"no contract-carrying implementation matches '{name}'")
    me = subj[0]

    adapters_from = {}
    for frm, to, op, note in _COMPOSE_ADAPTERS:
        adapters_from.setdefault(frm, []).append((to, op, note))

    hits = []
    if direction == "downstream":
        out = me["out"]
        reach = {out.get("role"): (None, None)}
        for to, op, note in adapters_from.get(out.get("role"), []):
            reach.setdefault(to, (op, note))
        for u in universe:
            if u["entry"] == me["entry"] or u["lvl"] < min_level:
                continue
            for p in u["params"]:
                for role, (op, note) in reach.items():
                    probe = dict(out); probe["role"] = role
                    if _unify(probe, p):
                        hits.append({"entry": u["entry"], "method": u["method"],
                                     "paper": u["paper"], "verification_level": u["lvl"],
                                     "source_kind": u["source_kind"],
                                     "expects_ndim": p.get("ndim"),
                                     "dependencies": u.get("deps") or [],
                                     "consumes_param": p.get("name"), "via_role": role,
                                     "tier": "typed" if op is None else "adapter",
                                     "adapter_op": op, "adapter_note": note})
                        break
    else:
        for u in universe:
            if u["entry"] == me["entry"] or u["lvl"] < min_level:
                continue
            uo = u["out"]
            reach = {uo.get("role"): (None, None)}
            for to, op, note in adapters_from.get(uo.get("role"), []):
                reach.setdefault(to, (op, note))
            for p in me["params"]:
                for role, (op, note) in reach.items():
                    probe = dict(uo); probe["role"] = role
                    if _unify(probe, p):
                        hits.append({"entry": u["entry"], "method": u["method"],
                                     "paper": u["paper"], "verification_level": u["lvl"],
                                     "source_kind": u["source_kind"],
                                     "produces_ndim": (u["out"] or {}).get("shape_ndim"),
                                     "dependencies": u.get("deps") or [],
                                     "produces_for_param": p.get("name"), "via_role": role,
                                     "tier": "typed" if op is None else "adapter",
                                     "adapter_op": op, "adapter_note": note})
                        break

    hits.sort(key=lambda h: (h["tier"] != "typed", -h["verification_level"]))
    eff_terminal = (direction == "downstream"
                    and me["out"].get("role") in _COMPOSE_TERMINAL
                    and not any(h["tier"] == "adapter" for h in hits))
    return {
        "query": name,
        "resolved_to": {"entry": me["entry"], "method": me["method"],
                        "paper": me["paper"], "verification_level": me["lvl"],
                        "source_kind": me["source_kind"],
                        "output_contract": me["out"],
                        "input_contract": me["params"],
                        "dependencies": me.get("deps") or [],
                        "shape_contract": (json.loads(me["shape"])
                                           if me.get("shape") else None)},
        "direction": direction,
        "min_level_applied_to_partner": min_level,
        "total": len(hits),
        "typed": sum(1 for h in hits if h["tier"] == "typed"),
        "adapter": sum(1 for h in hits if h["tier"] == "adapter"),
        "effectively_terminal": eff_terminal,
        "partners": hits[:limit],
        "note": ("An edge is TYPE-VALID, not drop-in: executing sampled pairs "
                 "with matched shapes composed 89% of the time, and the same "
                 "pairs with mismatched shapes only 42%. Compare produces_ndim "
                 "against expects_ndim and reshape as needed."),
    }


# ---------------------------------------------------------------------------
# RE-LIFTED from main.py@cbc9a69 for v1.3 (2026-08-31). v1.2 measured the
# c70c1ea state: token matching in `list` only. Since then production gained
# (a) a token fallback in `get` so it degrades to a near match instead of
# raising "no method named X is in the graph", (b) inline
# `verified_reference_implementations` in get_paper / get_code_for_paper, and
# (c) server-level instructions (carried in agent_harness's system context,
# not here). Lifted programmatically by ast extraction, not by hand, so shim
# and production cannot drift silently.
# ---------------------------------------------------------------------------

# Tokens too common to identify a method. Three separate resolver paths had the
# same bug independently -- matching a query to an unrelated method on a shared
# word like "method" or "model" -- so the list lives here, once, and every path
# that scores name overlap imports it from this one place.
GENERIC_METHOD_TOKENS = {
    "method", "model", "loss", "layer", "network", "algorithm", "function",
    "module", "step", "update", "score", "block", "learning", "training",
    "optimizer", "based", "aware", "neural", "deep", "adaptive", "efficient",
    "new", "novel", "fast", "the", "for", "with", "and", "of", "a", "an",
}


def _significant_tokens(text: str) -> list:
    """Query tokens that could actually identify a method."""
    toks = [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t]
    return [t for t in toks if t not in GENERIC_METHOD_TOKENS and len(t) > 1]


def _verified_impls_for_paper(session, arxiv_id: str, limit: int = 5) -> dict:
    """Reference implementations this paper's methods have, for inlining.

    THE STRUCTURAL FIX from the 2026-08-31 A/B run, and it is structural on
    purpose because words were measured and found insufficient. Across three
    ablations, agents adopted `get_reference_implementation` 0/24, then 1/24,
    then 6/22 as its description improved -- while calling get_paper 23 times
    and get_code_for_paper 18 times and then going to GitHub for the code
    anyway. The workflow prior "graph = metadata, GitHub = code" survived the
    best description anyone wrote for the tool. So the verified code is put on
    the path agents already walk instead of asking them to learn a new one.

    Same unbacked-level discipline as the other two code-lane tools: a level
    with no verification_report behind it is reported as 0 regardless of what
    the node claims. 313 CodeSamples were once served as machine-verified on a
    hardcoded 3 with nothing behind it, and this must not become a fourth place
    that can happen.

    Returns {} when the paper has none, so the key is absent rather than an
    empty list on the ~99.9% of papers that have no implementation -- presence
    of the field is itself the signal.
    """
    rows = session.run("""
        MATCH (p:Paper {arxiv_id: $aid})-[:PROPOSES]->(m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
        RETURN m.name AS method, cs.language AS language,
               cs.verification_level AS level, cs.verification_report AS report,
               cs.code_sha256 AS sha
        ORDER BY cs.verification_level DESC, m.name ASC
    """, aid=arxiv_id).data()
    rows = [r for r in rows if not benchmark_holdout.blocks(r.get("sha"))]
    if not rows:
        return {}
    impls, best = [], 0
    for r in rows[:limit]:
        lvl = int(r["level"] or 0)
        if r.get("report") is None:
            lvl = 0
        best = max(best, lvl)
        impls.append({"method": r["method"], "language": r["language"],
                      "verification_level": lvl,
                      "retrieve_with": f"get_reference_implementation(name={r['method']!r})"})
    n = len(rows)
    more = f" ({n} total, showing {len(impls)})" if n > len(impls) else ""
    if best >= 2:
        note = (f"This paper has {n} reference implementation(s) IN THIS GRAPH{more}, "
                f"machine-verified to level {best} -- the code was executed against "
                f"held-out tests, not just retrieved. Fetch it with "
                f"get_reference_implementation before searching GitHub or writing "
                f"your own; agents that fetched it passed 17/17 in benchmarking.")
    else:
        note = (f"This paper has {n} reference implementation(s) in this graph{more}, "
                f"at verification level 0 -- present and callable, but NOT executed "
                f"against held-out tests. Treat as a starting point, not a "
                f"guarantee.")
    return {"verified_reference_implementations": impls, "note": note}



def _licensed_harvested(arxiv_id: str, limit: int = 3) -> list:
    """Harvested code we MAY redistribute, with the code, at level 0.

    31,902 harvested samples carry license_inline_ok -- a permissive upstream
    licence, overwhelmingly MIT/Apache/BSD -- and none was reachable by any
    code-returning path. They attach to 4,279 methods, against the 2,830 that
    hold a verified implementation, so withholding them roughly halved what the
    graph could answer with, for no legal reason at all.

    This returns the CODE, unlike _harvested_pointers, because a permissive
    licence is exactly permission to redistribute. What it must never do is let
    that be mistaken for a reference implementation: verification_level is 0
    and stated, attribution and licence ride along, and the tier is named
    `licensed_harvested` rather than folded into `implementations`. A caller
    that wants only verified code filters on the tier and is unaffected.
    """
    # Opens its OWN session: the caller's has already closed by the time the
    # fallback return runs, which is what "Session closed" was telling me.
    with _get_session() as session:
        rows = session.run("""
            MATCH (p:Paper {arxiv_id: $aid})-[:HAS_HARVESTED_IMPL]->(cs:CodeSample)
            WHERE cs.license_inline_ok = true AND cs.code IS NOT NULL
            RETURN cs.entry AS entry, cs.code AS code, cs.generated_by AS repo,
                   cs.source_path AS path, cs.upstream_license AS spdx,
                   cs.code_sha256 AS sha, coalesce(cs.verification_level,0) AS lvl
            ORDER BY size(cs.code) DESC LIMIT $limit
        """, aid=arxiv_id, limit=limit).data()
    return [{
        "entry": r["entry"], "code": r["code"], "code_sha256": r["sha"],
        "verification_level": r["lvl"],
        "upstream_license": r["spdx"],
        "attribution": f"https://github.com/{r['repo']}/blob/HEAD/{r['path']}",
        "what_this_is": ("code from the authors' repository for this paper, "
                         "redistributed under its upstream licence. UNVERIFIED: "
                         "not run, and not checked to implement this method."),
    } for r in rows]

def get_reference_implementation(name: str, min_level: int = 2) -> dict:
    resolved_via = None
    """v2.3 CodeSample serving (2026-08-26). Exact-then-CONTAINS method
    resolution (T9's shape, including its multi-node DASH lesson: same
    name can be several genuinely distinct Methods -- every match's
    implementations are returned, each attributed to its origin paper).
    Serving rule: never serve below the caller's floor; the decline
    NAMES the highest level that exists so an agent can lower its floor
    deliberately. Mathematically-wrong specs (spec_review=hard_error)
    are excluded at load time and never reach this query."""
    q = """
        MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
        WHERE m.name_lower = toLower($name)
        RETURN m.name AS method, m.origin_arxiv_id AS origin, cs
        UNION
        MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
        WHERE m.name_lower <> toLower($name)
          AND m.name_lower CONTAINS toLower($name)
        RETURN m.name AS method, m.origin_arxiv_id AS origin, cs
        LIMIT 25
    """
    with _get_session() as session:
        rows = session.run(q, name=name).data()
    rows = [r for r in rows
            if not benchmark_holdout.blocks(r["cs"].get("code_sha256"))]
    if not rows:
        # TOKEN FALLBACK before declaring absence. Exact-then-CONTAINS has the
        # same brittleness the A/B run found in the browse tool: "IS-MBPG
        # momentum" against a graph holding "IS-MBPG*" resolved to nothing, and
        # here the consequence is worse -- this path RAISES "no method named X
        # is in the graph", a flat assertion of absence for a method we hold.
        # One descriptive word appended to an exact name turned a guaranteed win
        # into a 17-turn failure.
        toks = [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]
        if toks:
            with _get_session() as session:
                cand = session.run("""
                    MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
                    RETURN DISTINCT m.name AS method
                """).data()
            # GENERIC TOKENS DO NOT COUNT. The first version of this fallback
            # resolved "totally absent method zzz" to "OOD detection method" on
            # the shared token "method" -- trading a false ABSENCE for a false
            # PRESENCE, which is strictly worse: the agent gets confidently
            # wrong code instead of a dead end it can recover from.
            sig = _significant_tokens(name)
            scored = []
            for c in cand:
                hay = (c["method"] or "").lower()
                # Only DISTINCTIVE tokens can carry a match, and the match must
                # cover at least half the distinctive query -- one shared word
                # out of four is not a resolution.
                hits = sum(1 for t in sig if t in hay)
                if sig and hits / len(sig) >= 0.5:
                    scored.append((hits, len(hay), c["method"]))
            if scored:
                # most query tokens matched, then shortest name -- "IS-MBPG*"
                # beats a longer method that merely contains one token.
                scored.sort(key=lambda x: (-x[0], x[1]))
                best_name = scored[0][2]
                if best_name.lower() != name.lower():
                    with _get_session() as session:
                        rows = session.run(q, name=best_name).data()
                    rows = [r for r in rows
                            if not benchmark_holdout.blocks(
                                r["cs"].get("code_sha256"))]
                    if rows:
                        resolved_via = best_name
    if not rows:
        # Degrade, do not fail. A caller that asked a reasonable question should
        # leave with the best thing we have rather than an exception -- the
        # tier field says exactly what they got and `verified_implementation`
        # is False, so nothing is passed off as verified.
        with _get_session() as session:
            alt = _best_available_for_method(session, name)
        if alt is None:
            # SAY WHICH ABSENCE THIS IS. "no method named X is in the graph" was
            # false for a large class of queries: 87 Methods contain
            # "quantization" and none has a reference implementation, so the old
            # message told the agent the graph knows nothing about quantization.
            # An agent that believes that leaves for web search and never comes
            # back -- a far costlier error than one failed lookup.
            toks_a = _significant_tokens(name)
            named = []
            if toks_a:
                with _get_session() as session:
                    named = session.run(
                        "MATCH (m:Method) WHERE any(t IN $toks WHERE m.name_lower CONTAINS t) "
                        "RETURN DISTINCT m.name AS name ORDER BY size(m.name) LIMIT 6",
                        toks=toks_a).data()
            if named:
                names = ", ".join(f"'{r['name']}'" for r in named)
                raise ValueError(
                    f"no reference implementation for '{name}'. The graph DOES hold "
                    f"related methods ({names}) -- they have no extracted code yet. "
                    f"Absence of code here is not absence of the method.")
            raise ValueError(
                f"'{name}' matched no method name in the graph. This is a name-match "
                f"failure, not proof the method is unknown -- try the canonical "
                f"paper name, or list_reference_implementations to browse.")
        lic = []
        if isinstance(alt, dict) and alt.get("origin_arxiv_id"):
            lic = _licensed_harvested(alt["origin_arxiv_id"])
        note = ("No verified implementation exists. `fallback` carries the "
                "most actionable thing available; see fallback.tier.")
        if lic:
            note += (f" We DO hold {len(lic)} permissively-licensed file(s) from the "
                     f"authors' own repository, served in `licensed_harvested` -- "
                     f"UNVERIFIED (level 0), not checked to implement this method, "
                     f"and attributed to source.")
        return {"query": name, "implementations": [], "fallback": alt,
                "licensed_harvested": lic or None, "note": note}
    exact = [r for r in rows if r["method"].lower() == name.lower()]
    matches = exact or rows
    servable, best = [], -1
    for r in matches:
        cs = r["cs"]
        lvl = int(cs.get("verification_level", 0))
        # A level with no verification_report is SELF-REPORTED, and this tool's
        # promise is machine-verified code. Treat unbacked levels as 0 no matter
        # what the node claims (2026-08-28: 313 nodes carried a hardcoded level 3
        # with no report and were being served as verified).
        if cs.get("verification_report") is None:
            lvl = 0
        best = max(best, lvl)
        if lvl < min_level:
            continue
        servable.append({
            "method": r["method"],
            "origin_arxiv_id": r["origin"],
            "entry": cs.get("entry"),
            "signature": cs.get("signature"),
            "language": cs.get("language"),
            "verification_level": lvl,
            "verification_report": json.loads(cs["verification_report"])
                if cs.get("verification_report") else None,
            # The inputs the V1/V2 checks above actually ran on. Attached so a
            # caller can REPRODUCE the recorded level rather than trust it;
            # loaded only where the file's case count matched the report's own
            # n_inputs, so these always correspond to the result shown.
            "test_cases": json.loads(cs["test_cases"]) if cs.get("test_cases") else None,
            "test_cases_provenance": cs.get("test_cases_provenance"),
            "env": json.loads(cs["env"]) if cs.get("env") else None,
            "generated_by": cs.get("generated_by"),
            "cross_checked_by": cs.get("cross_checked_by"),
            "spec_review": cs.get("spec_review"),
            "review_note": cs.get("review_note") or None,
            "code": cs.get("code"),
            "attribution": (f"Generated from arXiv:{r['origin']}'s own algorithm "
                            f"description; reference implementation, not audited "
                            f"production code."),
        })
    if not servable:
        raise ValueError(
            f"a reference implementation for '{name}' exists but its "
            f"verification level (V{best}) is below your floor "
            f"(min_level={min_level}); call again with min_level={best} to "
            f"receive it, understanding the weaker guarantee")
    out = {"implementations": servable}
    if resolved_via:
        out["resolved_via"] = resolved_via
        # RESOLUTION ORDER (2026-09-15). A token-overlap match is a DIFFERENT
        # method: asked for "Weighted Preference Optimization (WPO)", served
        # "Tree Preference Optimization (TPO)"; asked for "Prophet Attention",
        # served "ReAttention". Verified code for the wrong method used to be
        # the only thing offered, and it outranked the RIGHT paper's own code
        # purely because the substitute happened to carry a verification level.
        # Measured on 12 sampled methods: substitution pre-empted the correct
        # paper's licensed code on 4.
        #
        # Neither dominates -- one is verified-but-wrong-method, the other is
        # right-paper-but-unverified -- so both are returned and NEITHER is
        # silently dropped. What changes is the order and the note: the code
        # from the paper actually asked about comes first, because an agent
        # that takes the first thing should take the one attached to the right
        # question.
        own = _licensed_harvested_for_method(name)
        if own:
            out["from_the_method_you_asked_for"] = own
            out["note"] = (
                f"'{name}' did not match exactly. `implementations` below is "
                f"'{resolved_via}' -- a DIFFERENT method reached by token overlap. "
                f"Prefer `from_the_method_you_asked_for`: {len(own)} file(s) from "
                f"the repository of the paper that actually proposes '{name}', "
                f"permissively licensed, UNVERIFIED (level 0). Confirm which you "
                f"meant before using either.")
        else:
            out["note"] = (f"'{name}' did not match exactly; resolved by token overlap "
                           f"to '{resolved_via}'. Confirm this is the method you meant.")
    return out


def _licensed_harvested_for_method(name: str, limit: int = 3) -> list:
    """Licensed harvested code from the paper that proposes THIS method.

    Exists so an inexact resolution can offer the right paper's code rather
    than only a lexical neighbour's. Matches the method name exactly -- a fuzzy
    match here would reintroduce the very substitution this is meant to rank
    below.
    """
    with _get_session() as session:
        rows = session.run("""
            MATCH (m:Method) WHERE toLower(m.name) = toLower($name)
            MATCH (p:Paper)-[:PROPOSES]->(m)
            MATCH (p)-[:HAS_HARVESTED_IMPL]->(cs:CodeSample)
            WHERE cs.license_inline_ok = true AND cs.code IS NOT NULL
            RETURN DISTINCT cs.entry AS entry, cs.code AS code,
                   cs.generated_by AS repo, cs.source_path AS path,
                   cs.upstream_license AS spdx, cs.code_sha256 AS sha,
                   p.arxiv_id AS paper
            LIMIT $limit
        """, name=name, limit=limit).data()
    return [{
        "entry": r["entry"], "code": r["code"], "code_sha256": r["sha"],
        "verification_level": 0, "upstream_license": r["spdx"],
        "origin_arxiv_id": r["paper"],
        "attribution": f"https://github.com/{r['repo']}/blob/HEAD/{r['path']}",
        "what_this_is": ("from the repository of the paper that proposes the method "
                         "you asked for. UNVERIFIED: not run, not checked to "
                         "implement it."),
    } for r in rows]


def list_reference_implementations(query: str = None, min_level: int = 0, limit: int = 50) -> dict:
    """v2.3 CodeSample discovery (2026-08-30), the browse-before-you-fetch
    companion to get_reference_implementation: that tool requires already
    knowing an exact-or-close method name, which is no help to a caller who
    doesn't yet know what exists. This one lists the index -- method name,
    origin paper, publication year, verification level, language -- with
    no source code attached, so scanning it costs nothing like fetching
    584 full samples would. Same unbacked-level discipline as get_reference_implementation:
    a level with no verification_report behind it is represented as 0, no
    matter what the node claims (2026-08-28 incident this exists to never
    repeat). query does a case-insensitive substring match against method
    name AND paper title (e.g. "diffusion" surfaces both a method literally
    named that and any paper title containing it); omit it to browse
    everything. limit is capped at 200 to keep the response a scan, not a
    dump -- default 50 is a first page, not a promise there's no more."""
    limit = max(1, min(int(limit), 200))
    q = """
        MATCH (p:Paper)-[:PROPOSES]->(m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
        RETURN m.name AS method, m.origin_arxiv_id AS origin, p.title AS paper_title,
               p.year AS year, cs.language AS language, cs.verification_level AS level,
               cs.verification_report AS report, cs.code_sha256 AS sha
        ORDER BY cs.verification_level DESC, m.name ASC
    """
    with _get_session() as session:
        rows = session.run(q).data()
    # The browse index is a retrieval surface too: leaving a held-out method
    # listed here would tell the subject the catalog holds exactly what it was
    # asked for, and send it to a fetch that then refuses. The hold-out has to
    # be invisible, not merely unfetchable.
    rows = [r for r in rows if not benchmark_holdout.blocks(r.get("sha"))]

    # TOKEN MATCHING, not whole-string containment. The A/B run (2026-08-31)
    # traced all three in-catalog graph-arm failures to one root cause here:
    # a query of "IS-MBPG momentum" against a catalog holding "IS-MBPG*"
    # returned total_matching: 0, because the whole string is not a substring.
    # One token of query slop manufactured a false "not in catalog", and a
    # rational agent stopped looking -- the failure was ours, not the model's.
    #
    # The ergonomic requirement is sharper than better recall: this tool must
    # NEVER report 0 when it holds a near match. A zero is read as absence and
    # ends the search; a ranked partial keeps it alive.
    def _toks(t):
        return [x for x in re.split(r"[^a-z0-9]+", (t or "").lower()) if x]

    q_toks = _toks(query)
    # A near match earns its place on DISTINCTIVE overlap. Scoring raw token
    # hits let a row that shares only "method" or "model" surface as a near
    # match, which is noise dressed as a lead -- same defect the get resolver
    # had, so both now score against _significant_tokens.
    q_sig = set(_significant_tokens(query)) if query else set()
    items, partial = [], []
    for r in rows:
        lvl = int(r["level"] or 0)
        if r.get("report") is None:
            lvl = 0
        if lvl < min_level:
            continue
        item = {
            "method": r["method"],
            "origin_arxiv_id": r["origin"],
            "paper_title": r["paper_title"],
            "year": r["year"],
            "language": r["language"],
            "verification_level": lvl,
        }
        if not q_toks:
            items.append(item)
            continue
        hay = f"{r['method'] or ''} {r['paper_title'] or ''}".lower()
        hay_toks = set(_toks(hay))
        hit = sum(1 for t in q_toks if t in hay_toks or t in hay)
        sig_hit = sum(1 for t in q_sig if t in hay_toks or t in hay)
        if hit == len(q_toks):
            items.append(item)
        elif sig_hit:
            # rank on distinctive overlap; a purely generic overlap scores 0
            # and is dropped rather than offered as a lead.
            partial.append(({**item, "matched_tokens": hit,
                             "of_tokens": len(q_toks),
                             "matched_distinctive": sig_hit,
                             "of_distinctive": len(q_sig)}, sig_hit))

    out = {
        "total_matching": len(items),
        "returned": min(len(items), limit),
        "implementations": items[:limit],
    }
    if q_toks and not items and partial:
        partial.sort(key=lambda x: -x[1])
        out["near_matches"] = [p for p, _ in partial[:limit]]
        out["note"] = (
            f"No entry matched all {len(q_toks)} query tokens, but "
            f"{len(partial)} matched some. This is NOT an empty catalog -- see "
            f"near_matches and retry with a shorter query (e.g. just the method "
            f"name without qualifiers).")
    return out


def get_paper(id_or_title: str) -> dict:
    with _get_session() as session:
        link = _resolve_or_raise(session, id_or_title)
        result = templates.t1_paper_lookup(session, link.node_id)
        if result is None:
            raise ValueError(f"no paper found for '{id_or_title}'")
        return {**result, **_verified_impls_for_paper(session, link.node_id)}


def get_code_for_paper(id_or_title: str) -> dict:
    with _get_session() as session:
        link = _resolve_or_raise(session, id_or_title)
        # The 18/24-run path. A caller here has already said "I want this
        # paper's code" -- withholding the verified implementation at exactly
        # this moment and hoping they call a second tool is the defect the
        # benchmark measured.
        return {"arxiv_id": link.node_id,
                "repos": templates.t2_code_for_paper(session, link.node_id),
                **_verified_impls_for_paper(session, link.node_id)}


TOOLS = {
    "syntology_get_paper": get_paper,
    "syntology_get_code_for_paper": get_code_for_paper,
    "syntology_get_code_for_method": get_code_for_method,
    "syntology_get_reference_implementation": get_reference_implementation,
    "syntology_list_reference_implementations": list_reference_implementations,
    "syntology_compose": compose,
}


if __name__ == "__main__":
    # Tiny live smoke: list 3, fetch 1, and exercise the fallback path.
    print(json.dumps(list_reference_implementations(min_level=3, limit=3), indent=1)[:800])


# --- PROPOSED: have(x) -- the ask-shaped coverage check ------------------------
# (2026-09-03, user decision; HAVE_TOOL_PROPOSAL.md). Not in TOOLS on purpose:
# adding it would change the benchmark arms' roster mid-freeze. It lives here so
# it can be exercised against the live graph before the serving lane lifts it.
_ARXIV_ID = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")


def _method_rows(session, name: str):
    return session.run("""
        MATCH (m:Method) WHERE m.name_lower = toLower($name)
        OPTIONAL MATCH (m)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
        RETURN m.name AS method, m.origin_arxiv_id AS origin,
               collect({lvl: cs.verification_level, backed: cs.verification_report IS NOT NULL}) AS impls
    """, name=name).data()


def _best_backed_level(impls):
    best = None
    for i in impls or []:
        if i.get("lvl") is None:
            continue
        lvl = int(i["lvl"]) if i.get("backed") else 0
        best = lvl if best is None else max(best, lvl)
    return best



def _harvested_pointers(session, arxiv_id: str, limit: int = 5) -> list:
    """Repos we harvested code FROM, as pointers. Never the code itself.

    WHY THIS EXISTS (2026-09-15). have() answered `no_code` for 14,959 methods
    whose paper has harvested code sitting in the graph with a working GitHub
    link on it -- 16.9% of all methods, against the 3.19% that hold a verified
    implementation. Saying "no" while holding the authors' own repository URL
    is not honesty, it is a category error: **a link is not redistribution.**
    No licence is required to state where code lives, including -- especially --
    for the 68% of harvested samples whose repo declares no licence at all,
    because a pointer is then the only lawful way to surface them.

    So this returns repo, path, url, SPDX id and verification_level, and never
    a `code` field. `license_inline_ok` is reported so a caller can see at a
    glance whether it may copy what it is being pointed at; `upstream_license:
    null` means the repo declared none, which means look-do-not-reuse.

    verification_level is 0 by construction -- a repository does not come with
    evidence -- and is stated rather than implied, so this can never be read as
    a reference implementation. That distinction is the 313-node lesson.
    """
    rows = session.run("""
        MATCH (p:Paper {arxiv_id: $aid})-[:HAS_HARVESTED_IMPL]->(cs:CodeSample)
        WHERE cs.generated_by IS NOT NULL
        RETURN DISTINCT cs.generated_by AS repo, cs.source_path AS path,
               cs.upstream_license AS spdx, cs.license_inline_ok AS inline_ok,
               coalesce(cs.verification_level, 0) AS lvl
        ORDER BY (cs.upstream_license IS NULL), repo LIMIT $limit
    """, aid=arxiv_id, limit=limit).data()
    out = []
    for r in rows:
        out.append({
            "repo": r["repo"], "path": r["path"],
            "url": f"https://github.com/{r['repo']}/blob/HEAD/{r['path']}",
            "upstream_license": r["spdx"],
            "may_reuse": bool(r["inline_ok"]),
            "verification_level": r["lvl"],
            "what_this_is": ("code from the authors' own repository for this paper, "
                             "UNVERIFIED and not checked to implement this method"),
            "what_you_may_do": ("read it" if not r["inline_ok"]
                                else f"read and reuse it under {r['spdx']}"),
        })
    return out

def _have_method(session, name: str) -> dict:
    """Method branch of have(x). Three edges this MUST get right (found by
    probing the first shipped version, 2026-09-03):
      1. Same-name collisions: 80 method names are shared by several nodes
         where at least one holds code ("DUET", "DASH", ...). Taking the first
         row could report the code-less twin. Every homonym is aggregated.
      2. Exact match must not short-circuit siblings: "IS-MBPG" (no code) is one
         character from "IS-MBPG*" (V3, same paper). A no_code answer always
         carries code_nearby -- same-paper implemented methods and token-sibling
         methods that hold code -- and asserts absence only for the exact name.
      3. Token resolution is WHOLE-token and covered: a candidate resolves only
         if every distinctive token of ITS name appears in the query (an extra
         qualifier in the query resolves; a more specific variant does not), so
         "IS-MBPG momentum" -> IS-MBPG*, but "LoRA" does not become FLORA
         (substring) or LoRA-Flow (extra token). Those are near_matches only.
    unknown_name never asserts absence; it says the name did not match."""
    def toks(s):
        return set(_significant_tokens(s))
    def raw_toks(s):
        # Candidate side: keep EVERY token, short and generic alike. Dropping
        # short ones made "LoRA-X" look identical to "LoRA"; dropping generic
        # ones let "low-rank adaptation module" absorb "Low-Rank Adaptation" and
        # answer no_code for a method the graph does not hold under any name.
        # A candidate resolves only when the query says everything its name
        # says; anything less is a near_match, never an assertion of absence.
        return {t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if t}
    rows = _method_rows(session, name)
    resolved_via, siblings, near = None, [], []
    q_toks = toks(name)
    if not rows and q_toks:
        cand = session.run("""
            MATCH (m:Method)
            WITH m, size([t IN $toks WHERE m.name_lower CONTAINS t]) AS hits
            WHERE hits > 0
            OPTIONAL MATCH (m)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
            RETURN m.name AS method, count(cs) AS n_impl, hits
            ORDER BY hits DESC, size(m.name) LIMIT 60
        """, toks=list(q_toks)).data()
        scored = []
        for c in cand:
            c_toks = raw_toks(c["method"])
            if not c_toks:
                continue
            covered = c_toks <= q_toks                      # candidate fully covered, short tokens included
            overlap = len(c_toks & q_toks) / len(q_toks)    # share of the query matched
            if covered and overlap >= 0.5:
                scored.append((len(c_toks & q_toks), 0 if c["n_impl"] > 0 else 1,
                               len(c["method"]), c["method"]))
        near = [{"method": c["method"], "has_code": c["n_impl"] > 0}
                for c in cand if toks(c["method"]) & q_toks][:8]
        if scored:
            scored.sort(key=lambda x: (-x[0], x[1], x[2]))
            resolved_via = scored[0][3]
            rows = _method_rows(session, resolved_via)
            siblings = [x[3] for x in scored[1:4] if x[0] == scored[0][0]]
    if not rows:
        return {"have": "unknown_name", "kind": "method", "absence_asserted": False,
                "near_matches": near,
                "note": (f"'{name}' matched no method name in the graph. This is a "
                         f"name-match failure, not a statement that the method is absent "
                         f"-- try the canonical paper name or an arXiv id."
                         + (" Nearby names are listed; ask again with one of them." if near else ""))}
    # Aggregate every same-name node: answer for the best code-bearing one.
    per = []
    for r in rows:
        per.append((_best_backed_level(r["impls"]), r))
    with_code = [(l, r) for l, r in per if l is not None]
    best_lvl, r = max(with_code, key=lambda x: x[0]) if with_code else (None, rows[0])
    out = {"kind": "method",
           "resolved_to": {"method": r["method"], "origin_arxiv_id": r["origin"]}}
    if len(rows) > 1:
        out["homonyms"] = [{"origin_arxiv_id": rr["origin"],
                            "code_level": _best_backed_level(rr["impls"])} for _, rr in per]
        out["note_homonyms"] = (f"{len(rows)} distinct methods share the name "
                                f"'{r['method']}'; the answer below is for the one that "
                                f"holds code, attributed to its own paper. Check origin_arxiv_id.")
    if resolved_via:
        out["resolved_via_token_match"] = True
        out["note_resolution"] = (f"'{name}' did not match exactly; resolved by whole-token "
                                  f"overlap to '{r['method']}'. Confirm this is the method you meant.")
        if siblings:
            out["also_matched"] = siblings
    if best_lvl is not None and best_lvl >= 2:
        out.update(have="verified_code", verification_level=best_lvl, absence_asserted=False,
                   retrieve_with=f"get_reference_implementation(name={r['method']!r})",
                   note=(f"Yes: a machine-verified implementation of '{r['method']}' is stored "
                         f"here at level V{best_lvl} (report-backed). Fetch it with the call above."))
    elif best_lvl is not None:
        out.update(have="unverified_code", verification_level=best_lvl, absence_asserted=False,
                   retrieve_with=f"get_reference_implementation(name={r['method']!r}, min_level={best_lvl})",
                   note=(f"Code for '{r['method']}' is stored here but only at level V{best_lvl} -- "
                         f"present and callable, NOT executed against held-out tests. Treat as a "
                         f"starting point; lowering min_level is a deliberate choice."))
    else:
        alt = _best_available_for_method(session, r["method"]) or {}
        nearby = []
        if r["origin"]:
            same_paper = _verified_impls_for_paper(session, r["origin"]).get(
                "verified_reference_implementations") or []
            nearby += [{"method": i["method"], "verification_level": i["verification_level"],
                        "relation": "same_paper", "retrieve_with": i["retrieve_with"]}
                       for i in same_paper if i["method"].lower() != r["method"].lower()]
        if q_toks:
            sib = session.run("""
                MATCH (m:Method)-[:HAS_REFERENCE_IMPL]->(cs:CodeSample)
                WHERE m.name_lower <> toLower($exact)
                  AND any(t IN $toks WHERE m.name_lower CONTAINS t)
                RETURN m.name AS method, m.origin_arxiv_id AS origin,
                       max(CASE WHEN cs.verification_report IS NOT NULL
                                THEN cs.verification_level ELSE 0 END) AS lvl
                ORDER BY size(m.name) LIMIT 12
            """, exact=r["method"], toks=list(q_toks)).data()
            seen = {n["method"].lower() for n in nearby}
            for s_ in sib:
                if toks(s_["method"]) & q_toks and s_["method"].lower() not in seen:
                    nearby.append({"method": s_["method"], "origin_arxiv_id": s_["origin"],
                                   "verification_level": int(s_["lvl"] or 0),
                                   "relation": "shares_name_tokens",
                                   "retrieve_with": f"get_reference_implementation(name={s_['method']!r})"})
            nearby = nearby[:6]
        note = (f"No code under the exact name '{r['method']}' (paper arXiv:{r['origin']}). "
                f"{alt.get('what_this_means', '')}").strip()
        if nearby:
            note += (f" HOWEVER, code IS stored for related methods -- see code_nearby "
                     f"(e.g. '{nearby[0]['method']}', V{nearby[0]['verification_level']}); "
                     f"check whether one of them is what you mean before concluding absence.")
        ptrs = _harvested_pointers(session, r["origin"]) if r.get("origin") else []
        if ptrs:
            n_reuse = sum(1 for x in ptrs if x["may_reuse"])
            note += (f" We DO hold the authors' repository for this paper: see "
                     f"harvested_pointers ({len(ptrs)} link(s), {n_reuse} under a "
                     f"licence that permits reuse). Pointers only -- no code is "
                     f"served here and none of it has been run.")
        out.update(have="no_code", absence_asserted="for_this_exact_name_only",
                   tier=("repo_known" if ptrs else alt.get("tier", "paper_only")),
                   fallback=alt or None, code_nearby=nearby,
                   harvested_pointers=ptrs or None, note=note)
    return out


def _have_paper(session, ident: str) -> dict:
    link = linker.resolve(session, ident)
    if link.status == "not_found":
        return {"have": "unknown_name", "kind": "paper", "absence_asserted": False,
                "note": f"'{ident}' did not resolve to a paper in the graph -- a non-match, not a statement that the paper is absent."}
    if link.status == "ambiguous":
        return {"have": "unknown_name", "kind": "paper", "absence_asserted": False,
                "candidates": [c.get("title") for c in link.candidates][:5],
                "note": f"'{ident}' matches more than one paper; pick one of the candidates."}
    impls = _verified_impls_for_paper(session, link.node_id)
    out = {"kind": "paper", "resolved_to": {"arxiv_id": link.node_id}}
    lst = impls.get("verified_reference_implementations") or []
    best = max([i["verification_level"] for i in lst], default=None)
    if best is not None and best >= 2:
        out.update(have="verified_code", verification_level=best, implementations=lst,
                   absence_asserted=False, note=impls.get("note"))
    elif best is not None:
        out.update(have="unverified_code", verification_level=best, implementations=lst,
                   absence_asserted=False, note=impls.get("note"))
    else:
        repos = templates.t2_code_for_paper(session, link.node_id)
        out.update(have="no_code", tier="repo_known" if repos else "paper_only",
                   absence_asserted="for_this_paper_only", declared_repos=repos or None,
                   note=("No: this paper is in the graph but none of its methods has a stored "
                         "implementation." + (" Its declared repositories are listed -- pointers, "
                                              "nothing here has been run." if repos else "")))
    return out


def have(x: str) -> dict:
    """Do you have X? X is a method name, an arXiv id, or a paper title.
    Answers honestly with no code payload: verified_code / unverified_code /
    no_code / unknown_name, distinguishing 'we hold no code for this' from
    'we could not match this name'. Free."""
    x = (x or "").strip()
    with _get_session() as session:
        if _ARXIV_ID.match(x):
            out = _have_paper(session, x)
        elif _method_rows(session, x):
            out = _have_method(session, x)          # exact method name wins
        else:
            # RESOLUTION ORDER MATTERS: paper resolver BEFORE token fallback.
            # "Attention Is All You Need" token-matched to DIAYN on 4/5 shared
            # words when the method path ran first; a title must reach the
            # paper resolver before any fuzzy method match is attempted.
            out = _have_paper(session, x)
            if out["have"] == "unknown_name":
                out = _have_method(session, x)      # token fallback, last
    out["query"] = x
    out["cost"] = "free"
    # Telemetry is handed the finished verdict and cannot reach the response:
    # record() takes a copy, never raises, and returns nothing. A serving path
    # must not answer differently because logging had a bad day.
    try:
        import demand_log
        demand_log.record(x, dict(out), surface="have")
    except Exception:                                            # noqa: BLE001
        pass
    return out


PROPOSED_TOOLS = {"syntology_have": have}
