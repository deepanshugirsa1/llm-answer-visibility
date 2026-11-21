# Design notes

## Why these three tables
`raw_answers` keeps the model's prose exactly as returned. Everything else is
derived, so when the parser changes the answers do not have to be re-collected —
re-parsing is cheap, re-querying a model is not. `answer_citations` and
`brand_mentions` are the two structured views a marketer actually asks about:
*who got named* and *who got linked*.

## Idempotency
`answer_key = sha256(run_id | prompt_id | model_id)` is the natural key.
ClickHouse uses `ReplacingMergeTree(collected_at)` ordered by that key, and the
offline store's `dedupe()` keeps the last row per key. A retried or partially
failed run can be replayed whole without inflating mention counts — which would
otherwise show up as a brand "gaining visibility" purely because a job retried.

## Incremental by default
`mv_brand_daily` is a `SummingMergeTree` materialized view fed on insert, so the
daily rollup never rescans the full answer corpus. The tradeoff: late-arriving
rows for an earlier day need a targeted re-aggregation of that partition rather
than a free full refresh. At this grain that is the right trade — the corpus
only grows, and the alternative is a full scan whose cost rises every day.

## Rank, not just presence
Being named third in an answer is not the same as being named first. `rank` is
the order of first appearance within an answer, which is the closest available
proxy for prominence without parsing sentence structure. `cited` is tracked
separately because a brand can be discussed without being linked, and a domain
can be cited without the brand being named.

## Quality gates before marts
Four checks run before anything is reported: coverage (every prompt-model pair
present), freshness (newest answer inside the window), parse yield (a parser
that silently stops matching looks exactly like a brand vanishing), and drift (a
swing beyond threshold is flagged, not published). The parse-yield check exists
because the failure it catches is invisible in the output — the marts still
build, they are just wrong.

## What is synthetic
The offline provider composes answers deterministically from a hash of
(model, prompt). It exercises the full path — collection, parsing, storage,
aggregation, gating — with no network. Swapping in a real provider means
implementing one method; nothing downstream changes.
