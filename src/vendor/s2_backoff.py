#!/usr/bin/env python3
"""
ONE backoff ladder for Semantic Scholar 429s, measured rather than guessed.

WHY THIS MODULE EXISTS. `backoff = 15 * attempt` was written three separate
times -- 08_fetch_reference_edges.py, and both the title-match and DOI-batch
paths of 04_resolve_citations.py. Fixing it in one place on 2026-08-29 left the
other two, and doi-tier-verify was still logging 15s backoffs a day later. The
standing rule for something that bites twice is a shared module, not a third
patch at the site.

WHAT WAS MEASURED. S2 sends NO Retry-After header on a 429, so there is nothing
to obey and the wait is a pure guess. The limit clears in roughly a second.
Against that, a 15/30/45 ladder spends up to 90 seconds per item waiting out a
window that has already reopened -- on stage 8 that was the difference between
97 and 2,080 papers/minute once corrected.

TWO LADDERS, because the two failure modes are not the same thing:
  * THROTTLE (429): the server is fine and the window reopens almost at once.
    Start at 2s and stay short.
  * NETWORK (timeout, connection reset): something is actually wrong and
    hammering it does not help. Start at 15s.
Collapsing these into one ladder is what made the original wrong in both
directions at once -- too slow for throttling, too fast for a real outage.
"""
from __future__ import annotations

import time

THROTTLE_START_S = 2.0
THROTTLE_CAP_S = 30.0
NETWORK_START_S = 15.0
NETWORK_CAP_S = 180.0


class Backoff:
    """Stateful ladder. Separate throttle/network counters so a burst of 429s
    never inflates the wait for a subsequent real network error, or vice versa.

        b = Backoff()
        ...
        if resp.status_code == 429:
            b.wait_throttled(); continue
    """

    def __init__(self, *, sleep=time.sleep, on_wait=None):
        self._throttle = THROTTLE_START_S
        self._network = NETWORK_START_S
        self._sleep = sleep
        self._on_wait = on_wait

    def wait_throttled(self) -> float:
        w = self._throttle
        if self._on_wait:
            self._on_wait("throttle", w)
        self._sleep(w)
        self._throttle = min(self._throttle * 2, THROTTLE_CAP_S)
        return w

    def wait_network(self) -> float:
        w = self._network
        if self._on_wait:
            self._on_wait("network", w)
        self._sleep(w)
        self._network = min(self._network * 2, NETWORK_CAP_S)
        return w

    def reset(self) -> None:
        """Call after a success: the next 429 starts from the bottom again,
        so a long healthy run never carries a stale inflated wait."""
        self._throttle = THROTTLE_START_S
        self._network = NETWORK_START_S
