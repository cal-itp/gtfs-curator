----------------------------------------------------------
-- (1) tiffany_mart_ntd_explore.fct_monthly_ridership_by_mode 
-- save in `mart_ntd_ridership` with source 
-- the 2nd table of last year's year-mode-tos upt is exported to Excel
----------------------------------------------------------
-- adapt fct_complete_monthly_ridership_with_adjustments_and_estimates and remove seed, use macro
-- TODO: rename columns to match: mode_name -> mode_full_name; tos -> type_of_service
-- TODO: annual, can service_type be flagged too?
-- TODO: should annual and monthly both merge in bridge table and keep county_name, rtpa_name, caltrans_district_name?

WITH monthly_upt AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.fct_complete_monthly_ridership_with_adjustments_and_estimates`
    -- {{ ref('fct_complete_monthly_ridership_with_adjustments_and_estimates') }}
    -- this one has dt, execution_ts too
),

fct_monthly_ridership AS (
    SELECT 
        *,
    LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY PERIOD_MONTH, PERIOD_YEAR) AS upt_prior_year_month, 
          upt - LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY PERIOD_MONTH, PERIOD_YEAR) AS upt_change_1yr,
          ROUND(SAFE_DIVIDE(
            (upt - LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY PERIOD_MONTH, PERIOD_YEAR)),
            LAG(upt) OVER (PARTITION BY ntd_id, mode, type_of_service ORDER BY PERIOD_MONTH, PERIOD_YEAR)
        ), 4) AS upt_pct_change_1yr,
)

SELECT * FROM fct_monthly_ridership
