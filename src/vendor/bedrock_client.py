#!/usr/bin/env python3
"""
bedrock_client.py -- the ONE way this codebase calls Bedrock.

Closes the Titan retry gap (user-flagged 2026-08-28, the only defect in
that audit that LOSES work instead of misrecording it): four scripts
called Bedrock four different ways, and the ones without retries turned
any transient throttle into lost work -- a skipped embedding, a dropped
narration, a user-facing reviewer-bot failure.

    from bedrock_client import invoke_model_with_retry, embed_titan

    vec  = embed_titan(client, text)                       # Titan text v2
    body = invoke_model_with_retry(client, model_id=..., body={...})

Retry policy, uniform everywhere: exponential backoff with full jitter
on the retryable failure classes only (throttles, timeouts, 5xx-shaped
service errors, connection drops). Non-retryable errors (validation,
access denied, model not found) raise IMMEDIATELY -- retrying a bad
request is not resilience, it is noise with a bill. Exhaustion raises
BedrockRetriesExhausted so callers decide what a lost call means for
THEIR run (count it, exit 4, degrade) -- the client never swallows it.

Throttle accounting is a first-class output, not a log line: pass
on_throttle=ledger-style callable (or read the returned
`InvocationStats`) so a run's provenance can carry how contended the
lane was. Acceptance for the consolidation is greppable and enforced:
qc_bedrock_discipline.py fails the suite if a bare `.invoke_model(`
exists in live code outside this module.

No converse() path existed here until 2026-08-29 -- every script drafting a
spec or generating code (Converse, not InvokeModel) built its own client and
its own retry, which is exactly the "four scripts, four policies" problem
this module exists to close, just on the other API. Consolidating onto
converse_with_retry / converse_text is the prerequisite qc_bedrock_discipline.py
names for retiring the 32-script own-client census (measured worst case:
<INTERNAL>/13's call_with_backoff retries only on the string "Throttling",
so ServiceUnavailableException/InternalServerException/ModelTimeoutException
and read timeouts are silently NOT retried -- lost work, not misrecorded).
"""
from __future__ import annotations

import json
import random
import time

from botocore.exceptions import BotoCoreError, ClientError

TITAN_MODEL_ID = "amazon.titan-embed-text-v2:0"

# WHICH DOOR WE USE, and what each one is worth per day (us-east-1 service quotas,
# read 2026-09-07). We had been calling the SMALLEST one and treating its cap as a
# fact about Bedrock rather than a fact about our own model id:
#
#   us.anthropic.claude-sonnet-4-5      5,400,000/day   <- what every lane used
#   global.anthropic.claude-sonnet-4-5 10,800,000/day   <- same model, 2x, reachable
#   ...-4-5 1M Context (global)        54,000,000/day   <- 10x
#   mistral.mistral-large-3-675b    5,400,000,000/day   <- 1,000x
#   deepseek.v3.2                   5,400,000,000/day   <- 1,000x
#
# The two peer families are not a downgrade on the work we actually run them on:
# measured 2026-09-07, Mistral 94% / DeepSeek 88% / Sonnet 70% V2+ on the peer
# implementation bake-off, and both answered 90/90 relation judgements while Sonnet
# failed 64 of 90 to its cap. Reach for PEERS first on judging and extraction; keep
# Sonnet for drafting, where it was measured better.
HAIKU = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
SONNET = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
SONNET_REGIONAL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"   # the 5.4M pool, as a fallback
MISTRAL = "mistral.mistral-large-3-675b-instruct"
DEEPSEEK = "deepseek.v3.2"
PEERS = (MISTRAL, DEEPSEEK)   # independent of each other and of llama; 5.4B/day each
LLAMA = "us.meta.llama3-3-70b-instruct-v1:0"

# LANE PARTITION (2026-09-04). The interactive front door and the long-running
# batch lanes share one AWS account, and a per-day token cap is scoped per MODEL
# and per REGION -- measured directly: Haiku was ServiceUnavailable in us-east-1
# while Sonnet answered there in 1.4s, and Haiku answered in us-west-2.
#
# The incident these exist to prevent already happened, to us, in the same hour
# they were written: three harvest-verification workers on Sonnet us-east-1
# exhausted every link of the /ask terminal's fallback chain, and a terminal
# question came back BedrockDayCapped. Our own background job took the human
# front door down. That is survivable while nobody is looking and not
# survivable when someone is.
#
# THESE TWO LISTS MUST STAY DISJOINT. qc_bedrock_lanes.py enforces it.
# Interactive leads with the measured-fastest link, because a person is waiting;
# batch leads with throughput, because nobody is.
# The split is BY REGION, deliberately: "interactive is us-west-2, batch is
# us-east-1" is a rule a person can hold in their head and check at a glance,
# and every batch script already written targets us-east-1, so they are
# compliant without being touched. A first attempt partitioned per (model,
# region) and immediately put Haiku us-east-1 -- which five existing batch
# scripts use, including the running fixture synthesiser -- on the interactive
# side. The gate caught it. Keep the rule dumb enough to stay true.
INTERACTIVE_LANE = [
    (SONNET, "us-west-2"),
    (HAIKU, "us-west-2"),
]
BATCH_LANE = [
    (SONNET, "us-east-1"),
    (LLAMA, "us-east-1"),
    (HAIKU, "us-east-1"),
]

# The region a user-facing call must be made in, derived from the lane
# above rather than written out a second time.
#
# This constant exists because the split was documented, tested and then
# not used by the one process it was written to protect. main.py built
# its own boto3 client from AWS_DEFAULT_REGION, which the deployed
# service sets to us-east-1 -- so every narration, every Text2Cypher
# generation and every explorer turn the front door made was running in
# the BATCH region, sharing a quota with the verification jobs. Measured
# live 2026-09-05 while a code-verification run was going: the same
# narration that takes ~1.0s from us-west-2 took a request from 2s to
# 22-50s, and one of them gave up without narrating at all.
INTERACTIVE_REGION = INTERACTIVE_LANE[0][1]

# How long one interactive model call may hold the socket. Deliberately
# shorter than the request budget it lives inside (SYNTOLOGY_ASK_BUDGET_S,
# 25s): a call that cannot be abandoned is a budget that cannot be kept,
# and the ladder needs room to give up and say so.
INTERACTIVE_READ_TIMEOUT_S = 12
# What a call actually costs, per 1M tokens, at Bedrock list price.
#
# One table, here, because this module is the one place that owns which
# models exist. Before 2026-09-05 there were two `_dollar_cost`
# functions in two modules, each hardcoding ONE model's prices and each
# used by call sites running a different model: text2cypher priced
# everything at Sonnet, and graph_explorer_fallback priced everything at
# Haiku. So the explorer's cost was reported 3x high and any Sonnet turn
# that reached the other function was reported 3x low, in the same
# product, from the same field name. A cost you cannot trust is worse
# than no cost, because it gets quoted.
#
# The surcharge is the regional uplift this account pays and applies to
# both directions.
PRICE_PER_1M = {
    SONNET: {"in": 3.00, "out": 15.00},
    HAIKU: {"in": 1.00, "out": 5.00},
    LLAMA: {"in": 0.72, "out": 0.72},
    # The peers were UNPRICED until 2026-09-07, which means every peer cost this
    # project reported was silently billed at the fallback -- the most expensive rate
    # known, i.e. Sonnet's. That is the safe direction to be wrong in and it still
    # misled: it made the peers look 6x more expensive than they are, in the same
    # week their measured quality beat Sonnet's on two tasks.
    # Rates below come from this repo's own August pricing research
    # (pilot_method_concept_extraction.py, WHITEPAPER.md). Mistral's entry is recorded
    # there as being FOR Mistral Large 3 specifically. DeepSeek V3.2's is the sharpest
    # uncertainty: the repo only ever priced DeepSeek-R1, a REASONING model that burns
    # output tokens on internal reasoning, so R1's $1.35/$5.40 is an upper bound for
    # V3.2 rather than its rate. Priced at R1 until confirmed, so the error stays
    # conservative.
    MISTRAL: {"in": 0.50, "out": 1.50},          # repo-researched, Mistral Large 3
    DEEPSEEK: {"in": 1.35, "out": 5.40},         # UPPER BOUND (DeepSeek-R1's rate)
}
PRICE_CONFIDENCE = {
    SONNET: "confirmed", HAIKU: "confirmed", LLAMA: "confirmed",
    MISTRAL: "repo-researched 2026-08-13",
    DEEPSEEK: "UPPER BOUND -- priced at DeepSeek-R1, V3.2's own rate unconfirmed",
}
REGIONAL_SURCHARGE = 1.10


def dollar_cost(tokens_in: int, tokens_out: int, model_id: str | None = None) -> float:
    """Real cost for THIS model's tokens.

    An unrecognised model is priced at the most expensive rate we know
    rather than the cheapest: a cost estimate that is quietly too low is
    the one that gets built into a price.
    """
    price = PRICE_PER_1M.get(model_id or "")
    if price is None:
        price = max(PRICE_PER_1M.values(), key=lambda p: p["out"])
    return ((tokens_in or 0) / 1_000_000 * price["in"]
            + (tokens_out or 0) / 1_000_000 * price["out"]) * REGIONAL_SURCHARGE


TITAN_DIMENSIONS = 1024
TITAN_MAX_CHARS = 8000

RETRYABLE_ERROR_CODES = {
    "ThrottlingException", "TooManyRequestsException", "ServiceUnavailableException",
    "InternalServerException", "ModelTimeoutException", "ServiceQuotaExceededException",
}


class BedrockRetriesExhausted(Exception):
    """All attempts spent on retryable failures. Carries the attempt count
    and the last underlying error; the caller decides what a lost call
    means for its run."""

    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Bedrock call failed after {attempts} attempts; "
                         f"last error: {type(last_error).__name__}: {last_error}")


class BedrockDayCapped(Exception):
    """A per-DAY token cap, not transient throttling -- both surface as
    ThrottlingException with the same error CODE, distinguishable only by
    message text ("Too many tokens"). Retrying against a day cap with the
    normal backoff ladder just spends the full max_attempts budget
    (measured: 711 of 719 errors in one sweep were exactly this, burned
    against a wall no amount of waiting clears). Raised immediately,
    bypassing the retry loop entirely, so a caller running multiple models
    can abandon the capped one mid-run instead of stalling on it."""

    def __init__(self, model_id: str, underlying: Exception):
        self.model_id = model_id
        self.underlying = underlying
        super().__init__(f"{model_id} is day-capped: {underlying}")


def _is_day_capped(err: Exception) -> bool:
    """A DAILY quota exhaustion, which retrying cannot clear.

    Match "per day" specifically. Bedrock uses "Too many tokens, please
    wait before trying again" for ordinary per-minute token throttling
    too, and this predicate is checked BEFORE the retryable path -- so a
    bare "Too many tokens" match converts a transient TPM throttle into a
    fatal stop that callers treat as "no work available". The daily
    message is distinct: "Too many tokens per day, please wait ..."."""
    m = str(err).lower()
    return "too many tokens" in m and "per day" in m


class InvocationStats:
    """Mutable throttle/retry accounting for one logical run. Attach one
    per script run and put as_dict() into the run's provenance params."""

    def __init__(self):
        self.calls = 0
        self.retries = 0
        self.throttled = 0

    def as_dict(self) -> dict:
        return {"bedrock_calls": self.calls, "bedrock_retries": self.retries,
                "bedrock_throttled": self.throttled}


def _is_retryable(err: Exception) -> bool:
    if isinstance(err, ClientError):
        return err.response.get("Error", {}).get("Code") in RETRYABLE_ERROR_CODES
    # Connection resets, read timeouts, endpoint hiccups -- botocore's
    # non-ClientError family. Anything ClientError-shaped but not in the
    # allowlist (ValidationException, AccessDenied...) is NOT retryable.
    return isinstance(err, BotoCoreError)


def invoke_model_with_retry(client, *, model_id: str, body: dict,
                            max_attempts: int = 6, base_delay_s: float = 1.0,
                        deadline: float | None = None,
                            max_delay_s: float = 30.0,
                            stats: InvocationStats | None = None,
                            on_throttle=None, _sleep=time.sleep) -> dict:
    """One Bedrock invoke_model with the uniform policy. Returns the
    parsed JSON response body. `_sleep` is injectable for tests only."""
    if stats is not None:
        stats.calls += 1
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.invoke_model(modelId=model_id, body=json.dumps(body))
            return json.loads(resp["body"].read())
        except Exception as e:  # classified below; unknown -> raise
            if not _is_retryable(e):
                raise
            last_err = e
            code = e.response["Error"]["Code"] if isinstance(e, ClientError) else type(e).__name__
            if stats is not None:
                stats.retries += 1
                if "Throttl" in code or "TooMany" in code or "Quota" in code:
                    stats.throttled += 1
            if attempt == max_attempts:
                break
            # A retry ladder inside a request budget must know about the
            # budget (2026-09-05). Without this the ladder keeps its own
            # promise -- six attempts with backoff -- while breaking the
            # only one a person can feel. Measured: a 25s budget was in
            # force while a single question spent over three minutes here.
            if deadline is not None and time.monotonic() >= deadline:
                break
            # Full jitter: delay in [0, min(cap, base * 2^(attempt-1))].
            # Deliberately not a fixed ladder -- four processes on one
            # account with the same fixed ladder re-collide forever
            # (measured live 2026-08-24 in 04_resolve_citations.py's
            # adaptive-pacing fix; same physics here).
            cap = min(max_delay_s, base_delay_s * (2 ** (attempt - 1)))
            delay = random.uniform(0, cap)
            if on_throttle is not None:
                on_throttle(attempt, delay, code)
            _sleep(delay)
    raise BedrockRetriesExhausted(max_attempts, last_err)


def embed_titan(client, text: str, *, stats: InvocationStats | None = None,
                on_throttle=None, _sleep=time.sleep) -> list[float]:
    """The Titan text-embedding call every embedder converges on --
    replaces the two hand-rolled copies in generate_embeddings.py and
    reviewer_bot_grounding.py (which duplicated it to dodge argparse
    side effects; this module has none) and the research batcher's."""
    body = invoke_model_with_retry(
        client, model_id=TITAN_MODEL_ID,
        body={"inputText": text[:TITAN_MAX_CHARS],
              "dimensions": TITAN_DIMENSIONS, "normalize": True},
        stats=stats, on_throttle=on_throttle, _sleep=_sleep)
    return body["embedding"]


def converse_with_retry(client, *, model_id: str, messages: list[dict],
                        inference_config: dict | None = None,
                        system: list[dict] | None = None,
                        tool_config: dict | None = None,
                        max_attempts: int = 6, base_delay_s: float = 1.0,
                        deadline: float | None = None,
                        max_delay_s: float = 30.0,
                        stats: InvocationStats | None = None,
                        on_throttle=None, _sleep=time.sleep) -> dict:
    """The Converse-API sibling of invoke_model_with_retry -- same policy,
    same jitter, same accounting, different wire call. Returns the raw
    Converse response dict (not just the text) so a caller that needs
    stopReason/usage/toolUse still has it; converse_text below is the
    batteries-included wrapper most callers actually want.

    Day-cap detection is unconditional, not opt-in: a per-day token cap
    and transient throttling share the same error CODE (ThrottlingException)
    and are distinguishable only by message text. Retrying a day cap with
    this function's own backoff ladder just spends the full max_attempts
    budget against a wall no amount of waiting clears -- measured directly
    in this codebase (a sweep burned 711 of 719 errors exactly this way
    before the distinction existed anywhere). BedrockDayCapped is raised
    immediately, bypassing the retry loop, so a caller running more than
    one model can abandon the capped one mid-run instead of stalling.
    """
    if stats is not None:
        stats.calls += 1
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            # system/toolConfig are passed only when supplied: Converse
            # rejects empty lists for both, so absence must mean absence.
            kwargs = {"modelId": model_id, "messages": messages,
                      "inferenceConfig": inference_config or {}}
            if system:
                kwargs["system"] = system
            if tool_config:
                kwargs["toolConfig"] = tool_config
            return client.converse(**kwargs)
        except Exception as e:
            if _is_day_capped(e):
                raise BedrockDayCapped(model_id, e) from e
            if not _is_retryable(e):
                raise
            last_err = e
            code = e.response["Error"]["Code"] if isinstance(e, ClientError) else type(e).__name__
            if stats is not None:
                stats.retries += 1
                if "Throttl" in code or "TooMany" in code or "Quota" in code:
                    stats.throttled += 1
            if attempt == max_attempts:
                break
            # A retry ladder inside a request budget must know about the
            # budget (2026-09-05). Without this the ladder keeps its own
            # promise -- six attempts with backoff -- while breaking the
            # only one a person can feel. Measured: a 25s budget was in
            # force while a single question spent over three minutes here.
            if deadline is not None and time.monotonic() >= deadline:
                break
            cap = min(max_delay_s, base_delay_s * (2 ** (attempt - 1)))
            delay = random.uniform(0, cap)
            if on_throttle is not None:
                on_throttle(attempt, delay, code)
            _sleep(delay)
    raise BedrockRetriesExhausted(max_attempts, last_err)


def converse_text(client, model_id: str, prompt: str, *, max_tokens: int = 2000,
                  temperature: float = 0.2, stats: InvocationStats | None = None,
                  on_throttle=None, _sleep=time.sleep) -> str:
    """Single-turn text-in/text-out convenience wrapper -- the shape every
    spec-draft and code-generation call site in this codebase actually
    wants (<INTERNAL>/13's call_model, run_v3_sweep's call_model_retry,
    both hand-rolled before this existed). Raises BedrockDayCapped /
    BedrockRetriesExhausted same as the primitive; does not swallow either."""
    resp = converse_with_retry(
        client, model_id=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inference_config={"maxTokens": max_tokens, "temperature": temperature},
        stats=stats, on_throttle=on_throttle, _sleep=_sleep)
    return resp["output"]["message"]["content"][0]["text"]



_CLIENT = None


def client(region: str | None = None, *, interactive: bool = False):
    """The ONE bedrock-runtime client factory (added 2026-09-01). Every
    script that built its own boto3 client also wrote its own retry ladder;
    qc_bedrock_discipline.py's own-client census counts them. A script that
    gets its client here and calls the *_with_retry helpers is out of the
    census by construction. Region: explicit arg, else AWS_DEFAULT_REGION,
    else us-east-1. Credentials are whatever boto3 resolves (env, profile,
    task role) -- nothing is passed explicitly, so a container running under
    an IAM role needs no keys."""
    global _CLIENT
    import os
    resolved = region or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    key = (resolved, bool(interactive))
    # Keyed by region 2026-09-05: this cached ONE client and returned it
    # for any region asked for, so a process that built a batch client
    # first would hand it back to a caller asking for the interactive
    # lane -- silently undoing the lane split at the call it was meant to
    # protect.
    if _CLIENT is None or _CLIENT[0] != key:
        import boto3
        from botocore.config import Config
        if interactive:
            # Someone is waiting. Bound the socket, and let this module's
            # own retry ladder be the ONLY retry ladder -- botocore
            # defaults to 60s read with its own attempts on top, so a
            # hung call multiplied out to minutes underneath a request
            # deadline that could only be checked between calls. Measured
            # 2026-09-05: a single generation blocked in one SSL read for
            # over three minutes while a 25s budget was in force.
            cfg = Config(connect_timeout=3, read_timeout=INTERACTIVE_READ_TIMEOUT_S,
                         retries={"max_attempts": 1, "mode": "standard"})
        else:
            # Batch work is not waited on and would rather finish than
            # fail fast; these are botocore's defaults, stated.
            cfg = Config(connect_timeout=10, read_timeout=120,
                         retries={"max_attempts": 3, "mode": "standard"})
        _CLIENT = (key, boto3.client("bedrock-runtime", region_name=resolved, config=cfg))
    return _CLIENT[1]
