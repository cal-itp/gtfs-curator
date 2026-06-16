----------------------------------------------------------
-- (1)
-- fct_service_data_and_operating_expenses_time_series_by_mode_upt/voms/vrh feel repetitive
-- what's there: noticed that intermediate tables all use `dim_agency_information`
-- what I want to change: combine the intermediate tables, then bring in dim_agency_information, and filter out bad keys
----------------------------------------------------------
WITH int_mode_upt AS (
    SELECT *
    FROM {{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_upt') }}
),

int_mode_vrh AS (
    SELECT *
    FROM {{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_vrh') }}
),

int_mode_vrm AS (
    SELECT *
    FROM {{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_vrm') }}
),

int_mode_voms AS (
    SELECT *
    FROM {{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_voms') }}
),

int_mode_pmt AS (
    SELECT *
    FROM {{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_pmt') }}
),

fct_service_data_and_operating_expenses_time_series_by_mode AS (
    SELECT

        COALESCE(int_upt.ntd_id, int_vrh.ntd_id, int_vrm.ntd_id, int_voms.ntd_id, int_pmt.ntd_id) AS ntd_id,
        COALESCE(int_upt.year, int_vrh.year, int_vrm.year, int_voms.year, int_pmt.year) AS year,

        --agency.agency_name,
        --agency.city,
        --agency.state,
        --agency.caltrans_district_current,
        --agency.caltrans_district_name_current,

        COALESCE(int_upt.mode, int_vrh.mode, int_vrm.mode, int_voms.mode, int_pmt.mode) AS mode,
        COALESCE(int_upt.type_of_service, int_vrh.type_of_service, int_vrm.type_of_service, int_voms.type_of_service, int_pmt.type_of_service) AS type_of_service,
        COALESCE(int_upt.agency_status, int_vrh.agency_status, int_vrm.agency_status, int_voms.agency_status, int_pmt.agency_status) AS agency_status,
        COALESCE(int_upt.census_year, int_vrh.census_year, int_vrm.census_year, int_voms.census_year, int_pmt.census_year) AS census_year,
        COALESCE(int_upt.last_report_year, int_vrh.last_report_year, int_vrm.last_report_year, int_voms.last_report_year, int_pmt.last_report_year) AS last_report_year,
        COALESCE(int_upt.mode_status, int_vrh.mode_status, int_vrm.mode_status, int_voms.mode_status, int_pmt.mode_status) AS mode_status,
        COALESCE(int_upt.last_report_year, int_vrh.last_report_year, int_vrm.last_report_year, int_voms.last_report_year, int_pmt.last_report_year) AS last_report_year,
        COALESCE(int_upt.reporter_type, int_vrh.reporter_type, int_vrm.reporter_type, int_voms.reporter_type, int_pmt.reporter_type) AS reporter_type,

        --int.reporting_module,
        --int.uace_code,
        --int.uza_area_sq_miles,
        --int.primary_uza_name,
        --int.uza_population,
        --int.agency_name AS source_agency,
        --int.city AS source_city,
        --int.state AS source_state,

        int_mode_upt.upt,
        int_mode_vrh.vrh,
        int_mode_vrm.vrm,
        int_mode_voms.voms,

        int.dt, -- are these the same across all the datasets?
        int.execution_ts -- are these the same across all the datasets?
    FROM int_mode_upt
    LEFT JOIN int_mode_vrh
        USING (key)
    LEFT JOIN int_mode_vrm
        USING (key)
    LEFT JOIN int_mode_voms
        USING (key)
    LEFT JOIN int_mode_pmt
        USING (key)

    --LEFT JOIN dim_agency_information AS agency
        ON int.ntd_id = agency.ntd_id
            AND int.year = agency.year
    -- remove bad rows for 'Advance Transit, Inc. NH' and 'Southern Teton Area Rapid Transit'
    WHERE int.key NOT IN ('e41f3812655066d28ec4bbc851545517','f5f160d19e3753e3a99d9ad55b4f2210','7d3e30725b3fa42c6d1722308f9cc855',
        'da108425cb2696446aa1017bca72340f','a31019318eddb35b747ab79470e10017','98692053a5a16aae8ef8e2579f19b8a3',
        'd6809f84a9d19808f8b1f013fc1cd537','c3ae0b0299c10ffa25e1193404762136','564993fcc3a920cc0800005f3af9fd73',
        '73f01d2aa1c268ec1dafbcf1fdaa84fc','5b13563073a95faa05c9da4f77c0b3a8','0fab2ef186a2a74edc98d16427d4d61a')
)

-- step 1 sanity check:
-- do all the left joins work? do any rows drop? if nothing, can it be inner join?
-- the keys are dbt_utils.generate_surrogate_key(['ntd_id', 'year', 'mode', 'type_of_service']) }}
