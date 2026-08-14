-- Pre-aggregated monthly revenue with MoM/YoY growth, for direct BI
-- consumption (Looker Studio) without recomputing window functions on the
-- much larger fct_sales table each time a dashboard loads.
with monthly as (
    select
        order_month,
        product_category_name_english,
        sum(revenue) as revenue,
        sum(freight_value) as freight,
        count(distinct order_id) as order_count,
        sum(revenue) / nullif(count(distinct order_id), 0) as avg_order_value
    from {{ ref('fct_sales') }}
    group by order_month, product_category_name_english
)

select
    *,
    lag(revenue) over (
        partition by product_category_name_english order by order_month
    ) as prev_month_revenue,
    safe_divide(
        revenue - lag(revenue) over (
            partition by product_category_name_english order by order_month
        ),
        lag(revenue) over (
            partition by product_category_name_english order by order_month
        )
    ) as mom_growth_pct,
    lag(revenue, 12) over (
        partition by product_category_name_english order by order_month
    ) as revenue_12mo_ago,
    safe_divide(
        revenue - lag(revenue, 12) over (
            partition by product_category_name_english order by order_month
        ),
        lag(revenue, 12) over (
            partition by product_category_name_english order by order_month
        )
    ) as yoy_growth_pct
from monthly
