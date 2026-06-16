----------------------------------------------------------
-- (1) tiffany_mart_ntd_explore.fct_service_data_time_series_by_mode
-- fct_service_data_and_operating_expenses_time_series_by_mode_upt/voms/vrh feel repetitive
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

t1 AS (
    SELECT
        COALESCE(int_upt.key, int_vrh.key, int_vrm.key, int_voms.key, int_pmt.key) AS key,
        COALESCE(int_upt.ntd_id, int_vrh.ntd_id, int_vrm.ntd_id, int_voms.ntd_id, int_pmt.ntd_id) AS ntd_id,
        COALESCE(int_upt.year, int_vrh.year, int_vrm.year, int_voms.year, int_pmt.year) AS year,

        COALESCE(int_upt.mode, int_vrh.mode, int_vrm.mode, int_voms.mode, int_pmt.mode) AS mode,
        COALESCE(int_upt.type_of_service, int_vrh.type_of_service, int_vrm.type_of_service, int_voms.type_of_service, int_pmt.type_of_service) AS type_of_service,
        COALESCE(int_upt.agency_status, int_vrh.agency_status, int_vrm.agency_status, int_voms.agency_status, int_pmt.agency_status) AS agency_status,
        COALESCE(int_upt.census_year, int_vrh.census_year, int_vrm.census_year, int_voms.census_year, int_pmt.census_year) AS census_year,
        COALESCE(int_upt.last_report_year, int_vrh.last_report_year, int_vrm.last_report_year, int_voms.last_report_year, int_pmt.last_report_year) AS last_report_year,
        COALESCE(int_upt.mode_status, int_vrh.mode_status, int_vrm.mode_status, int_voms.mode_status, int_pmt.mode_status) AS mode_status,
        COALESCE(int_upt.reporter_type, int_vrh.reporter_type, int_vrm.reporter_type, int_voms.reporter_type, int_pmt.reporter_type) AS reporter_type,
        COALESCE(int_upt.reporting_module, int_vrh.reporting_module, int_vrm.reporting_module, int_voms.reporting_module, int_pmt.reporting_module) AS reporting_module,
        COALESCE(int_upt.uace_code, int_vrh.uace_code, int_vrm.uace_code, int_voms.uace_code, int_pmt.uace_code) AS uace_code,
        COALESCE(int_upt.uza_area_sq_miles, int_vrh.uza_area_sq_miles, int_vrm.uza_area_sq_miles, int_voms.uza_area_sq_miles, int_pmt.uza_area_sq_miles) AS uza_area_sq_miles,
        COALESCE(int_upt.primary_uza_name, int_vrh.primary_uza_name, int_vrm.primary_uza_name, int_voms.primary_uza_name, int_pmt.primary_uza_name) AS primary_uza_name,
        COALESCE(int_upt.uza_population, int_vrh.uza_population, int_vrm.uza_population, int_voms.uza_population, int_pmt.uza_population) AS uza_population,

        int_upt.upt,
        int_vrh.vrh,
        int_vrm.vrm,
        int_voms.voms,
        int_pmt.pmt,

        COALESCE(int_upt.agency_name, int_vrh.agency_name, int_vrm.agency_name, int_voms.agency_name, int_pmt.agency_name) AS source_agency,
        COALESCE(int_upt.city, int_vrh.city, int_vrm.city, int_voms.city, int_pmt.city) AS source_city,
        COALESCE(int_upt.state, int_vrh.state, int_vrm.state, int_voms.state, int_pmt.state) AS source_state,
        COALESCE(int_upt.dt, int_vrh.dt, int_vrm.dt, int_voms.dt, int_pmt.dt) AS dt, -- are these the same across all the datasets?
        COALESCE(int_upt.execution_ts, int_vrh.execution_ts, int_vrm.execution_ts, int_voms.execution_ts, int_pmt.execution_ts) AS execution_Ts, -- are these the same across all the datasets?

    FROM int_upt
    LEFT JOIN int_vrh
        USING (key)
    LEFT JOIN int_vrm
        USING (key)
    LEFT JOIN int_voms
        USING (key)
    LEFT JOIN int_pmt
        USING (key)
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
