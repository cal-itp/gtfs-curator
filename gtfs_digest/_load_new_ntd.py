import gcsfs
import google.auth
import pandas as pd
from google.cloud import bigquery
from gtfs_curator_utils import bq_utils
from update_vars import PROCESSED_GCS

credentials, project = google.auth.default()


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


def prep_ntd(df: pd.DataFrame) -> pd.DataFrame:
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
    download_new_ntd_table(min_year=2022)
