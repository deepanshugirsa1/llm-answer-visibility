-- Share of voice: of the answers a brand could have appeared in, how many
-- named it, how early, and how often a citation pointed back at it.
with answers as (
    select answer_date, category, model_id, count(*) as answers_total
    from {{ ref('stg_answers') }}
    where status = 'ok'
    group by 1, 2, 3
),
named as (
    select answer_date, category, model_id, brand,
           count(*)         as answers_naming_brand,
           avg(rank)        as avg_rank,
           avg(cited)       as cited_rate
    from {{ ref('int_answer_brand') }}
    where brand is not null
    group by 1, 2, 3, 4
)
select
    n.answer_date,
    n.category,
    n.model_id,
    n.brand,
    n.answers_naming_brand,
    a.answers_total,
    n.answers_naming_brand / a.answers_total as mention_rate,
    n.avg_rank,
    n.cited_rate
from named n
join answers a using (answer_date, category, model_id)
