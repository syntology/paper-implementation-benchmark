#!/usr/bin/env python3
"""The ONE way to say "the source did not answer" -- as distinct from
"the source answered, and there is nothing there".

WHY THIS EXISTS (2026-09-09). Five instances in two days, each found by a
different accident and none by looking for them (SILENT_ABSENCE_BRIEF.md).
The shape is always the same:

    try:
        body = fetch(url)
    except Exception:
        return []          # <- indistinguishable from "no results"

A caller downstream then reads a fact about the WORLD where there was only
a fact about the NETWORK. It cost, concretely:

  - detect_duplicate_works    "checked 551 of 551, 0 duplicates" -- every
                              call had 400'd.
  - fetch_arxiv_authors_batch HTTP 429 became "arXiv has no record of these
                              1,559 papers".
  - check_mcp_discovery_traffic  a Cloudflare GraphQL error became a quiet
                              day WRITTEN TO STATE as the baseline every
                              later run diffs against. That one did not
                              report a wrong number, it persisted one.

The idiom is not wrong in general -- it is right for optional enrichment,
where a nice-to-have field that failed to load should not take a page
down. It is wrong for anything feeding a completeness claim, and this
codebase is almost entirely completeness claims. A silent empty defeats R3
and R4 from underneath: the exclusion never reaches the counter, so the
gate sees a clean result.

TWO copies of this class were written independently on the same day, in
audit_author_extraction.py and check_mcp_discovery_traffic.py, which is
how a convention dies. It is one class, here, and it is a type so that a
caller can catch it WITHOUT catching the transport exceptions it does not
know how to interpret.

HOW TO USE IT

Raise, at the exhaustion of retries, in any fetcher whose result feeds a
count, a stamp, a state file or the graph:

    for attempt in range(4):
        try:
            return session.get(url, timeout=30).json()
        except requests.RequestException as e:
            if attempt == 3:
                raise SourceUnavailable(f"S2 did not answer for {key}: {e}")
            time.sleep(5 * (attempt + 1))

Catch it where the job knows what an unanswered source MEANS, and account
for it there rather than folding it into the result -- the ledger channel
is separate from the exclusion channel precisely so the two cannot merge:

    try:
        rec = fetch(key)
    except SourceUnavailable as e:
        ledger.unanswered("s2_did_not_answer", note=str(e))
        continue
    ...
    ledger.enforce(accept=("not_indexed_by_s2",))   # exit 4 on unanswered

The rule the gate enforces (qc_silent_absence.py): a job that says
"checked N of M" must be able to say how many it ASKED about and how many
ANSWERED. All five instances above become visible the moment those two
numbers are printed separately.
"""
from __future__ import annotations

# The house exit-code contract (CLAUDE.md, syntology/qc.py):
#   0 clean · 1 findings · 2 drift · 3 unaccepted exclusions · 4 unresolved partials
# An unanswered source is a PARTIAL, not an exclusion: nobody decided to
# drop it, the source simply never spoke. It gets 4, and it is deliberately
# NOT reachable through the accept-list that clears a 3 -- accepting
# "s2_did_not_answer" as a category would be accepting a permanent hole.
EXIT_UNRESOLVED_PARTIAL = 4


class SourceUnavailable(RuntimeError):
    """An outside source did not answer: rate limit, timeout, malformed
    request, transport error, an API-level error body, or a response whose
    shape means the question was never really asked.

    Distinct from "the source answered, and has no record" -- and the
    distinction is the whole point. A caller that cannot tell them apart
    reports silence as absence.

    Raise this instead of returning None/[]/{}/0 from any fetcher whose
    result reaches a completeness claim. Returning falsy is correct only
    for optional enrichment, where the caller genuinely does not care why
    the value is missing.

    NOTE ON SCOPE. This exception is for a SOURCE that did not answer, so
    it is network-shaped by nature. The ledger channel it feeds
    (ExclusionLedger.unanswered) is broader and deliberately so: the test
    there is whether anyone can say WHICH answer this was, not whether a
    socket was involved. An extractor that cannot distinguish "found none"
    from "there are none" produces an unanswered question without raising
    anything -- book it with ledger.unanswered() directly.
    """
