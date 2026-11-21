select
    answer_key,
    toDate(collected_at) as answer_date,
    prompt_id,
    model_id,
    position,
    domain
from {{ source('lav', 'answer_citations') }}
