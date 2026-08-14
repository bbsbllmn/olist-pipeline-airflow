-- Collapses stg_payments (one row per order per payment method) down to one
-- row per order, keeping the dominant payment_type and the total paid.
with payments as (
    select * from {{ ref('stg_payments') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by order_id order by payment_value desc
        ) as rn
    from payments
),

order_totals as (
    select
        order_id,
        sum(payment_value) as total_payment_value
    from payments
    group by order_id
)

select
    r.order_id,
    r.payment_type as primary_payment_type,
    r.payment_installments,
    t.total_payment_value
from ranked r
join order_totals t using (order_id)
where r.rn = 1
