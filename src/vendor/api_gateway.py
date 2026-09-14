#!/usr/bin/env python3
"""
api_gateway -- the ONE way this codebase talks to any outside service.

WHY A GATEWAY AND NOT A THIRD CLIENT (owner-set, 2026-09-10): *"we need a
single client to communicate with all external reference sites to ensure we
abide by the rules of the API use. That's how we got in trouble with arxiv."*

The pattern we were repeating is reactive by construction. arXiv blocked our
User-Agent on 2026-09-09; `arxiv_client.py` was written that afternoon
(ARXIV_BLOCK_2026-09-09.md). S2 saturated our own quota on 2026-09-10 -- a
25-id probe got HTTP 429 six times over 105 seconds while a 780,552-reference
backlog sat behind ~180 free `/paper/batch` calls -- and the next move would
have been `s2_client.py`. Two clients means the THIRD service is unprotected
until it, too, refuses us. Measured the same day, this repo reaches **fifteen
external hosts**, and six of them are volunteer-run academic infrastructure
(dblp, mlr.press, ecva, ijcai, proceedings.neurips.cc, openaccess.thecvf.com)
where being blocked costs something we cannot buy back.

So: policy is DATA (`POLICY` below), the wire is one implementation, and
adding a service means adding a ROW -- not writing a client, and not quietly
inheriting a default.

    from api_gateway import get, post, Unanswered
    r = get("https://api.semanticscholar.org/graph/v1/paper/batch")

THE FOUR PROPERTIES, each one paid for by a real incident.

1. **Per-host shared clock and lock.** The floor is enforced on a monotonic
   clock held per host, behind a per-host lock, so concurrent callers in one
   process DIVIDE that host's budget instead of each claiming it. This is the
   property that actually mattered for arXiv, where "four compliant processes
   each obeying three seconds independently" was the hole. Per-HOST, because a
   PDF pull and a metadata query are the same servers -- `qc_arxiv_discipline`
   went green for a day while `arxiv.org/pdf/` ran unpaced one hostname over
   from `export.arxiv.org`.

2. **An unknown host is refused, by name.** `UnknownHost` rather than a
   permissive default. A default is how the next arXiv happens: the request
   works, nobody writes a row, and the first time anyone thinks about that
   service's rules is the day it stops answering. Adding a service is
   deliberate.

3. **Never spoof a User-Agent.** Every request carries the host's declared
   identifier, set on the session so no call site can omit it, and a caller
   that passes its own `User-Agent` header is REFUSED. Two scripts were found
   on 2026-09-10 sending `Mozilla/5.0` -- one of them at the very service that
   had blocked us. ARXIV_BLOCK_2026-09-09.md states the position: changing the
   identifier to get past a block we earned is evasion, and a bot that cannot
   be contacted can only be blocked. Hosts that ask for a contact address
   (Crossref's and OpenAlex's polite pools) get one, and the gateway refuses to
   call them if it has none to give.

4. **Silence is never a result.** A 429 or 5xx that outlives the retries, or a
   transport failure, raises `Unanswered` -- a `source_availability.
   SourceUnavailable`, so a caller that already books unanswered sources
   catches it for free (`ledger.unanswered()`, exit 4, unclearable). A refusal
   that will not clear by retrying (arXiv's 403) raises `Blocked`, on the first
   attempt, never retried. Neither ever comes back as an empty list a caller
   can read as "the source says there is nothing". `12d0c869e` fixed exactly
   that in `05_incremental_paper_sweep.py`, where a throttled minute became
   the permanent claim "this paper has no arXiv preprint"; do not undo it by
   catching `Unanswered` and returning falsy.

   An ANSWER is returned whatever it says: 404 ("no such record"), 400 ("your
   request is wrong"), anything else non-retryable. This module knows about the
   wire, not about what a missing paper means to stage 13.

5. **A block is learned once per host, not once per item.** `Blocked` used to
   be recomputed from scratch on every request, and computing it means BUYING A
   RATE SLOT to be refused -- 3 s each on arXiv. The 2026-09-10 rehearsal
   measured 3.75 h of a single release-day run spent collecting 403s we already
   knew were coming. `raise_if_blocked` now records the block on the host's
   state and `request`/`stream` refuse from the memo before taking `budget()`.
   The memo EXPIRES after `BLOCK_RECHECK_S` and any non-block answer clears it,
   because a remembered block that outlives the block is a worse defect than
   the cost it saves -- see `_refuse_if_block_remembered`.

WHAT `max_concurrency` MEANS, because it is two rules in one number.
`max_concurrency == 1` is arXiv's "limit requests to a single connection at a
time": the lock is held for as long as the connection is OPEN -- across a 40 MB
e-print body -- and the clock is stamped when it closes. Anything greater is a
pure REQUEST RATE: the clock is stamped when the request is ISSUED and the lock
released before the body, so requests may overlap in flight while their issue
times stay `interval` apart. That distinction is worth more than it looks: S2
publishes a rate and no concurrency rule, and stamping on exit at S2's observed
~1.5 s latency would turn a 1 req/s quota into 0.4 req/s -- making the backlog
sweep slower than the throttling it exists to avoid.

WHAT IT CANNOT DO. The clock is process-local. Four shards each obeying the
interval are still four times the rate, and that is precisely the shape of the
S2 measurement above: a probe and a sweep, two processes, each individually
polite. Anything running concurrent work against a host MUST pass
`share_budget=N` (or set `SYNTOLOGY_SHARE_BUDGET=N` in its environment, which
every call site honours without being edited) so the floor becomes
N*interval. Naming the hole is not closing it; a cross-process lease would
close it and does not exist yet.

`arxiv_client.py` remains as arXiv's VOCABULARY -- `get(params)`,
`head_url`, `stream_url`, `is_arxiv_url` -- and is a view onto this module's
`arxiv.org` row. It is not a second mechanism: it owns no clock, no lock and
no session. See its header.
"""
from __future__ import annotations

import contextlib
import logging
import os
import threading
import time as _real_time
import urllib.parse
from dataclasses import dataclass, field
from typing import Callable

import requests

from source_availability import SourceUnavailable

log = logging.getLogger("api_gateway")

# The one address a blocked service can reach us at. Not a personal mailbox:
# an identifier that outlives whoever ran the job.
CONTACT = "media@syntology.ai"
UA = f"syntology-research-bot/0.2 (+https://syntology.ai; contact: {CONTACT})"

# Identifiers we must never send. A spoofed browser UA is what
# ARXIV_BLOCK_2026-09-09.md refuses to do, and it was still live in two files
# on 2026-09-10.
SPOOFED = ("mozilla/", "chrome/", "safari/", "curl/", "wget/", "python-requests/")


class Unanswered(SourceUnavailable):
    """The source never answered: a 429 past its retries, an exhausted 5xx, or
    a transport failure.

    NOT a result. Deliberately a `SourceUnavailable`, so a caller that already
    books unanswered sources catches it without knowing this module exists;
    deliberately an exception, so a caller that does nothing crashes instead of
    writing silence into the graph as a fact about a paper."""

    def __init__(self, message: str, *, host: str = "", attempts: int = 0,
                 last_status: int | None = None):
        super().__init__(message)
        self.host, self.attempts, self.last_status = host, attempts, last_status


class Blocked(RuntimeError):
    """The service has refused US, and it will not clear by retrying.

    Distinct from `Unanswered` because the correct response is opposite: an
    unanswered call is re-asked later, a block is stopped and apologised for.
    Never retried here, and never worked around by changing the identifier --
    see property 3 in this module's header."""


class UnknownHost(RuntimeError):
    """No policy row for this host. Property 2: a service we have not thought
    about does not get a default, it gets a refusal naming itself."""


def _linear_floor(attempt: int, floor: float, kind: str) -> float:
    """arXiv's ladder, preserved exactly: back off ON TOP of the floor, the
    same wait whether the cause was a throttle or a socket. Its numbers are
    pinned by `test_arxiv_client.py` (6.0, 12.0 at a 3 s floor)."""
    return floor * attempt * 2


def _measured_ladder(attempt: int, floor: float, kind: str) -> float:
    """`s2_backoff.py`'s two ladders, which were MEASURED rather than guessed:
    S2 sends no Retry-After, the window reopens in about a second, and a
    15/30/45 ladder spent 96% of a run asleep (97 -> 2,080 papers/min on
    stage 8 once corrected). A real network fault is the other case and starts
    at 15 s, because hammering a broken host does not help.

    The constants are imported, not copied -- one definition of a measured
    number, per the module those measurements are recorded in."""
    from s2_backoff import (THROTTLE_START_S, THROTTLE_CAP_S,
                            NETWORK_START_S, NETWORK_CAP_S)
    if kind == "throttle":
        return min(THROTTLE_START_S * (2 ** (attempt - 1)), THROTTLE_CAP_S)
    return min(NETWORK_START_S * (2 ** (attempt - 1)), NETWORK_CAP_S)


def _s2_headers() -> dict:
    """S2's key, attached HERE so no call site can forget it.

    `05_incremental_paper_sweep.py` built `requests.Session()` and handed it
    straight to the title-match path with no `x-api-key` at all, while a valid
    44-character key sat in `.env` -- so the release-day discovery pass, the
    one that costs papers their arXiv identity when it is throttled, ran
    against the contended public pool. No reviewer could see that at the call
    site, which is why authentication is policy and not an argument."""
    from s2_api_key import get_s2_api_key
    if not os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:                       # dotenv absent: environment only
            pass
    key = get_s2_api_key()
    return {"x-api-key": key} if key else {}


def _github_headers() -> dict:
    """GitHub's token, same rule. Unauthenticated REST is 60 requests/hour;
    with a token it is 5,000/hour, which is the difference between a lane that
    runs and a lane that does not."""
    tok = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    return {"Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json"} if tok else {}


ARXIV_BLOCK_MESSAGE = (
    "arXiv returned 403 for this User-Agent. This is a block, not a "
    "throttle: it does not clear by retrying and MUST NOT be worked "
    "around by changing the UA. Stop the offending caller, then "
    "contact arXiv. See ARXIV_BLOCK_2026-09-09.md.")


@dataclass(frozen=True)
class Policy:
    """One host's rules, as data.

    `host` matches itself and any subdomain, so `arxiv.org` covers
    `export.arxiv.org` and `rss.arxiv.org` -- the terms are about a service's
    SERVERS, not about one path or one name on them, which is the correction
    `qc_arxiv_discipline` had to make the same day it was written.

    `enforced` is the gate's business, not the wire's: it says whether the
    call-site migration for this host has LANDED. Unenforced hosts still go
    through this module when they are called through it; what `enforced=False`
    means is that `qc_api_discipline.py` counts remaining direct call sites as
    a ratchet instead of failing on them. Flipping it to True without doing
    the migration turns the suite red on work nobody has scheduled, which is
    how a check stops being read."""
    host: str
    interval: float
    max_concurrency: int
    why: str
    interval_unauthenticated: float | None = None
    headers: Callable[[], dict] | None = None
    mailto_param: str | None = None
    requires_contact: bool = False
    block_statuses: tuple[int, ...] = ()
    block_message: str = ""
    backoff: Callable[[int, float, str], float] = _measured_ladder
    max_attempts: int = 4
    enforced: bool = False


# ---------------------------------------------------------------------------
# THE POLICY TABLE. Adding a service is adding a row here.
#
# Every `interval` is either the service's published rate or, where none is
# published, a deliberately conservative courtesy rate with the reason in
# `why`. Where a rate IS published we run at or under it -- never at it plus
# optimism. The six volunteer-run hosts are all at 2 s and concurrency 1 by
# the same argument: they publish nothing, they are not funded to absorb us,
# and the cost of being wrong is asymmetric.
# ---------------------------------------------------------------------------
POLICY: dict[str, Policy] = {p.host: p for p in (
    Policy(
        host="arxiv.org",
        interval=3.0, max_concurrency=1, max_attempts=3,
        backoff=_linear_floor,
        block_statuses=(403,), block_message=ARXIV_BLOCK_MESSAGE,
        requires_contact=True, enforced=True,
        why="arXiv's terms of use, quoted: 'no more than one request every three "
            "seconds, and limit requests to a single connection at a time.' We were "
            "blocked on 2026-09-09 for 442 rate-limit responses in five days; the "
            "concurrency of 1 is theirs, not a guess."),
    Policy(
        host="semanticscholar.org",
        interval=1.0, interval_unauthenticated=3.5, max_concurrency=4,
        max_attempts=6, headers=_s2_headers, enforced=True,
        why="S2 documents 1 req/s for an API key on the shared-pool endpoints "
            "(/paper/batch, /paper/search, /recommendations) and more elsewhere; we "
            "run the strict rate for every endpoint, which is what 02b's own "
            "--rate-limit-s help text already claimed ('1 req/sec, cumulative "
            "across all endpoints'). A second faster lane would be two budgets "
            "again, one of them unmeasured. Unauthenticated is the contended public "
            "pool -- this repo measured persistent 429s there even at 3.5 s, so that "
            "number is politeness, not safety."),
    Policy(
        host="api.github.com",
        interval=0.8, interval_unauthenticated=60.0, max_concurrency=2,
        headers=_github_headers,
        why="GitHub publishes 5,000 requests/hour authenticated (1.39/s) and 60/hour "
            "unauthenticated (one per minute), plus a secondary limit on concurrent "
            "requests. 0.8 s is 4,500/hour -- under the primary limit with room for "
            "the retries, and the unauthenticated row is the real published number "
            "rather than an optimistic one."),
    Policy(
        host="raw.githubusercontent.com",
        interval=0.5, max_concurrency=4,
        why="Raw file serving, not the API, and not counted against the REST quota. "
            "No published rate; 0.5 s is a courtesy floor so a file sweep cannot "
            "become a burst."),
    Policy(
        host="joss.theoj.org",
        interval=2.0, max_concurrency=1,
        why="The Journal of Open Source Software runs on volunteer infrastructure "
            "(Open Journals) and publishes no rate limit at all. Same argument as "
            "the six other volunteer-run hosts on this table: nothing published, "
            "nobody funded to absorb us, no paid tier to fall back to, so 2 s and "
            "one connection. Its published.json paginates 20 rows a page, so a full "
            "enumeration of ~3,700 papers is ~186 requests -- six minutes at this "
            "rate, which is cheap enough that there is no case for going faster."),
    Policy(
        host="dblp.org",
        interval=2.0, max_concurrency=1,
        why="Volunteer-run, publishes no rate, and answers 429 with Retry-After when "
            "it has had enough. Conservative on purpose: dblp is not funded to "
            "absorb us and there is no paid tier to fall back to."),
    Policy(
        host="openreview.net",
        interval=1.0, max_concurrency=2, enforced=True,
        why="OpenReview throttles visibly (login is 3 per 60 s, which this repo has "
            "already hit). No published API rate; 1 s with two connections has run "
            "the venue sweeps without 429s. Covers api.openreview.net and "
            "api2.openreview.net -- one service, two names. ENFORCED 2026-09-10: the "
            "2026-09-10 rehearsal 429'd inside 24 seconds because PDF pulls -- the "
            "heaviest traffic we send them -- never reached this row at all, and on "
            "release day OpenReview is the ONLY place a NeurIPS PDF exists. arXiv "
            "blocking us costs 60% of a cohort; this costs 100%."),
    Policy(
        host="api.crossref.org",
        interval=1.0, max_concurrency=2, mailto_param="mailto", requires_contact=True,
        why="Crossref's POLITE POOL: they ask for a contact address and give better "
            "service for it. The mailto is added here so it cannot be forgotten, and "
            "the gateway refuses the host if it has no address to send."),
    Policy(
        host="api.openalex.org",
        interval=0.2, max_concurrency=2, mailto_param="mailto", requires_contact=True,
        why="OpenAlex publishes 10 req/s and 100k/day and runs a polite pool keyed "
            "on a mailto. 0.2 s is half the published rate; the mailto is required "
            "for the same reason as Crossref's."),
    Policy(
        host="huggingface.co",
        interval=1.0, max_concurrency=2,
        why="No published anonymous rate; HF throttles by IP when pushed. 1 s is a "
            "courtesy floor for metadata reads."),
    Policy(
        host="proceedings.mlr.press",
        interval=2.0, max_concurrency=1,
        why="Volunteer-run proceedings host (PMLR). Static pages, no published rate, "
            "no operator to absorb a burst."),
    Policy(
        host="openaccess.thecvf.com",
        interval=2.0, max_concurrency=1,
        why="Volunteer-run (CVF). Same argument as PMLR."),
    Policy(
        host="proceedings.neurips.cc",
        interval=2.0, max_concurrency=1,
        why="Volunteer-run (NeurIPS). Same argument as PMLR."),
    Policy(
        host="ojs.aaai.org",
        interval=2.0, max_concurrency=1,
        why="AAAI's OJS instance -- a journal system on modest hosting, which is the "
            "kind of thing a sweep takes down."),
    Policy(
        host="ijcai.org",
        interval=2.0, max_concurrency=1,
        why="Volunteer-run proceedings. Same argument as PMLR."),
    Policy(
        host="ecva.net",
        interval=2.0, max_concurrency=1,
        why="Volunteer-run (ECCV/ECVA). Same argument as PMLR."),
    Policy(
        host="aclanthology.org",
        interval=2.0, max_concurrency=1,
        why="Volunteer-run (ACL Anthology), and the single largest PDF host this "
            "repo pulls from after arXiv: 27,185 rows across "
            "all_papers_phase2_language.json (16,685) and _language_findings.json "
            "(10,500), every one a multi-megabyte PDF. It had no row while "
            "`pdf_fetch` still had a raw-session fallback, which is the arrangement "
            "that left OpenReview ungoverned -- so it gets one in the same commit "
            "that removes the fallback. Same argument as PMLR: no published rate, "
            "no operator funded to absorb a sweep."),
    Policy(
        host="creativecommons.org",
        interval=2.0, max_concurrency=1,
        why="Licence legalcode, read rather than recalled. Every corpus this repo "
            "considers acquiring declares an SPDX tag and nothing more (pwc-archive "
            "is `license: cc-by-sa-4.0` in a 191-byte dataset card), so the only "
            "place the ACTUAL terms exist is here -- and a ShareAlike obligation "
            "quoted from memory is exactly the failure mode <INTERNAL>/46 was "
            "written to stop. Static documents, a handful of reads per lane, "
            "non-profit host publishing no rate: 2 s and one connection, the same "
            "argument as the volunteer-run rows above."),
)}


# How long a remembered block stands before ONE call is allowed through to
# re-test it. Long enough that a 7,500-paper run pays the refusal once rather
# than 7,500 times; short enough that a host coming back is noticed inside five
# minutes. See `_refuse_if_block_remembered`.
BLOCK_RECHECK_S = float(os.environ.get("SYNTOLOGY_BLOCK_RECHECK_S", "300"))


# ---------------------------------------------------------------------------
# Per-host state. Everything mutable lives here, one record per host, so
# "the shared clock" is a thing you can point at.
# ---------------------------------------------------------------------------
@dataclass
class HostState:
    policy: Policy
    # `time` is a field and not an import so a test can substitute a fake clock
    # for ONE host without stopping the world. `arxiv_client` exposes this
    # host's fields as its own module attributes -- see its header.
    time: object = _real_time
    _last: float = 0.0
    _session: requests.Session | None = None
    # (status, monotonic when we learned it), or None. See
    # `_refuse_if_block_remembered` for why this is a memo and not a latch.
    _blocked: tuple[int, float] | None = None
    MIN_INTERVAL: float = 0.0
    clock_lock: threading.Lock = field(default_factory=threading.Lock)
    gate: threading.Semaphore | None = None

    def __post_init__(self):
        if not self.MIN_INTERVAL:
            self.MIN_INTERVAL = self.policy.interval
        if self.gate is None:
            self.gate = threading.BoundedSemaphore(max(1, self.policy.max_concurrency))


_STATE: dict[str, HostState] = {}
_STATE_LOCK = threading.Lock()


def registrable(url_or_host: str) -> str:
    """The policy key for a URL or host: the row whose host is it or a parent
    of it. `export.arxiv.org` -> `arxiv.org`, `api2.openreview.net` ->
    `openreview.net`.

    Longest match wins, so a row for `api.github.com` is not shadowed by a
    hypothetical `github.com` row. Raises `UnknownHost` when nothing matches
    -- property 2."""
    host = url_or_host
    if "//" in url_or_host or url_or_host.startswith("http"):
        host = urllib.parse.urlsplit(url_or_host).hostname or ""
    host = host.lower().strip(".")
    best = ""
    for key in POLICY:
        if host == key or host.endswith("." + key):
            if len(key) > len(best):
                best = key
    if not best:
        raise UnknownHost(
            f"no api_gateway policy for host {host or url_or_host!r}. Every outside "
            f"service this codebase calls declares its rules in api_gateway.POLICY -- "
            f"request interval, concurrency, identifier, and whether it wants a "
            f"contact address. Add a row (with the published rate, or a conservative "
            f"courtesy rate and the reason) rather than letting a new service inherit "
            f"a default: a default is how arXiv blocked us.")
    return best


def known_host(url: str) -> bool:
    """True if `url` names a host this module has a policy for. For the
    chokepoints handed a URL at RUNTIME -- `pdf_fetch.fetch_pdf`, the
    benchmark's model-chosen `fetch_url` -- which no grep can decide."""
    try:
        registrable(url)
        return True
    except UnknownHost:
        return False


def state(host: str) -> HostState:
    """The one mutable record for a host. Created on first use, never
    replaced -- a caller holding a reference is holding THE clock."""
    key = registrable(host)
    with _STATE_LOCK:
        st = _STATE.get(key)
        if st is None:
            st = _STATE[key] = HostState(policy=POLICY[key])
        return st


def authenticated(host: str) -> bool:
    st = state(host)
    return bool(st.policy.headers and st.policy.headers())


def interval(host: str) -> float:
    """The floor for this host in this process, which can depend on whether we
    are authenticated -- an unauthenticated caller is on somebody else's shared
    pool and does not get to move at our rate."""
    st = state(host)
    p = st.policy
    if p.interval_unauthenticated is not None and not authenticated(host):
        # MIN_INTERVAL may have been overridden (tests scale time); honour the
        # override, and only fall back to the unauthenticated rate when it is
        # still the policy's own number.
        if st.MIN_INTERVAL == p.interval:
            _warn_unauthenticated(p)
            return p.interval_unauthenticated
    return st.MIN_INTERVAL


_warned: set[str] = set()


def _warn_unauthenticated(p: Policy) -> None:
    if p.host in _warned:
        return
    _warned.add(p.host)
    log.warning(
        f"No credential for {p.host} -- running on its shared/anonymous pool at "
        f"{p.interval_unauthenticated}s instead of {p.interval}s. That is politeness, "
        f"not safety; set the key. ({p.why})")


def _share(explicit: int | None = None) -> int:
    """How many PROCESSES are calling concurrently.

    `SYNTOLOGY_SHARE_BUDGET` exists because the incidents were processes, not
    threads -- a probe beside a sweep -- and there are dozens of scripts here.
    An environment variable is the only lever that reaches all of them without
    editing all of them. An explicit argument always wins."""
    if explicit is not None:
        return max(1, int(explicit))
    try:
        return max(1, int(os.environ.get("SYNTOLOGY_SHARE_BUDGET", "1")))
    except ValueError:
        return 1


def share_for(host: str, desired_interval: float | None) -> int:
    """A caller's `--rate-limit-s` expressed as a SHARE of the host's budget.

    Nine migrated scripts carried a `--rate-limit-s` flag and a `time.sleep()`
    after every call. That sleep is now a second clock sitting on top of this
    module's, which is the arrangement the gateway exists to end -- but the
    flag still means something real: "pace me slower than the default, because
    I am not the only thing running". `share_budget=N` says exactly that on
    the one clock, so `--rate-limit-s 2.0` against a 1.0s policy floor becomes
    share 2 and the flag keeps its meaning instead of being silently ignored.

    Never returns less than 1: a flag asking to go FASTER than the declared
    rate is not a thing a call site gets to do."""
    if not desired_interval:
        return 1
    return max(1, round(float(desired_interval) / state(host).policy.interval))


def session(host: str) -> requests.Session:
    """The one session for a host: our identifier, and its credential if it has
    one. Headers are set on the SESSION, not per call, so no call site can omit
    them."""
    st = state(host)
    if st._session is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA})
        if st.policy.headers:
            s.headers.update(st.policy.headers())
        st._session = s
    return st._session


@contextlib.contextmanager
def budget(host: str, share_budget: int | None = None):
    """Hold a host's rate budget. THE clock and THE lock; every request in this
    module goes through here, so a caller that takes the budget directly is on
    the same clock as everything else by construction rather than by a second
    copy of the arithmetic.

    `max_concurrency == 1` (arXiv): the semaphore is held across the body and
    the clock is stamped on the way OUT, so "one connection at a time" holds
    for as long as the connection is open -- a 40 MB e-print included. Use it
    directly when you must own the response STREAM; `pdf_fetch.fetch_pdf` does,
    because it writes the body to a temp file and checks it against
    Content-Length before renaming into place.

    `max_concurrency > 1`: the clock is stamped at ISSUE and the lock released
    before the body, so the RATE is held while requests may overlap.

    The stamp is in a `finally` either way: a call that dies mid-body still
    spent the budget.

    NOT re-entrant for a concurrency-1 host: the semaphore is bounded, so
    calling `get()` from inside a `budget()` block on arXiv deadlocks -- which
    is the correct shape for "one connection at a time" and the reason this is
    a narrow escape hatch and not a decorator to sprinkle around."""
    st = state(host)
    floor = interval(host) * _share(share_budget)
    hold = st.policy.max_concurrency <= 1
    st.gate.acquire()
    try:
        with st.clock_lock:
            wait = floor - (st.time.monotonic() - st._last)
            if wait > 0:
                st.time.sleep(wait)
            if not hold:
                st._last = st.time.monotonic()
        try:
            yield
        finally:
            if hold:
                st._last = st.time.monotonic()
    finally:
        st.gate.release()


def raise_if_blocked(host: str, status_code: int) -> None:
    """The block refusal, in one place, for callers holding their own response.

    A caller that takes `budget()` gets the clock but not `request()`'s status
    handling, and the one status that must never be re-interpreted per call
    site is a block -- the tempting local fix for it is a User-Agent change.

    Also REMEMBERS the block on the host's state, which is what makes
    `_refuse_if_block_remembered` able to refuse the next 7,499 papers without
    each of them buying a 3 s slot first."""
    st = state(host)
    p = st.policy
    if status_code in p.block_statuses:
        st._blocked = (status_code, st.time.monotonic())
        raise Blocked(p.block_message or f"{p.host} returned HTTP {status_code} for our "
                                         f"User-Agent. Not a throttle; stop and ask.")


def clear_block(host: str) -> None:
    """Forget a remembered block. For an operator who knows the block lifted
    and does not want to wait out `BLOCK_RECHECK_S`, and for tests."""
    state(host)._blocked = None


def _refuse_if_block_remembered(host: str) -> None:
    """Refuse a request to a host we have ALREADY been refused by, without
    spending its rate budget first.

    WHY THIS EXISTS (2026-09-10 rehearsal). `raise_if_blocked` was stateless,
    so a block was re-learned per paper -- and learning it means taking arXiv's
    budget slot, which is a 3 s floor held across the connection. Measured over
    the release-day cohort that is **3.75 h per run spent purely collecting
    403s** we already knew we would get. arXiv has been blocking us since
    09-04; every daily run since has paid it.

    WHY IT IS A MEMO AND NOT A LATCH, which is the part that could make this
    worse than the bug. A cached "blocked" that outlives the block is the
    R3d failure in a new costume: it would turn our own stale state into the
    permanent claim "this host refuses us", and no amount of the host coming
    back would change it. So the memo EXPIRES: after `BLOCK_RECHECK_S` the
    next caller is let through at full price to find out for real, and any
    answer that is not a block clears it (`request`/`stream` both do that on
    the way out). Worst case the memo costs one host-interval per five
    minutes; it can never outlive the condition by more than that.

    Process-local by construction, like the clock it protects: a new run
    always re-asks."""
    st = state(host)
    remembered = st._blocked
    if remembered is None:
        return
    status, learned_at = remembered
    if st.time.monotonic() - learned_at >= BLOCK_RECHECK_S:
        st._blocked = None                  # time to find out again, at full price
        return
    p = st.policy
    raise Blocked(
        (p.block_message or f"{p.host} returned HTTP {status} for our User-Agent.")
        + f" [remembered from an earlier HTTP {status} in this process; not re-asked, "
          f"and not charged {p.host}'s rate budget to be refused again. One call is "
          f"let through every {BLOCK_RECHECK_S:.0f}s to re-test, and any non-block "
          f"answer clears it. api_gateway.clear_block({p.host!r}) forgets it now.]")


def _prepare(host: str, url: str, params: dict | None, headers: dict | None):
    """Identifier and contact enforcement -- property 3, at the wire."""
    if headers:
        for k in headers:
            if k.lower() == "user-agent":
                raise ValueError(
                    f"refusing a caller-supplied User-Agent for {host}. Every request "
                    f"carries {UA!r}, set on the session so no call site can omit or "
                    f"replace it. Spoofing an identifier is what ARXIV_BLOCK_2026-09-09.md "
                    f"refuses to do; if this host needs something different, it belongs "
                    f"in its POLICY row, not in one call.")
    low = UA.lower()
    for bad in SPOOFED:
        if low.startswith(bad):
            raise ValueError(f"our own User-Agent is spoofing {bad!r}: {UA}")
    p = state(host).policy
    if p.requires_contact and "@" not in UA:
        raise ValueError(
            f"{p.host} asks for a contact address and our User-Agent has none. A bot "
            f"that cannot be contacted can only be blocked.")
    if p.mailto_param:
        params = dict(params or {})
        params.setdefault(p.mailto_param, CONTACT)
    return params


def request(method: str, url: str, *, params: dict | None = None,
            json: dict | None = None, data=None, headers: dict | None = None,
            timeout: float = 90.0, share_budget: int | None = None,
            max_attempts: int | None = None, stream: bool = False,
            allow_redirects: bool = True,
            stats: dict | None = None) -> requests.Response:
    """One request to a known host, never faster than its declared rate.

    `stats` is an optional dict this call counts into -- `calls`, `attempts`,
    `throttled`, `network_errors`. It exists because a caller can no longer see
    a 429 that the gateway retried past, and one caller needs to: stage 4's
    `TitleMatchResult.hit_rate_limit` drives an adaptive backoff, and it was
    added in the first place because a 429 that the retry loop RECOVERED from
    was indistinguishable, from the caller's side, from a call that never hit
    one -- so the backoff kept decaying back to its floor while most calls were
    quietly eating a real retry cost.

    Returns the response for any status the caller has to judge (200, 404,
    400, ...). Raises `Blocked` on a declared block status, on the first
    attempt, never retried. Raises `Unanswered` once 429/5xx/transport
    failures exhaust the attempts -- which means the source NEVER ANSWERED and
    is not the same fact as "the source returned nothing" (R3d). Raises
    `UnknownHost` for a service with no policy row."""
    host = registrable(url)
    st = state(host)
    p = st.policy
    # BEFORE the budget, deliberately: the whole point is not to buy a rate
    # slot in order to be told "no" again.
    _refuse_if_block_remembered(host)
    attempts = max_attempts if max_attempts is not None else p.max_attempts
    params = _prepare(host, url, params, headers)
    floor = interval(host) * _share(share_budget)
    last_status: int | None = None
    last_err = "no attempt made"

    # Only the kwargs this call actually needs. A `requests.Session` would take
    # them all, but the fake sessions the throttle tests inject are deliberately
    # minimal (`get(url, params, timeout)`), and a client that only works against
    # the full requests API cannot be tested without generating real volume
    # against services that have already refused us once.
    kw: dict = {"params": params, "timeout": timeout}
    if json is not None:
        kw["json"] = json
    if data is not None:
        kw["data"] = data
    if headers is not None:
        kw["headers"] = headers
    if stream:
        kw["stream"] = True
    if method == "HEAD":
        kw["allow_redirects"] = allow_redirects

    if stats is not None:
        stats["calls"] = stats.get("calls", 0) + 1

    for attempt in range(1, attempts + 1):
        r = None
        kind = "network"
        if stats is not None:
            stats["attempts"] = stats.get("attempts", 0) + 1
        with budget(host, share_budget):
            try:
                r = getattr(session(host), method.lower())(url, **kw)
            except requests.RequestException as e:
                # A transport failure is UNANSWERED, not empty (R3d). It leaves
                # by the same documented door as an exhausted 429, or every call
                # site migrating onto this module re-invents `except: return []`
                # -- the shape that let an HTTP 429 be recorded as "arXiv has no
                # record of 1,559 papers".
                last_err = f"{type(e).__name__}: {e}"[:200]
                last_status = None
                if stats is not None:
                    stats["network_errors"] = stats.get("network_errors", 0) + 1
        if r is not None:
            raise_if_blocked(host, r.status_code)
            last_status = r.status_code
            if r.status_code == 429:
                last_err, kind = "HTTP 429", "throttle"
                if stats is not None:
                    stats["throttled"] = stats.get("throttled", 0) + 1
            elif 500 <= r.status_code < 600:
                last_err = f"HTTP {r.status_code}"
            else:
                # An ANSWER, of any shape, is proof the host is talking to us:
                # the memo must not outlive the condition it describes.
                st._blocked = None
                return r
            if attempt < attempts:
                w = p.backoff(attempt, floor, kind)
                log.warning(f"  {host} {last_err} on {method} (attempt {attempt}/"
                            f"{attempts}) -- backing off {w:.0f}s")
                st.time.sleep(w)                # ON TOP of the floor
            continue
        if attempt < attempts:
            st.time.sleep(p.backoff(attempt, floor, "network"))
    raise Unanswered(f"{host} unanswered after {attempts} attempts: {last_err}",
                     host=host, attempts=attempts, last_status=last_status)


def get(url: str, params: dict | None = None, **kw) -> requests.Response:
    """One GET. See `request` for the raise/return contract."""
    return request("GET", url, params=params, **kw)


def post(url: str, params: dict | None = None, *, json: dict | None = None,
         data=None, **kw) -> requests.Response:
    """One POST. See `request` for the raise/return contract."""
    return request("POST", url, params=params, json=json, data=data, **kw)


def head(url: str, params: dict | None = None, **kw) -> requests.Response:
    """One HEAD, on the same budget as everything else.

    A separate verb rather than a flag because the difference is not cosmetic:
    `<INTERNAL>/probe_pdf_integrity.py` HEADs for
    Content-Length to tell a truncated local PDF from a complete one, and
    answering that with a GET would pull the whole multi-megabyte body it is
    explicitly not downloading. Redirects are followed, so one call can be more
    than one request -- the same as any GET, and the reason it holds a full
    budget slot."""
    return request("HEAD", url, params=params, **kw)


@contextlib.contextmanager
def stream(url: str, *, timeout: float = 90.0, share_budget: int | None = None,
           headers: dict | None = None, params: dict | None = None):
    """A streamed GET, holding the budget across the body.

    For a caller that must consume the response itself -- `pdf_fetch.fetch_pdf`
    writes to a temp file, checks Content-Length and the %%EOF trailer, and
    only then renames into place, so it cannot hand the response back to a
    function that has already released the lock.

    This does NOT retry: `pdf_fetch` owns retry/backoff for a short read, and
    two retry layers multiply attempts against a service that has refused us
    once. It does raise `Blocked`, because that decision must never be re-made
    per call site."""
    host = registrable(url)
    _refuse_if_block_remembered(host)          # before the budget -- see `request`
    params = _prepare(host, url, params, headers)
    with budget(host, share_budget):
        r = session(host).get(url, stream=True, timeout=timeout, headers=headers,
                              params=params)
        try:
            raise_if_blocked(host, r.status_code)
            state(host)._blocked = None        # it answered; forget any memo
            yield r
        finally:
            r.close()


# ---------------------------------------------------------------------------
# Service shapes. NOT a second client: the wire above is the only wire. This is
# the one place that knows a specific endpoint's response CONTRACT, and it
# lives here because the alternative is fifteen call sites each re-deriving it.
# ---------------------------------------------------------------------------
S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_BATCH_MAX_IDS = 500          # S2's documented per-request cap on /paper/batch


def s2_batch(ids, fields: str, **kw) -> list:
    """POST /paper/batch -- the shape fifteen S2 call sites use.

    Returns the list S2 returns: one slot per input id, in input order, `null`
    for an id it has no record of. That `null` is an ANSWER and stays one.

    Raises `Unanswered` when S2 never answered, and ALSO on a 200 whose body
    will not parse or is not the aligned list the endpoint documents -- a body
    we cannot read is a question we did not really get to ask, and zipping a
    malformed response against the input ids is how a wrong paper gets a right
    id. An answered non-200 raises too, because there is no shape of this
    return value that could honestly carry it."""
    ids = list(ids)
    if len(ids) > S2_BATCH_MAX_IDS:
        raise ValueError(f"/paper/batch takes at most {S2_BATCH_MAX_IDS} ids; got "
                         f"{len(ids)}. Chunk at the call site so each chunk's failure "
                         f"is countable.")
    r = post(f"{S2_BASE}/paper/batch", {"fields": fields}, json={"ids": ids}, **kw)
    if r.status_code != 200:
        raise Unanswered(f"S2 /paper/batch answered HTTP {r.status_code} for {len(ids)} "
                         f"ids: {getattr(r, 'text', '')[:200]}",
                         host="semanticscholar.org", attempts=1, last_status=r.status_code)
    try:
        rows = r.json()
    except ValueError as e:
        raise Unanswered(f"S2 /paper/batch returned an unparseable 200 body: {e}",
                         host="semanticscholar.org", attempts=1, last_status=200) from None
    if not isinstance(rows, list) or len(rows) != len(ids):
        raise Unanswered(
            f"S2 /paper/batch returned {type(rows).__name__} of "
            f"{len(rows) if hasattr(rows, '__len__') else '?'} for {len(ids)} ids; the "
            f"endpoint documents one aligned slot per id. Refusing to zip it.",
            host="semanticscholar.org", attempts=1, last_status=200)
    return rows


def s2_get(path: str, params: dict | None = None, **kw) -> requests.Response:
    """A graph/v1 GET by path (`/paper/search/match`). Sugar over `get`, so a
    call site reads as the endpoint it is calling."""
    return get(S2_BASE + (path if path.startswith("/") else "/" + path), params, **kw)


def hosts_report() -> str:
    lines = [f"{'host':<28} {'interval':>9} {'conc':>5}  auth  enforced"]
    for key in sorted(POLICY):
        p = POLICY[key]
        iv = f"{p.interval}s"
        if p.interval_unauthenticated is not None:
            iv += f"/{p.interval_unauthenticated}s"
        auth = ("yes" if p.headers and p.headers() else "NO ") if p.headers else "n/a"
        lines.append(f"{key:<28} {iv:>9} {p.max_concurrency:>5}  {auth:<5} "
                     f"{'gated' if p.enforced else 'ratchet'}")
    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(hosts_report())
    print(f"\ncontact: {CONTACT}\nUA: {UA}\nshare_budget: {_share()}")
