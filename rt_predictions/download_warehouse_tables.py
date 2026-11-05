"""
Download tables for creating RT stop, route, operator report.
"""

import datetime
import sys

import google.auth
from google.cloud import bigquery, bigquery_storage
from gtfs_curator_utils import bq_utils
from loguru import logger
from shared_vars import PREDICTIONS_GCS, RT_MSA_DICT

credentials, project = google.auth.default()
client = bigquery.Client(project="cal-itp-data-infra-staging", credentials=credentials)
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def download_monthly_tu_stops(start_date: list, filename: str):
    bq_utils.download_table(
        "SELECT * FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs_rollup.fct_monthly_tu_stops`",
        filter_dict={"month_first_day": start_date},
        client=client,
        geography_column="pt_geom",
        output_path=f"{PREDICTIONS_GCS}{filename}.parquet",
    )

    return


def download_stop_order(filename: str):
    """
    For monthly stops, monthly routes, we lose feed_key,
    so having this by feeds is still too granular.
    _valid_from_service_date / _valid_to_service_date isn't that easy to use.

    Ultimately, want to figure out a rough ordering by route, so maybe
    do aggregation already?
    """
    bq_utils.download_table(
        "SELECT * FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.int_gtfs_schedule__stop_order_by_route2`",
        filter_dict={},
        client=client,
        output_path=f"{PREDICTIONS_GCS}{filename}.parquet",
    )

    return


def download_monthly_route_direction(start_date: list, filename: str):
    bq_utils.download_table(
        "SELECT * FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs_rollup.fct_monthly_trip_updates_route_direction_summary`",
        filter_dict={"month_first_day": start_date},
        client=client,
        output_path=f"{PREDICTIONS_GCS}{filename}.parquet",
    )
    return


if __name__ == "__main__":
    LOG_FILE = "./logs/download_warehouse.log"
    logger.add(LOG_FILE, retention="2 months")
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level="INFO",
    )

    start = datetime.datetime.now()
    DOWNLOADED_DICT = RT_MSA_DICT.dbt_model_downloads

    """
    # these would be shared with GTFS digest, so may not have to download operator summary or monthly routes
    bq_utils.download_table(
        "SELECT * FROM `cal-itp-data-infra.mart_gtfs_rollup.fct_monthly_operator_summary`",
        filter_dict={"month_first_day": operator_report_month},
        output_path=f"{PREDICTIONS_GCS}{DOWNLOADED_DICT.weekday_operator_grain}.parquet",
    )

    routes_gdf = bq_utils.download_table(
        "SELECT * FROM `cal-itp-data-infra.mart_gtfs_rollup.fct_monthly_routes`",
        filter_dict={"month_first_day": operator_report_month},
        output_path=None,
    )

    routes_gdf = geography_utils.convert_to_gdf(routes_gdf, "pt_array", "line")

    utils.geoparquet_gcs_export(
        routes_gdf,
        PREDICTIONS_GCS,
        {DOWNLOADED_DICT.route_geom},
    )
    
    download_monthly_route_direction(["2026-09-01"], DOWNLOADED_DICT.weekday_route_direction_grain)

    download_monthly_tu_stops(["2026-09-01"], DOWNLOADED_DICT.weekday_stop_grain)
    """
    download_stop_order(DOWNLOADED_DICT.stop_order)
    end = datetime.datetime.now()
