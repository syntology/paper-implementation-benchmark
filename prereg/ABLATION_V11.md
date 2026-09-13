# v1.1 ablation: is 0/24 adoption fixable with words alone?

**Pre-registered 2026-08-31, before any v1.1 run.** Run 1 found the
`both` arm never called `get_reference_implementation` (0/24). Before
proposing any serving-code change, measure whether description-level
salience alone moves adoption.

**Intervention (one bundle, mirroring what mcp_server.py could ship):**
in the `both` arm only — (a) syntology tools listed BEFORE search tools
in the tool config; (b) `get_reference_implementation` description
opens with "For known ML methods, CHECK THIS FIRST — one call returns
verified ready-to-run code, usually replacing paper+repo search
entirely"; (c) `list_reference_implementations` description gains "if a
multi-word query returns 0, retry with the single most distinctive
token — matching is whole-string substring." Nothing else changes:
same tasks, model, budgets, referee; output to `runs_v11/`.

**Predictions:** adoption (any getref call) ≥ 12/24; in-catalog
`both` pass ≥ 10/12; median in-catalog cost drops below $0.30 (v1:
$0.488). **Decision:** adoption ≥ 12 → propose the description change
for production serving (owner sign-off; serving files under active
edit today). Adoption < 6 → words are insufficient; the fix is
structural (tool consolidation or resolver behavior), and that goes to
v2 design instead.

## RESULT (2026-08-31, 24/24 runs, $8.87)

**Adoption 1/24 → the <6 rule fires: words are insufficient, the fix
is structural.** Prediction 1 wrong (1 vs ≥12); prediction 2 right
(10/12 in-catalog); prediction 3 partially (cost fell to $0.406
in-catalog median, not $0.30).

Secondary, suggestive-only (n=24, +3/−0 paired, p≈0.25): the bundle
still improved everything — pass 18/24 vs 15/24, arm cost $8.87 vs
$12.94, wall median ~88s vs ~140s, no-submissions 3 vs 5 — but NOT via
the intended mechanism, so it cannot be attributed to salience wording.

**Why words failed, from the v1.1 tool mix:** agents adopted the
graph's PAPER tools at near-parity with search (get_paper 23 calls,
get_code_for_paper 18, vs github_fetch_file 89, fetch_url 92) and then
went to GitHub for code. The learned workflow shape is "graph =
metadata, GitHub = code"; a promoted description does not override it.

**Structural proposal for serving (needs owner sign-off):** put
verified code on the path agents already walk — `get_code_for_paper`
(called in 18/24 runs) and `get_paper` should carry an inline
`verified_reference_implementations` block (or at minimum a one-line
pointer naming the exact `get_reference_implementation` call) whenever
served samples exist for that paper's methods. Plus the resolver fix
from run 1 (tokenized AND-matching in list/get — the browse-zero
defect is independent of this one). MCP server-level `instructions`
(system-context, stronger than tool descriptions) is the third lever.
