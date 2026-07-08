----------------------------------------------------------
-- (1) stg_ntd__complete_monthly_ridership_with_adjustments_and_estimates
-- can I get columns renamed here so the lineage is clearer?
-- fix year, month so they are not strings, just period_year_month is string
----------------------------------------------------------
WITH external_complete_monthly_ridership_with_adjustments_and_estimates AS (
    SELECT *
    FROM {{ source('external_ntd__ridership', 'historical__complete_monthly_ridership_with_adjustments_and_estimates') }}
),

get_latest_extract AS(
    SELECT *
    FROM external_complete_monthly_ridership_with_adjustments_and_estimates
    -- we pull the whole table every month in the pipeline, so this gets only the latest extract
    QUALIFY DENSE_RANK() OVER (ORDER BY execution_ts DESC) = 1
),

stg_ntd__complete_monthly_ridership_with_adjustments_and_estimates AS (
    SELECT
        FORMAT("%05d", CAST(CAST(ntd_id AS NUMERIC) AS INT64)) AS ntd_id,
        {{ trim_make_empty_string_null('agency') }} AS agency,
        SAFE_CAST(date AS DATETIME) AS date,
        CAST(FORMAT_DATE('%m', date) AS INT) AS month,
        CAST(FORMAT_DATE('%Y', date) AS INT) AS year,
        DATE(CAST(FORMAT_DATE('%Y', date) AS INT), CAST(FORMAT_DATE('%m', date) AS INT), 1) AS month_first_day,
        {{ trim_make_empty_string_null('tos') }} AS type_of_service,
        {{ trim_make_empty_string_null('mode') }} AS mode,
        {{ trim_make_empty_string_null('agency_mode_tos_date') }} AS agency_mode_tos_date,
        SAFE_CAST(voms AS NUMERIC) AS voms,
        SAFE_CAST(upt AS NUMERIC) AS upt,
        {{ trim_make_empty_string_null('_3_mode') }} AS _3_mode,
        SAFE_CAST(vrm AS NUMERIC) AS vrm,
        {{ trim_make_empty_string_null('uza_name') }} AS uza_name,
        FORMAT("%05d", SAFE_CAST(uace_cd AS INT64)) AS uace_cd,
        {{ trim_make_empty_string_null('fta_region') }} AS fta_region,
        {{ trim_make_empty_string_null('state') }} AS state,
        {{ trim_make_empty_string_null('reporter_type') }} AS reporter_type,
        {{ trim_make_empty_string_null('mode_type_of_service_status') }} AS mode_type_of_service_status,
        SAFE_CAST(vrh AS NUMERIC) AS vrh,
        {{ trim_make_empty_string_null('legacy_ntd_id') }} AS legacy_ntd_id,
        dt,
        execution_ts,
    FROM get_latest_extract
    WHERE ntd_id IS NOT NULL

)

SELECT * FROM stg_ntd__complete_monthly_ridership_with_adjustments_and_estimates


----------------------------------------------------------
-- (2) fct_complete_monthly_ridership_with_adjustments_and_estimates
----------------------------------------------------------
{{ config(materialized="table") }}

WITH staging_complete_monthly_ridership_with_adjustments_and_estimates AS (
    SELECT *
    FROM {{ ref('stg_ntd__complete_monthly_ridership_with_adjustments_and_estimates') }}
),

dim_agency_information AS (
    SELECT
        ntd_id,
        year,
        agency_name,
        city,
        state,
    FROM `cal-itp-data-infra.mart_ntd_annual_reporting.dim_agency_information`--{{ ref('dim_agency_information') }}
    GROUP BY 1, 2, 3, 4, 5
),

fct_complete_monthly_ridership_with_adjustments_and_estimates AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['stg.ntd_id', 'stg.mode', 'stg.type_of_service', 'month_first_day']) }} as key,

        stg.ntd_id,
        stg.agency,

        stg.date,
        stg.month,
        stg.year,
        stg.month_first_day,
        stg.type_of_service,
        stg.mode,

        {{ generate_ntd_mode_full_name('mode') }} AS mode_full_name,
        {{ generate_ntd_type_of_service_full_name('type_of_service') }} AS type_of_service_full_name,
        {{ generate_ntd_mode_service_type('stg.mode') }} AS service_type,

        stg.agency_mode_tos_date,
        stg.voms,
        stg.upt,
        stg._3_mode,
        stg.vrm,
        stg.uza_name,
        stg.uace_cd,
        stg.fta_region,
        stg.state,
        stg.reporter_type,
        stg.mode_type_of_service_status,
        stg.vrh,

        LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY month_first_day) AS upt_prior_year_month,
            upt - LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY month_first_day) AS upt_change_1yr,
        ROUND(SAFE_DIVIDE(
            (upt - LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY month_first_day)),
            LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY month_first_day)
        ), 4) AS upt_pct_change_1yr,

        stg.legacy_ntd_id,
        stg.dt,
        stg.execution_ts
    FROM staging_complete_monthly_ridership_with_adjustments_and_estimates AS stg
)

SELECT * FROM fct_complete_monthly_ridership_with_adjustments_and_estimates
