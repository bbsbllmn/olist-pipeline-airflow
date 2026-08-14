{% macro generate_schema_name(custom_schema_name, node) -%}
    {#- Use the custom schema (silver/gold) as the actual BigQuery dataset name,
        rather than dbt's default "<target_schema>_<custom_schema>" concatenation.
        This lets models declare `+schema: silver` / `+schema: gold` in
        dbt_project.yml and land straight in `olist_silver` / `olist_gold`. -#}
    {%- if custom_schema_name is not none -%}
        {{ 'olist_' ~ custom_schema_name | trim }}
    {%- else -%}
        {{ target.schema }}
    {%- endif -%}
{%- endmacro %}
