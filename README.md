# LLM Answer Visibility

Track how brands show up in AI assistant answers: run a prompt set across
several models on a schedule, land the raw answers, extract brand mentions and
citations, and publish share-of-voice and citation-rank marts — with quality
gates that fail the build before a wrong number reaches a report.

The hard part is not the dashboard. It is that the source is unstructured prose
from a system that answers differently every run, so the pipeline has to be
idempotent, the parser has to be guarded, and a swing in the numbers has to be
provably a real change rather than a parsing regression.

## What it does

1. **Collect** — every prompt in `config/prompts.yml` against every model in
   `config/models.yml`, one row per prompt-model pair.
2. **Parse** — citations (markdown links and bare URLs, deduped, ordered,
   normalised to domains) and brand mentions (alias matching, longest-alias
   first, word-boundary safe, ranked by first appearance, flagged when a
   citation points back at the brand's own domain).
3. **Store** — ClickHouse `ReplacingMergeTree` keyed on `answer_key`, so a
   replayed run cannot double count. A file-backed store mirrors the same
   layout for local runs and CI.
4. **Model** — dbt staging → intermediate → marts: `mart_share_of_voice`,
   `mart_citation_rank`, `mart_visibility_movement` (week over week).
5. **Gate** — coverage, freshness, parse yield and drift checks. P0 exits 2,
   P1 exits 1, so CI fails rather than publishing.

## Run it

```bash
pip install -r requirements.txt
make all          # run -> report -> check
make test         # 27 tests
```

No API keys and no network: the default provider is deterministic and offline.

Sample output:

```
Lumen Metrics            83.3%  avg rank  2.2  cited 100.0%
Northwind Analytics      75.0%  avg rank 2.06  cited 100.0%
Castellan Data           70.8%  avg rank 2.18  cited 100.0%
Pathline                 70.8%  avg rank 1.94  cited 100.0%
```

## Layout

```
config/      prompt set, tracked brands and aliases, model registry
src/lav/     config, providers, collect, parse, store, report, quality, cli
sql/         ClickHouse DDL (ReplacingMergeTree + SummingMergeTree rollup)
dbt/         staging -> intermediate -> marts, with schema tests and freshness
tests/       27 pytest tests
docs/        design notes and tradeoffs
```

## Design notes

See [docs/DESIGN.md](docs/DESIGN.md) for why answers and derived rows are
separated, how idempotency works, why the daily rollup is incremental rather
than a full refresh, and what the parse-yield gate is guarding against.

## Status — what has and has not been run

**Exercised:** the whole pipeline through the offline store — collection,
parsing, dedupe, marts, quality gates, 27 passing tests, CI on every push plus
a daily scheduled run.

**Written and schema-reviewed, not yet run against a live server:** the
ClickHouse store (`src/lav/store/clickhouse.py`), the DDL in
`sql/clickhouse/schema.sql`, and the dbt models, which target ClickHouse.

**Not built:** real model providers (the interface is one method —
`answer(prompt_text) -> AnswerResult`), sentence-level prominence scoring
beyond first-appearance rank, and sentiment on the mention.

The numbers above come from the bundled synthetic corpus, not production
traffic.
