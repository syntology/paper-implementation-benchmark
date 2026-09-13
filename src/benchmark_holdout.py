#!/usr/bin/env python3
"""
The substitution experiment's hold-out registry (PREREGISTRATION_SUBSTITUTION.md).

ONE LIST, TWO ENFORCEMENT POINTS. The experiment asks whether the graph's
neighbourhood finds a usable substitute where a flat index cannot. That
question is only asked if the exact answer is unreachable to BOTH arms, and
the only way to make that credible is for both arms to enforce the *same*
sha set rather than each removing its own idea of "the answer". This module
holds that set; `code_only_arm_tools` and `syntology_arm_tools` both consult
it, and `verify_holdout.py` proves mechanically that they do.

WHY THREAD-LOCAL AND NOT A MODULE GLOBAL. agent_harness runs `--workers 2`
as a ThreadPoolExecutor inside ONE process, and both arm modules cache their
driver/index in module globals shared by those threads. A global hold-out
would mean task A's exclusions applying to task B's run, silently, and the
resulting numbers would look completely normal. So the active set is
thread-local, installed by the worker thread that owns the run and removed
in a finally. `verify_holdout.py` runs a two-thread cross-talk check that
fails if this ever regresses.

The set is a set of `code_sha256` strings -- CodeSample identity, never the
entry name (`entry is display, not identity`: 386 of 1,179 served entry
names collide across distinct samples, so an entry-keyed hold-out would
exclude the wrong artifacts and miss the right ones).

A blocked fetch must be INDISTINGUISHABLE from a fetch of something the
corpus never had. If a tool answered "that sample is held out" the subject
would learn that an exact answer exists and is being withheld, which is a
different experiment -- and a leak the transcripts would not obviously show.
So callers raise their own ordinary not-found error; see `code_get`.
"""
from __future__ import annotations

import threading

_state = threading.local()


def set_holdout(shas) -> None:
    """Install the hold-out for the CURRENT thread."""
    _state.shas = frozenset(s for s in (shas or ()) if s)


def clear_holdout() -> None:
    _state.shas = frozenset()


def active() -> frozenset:
    """The hold-out in force on this thread; empty when none is installed.

    Empty is the default and makes every consumer a no-op, which is what
    keeps the v1.5 arms byte-equivalent in behaviour when no hold-out is
    installed (asserted by verify_holdout.py's parity check).
    """
    return getattr(_state, "shas", None) or frozenset()


def blocks(sha: str) -> bool:
    return bool(sha) and sha in active()


class _Scope:
    def __init__(self, shas):
        self.shas = shas
        self.prev = None

    def __enter__(self):
        self.prev = active()
        set_holdout(self.shas)
        return self

    def __exit__(self, *exc):
        set_holdout(self.prev)
        return False


def scope(shas):
    """`with holdout.scope(shas): ...` -- restores the previous set on exit."""
    return _Scope(shas)
