-- Week-over-week movement, the number a marketer actually acts on.
with weekly as (
    select
        toMonday(answer_date) as week,
        category,
        brand,
        sum(answers_naming_brand) / sum(answers_total) as mention_rate
    from {{ ref('mart_share_of_voice') }}
    group by 1, 2, 3
)
select
    week,
    category,
    brand,
    mention_rate,
    lagInFrame(mention_rate) over (
        partition by category, brand order by week
    ) as prev_mention_rate,
    mention_rate - lagInFrame(mention_rate) over (
        partition by category, brand order by week
    ) as delta
from weekly
