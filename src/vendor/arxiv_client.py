#!/usr/bin/env python3
"""
arxiv_client -- arXiv's VOCABULARY. The clock, the lock and the session live in
`api_gateway.py`; this module owns none of them.

WHY THIS EXISTS, dated and ours. On 2026-09-03T16:51 `classify-paper-level-r3`
started; it rate-limits GitHub carefully (checks /rate_limit, sleeps on the real
remaining quota) and had NO arXiv throttle at all. It logged 442 rate-limit
responses before being stopped on 2026-09-08. arXiv blocklisted our User-Agent;
the daily ingest lane produced nothing for five days, correctly refusing to
claim it had seen zero new papers when it had been unable to ask
(ARXIV_BLOCK_2026-09-09.md).

WHY IT IS NOW A VIEW AND NOT A CLIENT (2026-09-10, owner-set). Writing a client
per service after that service refuses us is reactive by construction: S2
saturated our own quota the next day, and the next move would have been
`s2_client.py`, leaving the fifteenth host unprotected until it, too, stopped
answering. Policy became DATA in `api_gateway.POLICY`, one row per host. arXiv's
row is the same rules it always had -- 3.0s, one connection at a time, 403 is a
block and not a throttle -- and every guarantee this module made is now made by
the gateway for every host:

  * a per-host lock, so "a single connection at a time" holds even when two
    threads in one process both want arXiv;
  * a monotonic clock floor shared across every caller in the process;
  * a User-Agent that identifies us with a contact address, set on the session
    so no call site can omit it, and REFUSED if a caller passes its own;
  * `share_budget=N` for the cross-process hole, which is the exact hole the
    September incident went through and is still named rather than closed.

The four verbs stay, because a call site reading `arxiv_client.get({"id_list":
...})` says what it is doing better than a URL would:

    get(params)               the API query -- the common case
    get_url(url)              any other arXiv path, materialised
    head_url(url)             a HEAD (Content-Length), without pulling the body
    stream_url(url)           a streamed GET the caller consumes itself
    budget(share_budget=N)    the raw clock+lock, for a caller that must own
                              the response stream (pdf_fetch does)

`is_arxiv_url(url)` is how the two chokepoints whose URL is not knowable from
the source -- `pdf_fetch.fetch_pdf` and the benchmark's `fetch_url` tool --
decide at runtime whether the thing they were handed is arXiv's.

**arXiv'S TERMS ARE ABOUT THEIR SERVERS, NOT ONE PATH ON THEM** (widened
2026-09-09). The first migration routed the 18 `export.arxiv.org` call sites and
left `arxiv.org` itself alone: PDF pulls, a HEAD probe, an HTML fetch and an
agent-driven `fetch_url` tool, none of them holding any request-rate floor.
That is `qc_bedrock_discipline`'s old mistake exactly -- a gate reporting clean
while the identical defect lived one hostname over. The gateway's policy key is
the registrable domain for precisely this reason: `arxiv.org` matches
`export.arxiv.org` and `rss.arxiv.org` and anything else they put up.

FOUR NAMES HERE ARE NOT MODULE GLOBALS. `time`, `_session`, `_last` and
`MIN_INTERVAL` are read and written through to `api_gateway.state("arxiv.org")`
-- the one record the gateway actually paces arXiv with. That is not a
convenience: it is what makes this a view instead of a second mechanism.
`test_arxiv_client.py` sets `A.time = fake_clock` and `A._last = 0.0` and then
asserts on real behaviour, and those assignments have to reach the clock the
gateway uses or the tests would be proving something about a module nobody
calls. See `_ArxivRowView` at the bottom.
"""
from __future__ import annotations

import contextlib

import api_gateway

HOST = "arxiv.org"

API = "https://export.arxiv.org/api/query"      # https: http answers 301
ARXIV_HOSTS = ("arxiv.org",)                     # and any subdomain of it
UA = api_gateway.UA
BLOCK_MESSAGE = api_gateway.ARXIV_BLOCK_MESSAGE

# A 403 from arXiv. Not transient, not retryable, and not to be worked around by
# changing the User-Agent. It is `api_gateway.Blocked` under another name rather
# than a subclass, deliberately: "a service has refused us and it will not clear
# by retrying" is one fact with one correct response, and giving each host its
# own exception class invites a caller to handle arXiv's and let the next
# host's through.
ArxivBlocked = api_gateway.Blocked


def _row():
    """arXiv's row in the gateway: the clock, the lock, the session."""
    return api_gateway.state(HOST)


def _sess():
    """The shared session -- our identifier, on the gateway's record."""
    return api_gateway.session(HOST)


def is_arxiv_url(url: str) -> bool:
    """True if `url` names arXiv's servers (any host under arxiv.org).

    Exposed because two chokepoints have to decide, at runtime, whether a URL
    they were HANDED is arXiv's: `pdf_fetch.fetch_pdf` (whose URL comes out of
    an acquisition manifest -- arXiv for the daily lane, PMLR/CVF/ACL/AAAI for
    the venue lanes) and the benchmark's `fetch_url` tool (whose URL is chosen
    by the model under test). Neither can be decided by reading the source, so
    neither can be decided by a grep; they decide here, against the same host
    rule `_check_host` refuses on, so there is one definition of "an arXiv
    host" and not two."""
    import urllib.parse
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in ARXIV_HOSTS)


def _check_host(url: str) -> None:
    """`get_url` is not a general HTTP client. Without this a caller could route
    any request through arXiv's budget -- and past the discipline gate."""
    if not is_arxiv_url(url):
        import urllib.parse
        host = (urllib.parse.urlsplit(url).hostname or "").lower()
        raise ValueError(
            f"arxiv_client only calls arXiv; {host or url!r} is not an arXiv host. "
            f"This module's lock and clock are arXiv's rate budget, not a "
            f"general-purpose throttle -- do not borrow them. If that host is a "
            f"service we call, give it a row in api_gateway.POLICY and call "
            f"api_gateway.get().")


@contextlib.contextmanager
def budget(share_budget: int = 1):
    """Hold arXiv's rate budget for the duration of the block.

    Use it only when you must own the response STREAM. `pdf_fetch.fetch_pdf`
    does: its whole reason for existing is writing the body to a temp file and
    checking it against Content-Length, so it cannot hand the response back to
    a function that has already released the lock. Holding the lock across the
    body is stricter than `get_url`, not looser -- "one connection at a time"
    means for as long as the connection is open, and a 40 MB e-print holds one
    for a while.

    NOT re-entrant: calling `get`/`get_url` from inside a `budget()` block
    deadlocks, which is the correct shape for "one connection at a time"."""
    with api_gateway.budget(HOST, share_budget):
        yield


def raise_if_blocked(status_code: int) -> None:
    """The 403 refusal, in one place, for callers holding their own response.

    A caller that takes `budget()` gets the clock but not the status handling,
    and the one status that must never be re-interpreted per call site is 403 --
    the tempting local fix for it is a User-Agent change."""
    api_gateway.raise_if_blocked(HOST, status_code)


def get(params: dict, *, timeout: float = 90.0, share_budget: int = 1,
        max_attempts: int = 3):
    """One arXiv API call, never faster than the terms allow.

    share_budget: how many processes are calling arXiv concurrently. The floor
    becomes share_budget * MIN_INTERVAL, because the clock is process-local and
    four compliant shards are still four times the rate.

    Raises ArxivBlocked on 403 (never retried) and `api_gateway.Unanswered`
    once 429/5xx or transport failures exhaust `max_attempts`. Both mean
    UNANSWERED, which is not the same fact as "arXiv returned nothing" --
    callers feeding a completeness claim book them with `ledger.unanswered()`
    (R3d). Any other status, 400 included, is returned for the caller to judge.
    """
    return api_gateway.get(API, params, timeout=timeout, share_budget=share_budget,
                           max_attempts=max_attempts)


def get_url(url: str, params: dict | None = None, *, timeout: float = 90.0,
            share_budget: int = 1, max_attempts: int = 3):
    """Any arXiv endpoint (`/e-print/<id>`, `/abs/<id>`, ...) on the SAME budget
    as the API.

    The terms of use are about arXiv's servers, not about one path on them: a
    bulk e-print harvest is heavier than a metadata query, not lighter."""
    _check_host(url)
    return api_gateway.get(url, params or {}, timeout=timeout, share_budget=share_budget,
                           max_attempts=max_attempts)


def head_url(url: str, *, timeout: float = 30.0, share_budget: int = 1,
             max_attempts: int = 3):
    """HEAD one arXiv URL, on the same budget as everything else.

    `<INTERNAL>/probe_pdf_integrity.py` HEADs arXiv for
    Content-Length to tell a truncated local PDF from a complete one, and
    answering that with a GET would pull the whole multi-megabyte body it is
    explicitly not downloading. Redirects are followed (arXiv answers /pdf/<id>
    with a redirect to a version), so one call can be more than one request --
    the same as any GET, and the reason it holds a full budget slot."""
    _check_host(url)
    return api_gateway.head(url, {}, timeout=timeout, share_budget=share_budget,
                            max_attempts=max_attempts)


@contextlib.contextmanager
def stream_url(url: str, *, timeout=90.0, share_budget: int = 1,
               headers: dict | None = None):
    """A streamed GET on an arXiv URL, holding the budget across the body.

    For `pdf_fetch.fetch_pdf`, which must consume the response itself: it
    writes to a temp file, checks Content-Length and the %%EOF trailer, and
    only then renames into place. It cannot use `get_url`, which materialises
    the whole body before returning.

    This does NOT retry: pdf_fetch already owns retry/backoff for a short read,
    and two retry layers would multiply attempts against a service that has
    blocked us once. It does raise ArxivBlocked on 403, because that decision
    must never be re-made per call site."""
    _check_host(url)
    with api_gateway.stream(url, timeout=timeout, share_budget=share_budget,
                            headers=headers) as r:
        yield r


def healthy() -> tuple[bool, str]:
    """Are we still blocked? Cheap enough for a QC gate to call."""
    try:
        r = get({"search_query": "cat:cs.LG", "max_results": 1})
    except ArxivBlocked as e:
        return False, str(e)[:120]
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"[:120]
    return (r.status_code == 200 and "<entry>" in r.text), f"HTTP {r.status_code}"


# ---------------------------------------------------------------------------
# The view. `time`, `_session`, `_last` and `MIN_INTERVAL` are NOT module
# globals -- they are `api_gateway.state("arxiv.org")`'s fields, read and
# written through this module's name.
#
# Why go to this trouble rather than let arxiv_client keep its own clock: a
# module that keeps its own clock IS a second mechanism, whatever its docstring
# says, and the whole point of the 2026-09-10 consolidation is that there is
# one. Why not just rewrite the tests to poke the gateway: because
# `test_arxiv_client.py` is the written record of what we told arXiv in the
# unblock letter, and a promise re-tested against a rewritten test is not the
# same promise. It passes unchanged, against the gateway's real clock.
# ---------------------------------------------------------------------------
_PROXIED = ("time", "_session", "_last", "MIN_INTERVAL")


def _install_view() -> None:
    import sys
    import types

    class _ArxivRowView(types.ModuleType):
        def __getattr__(self, name):
            if name in _PROXIED:
                return getattr(api_gateway.state(HOST), name)
            raise AttributeError(f"module {self.__name__!r} has no attribute {name!r}")

        def __setattr__(self, name, value):
            if name in _PROXIED:
                setattr(api_gateway.state(HOST), name, value)
            else:
                super().__setattr__(name, value)

    sys.modules[__name__].__class__ = _ArxivRowView


_install_view()


if __name__ == "__main__":
    ok, why = healthy()
    print(f"arXiv reachable: {ok}  ({why})")
    raise SystemExit(0 if ok else 1)
