with source as (
    select * from {{ source('olist_bronze', 'orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        order_status,
        timestamp(order_purchase_timestamp)      as order_purchase_ts,
        date(timestamp(order_purchase_timestamp)) as order_purchase_date,
        timestamp(order_approved_at)              as order_approved_ts,
        timestamp(order_delivered_carrier_date)   as order_delivered_carrier_ts,
        timestamp(order_delivered_customer_date)  as order_delivered_customer_ts,
        timestamp(order_estimated_delivery_date)  as order_estimated_delivery_ts
    from source
)

select * from renamed
