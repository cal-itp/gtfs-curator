import gcsfs
import google.auth
from google.cloud import bigquery
from gtfs_curator_utils import bq_utils
from update_vars import PROCESSED_GCS

sql_query = """
    WITH bridge AS (
        SELECT *
        FROM `cal-itp-data-infra.mart_transit_database.bridge_gtfs_analysis_name_x_ntd`
    ),

    dim_ntd AS (
        SELECT *
        FROM `cal-itp-data-infra.mart_ntd.dim_annual_agency_information`
        QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ntd_id
        ORDER BY _valid_from DESC
      ) = 1
    ),

    bridge_with_ntd AS (
      SELECT *
      FROM bridge
      INNER JOIN dim_ntd
        ON bridge.ntd_id_2022 = dim_ntd.ntd_id
    )

    SELECT * FROM bridge_with_ntd
"""


def download_new_ntd_table(
    project: str,
    dataset: str,
    table: str = "test_bridge_with_ntd",
):
    sql_query = f"""
        SELECT *
        FROM `{project}.{dataset}.{table}`
    """

    df = bq_utils.bq_param_query(sql_query)
    df.to_parquet(f"{PROCESSED_GCS}{table}.parquet", filesystem=gcsfs.GCSFileSystem())
    return


if __name__ == "__main__":
    credentials, _ = google.auth.default()
    client = bigquery.Client(
        project="cal-itp-data-infra-staging", credentials=credentials
    )
    download_new_ntd_table(
        project="cal-itp-data-infra-staging", dataset="tiffany_mart_transit_database"
    )
