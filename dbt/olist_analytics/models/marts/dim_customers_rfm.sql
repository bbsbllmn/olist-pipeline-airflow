-- RFM (Recency, Frequency, Monetary) segmentation, one row per unique
-- customer. Business use: identify at-risk high-value customers ("Champions"
-- gone quiet) vs. new/low-value ones, to target retention campaigns.
with customer_orders as (
    select * from {{ ref('int_customer_orders') }}
),

customer_agg as (
    select
        customer_unique_id,
        max(order_purchase_date) as last_order_date,
        count(distinct order_id) as frequency,
        sum(order_revenue) as monetary
    from customer_orders
    group by customer_unique_id
),

with_recency as (
    select
        *,
        date_diff(
            (select max(order_purchase_date) from customer_orders),
            last_order_date,
            day
        ) as recency_days
    from customer_agg
),

scored as (
    select
        *,
        ntile(5) over (order by recency_days desc) as r_score,   -- 5 = most recent
        ntile(5) over (order by frequency asc)      as f_score,  -- 5 = most frequent
        ntile(5) over (order by monetary asc)       as m_score   -- 5 = highest spend
    from with_recency
)

select
    customer_unique_id,
    last_order_date,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    r_score + f_score + m_score as rfm_total,
    case
        when r_score >= 4 and f_score >= 4 and m_score >= 4 then 'Champions'
        when r_score >= 4 and f_score <= 2 then 'New / Promising'
        when r_score <= 2 and f_score >= 4 and m_score >= 4 then 'At Risk (high value)'
        when r_score <= 2 and f_score <= 2 then 'Lost / Low Value'
        else 'Needs Attention'
    end as customer_segment
from scored
