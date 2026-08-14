with source as (
    select * from {{ source('olist_bronze', 'order_items') }}
),

renamed as (
    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        timestamp(shipping_limit_date) as shipping_limit_ts,
        cast(price as numeric)         as price,
        cast(freight_value as numeric) as freight_value
    from source
)

select * from renamed
