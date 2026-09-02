"""
Crosswalk
"""

import gcsfs
import google.auth
import pandas as pd
from google.cloud import bigquery
from gtfs_curator_utils import bq_utils
from update_vars import DIGEST_DICT, PROCESSED_GCS, abbrev_month

credentials, project = google.auth.default()


def load_crosswalk(
    project_name: str,
    dataset_name: str,
    table_name: str = "bridge3",
) -> pd.DataFrame:
    crosswalk_cols = [
        "schedule_gtfs_dataset_name",
        "analysis_name",
        "county_name",
        "caltrans_district",
        "caltrans_district_full",
        "ntd_id",
        "ntd_id_2022",
    ]

    df = bq_utils.download_table(
        project_name=project_name,
        dataset_name=dataset_name,
        table_name=table_name,
        date_col=None,
        columns=crosswalk_cols,
    )

    df2 = (
        df.dropna(subset=["ntd_id", "ntd_id_2022"])
        .drop_duplicates(
            subset=["analysis_name", "organization_name", "schedule_gtfs_dataset_name"]
        )
        .rename(
            columns={
                "schedule_gtfs_dataset_name": "name",
                "caltrans_district": "caltrans_district_int",
                "caltrans_district_full": "caltrans_district",
            }
        )
        .reset_index(drop=True)
    )

    df2.to_parquet(
        f"{PROCESSED_GCS}{DIGEST_DICT.crosswalk}_{abbrev_month}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    return


def download_new_ntd_table(
    min_year: int = 2022,
):
    """
    Set parameter to min_year >= 2022, because we are using ntd_id_2022
    in crosswalk.
    """
    sql_query = """
        SELECT *
        FROM `cal-itp-data-infra-stag.mart_ntd.dim_annual_agency_information`
        WHERE year >= @min_year
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY ntd_id
            ORDER BY _valid_from DESC
          ) = 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_year", "INT64", min_year),
        ]
    )
    df = bq_utils.bq_param_query(sql_query, job_config=job_config)

    df = prep_ntd(df)

    df.to_parquet(
        f"{PROCESSED_GCS}dim_annual_agency_information.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    print("exported dim_annual_agency_information")

    return


def prep_ntd(df):
    """
    Set dtypes, rounding.
    TODO: move this into warehouse, set the dtype there?
    """
    integrify_cols = [
        "year",
        "zip_code",
        "zip_code_ext",
        "service_area_sq_miles",
        "service_area_pop",
        "population",
        "region",
        "voms_do",
        "voms_pt",
        "total_voms",
        "volunteer_drivers",
        "personal_vehicles",
        "number_of_state_counties",
        "number_of_counties_with_service",
        "state_admin_funds_expended",
    ]

    float_cols = ["density", "sq_miles"]
    df = df.assign(
        density=df.density.astype(float).round(3),
    ).astype(
        {
            **{c: "Int64" for c in integrify_cols},
            **{c: "Float64" for c in float_cols},
        }
    )

    return df


if __name__ == "__main__":
    PROD_PROJECT = "cal-itp-data-infra-staging"
    PROD_MART = "tiffany_mart_transit_database"

    load_crosswalk(
        project_name=PROD_PROJECT,
        dataset_name=PROD_MART,
    )

    download_new_ntd_table(min_year=2022)
