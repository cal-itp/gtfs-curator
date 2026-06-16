----------------------------------------------------------
-- (1) tiffany_mart_ntd_explore.fct_service_data_time_series_by_mode
-- fct_service_data_and_operating_expenses_time_series_by_mode_[one_excel_sheet] feel repetitive
-- service values: upt, vrh, vrm, voms, pmt
-- funding values: vo, vm, nvm, ga, total
-- what's there: noticed that intermediate tables all use `dim_agency_information`
-- what I want to change: combine the intermediate tables, then bring in dim_agency_information, and filter out bad keys
----------------------------------------------------------
WITH int_upt AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_upt`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_upt') }}
),

int_vrh AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_vrh`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_vrh') }}
),

int_vrm AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_vrm`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_vrm') }}
),

int_voms AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_voms`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_voms') }}
),

int_pmt AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_pmt`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_pmt') }}
),

-- funding
int_vo AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_vo`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_vo') }}
),

int_vm AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_vm`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_vm') }}
),

int_ga AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_ga`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_ga') }}
),

int_nvm AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_nvm`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_nvm') }}
),

int_total AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_total`
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_total') }}
),

-- do this here, because int_ tables fix some values, such as NTD_ID
-- grab upt and opexp_total as representatives
agency_identifiers AS (
    SELECT
        key,
        ntd_id,
        mode,
        year,
        type_of_service,

        agency_status,
        census_year,
        last_report_year,
        mode_status,
        reporter_type,
        reporting_module,
        uace_code,
        uza_area_sq_miles,
        primary_uza_name,
        uza_population,
        agency_name AS source_agency,
        city AS source_city,
        state AS source_state,
        dt,
        execution_ts,
    FROM int_upt
    UNION ALL
    SELECT * int_total
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
),

t1 AS (
    SELECT
        COALESCE(int_upt.key, int_vrh.key, int_vrm.key, int_voms.key, int_pmt.key, int_vp.key, int_vm.key, int_nvm.key, int_ga.key, int_total.key) AS key,
        agency_identifiers.ntd_id,
        agency_identifiers.mode,
        agency_identifiers.year,
        agency_identifiers.type_of_service,

        int_upt.upt AS unlinked_passenger_trips,
        int_vrh.vrh AS vehicle_revenue_hours,
        int_vrm.vrm AS vehicle_revenue_miles,
        int_voms.voms AS vehicles_operated_in_maxiumum_service,
        int_pmt.pmt AS passenger_miles_traveled,

        int_vo.opexp_vo AS operating_expenses_vehicle_operations,
        int_vm.opexp_vm AS operating_expenses_vehicle_maintenance,
        int_nvm.opexp_nvm AS operating_expenses_nonvehicle_maintenance,
        int_ga.opexp_ga AS operating_expenses_general_administration,
        int_total.opexp_total AS operating_expenses_total,

        agency_identifiers.agency_status,
        agency_identifiers.census_year,
        agency_identifiers.last_report_year,
        agency_identifiers.mode_status,
        agency_identifiers.reporter_type,
        agency_identifiers.reporting_module,
        agency_identifiers.uace_code,
        agency_identifiers.uza_area_sq_miles,
        agency_identifiers.primary_uza_name,
        agency_identifiers.uza_population,
        agency_identifiers.source_agency,
        agency_identifiers.source_city,
        agency_identifiers.source_state,
        agency_identifiers.dt,
        agency_identifiers.execution_ts,

    FROM int_upt
    LEFT JOIN int_vrh USING (key)
    LEFT JOIN int_vrm USING (key)
    LEFT JOIN int_voms USING (key)
    LEFT JOIN int_pmt USING (key)
    LEFT JOIN int_vp USING (key)
    LEFT JOIN int_vm USING (key)
    LEFT JOIN int_nvm USING (key)
    LEFT JOIN int_ga USING (key)
    LEFT JOIN int_total USING (key)
    LEFT JOIN agency_identifiers USING (key)
)

SELECT * FROM t1
WHERE key NOT IN ('e41f3812655066d28ec4bbc851545517','f5f160d19e3753e3a99d9ad55b4f2210','7d3e30725b3fa42c6d1722308f9cc855',
    'da108425cb2696446aa1017bca72340f','a31019318eddb35b747ab79470e10017','98692053a5a16aae8ef8e2579f19b8a3',
    'd6809f84a9d19808f8b1f013fc1cd537','c3ae0b0299c10ffa25e1193404762136','564993fcc3a920cc0800005f3af9fd73',
    '73f01d2aa1c268ec1dafbcf1fdaa84fc','5b13563073a95faa05c9da4f77c0b3a8','0fab2ef186a2a74edc98d16427d4d61a'
)

-- step 1 sanity check:
-- do all the left joins work? do any rows drop? if nothing, can it be inner join? (did both left and inner join, and both got 47_820 rows)
-- the keys are dbt_utils.generate_surrogate_key(['ntd_id', 'year', 'mode', 'type_of_service']) }}
