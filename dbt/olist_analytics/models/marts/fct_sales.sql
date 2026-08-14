{{
  config(
    partition_by={'field': 'order_purchase_date', 'data_type': 'date'},
    cluster_by=['product_category_name_english', 'primary_payment_type']
  )
}}

with orders as (
    select * from {{ ref('stg_orders') }}
    where order_status in ('delivered', 'shipped')
),

items as (
    select * from {{ ref('stg_order_items') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

payments as (
    select * from {{ ref('int_order_payments_summary') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
)

select
    o.order_id,
    o.order_purchase_date,
    date_trunc(o.order_purchase_date, month) as order_month,
    o.order_status,
    c.customer_state,
    p.product_category_name_english,
    p.product_name_length,
    i.product_id,
    i.seller_id,
    i.price,
    i.freight_value,
    i.price + i.freight_value as revenue,
    pay.primary_payment_type,
    pay.payment_installments
from orders o
join items i on o.order_id = i.order_id
left join products p on i.product_id = p.product_id
left join payments pay on o.order_id = pay.order_id
left join customers c on o.customer_id = c.customer_id
