#!/usr/bin/env python3
"""
The `code_only` benchmark arm: 118,400 CodeSamples served FLAT.

THE QUESTION THIS ARM EXISTS TO ANSWER. Every arm this benchmark has ever
run tested the graph together with the code (`syntology`, `both`), or
neither (`none`, `search`). The owner's actual question is narrower and
sharper: *given* that the CodeSamples exist, is the graph load-bearing for
DISCOVERY? Answering it needs an arm that has the code and nothing else.
This is that arm.

WHAT IS REMOVED, relative to syntology_arm_tools.py:
  - :Method nodes entirely. No method names, no name resolution, no
    near-match ladder over a curated method vocabulary.
  - :Paper nodes entirely. No titles, abstracts, authors, reviews, years.
  - Every relationship. PROPOSES, HAS_REFERENCE_IMPL, CITES, COMPOSED_OF
    are never traversed; no query in this file contains a `-[`.
  - compose() -- typed tensor contracts and partner discovery.
  - The inline `verified_reference_implementations` structural fix, which
    is a Paper->Method->CodeSample traversal grafted onto a paper tool.
  - have(), neighborhoods, explore_paths.

WHAT IS KEPT, because it is a property of the code artifact and not of the
graph: the source, the entry name, the signature, the language, the
verification level AND its report, the test cases the level was measured
on, and `paper_attribution` -- the origin arXiv id, denormalised onto the
node by the harvester. Attribution is not optional in this product.

TWO DISCLOSED ASYMMETRIES, both in PREREGISTRATION_CODE_ONLY.md:
  1. `paper_attribution` is searchable. The graph arm reaches the same
     artifact from an arXiv id via get_code_for_paper, so withholding the
     flat equivalent would be tuning this arm to lose -- which the brief
     forbids more strongly than it forbids tuning it to win. Every hit that
     matched on the origin id is tagged `origin_id` in `matched_by`, so the
     analysis can report the result with and without that route.
  2. The task prompt gives the subject the exact entry function name (it
     has to: the referee imports and calls it). A flat code index is
     naturally queried by function name, so this arm can exact-match on a
     key the graph arm cannot use. The graph arm gets the method name,
     which its resolvers key on exactly. Both arms are handed their own
     natural key by the same prompt; that is the symmetry, and it is
     disclosed rather than engineered away.

R2 discipline is identical to the graph arm's: a verification_level with
no verification_report behind it is reported as 0, no matter what the node
claims. 313 CodeSamples were once served as machine-verified on a
hardcoded 3; this must not become a fourth surface where that can happen.

Read-only: NEO4J_USER is the read credential and nothing here writes.
"""
from __future__ import annotations

import json
import math
import os
import pickle
import re
import sys
import threading
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("BENCH_REPO_ROOT", HERE.parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402

import benchmark_holdout  # noqa: E402

INDEX_DIR = Path(os.environ.get("CODE_ONLY_INDEX", REPO / "code_index"))
BM25_K1, BM25_B = 1.2, 0.75
RRF_K = 60.0

_lock = threading.Lock()
_driver = None
_lex = None
_vecs = None
_bedrock = None
_entry_exact: dict[str, list[int]] | None = None
_sha_row: dict[str, int] | None = None


# --- shared plumbing ---------------------------------------------------------

def _get_session():
    global _driver
    with _lock:
        if _driver is None:
            from neo4j import GraphDatabase
            _driver = GraphDatabase.driver(
                os.environ["NEO4J_URI"],
                auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    return _driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j"))


def _load_index():
    """Lexicon + the full vector matrix, once per process.

    The matrix is mmap'd, not read: 485 MB paged in on demand and shared by
    every worker thread in the process, so two workers cost one copy.
    Vector row i corresponds to lexicon row i -- both artifacts are built
    with the same `ORDER BY c.code_sha256` cursor, and the alignment is
    asserted below rather than assumed (R10).
    """
    global _lex, _vecs, _entry_exact, _sha_row
    with _lock:
        if _lex is None:
            with (INDEX_DIR / "lexicon.pkl").open("rb") as fh:
                lex = pickle.load(fh)
            ex = defaultdict(list)
            for i, e in enumerate(lex["entry"]):
                ex[_norm(e)].append(i)
            _entry_exact = dict(ex)
            _sha_row = {sh: i for i, sh in enumerate(lex["sha"])}
            vp, sp = INDEX_DIR / "all_vectors.npy", INDEX_DIR / "all_shas.json"
            if vp.exists() and sp.exists():
                shas = json.loads(sp.read_text(encoding="utf-8"))
                if shas != lex["sha"]:
                    raise RuntimeError(
                        "all_shas.json and lexicon.pkl disagree on row order -- "
                        "rebuild both (build_code_index.py, build_code_vectors.py); "
                        "a misaligned vector matrix would return code for a "
                        "different sample than the one it ranked")
                _vecs = np.load(vp, mmap_mode="r")
            _lex = lex
    return _lex


def _get_bedrock():
    global _bedrock
    with _lock:
        if _bedrock is None:
            import bedrock_client
            _bedrock = bedrock_client.client()
    return _bedrock


def _blocked_rows() -> set:
    """Index rows the substitution experiment's hold-out removes, if any.

    Empty whenever no hold-out is installed on this thread, which is every
    v1.5 run and every offline probe -- so this is a no-op unless the
    substitution experiment turns it on (parity asserted by
    verify_holdout.py check P against the committed probe output).

    Filtering happens BEFORE ranking, not after. Removing rows from a
    finished ranked list would leave the excluded sample occupying a rank
    slot and hand the subject a short page -- an observable footprint of the
    hold-out, and a distorted ranking for everything below it.
    """
    ho = benchmark_holdout.active()
    if not ho:
        return set()
    _load_index()
    return {_sha_row[s] for s in ho if s in _sha_row}


_TOK = re.compile(r"[a-z0-9]+")


def _norm(s: str) -> str:
    return "".join(_TOK.findall((s or "").lower()))


def _tokenize(text: str) -> list[str]:
    """Same tokenisation as build_code_index.tokenize -- imported rather
    than re-typed would be better, but the builder imports neo4j at module
    scope and this module must load in a subject process. R10: the shapes
    are asserted by qc_code_only_index.py, which tokenises one record both
    ways and fails if they diverge."""
    out = []
    for t in _TOK.findall((text or "").lower()):
        out.append(t)
    for piece in re.findall(r"[A-Za-z][a-z0-9]*|[0-9]+", text or ""):
        p = piece.lower()
        if p and p not in out:
            out.append(p)
    return out


# --- lexical half ------------------------------------------------------------

def _bm25(query: str, min_level: int, cap: int,
          no_origin: bool = False) -> list[tuple[int, float, set]]:
    lex = _load_index()
    blocked = _blocked_rows()
    postings, doclen = lex["postings"], lex["doclen"]
    N = lex["n_docs"]
    avgdl = float(doclen.mean()) if N else 1.0
    generic = set(lex["generic_tokens"])

    toks = _tokenize(query)
    sig = [t for t in toks if t not in generic and len(t) > 1]
    # Drop generic tokens ONLY when something distinctive survives: a query
    # that is nothing but common words still deserves its best answer rather
    # than an empty result. This is the same rule the graph arm's resolvers
    # use, and it exists because scoring on "method"/"model" once resolved a
    # totally absent method to an unrelated one.
    use = sig or toks
    if no_origin:
        # The asymmetry-1 counterfactual (analysis only, never exposed as a
        # tool parameter): drop the numeric tokens that can only be reaching
        # the denormalised origin arXiv id, so the probe can report retrieval
        # WITHOUT that route.
        # No `or use` fallback: a query that is ONLY an arXiv id must come
        # back lexically empty under the counterfactual, or the counterfactual
        # silently measures the route it was meant to remove.
        use = [t for t in use if not (t.isdigit() and len(t) >= 4)]
    seen = defaultdict(float)
    matched = defaultdict(set)
    for t in set(use):
        p = postings.get(t)
        if p is None:
            continue
        ids, tfs = p
        df = len(ids)
        if df > N * 0.30:          # a token in a third of the corpus carries nothing
            continue
        idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
        dl = doclen[ids].astype(np.float32)
        tf = tfs.astype(np.float32)
        s = idf * (tf * (BM25_K1 + 1)) / (tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / avgdl))
        for i, v in zip(ids, s):
            seen[int(i)] += float(v)
            matched[int(i)].add(t)
    lvl = lex["level"]
    rows = []
    for i, v in seen.items():
        if lvl[i] < min_level or i in blocked:
            continue
        # Split the route, because asymmetry 1 in the pre-registration turns
        # on it: a hit carried ONLY by the denormalised origin arXiv id is a
        # different claim about flat retrieval than one carried by the code.
        # `matched[i]` holds the tokens that actually scored, so this is the
        # real route rather than a guess from the query string.
        norigin = _norm(lex["origin"][i])
        hit_toks = matched[i]
        by_origin = {t for t in hit_toks
                     if norigin and len(t) >= 4 and t in norigin}
        how = set()
        if by_origin:
            how.add("origin_id")
        if hit_toks - by_origin:
            how.add("keyword")
        rows.append((i, v, how))
    rows.sort(key=lambda r: -r[1])
    return rows[:cap]


# --- semantic half -----------------------------------------------------------

def _semantic(query: str, min_level: int, cap: int) -> list[tuple[int, float]]:
    """Exhaustive cosine over the whole corpus, in the same Titan v2 space
    the corpus was embedded in (`generate_code_embeddings.py`: entry + code,
    1024 dims, normalized).

    Brute force, not ANN. Two reasons, both in build_code_vectors.py: the
    read credential cannot execute `db.index.vector.queryNodes`, and exact
    ranking over the whole corpus is the only way a min_level filter stays
    meaningful when the filtered slice is 2.6% of the rows.
    """
    import bedrock_client
    vec = np.asarray(bedrock_client.embed_titan(_get_bedrock(), query),
                     dtype=np.float32)
    n = np.linalg.norm(vec)
    if n:
        vec = vec / n
    lex = _load_index()
    if _vecs is None:
        raise RuntimeError("all_vectors.npy missing -- run build_code_vectors.py")
    sims = np.asarray(_vecs @ vec, dtype=np.float32)
    if min_level > 0:
        sims = np.where(lex["level"] >= min_level, sims, -2.0)
    blocked = _blocked_rows()
    if blocked:
        sims = np.array(sims, copy=True)
        sims[list(blocked)] = -2.0
    take = min(cap, sims.shape[0])
    part = np.argpartition(-sims, take - 1)[:take]
    part = part[np.argsort(-sims[part])]
    return [(int(i), float(sims[i])) for i in part if sims[i] > -2.0]


# --- the two tools -----------------------------------------------------------

def code_search(query: str, limit: int = 15, min_level: int = 0, *,
                no_origin: bool = False) -> dict:
    """Hybrid lexical + semantic search over the flat CodeSample table.

    Fusion is reciprocal-rank (RRF, k=60) rather than a tuned score blend:
    RRF needs no per-corpus calibration, which means nothing in this arm was
    fitted on the benchmark's own tasks. An exact entry-name match is pinned
    above the fused list, because that is what every code index does and
    burying it would be a deliberate handicap.
    """
    lex = _load_index()
    limit = max(1, min(int(limit), 50))
    min_level = max(0, min(int(min_level), 3))
    cap = 200

    lexical = _bm25(query, min_level, cap, no_origin=no_origin)

    sem_err = None
    try:
        semantic = _semantic(query, min_level, cap)
    except Exception as e:               # noqa: BLE001 -- reported, not swallowed
        semantic, sem_err = [], f"{type(e).__name__}: {e}"

    fused: dict[int, float] = defaultdict(float)
    how: dict[int, set] = defaultdict(set)
    for rank, (i, _s, h) in enumerate(lexical):
        fused[i] += 1.0 / (RRF_K + rank + 1)
        how[i] |= h
    lvl = lex["level"]
    for rank, (i, _s) in enumerate(semantic):
        fused[i] += 1.0 / (RRF_K + rank + 1)
        how[i].add("semantic")

    # exact entry-name match pinned first
    blocked = _blocked_rows()
    pinned = []
    for i in _entry_exact.get(_norm(query), []):
        if lvl[i] >= min_level and i not in blocked:
            pinned.append(i)
            how[i].add("entry_exact")
    order = pinned + [i for i, _ in sorted(fused.items(), key=lambda kv: -kv[1])
                      if i not in set(pinned)]

    items = []
    for i in order[:limit]:
        items.append({
            "code_sha256": lex["sha"][i],
            "entry": lex["entry"][i],
            "language": lex["language"][i],
            "source_kind": lex["source_kind"][i],
            "verification_level": int(lvl[i]),
            "origin_arxiv_id": lex["origin"][i] or None,
            "code_chars": int(lex["code_len"][i]),
            "matched_by": sorted(how[i]),
            "fetch_with": f"code_get(code_sha256={lex['sha'][i]!r})",
        })
    out = {"query": query, "total_ranked": len(order), "returned": len(items),
           "results": items,
           "corpus": {"code_samples": lex["n_docs"],
                      "at_or_above_min_level": int((lvl >= min_level).sum())}}

    # A quality FACET on the same ranking, not a second search. 115,574 of the
    # 118,400 samples are harvested at level 0, so an unfiltered ranking can
    # bury the machine-verified answer under near-duplicates from public
    # repositories. Any faceted code search does this; withholding it would
    # handicap the arm against a graph catalog that is verified-only by
    # construction (1,179 methods, all with an implementation). Disclosed in
    # PREREGISTRATION_CODE_ONLY.md.
    if min_level < 2:
        ver = [i for i in order if lvl[i] >= 2][:5]
        if ver:
            out["verified_matches"] = [{
                "code_sha256": lex["sha"][i], "entry": lex["entry"][i],
                "verification_level": int(lvl[i]),
                "origin_arxiv_id": lex["origin"][i] or None,
                "matched_by": sorted(how[i]),
                "fetch_with": f"code_get(code_sha256={lex['sha'][i]!r})",
            } for i in ver]
            out["verified_note"] = (
                f"{len(ver)} of the ranked matches are machine-verified (level "
                f"2 or 3: executed against held-out tests, report attached). "
                f"They are listed separately because {lex['n_docs'] - int((lvl >= 2).sum())} "
                f"of the {lex['n_docs']} samples here are unverified harvested "
                f"code and can outrank them on wording alone.")
    if not items:
        out["note"] = (
            "Nothing matched. This index holds function-level code samples "
            "only -- it has no papers, no abstracts and no method vocabulary, "
            "so a query phrased as a paper title will do worse here than the "
            "function's own name or a description of what the code computes. "
            "Try the entry function name, or fewer words.")
    if sem_err:
        # R3d: a source that did not answer is not a source that answered
        # nothing. If the embedding call failed, the caller is told the
        # ranking is lexical-only rather than being handed a short list that
        # looks complete.
        out["degraded"] = (f"semantic half unavailable ({sem_err}); these "
                           f"results are lexical-only")
    return out


def code_get(code_sha256: str) -> dict:
    """Fetch one code sample by its identity.

    Identity is code_sha256, not the entry name: 386 of 1,179 served entry
    names collide across distinct samples, so an entry-keyed fetch is a
    silent wrong-answer generator. An entry name is accepted as a
    convenience and returns EVERY sample carrying it, plainly labelled,
    rather than picking one.
    """
    lex = _load_index()
    key = (code_sha256 or "").strip()
    # Resolve against the index's own sha set, not a length/charset regex.
    # Harvested samples carry a 16-hex code_sha256 and generated ones a
    # 64-hex one (115,574 vs 2,826) -- a regex written for one silently
    # rejects the other, and "not a sha" would then fall through to an entry
    # lookup that also misses, reporting absence for a sample we hold.
    # The hold-out is enforced HERE as well as in ranking, and it raises the
    # same message an unknown sha raises. A distinct "held out" error would
    # tell the subject an exact answer exists and is being withheld -- a
    # different experiment, and one whose leak would not be obvious in a
    # transcript. Indistinguishable from absence is the requirement.
    blocked = _blocked_rows()
    blocked_shas = {lex["sha"][i] for i in blocked}
    if key in _sha_row and key not in blocked_shas:
        shas = [key]
    elif key.lower() in _sha_row and key.lower() not in blocked_shas:
        shas = [key.lower()]
    else:
        hits = [i for i in _entry_exact.get(_norm(key), []) if i not in blocked]
        if not hits:
            raise ValueError(
                f"'{key}' is neither a code_sha256 nor an entry name in this "
                f"index. Identity here is code_sha256; use code_search first "
                f"and pass the code_sha256 it returns.")
        shas = [lex["sha"][i] for i in hits[:5]]

    with _get_session() as s:
        rows = s.run("""
            MATCH (c:CodeSample) WHERE c.code_sha256 IN $shas
            RETURN c.code_sha256 AS sha, c.entry AS entry, c.code AS code,
                   c.signature AS signature, c.language AS language,
                   c.source_kind AS source_kind,
                   c.verification_level AS level,
                   c.verification_report AS report,
                   c.test_cases AS test_cases,
                   c.test_cases_provenance AS test_cases_provenance,
                   c.env AS env, c.generated_by AS generated_by,
                   c.cross_checked_by AS cross_checked_by,
                   c.spec_review AS spec_review, c.review_note AS review_note,
                   c.paper_attribution AS origin,
                   c.embedding_truncated AS embedding_truncated
        """, shas=shas).data()
    if not rows:
        raise ValueError(f"no code sample with code_sha256 '{key}'")

    def _j(v):
        if v is None:
            return None
        try:
            return json.loads(v)
        except (TypeError, ValueError):
            return v

    out = []
    for r in rows:
        lvl = int(r["level"] or 0)
        if r["report"] is None:
            lvl = 0
        out.append({
            "code_sha256": r["sha"], "entry": r["entry"],
            "signature": r["signature"], "language": r["language"],
            "source_kind": r["source_kind"],
            "verification_level": lvl,
            "verification_report": _j(r["report"]),
            "test_cases": _j(r["test_cases"]),
            "test_cases_provenance": r["test_cases_provenance"],
            "env": _j(r["env"]), "generated_by": r["generated_by"],
            "cross_checked_by": r["cross_checked_by"],
            "spec_review": r["spec_review"],
            "review_note": r["review_note"] or None,
            "origin_arxiv_id": r["origin"],
            "code": r["code"],
            "attribution": (f"Reference implementation attributed to "
                            f"arXiv:{r['origin']}; reference code, not "
                            f"audited production code."),
        })
    res = {"samples": out}
    if len(out) > 1:
        res["note"] = (f"'{key}' is an entry NAME and {len(out)} distinct "
                       f"samples carry it. They are different code; pick by "
                       f"code_sha256.")
    return res


TOOLS = {
    "code_search": code_search,
    "code_get": code_get,
}


if __name__ == "__main__":
    from pprint import pprint
    q = sys.argv[1] if len(sys.argv) > 1 else "softmax with temperature"
    pprint(code_search(q, limit=5, min_level=int(sys.argv[2]) if len(sys.argv) > 2 else 0))
