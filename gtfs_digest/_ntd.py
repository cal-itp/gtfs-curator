"""
NTD Data
"""

ntd_query_sql = """
        SELECT 
        number_of_state_counties,
        primary_uza_name,
        density,
        number_of_counties_with_service,
        state_admin_funds_expended,
        service_area_sq_miles,
        population,
        service_area_pop,
        subrecipient_type,
        primary_uza_code,
        reporter_type,
        organization_type,
        agency_name,
        voms_pt,
        voms_do,
        ntd_id,
        year
        FROM `cal-itp-data-infra-staging`.`mart_ntd`.`dim_annual_agency_information`
        WHERE state = 'CA' AND _is_current = TRUE
    """


mobility_query_sql = """
            SELECT
            agency_name,
            counties_served,
            hq_county,
            is_public_entity,
            is_publicly_operating,
            funding_sources,
            on_demand_vehicles_at_max_service,
            vehicles_at_max_service
            FROM
            cal-itp-data-infra.mart_transit_database.dim_mobility_mart_providers  
            """


def load_mobility(query: str) -> pd.DataFrame:
    with db_engine.connect() as connection:
        df = pd.read_sql(query, connection)
    df2 = df.sort_values(
        by=["on_demand_vehicles_at_max_service", "vehicles_at_max_service"],
        ascending=[False, False],
    )
    df3 = df2.groupby("agency_name").first().reset_index()
    return df3


def load_ntd(query: str) -> pd.DataFrame:
    with db_engine.connect() as connection:
        df = pd.read_sql(query, connection)
    df2 = df.sort_values(by=df.columns.tolist(), na_position="last")
    df3 = df2.groupby("agency_name").first().reset_index()
    return df3


def merge_ntd_mobility(ntd_query: str, mobility_query: str) -> pd.DataFrame:
    """
    Merge NTD (dim_annual_ntd_agency_information) with
    mobility providers (dim_mobility_mart_providers)
    and dedupe and keep 1 row per agency.
    """
    ntd = load_ntd(ntd_query)
    mobility = load_mobility(mobility_query)
    crosswalk = load_crosswalk()[["analysis_name", "ntd_id_2022"]]

    m1 = pd.merge(mobility, ntd, how="inner", on="agency_name")

    m1 = m1.drop_duplicates(subset="agency_name").reset_index(drop=True)

    # Wherever possible, allow nullable integers. These columns are integers, but can be
    # missing if we don't find corresponding NTD info
    integrify_cols = [
        "number_of_state_counties",
        "number_of_counties_with_service",
        "service_area_sq_miles",
        "service_area_pop",
        "on_demand_vehicles_at_max_service",
        "vehicles_at_max_service",
        "voms_pt",
        "voms_do",
        "year",
    ]
    m1[integrify_cols] = m1[integrify_cols].astype("Int64")

    # Merge with crosswalk to get analysis_name
    m1 = pd.merge(
        m1, crosswalk, left_on=["ntd_id"], right_on=["ntd_id_2022"], how="inner"
    )

    gcs_pandas().data_frame_to_parquet(
        m1,
        f"{GTFS_DATA_DICT.gcs_paths.DIGEST_GCS}processed/{GTFS_DATA_DICT.gtfs_digest_rollup.ntd_profile}_{file_name}.parquet",
    )

    return m1
