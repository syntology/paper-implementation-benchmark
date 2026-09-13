"""
`query_engine` -- a stand-in, not the real thing.

`syntology_arm_tools.py` imports `linker` and `templates` from this package at
module load, and `agent_harness.py` imports that module unconditionally. In
Syntology's working repo those are the production paper-resolution and Cypher
template modules; they are NOT published, because they are the live serving
path of a private system rather than part of this benchmark.

This stand-in exists so that the arms which DO run outside Syntology -- `none`,
`code_only`, and `search` with your own API keys -- can import the harness and
start. Any actual use of the graph arm's paper tools raises with a sentence
that says why, rather than an ImportError three frames deep or, worse, a
quietly wrong answer.

If you have the real package, put it ahead of `src/vendor/` on `PYTHONPATH`
and it takes precedence; nothing here has to be removed.

What this means for reproduction: the `syntology` and `syntology_ho` arms
cannot be re-run outside Syntology at all. The graph they read is private, and
publishing a snapshot of it is a separate decision from publishing this
benchmark. Their per-run structure, referee outcomes and analyses are in
`data/`, so their NUMBERS are auditable even though their RUNS are not
repeatable. See REPRODUCTION.md.
"""


class _Unavailable:
    def __init__(self, name):
        self._name = name

    def __getattr__(self, attr):
        raise NotImplementedError(
            f"query_engine.{self._name}.{attr} is not available: the Syntology "
            f"graph arm reads a private Neo4j graph through production serving "
            f"code that is not published with this benchmark. The `none`, "
            f"`code_only` and `search` arms do not need it. See REPRODUCTION.md."
        )


linker = _Unavailable("linker")
templates = _Unavailable("templates")
