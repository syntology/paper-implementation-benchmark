#!/usr/bin/env python3
"""
s2_api_key.py -- the ONE way this codebase reads SEMANTIC_SCHOLAR_API_KEY.

WHY THIS EXISTS (2026-08-29): user reported repeated, direct observation of
this key being loaded with literal quote characters (' or ") still attached
-- a malformed x-api-key header value that Semantic Scholar's API would
reject outright, or (worse, and harder to notice) silently treat as absent,
falling back every caller to the shared, heavily-contended public pool
despite a real key existing. That exact failure mode -- "authenticated"
logged true while every request behaves as if it weren't -- is already
documented once in this repo (04_resolve_citations.py's own 2026-08-24
comment, a different root cause: load_dotenv() never called at all).

Direct testing this session (both a plain load_dotenv()+os.environ.get()
and the exact subprocess shape 06_process_new_papers.py actually uses)
found the CURRENT .env value and the CURRENT standard load path both clean,
no quotes -- so this isn't reproduced by the obvious path today. That does
not make the report wrong: it was reported directly, this session cannot
inspect a live subprocess's actual environ on macOS to fully rule it out,
and of the 13 real call sites for this key across this repo, only ONE
(run_incremental_paper_sweep.sh, shell) already defends against exactly
this -- proving someone already hit this class of bug once for this exact
key and fixed it in exactly one of thirteen places. Hardening beats
continued hunting: this is a no-op on an already-clean value and a real
fix on a corrupted one, so there is no cost to applying it everywhere
rather than narrowing down which of the thirteen was ever actually guilty.
"""
from __future__ import annotations

import os


def get_s2_api_key(env: dict | None = None) -> str | None:
    """Read SEMANTIC_SCHOLAR_API_KEY, stripped of whitespace and any
    surrounding quote characters -- single OR double, and only if they
    genuinely wrap the whole value (a key that legitimately starts and
    ends with the same character, vanishingly unlikely for an S2 key's
    real `s2k-...` shape, would not be mangled by this since both ends
    must match the same quote character to be stripped).

    `env` is injectable for tests only; real callers use the default
    (`os.environ`, read fresh on every call rather than cached at import
    time, so a `load_dotenv()` that runs after this module is imported
    is still picked up)."""
    raw = (env if env is not None else os.environ).get("SEMANTIC_SCHOLAR_API_KEY")
    if raw is None:
        return None
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        v = v[1:-1].strip()
    return v or None


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    key = get_s2_api_key()
    if key is None:
        print("SEMANTIC_SCHOLAR_API_KEY not set (or empty after stripping).")
    else:
        print(f"key loaded, {len(key)} chars, {key[:4]}...{key[-4:]} "
             f"-- no leading/trailing quote characters remain.")
