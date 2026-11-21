select
    answer_date,
    domain,
    count(*)      as citations,
    avg(position) as avg_position
from {{ ref('stg_citations') }}
group by 1, 2
