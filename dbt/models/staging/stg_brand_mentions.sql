select
    answer_key,
    toDate(collected_at) as answer_date,
    prompt_id,
    category,
    model_id,
    brand,
    mentions,
    rank,
    cited
from {{ source('lav', 'brand_mentions') }}
