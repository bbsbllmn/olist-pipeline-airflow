with source as (
    select * from {{ source('olist_bronze', 'order_payments') }}
),

-- one row per order per payment method (a single order can be split across
-- multiple installments/methods in the raw data)
aggregated as (
    select
        order_id,
        payment_type,
        max(payment_installments)        as payment_installments,
        sum(cast(payment_value as numeric)) as payment_value
    from source
    group by order_id, payment_type
)

select * from aggregated
