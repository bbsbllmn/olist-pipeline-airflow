with source as (
    select * from {{ source('olist_bronze', 'order_reviews') }}
),

-- an order can have more than one review row in the raw data; keep the most
-- recent review per order
deduped as (
    select
        order_id,
        review_id,
        cast(review_score as int64) as review_score,
        timestamp(review_creation_date) as review_creation_ts,
        row_number() over (
            partition by order_id order by review_creation_date desc
        ) as rn
    from source
)

select
    order_id,
    review_id,
    review_score,
    review_creation_ts
from deduped
where rn = 1
