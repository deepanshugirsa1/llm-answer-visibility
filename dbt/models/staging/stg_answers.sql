select
    answer_key,
    run_id,
    collected_at,
    toDate(collected_at) as answer_date,
    prompt_id,
    category,
    model_id,
    status,
    latency_ms
from {{ source('lav', 'raw_answers') }}
