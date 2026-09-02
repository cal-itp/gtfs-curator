"""
Download mart_gtfs_rollup tables for GTFS Digest
"""

import gcsfs
import google.auth
import pandas as pd
from google.cloud import bigquery, bigquery_storage
from gtfs_curator_utils import bq_utils, geography_utils, utils
from update_vars import (
    DIGEST_DICT,
    PROCESSED_GCS,
    RAW_GCS,
    abbrev_month,
    last_year,
    previous_month,
)

credentials, project = google.auth.default()
dataset = "mart_gtfs_rollup"
client = bigquery.Client(project=project, credentials=credentials)
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def merge_with_crosswalk(df: pd.DataFrame, columns=["name", "analysis_name"]):
    # Merge with crosswalk
    crosswalk_url = f"{PROCESSED_GCS}{DIGEST_DICT.crosswalk}.parquet"

    crosswalk_df = pd.read_parquet(
        crosswalk_url,
        columns=columns,
        filesystem=gcsfs.GCSFileSystem(),
    ).drop_duplicates()

    m1 = pd.merge(df, crosswalk_df, on="name", how="inner")

    return m1


def load_schedule_rt_route_direction_summary(
    start_date: str,
) -> pd.DataFrame:
    table = DIGEST_DICT.schedule_rt_route_direction
    # this scans all 300 MB, but only retrieves 4 MB to save
    sql_query = f"""
        SELECT *
        FROM `{project}.{dataset}.{table}`
        WHERE month_first_day >= @minimum_date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("minimum_date", "DATETIME", start_date),
        ]
    )

    df = bq_utils.bq_param_query(sql_query, job_config=job_config)

    df = df.rename(columns={"schedule_name": "name"}).pipe(merge_with_crosswalk)

    df.to_parquet(
        f"{RAW_GCS}{table}_{abbrev_month}.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    return


def load_operator_summary(start_date: str) -> pd.DataFrame:
    table = DIGEST_DICT.operator_summary

    sql_query = f"""
        SELECT *
        FROM `{project}.{dataset}.{table}`
        WHERE month_first_day >= @minimum_date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("minimum_date", "DATETIME", start_date),
        ]
    )

    df = bq_utils.bq_param_query(sql_query, job_config=job_config)

    df = df.rename(columns={"schedule_name": "name"}).pipe(
        merge_with_crosswalk, columns=["name", "analysis_name", "caltrans_district"]
    )

    df.to_parquet(
        f"{RAW_GCS}{table}_{abbrev_month}.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    return


def load_fct_monthly_routes(
    start_date: str,
) -> pd.DataFrame:
    table = DIGEST_DICT.route_map

    sql_query = f"""
        SELECT *
        FROM `{project}.{dataset}.{table}`
        WHERE month_first_day >= @minimum_date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("minimum_date", "DATETIME", start_date),
        ]
    )

    df = bq_utils.bq_param_query(
        sql_query, job_config=job_config, bqstorage_client=bqstorage_client
    )

    df = geography_utils.convert_to_gdf(df, "pt_array", "line").pipe(
        merge_with_crosswalk
    )

    utils.geoparquet_gcs_export(
        df,
        f"{RAW_GCS}",
        f"{table}_{abbrev_month}",
    )

    return


def load_fct_operator_hourly_summary(
    start_date: str,
) -> pd.DataFrame:
    table = DIGEST_DICT.hourly_day_type_summary

    sql_query = f"""
        SELECT *
        FROM `{project}.{dataset}.{table}`
        WHERE month_first_day >= @minimum_date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("minimum_date", "DATETIME", start_date),
        ]
    )

    df = bq_utils.bq_param_query(sql_query, job_config=job_config)
    df = merge_with_crosswalk(df)

    df.to_parquet(
        f"{RAW_GCS}{table}_{abbrev_month}.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    return


if __name__ == "__main__":
    load_schedule_rt_route_direction_summary(start_date=last_year)
    load_operator_summary(start_date=previous_month)
    # this one can't do .to_geodataframe(), it's an array of points, not geography type
    # this takes a couple minutes, but doesn't bump up the memory beyond 2MB
    load_fct_monthly_routes(start_date=previous_month)
    load_fct_operator_hourly_summary(start_date=last_year)
