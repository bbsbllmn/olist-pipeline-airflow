-- Seller-level scorecard: revenue, review score, and late-delivery rate.
-- Business use: marketplace curation -- which sellers to promote, coach, or
-- offboard.
with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
    where order_status = 'delivered'
),

reviews as (
    select * from {{ ref('stg_reviews') }}
),

delivery as (
    select * from {{ ref('fct_delivery_performance') }}
),

seller_revenue as (
    select
        seller_id,
        count(distinct order_id) as total_orders,
        sum(price + freight_value) as total_revenue
    from items
    group by seller_id
),

seller_reviews as (
    select
        i.seller_id,
        avg(r.review_score) as avg_review_score
    from items i
    join reviews r on i.order_id = r.order_id
    group by i.seller_id
),

seller_delivery as (
    select
        seller_id,
        avg(cast(is_late_delivery as int64)) as late_delivery_rate
    from delivery
    where seller_id is not null
    group by seller_id
)

select
    r.seller_id,
    r.total_orders,
    r.total_revenue,
    rv.avg_review_score,
    d.late_delivery_rate
from seller_revenue r
left join seller_reviews rv on r.seller_id = rv.seller_id
left join seller_delivery d on r.seller_id = d.seller_id
