-- One row per delivered order, joined to its customer and total order value,
-- as the base for RFM segmentation in dim_customers_rfm.
with orders as (
    select * from {{ ref('stg_orders') }}
    where order_status in ('delivered', 'shipped')
),

customers as (
    select * from {{ ref('stg_customers') }}
),

items as (
    select
        order_id,
        sum(price + freight_value) as order_revenue
    from {{ ref('stg_order_items') }}
    group by order_id
)

select
    o.order_id,
    c.customer_unique_id,
    o.order_purchase_date,
    i.order_revenue
from orders o
join customers c on o.customer_id = c.customer_id
join items i on o.order_id = i.order_id
