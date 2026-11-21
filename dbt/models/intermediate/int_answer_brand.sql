-- One row per answer per brand, with the answer grain attached so the marts
-- can divide by "answers that could have named this brand".
select
    a.answer_key,
    a.answer_date,
    a.category,
    a.model_id,
    m.brand,
    m.mentions,
    m.rank,
    m.cited
from {{ ref('stg_answers') }} a
left join {{ ref('stg_brand_mentions') }} m using (answer_key)
where a.status = 'ok'
