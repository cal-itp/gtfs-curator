----------------------------------------------------------
-- (1) tiffany_mart_ntd_explore.fct_service_data_and_operating_expenses_time_series_by_mode (did not remove keys)
-- fct_service_data_and_operating_expenses_time_series_by_mode_[one_excel_sheet] feel repetitive
-- service values: upt, vrh, vrm, voms, pmt, drm (directional_route_miles)
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

int_drm AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_drm` 
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_drm') }}
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

int_fares AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_fares` 
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_fares') }}
),

int_agency_information AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_agency_identifiers`
),

service_data_and_operating_expenses_time_series_by_mode AS (
    SELECT
        COALESCE(int_upt.key, int_vrh.key, int_vrm.key, int_voms.key, int_pmt.key, int_drm.key, 
            int_vo.key, int_vm.key, int_nvm.key, int_ga.key, int_total.key, int_fares.key) AS key,
        COALESCE(int_upt.ntd_id, int_vrh.ntd_id, int_vrm.ntd_id, int_voms.ntd_id, int_pmt.ntd_id, int_drm.ntd_id, 
            int_vo.ntd_id, int_vm.ntd_id, int_nvm.ntd_id, int_ga.ntd_id, int_total.ntd_id, int_fares.ntd_id) AS ntd_id,
        COALESCE(int_upt.mode, int_vrh.mode, int_vrm.mode, int_voms.mode, int_pmt.mode, int_drm.mode,
            int_vo.mode, int_vm.mode, int_nvm.mode, int_ga.mode, int_total.mode, int_fares.mode) AS mode,
        COALESCE(int_upt.year, int_vrh.year, int_vrm.year, int_voms.year, int_pmt.year, int_drm.year,
            int_vo.year, int_vm.year, int_nvm.year, int_ga.year, int_total.year, int_fares.year) AS year,
        COALESCE(int_upt.type_of_service, int_vrh.type_of_service, int_vrm.type_of_service, 
            int_voms.type_of_service, int_pmt.type_of_service, int_drm.type_of_service,
            int_vo.type_of_service, int_vm.type_of_service, int_nvm.type_of_service, int_ga.type_of_service, 
            int_total.type_of_service, int_fares.type_of_service) AS type_of_service,
   
        int_upt.upt AS unlinked_passenger_trips,
        int_vrh.vrh AS vehicle_revenue_hours,
        int_vrm.vrm AS vehicle_revenue_miles,          
        int_voms.voms AS vehicles_operated_in_maxiumum_service,
        int_pmt.pmt AS passenger_miles_traveled,
        int_drm.drm AS direction_route_miles, 
    
        int_vo.opexp_vo AS operating_expenses_vehicle_operations,
        int_vm.opexp_vm AS operating_expenses_vehicle_maintenance,
        int_nvm.opexp_nvm AS operating_expenses_nonvehicle_maintenance,
        int_ga.opexp_ga AS operating_expenses_general_administration,
        int_total.opexp_total AS operating_expenses_total,
        int_fares.fares AS fare_revenue,
    
        -- check these
        ROUND(SAFE_DIVIDE(int_total.opexp_total, int_vrh.vrh), 2) AS opex_per_vrh, -- should these be inflation-adjusted?
        ROUND(SAFE_DIVIDE(int_total.opexp_total, int_vrm.vrm, 2) AS opex_per_vrm,
        ROUND(SAFE_DIVIDE(int_total.opexp_total, int_upt.upt, 2) AS opex_per_upt,
        ROUND(SAFE_DIVIDE(int_upt.upt, int_vrh.vrh, 2) AS upt_per_vrh,
        ROUND(SAFE_DIVIDE(int_upt.upt, int_vrm.vrm, 2) AS upt_per_vrm,
        --ROUND(SAFE_DIVIDE(int_upt.fares, int_vrm.opexp_total, 2) AS farebox_recovery_ratio, 

        int_agency_information.agency_status,
        int_agency_information.census_year,
        int_agency_information.last_report_year,
        int_agency_information.mode_status,
        int_agency_information.reporter_type,
        int_agency_information.reporting_module,
        int_agency_information.uace_code,
        int_agency_information.uza_area_sq_miles,
        int_agency_information.primary_uza_name,
        int_agency_information.uza_population,  
        int_agency_information.source_agency,
        int_agency_information.source_city,
        int_agency_information.source_state,
        
    FROM int_upt
    LEFT JOIN int_vrh USING (key)
    LEFT JOIN int_vrm USING (key)
    LEFT JOIN int_voms USING (key)
    LEFT JOIN int_pmt USING (key)      
    LEFT JOIN int_drm USING (key)  
    LEFT JOIN int_vo USING (key)
    LEFT JOIN int_vm USING (key)
    LEFT JOIN int_nvm USING (key)
    LEFT JOIN int_ga USING (key)
    LEFT JOIN int_total USING (key)
    LEFT JOIN int_fares USING (key)
    LEFT JOIN int_agency_information USING (key)
)

fct_service_data_and_operating_expenses_time_series_by_mode AS (
    SELECT * 
    FROM service_data_and_operating_expenses_time_series_by_mode
    WHERE key NOT IN ('e41f3812655066d28ec4bbc851545517','f5f160d19e3753e3a99d9ad55b4f2210','7d3e30725b3fa42c6d1722308f9cc855',
    'da108425cb2696446aa1017bca72340f','a31019318eddb35b747ab79470e10017','98692053a5a16aae8ef8e2579f19b8a3',
    'd6809f84a9d19808f8b1f013fc1cd537','c3ae0b0299c10ffa25e1193404762136','564993fcc3a920cc0800005f3af9fd73',
    '73f01d2aa1c268ec1dafbcf1fdaa84fc','5b13563073a95faa05c9da4f77c0b3a8','0fab2ef186a2a74edc98d16427d4d61a'
    )
)

SELECT * FROM fct_service_data_and_operating_expenses_time_series_by_mode

-- step 1 sanity check: 
-- do all the left joins work? do any rows drop? if nothing, can it be inner join? (did both left and inner join, and both got 47_820 rows)
-- the keys are dbt_utils.generate_surrogate_key(['ntd_id', 'year', 'mode', 'type_of_service']) }}

----------------------------------------------------------
-- (2) tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_agency_identifiers
-- how do agency identifiers differ from dim_agency_information? the intermediatabe table is used for fct
-- agency identifiers that show up on each sheet of Excel
-- dim_agency_information isn't exactly the same, the columns are different
-- there's dt and execution_ts, which updates every time it hits the view?
----------------------------------------------------------
-- do this here, because int_ tables fix some values, such as NTD_ID
-- grab upt and opexp_total as representatives
WITH int_upt AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_upt` 
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_upt') }}
),

int_total AS (
    SELECT *
    FROM `cal-itp-data-infra-staging.tiffany_mart_ntd_explore.int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_total` 
    --{{ ref('int_ntd__service_data_and_operating_expenses_time_series_by_mode_opexp_total') }}
),

upt_agency_identifiers AS (
    SELECT
        key,
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

    FROM int_upt
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
),

opexp_agency_identifiers AS (
    SELECT
        key,
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

    FROM int_total
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
),

agency_identifiers AS (
    SELECT * FROM upt_agency_identifiers
    UNION DISTINCT SELECT * FROM opexp_agency_identifiers
)
SELECT * FROM agency_identifiers

----------------------------------------------------------
-- (3) crosswalk for ntd_id to bridge's ntd_id_2022 for portfolio deploy
----------------------------------------------------------
WITH bridge AS (
    SELECT 
        --schedule_gtfs_dataset_name,
        --analysis_name,
        organization_name,
        ntd_id_2022,
        county_geography_name,
        rtpa_name,
    FROM `cal-itp-data-infra.mart_transit_database.bridge_gtfs_analysis_name_x_ntd`
    --{{ ref('bridge_gtfs_analysis_name_x_ntd') }}
),

bridge_split_out_scag AS (
    SELECT 
        *,
        CASE 
            WHEN county_geography_name = "Ventura" THEN "Ventura County Transportation Commission"
            WHEN county_geography_name = "Los Angeles" THEN "Los Angeles County Metropolitan Transportation Authority"
            WHEN county_geography_name = "San Bernardino" THEN "San Bernardino County Transportation Authority"
            WHEN county_geography_name = "Riverside" THEN "Riverside County Transportation Commission"
            WHEN county_geography_name = "Orange" THEN "Orange County Transportation Authority"
            WHEN county_geography_name = "Imperial" THEN "Imperial County Transportation Commission"
            ELSE rtpa_name
        END AS rtpa_name
    FROM bridge
)

SELECT * FROM bridge_split_out_scag