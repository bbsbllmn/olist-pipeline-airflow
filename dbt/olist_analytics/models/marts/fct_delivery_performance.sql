{{
  config(
    partition_by={'field': 'order_purchase_date', 'data_type': 'date'},
    cluster_by=['customer_state']
  )
}}

-- Actual vs. estimated delivery performance per order and seller. Business use: which
-- states/sellers are chronically late, and how much lead-time buffer Olist
-- should quote customers by region.
with orders as (
    select * from {{ ref('stg_orders') }}
    where order_status = 'delivered'
      and order_delivered_customer_ts is not null
),

customers as (
    select * from {{ ref('stg_customers') }}
),

items as (
    select distinct order_id, seller_id from {{ ref('stg_order_items') }}
)

select
    o.order_id,
    o.order_purchase_date,
    c.customer_state,
    it.seller_id,
    date_diff(
        date(o.order_delivered_customer_ts), date(o.order_purchase_ts), day
    ) as actual_delivery_days,
    date_diff(
        date(o.order_estimated_delivery_ts), date(o.order_purchase_ts), day
    ) as estimated_delivery_days,
    date_diff(
        date(o.order_delivered_customer_ts), date(o.order_estimated_delivery_ts), day
    ) as days_late,
    o.order_delivered_customer_ts > o.order_estimated_delivery_ts as is_late_delivery
from orders o
join customers c on o.customer_id = c.customer_id
left join items it on o.order_id = it.order_id
