-- LLM Answer Visibility — ClickHouse schema.
-- ReplacingMergeTree on answer_key makes a re-run of the same (run, prompt,
-- model) idempotent: the newer row wins on merge instead of double counting.

CREATE DATABASE IF NOT EXISTS lav;

CREATE TABLE IF NOT EXISTS lav.raw_answers
(
    answer_key    String,
    run_id        String,
    collected_at  DateTime64(3, 'UTC'),
    prompt_id     LowCardinality(String),
    category      LowCardinality(String),
    prompt_text   String,
    model_id      LowCardinality(String),
    answer_text   String,
    latency_ms    UInt32,
    status        LowCardinality(String)
)
ENGINE = ReplacingMergeTree(collected_at)
PARTITION BY toYYYYMM(collected_at)
ORDER BY (answer_key);

CREATE TABLE IF NOT EXISTS lav.answer_citations
(
    answer_key    String,
    run_id        String,
    collected_at  DateTime64(3, 'UTC'),
    prompt_id     LowCardinality(String),
    model_id      LowCardinality(String),
    position      UInt16,
    url           String,
    domain        LowCardinality(String)
)
ENGINE = ReplacingMergeTree(collected_at)
PARTITION BY toYYYYMM(collected_at)
ORDER BY (answer_key, position);

CREATE TABLE IF NOT EXISTS lav.brand_mentions
(
    answer_key    String,
    run_id        String,
    collected_at  DateTime64(3, 'UTC'),
    prompt_id     LowCardinality(String),
    category      LowCardinality(String),
    model_id      LowCardinality(String),
    brand         LowCardinality(String),
    mentions      UInt16,
    rank          UInt16,
    cited         UInt8
)
ENGINE = ReplacingMergeTree(collected_at)
PARTITION BY toYYYYMM(collected_at)
ORDER BY (answer_key, brand);

-- Daily rollup. Incremental by design: the mart reads one partition per run
-- rather than rescanning raw_answers, which is what keeps cost flat as the
-- answer corpus grows.
CREATE MATERIALIZED VIEW IF NOT EXISTS lav.mv_brand_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, category, brand)
AS SELECT
    toDate(collected_at) AS day,
    category,
    brand,
    count()              AS answers_naming_brand,
    sum(cited)           AS cited_answers,
    sum(rank)            AS rank_sum
FROM lav.brand_mentions
GROUP BY day, category, brand;
