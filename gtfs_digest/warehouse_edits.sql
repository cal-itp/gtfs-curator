------------------------------------------------------
-- bridge_gtfs_analysis_name_x_ntd
------------------------------------------------------
WITH dim_gtfs_datasets AS (
    SELECT
        name,
        analysis_name,
        source_record_id,
        regional_feed_type,
        _valid_from,
        private_dataset,
        data_quality_pipeline,
    FROM `cal-itp-data-infra.mart_transit_database.dim_gtfs_datasets` 
    --{{ ref('dim_gtfs_datasets') }}
    WHERE ( data_quality_pipeline IS TRUE
           AND private_dataset IS NOT TRUE
           --AND regional_feed_type != "Regional Precursor Feed"
           AND analysis_name IS NOT NULL
           AND name != "Bay Area 511 Regional Schedule"
           AND type = "schedule")
),

deduped_analysis_name AS (
    SELECT
        analysis_name,
        source_record_id,
        name,
        regional_feed_type,

    FROM dim_gtfs_datasets
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY source_record_id, name
        ORDER BY _valid_from DESC
    ) = 1
),

-- this one has services, but we are ignoring services for these joins
dim_provider_gtfs_data AS (
    SELECT *
    FROM `cal-itp-data-infra.mart_transit_database.dim_provider_gtfs_data`--{{ ref('dim_provider_gtfs_data') }}
),

deduped_provider AS (
    SELECT DISTINCT
        organization_name,
        schedule_source_record_id,

    FROM dim_provider_gtfs_data
    QUALIFY ROW_NUMBER() OVER(
        PARTITION BY schedule_source_record_id, schedule_gtfs_dataset_name
        --this will keep every combination of source_record_id-gtfs_dataset_name
        --which means if the name changes, they will all show up
        --just schedule_source_record_id would keep the most recent name
        --but Foothill/Duarte have issues 
        
        ORDER BY _valid_from DESC
    ) = 1
),


dim_organizations AS (
    SELECT * FROM `cal-itp-data-infra.mart_transit_database.dim_organizations`--{{ ref('dim_organizations') }}
),

dim_county_geography AS (
    SELECT DISTINCT
        key,
        name,
        caltrans_district,
        caltrans_district_name,
    FROM `cal-itp-data-infra.mart_transit_database.dim_county_geography`--{{ ref('dim_county_geography') }}
),

bridge_org_county AS (
    SELECT
        organization_key,
        county_geography_key,
    FROM `cal-itp-data-infra.mart_transit_database.bridge_organizations_x_headquarters_county_geography` --{{ ref('bridge_organizations_x_headquarters_county_geography') }}
),

orgs_with_geog AS (
    SELECT
        dim_organizations.source_record_id AS organization_source_record_id,
        MAX(dim_organizations.name) AS organization_name,

        MAX(dim_county_geography.name) AS county_name,
        MAX(dim_county_geography.caltrans_district) AS caltrans_district,
        MAX(dim_county_geography.caltrans_district_name) AS caltrans_district_name,

        MAX(dim_organizations.ntd_id) AS ntd_id,
        MAX(dim_organizations.ntd_id_2022) AS ntd_id_2022,
        MAX(dim_organizations.rtpa_name) AS rtpa_name,
        MAX(dim_organizations.mpo_name) AS mpo_name,

    FROM dim_organizations
    INNER JOIN bridge_org_county
        -- join on organization_key will result in some values with the same
        -- organization_source_record_id not having ntd_id or rtpa filled in
        ON dim_organizations.key = bridge_org_county.organization_key
    INNER JOIN dim_county_geography
        ON bridge_org_county.county_geography_key = dim_county_geography.key
    GROUP BY organization_source_record_id
),

gtfs_to_orgs AS (
    SELECT
        orgs_with_geog.organization_name,
        orgs_with_geog.organization_source_record_id,
        deduped_provider.schedule_source_record_id,
        deduped_analysis_name.name AS schedule_gtfs_dataset_name,
        deduped_analysis_name.analysis_name,
        deduped_analysis_name.regional_feed_type,

        orgs_with_geog.county_name,
        orgs_with_geog.caltrans_district,
        orgs_with_geog.caltrans_district_name,
        CONCAT(CAST(caltrans_district AS STRING FORMAT '00'), " - ", caltrans_district_name) AS caltrans_district_full,
        orgs_with_geog.ntd_id,
        orgs_with_geog.ntd_id_2022,
        orgs_with_geog.rtpa_name,
        orgs_with_geog.mpo_name,

    FROM deduped_analysis_name 
    LEFT JOIN deduped_provider --left join doesn't work here either to solve it
        ON deduped_analysis_name.source_record_id = deduped_provider.schedule_source_record_id
    INNER JOIN orgs_with_geog
