"""
Download tables for creating RT operator report.
Operator report includes route-direction summary.
"""

import datetime
import sys

import google.auth
from google.cloud import bigquery
from gtfs_curator_utils import bq_utils, geography_utils, utils
from loguru import logger
from shared_vars import PREDICTIONS_GCS, RT_MSA_DICT

credentials, project = google.auth.default()
client = bigquery.Client(project="cal-itp-data-infra-staging", credentials=credentials)


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

    from shared_vars import operator_report_month

    start = datetime.datetime.now()

    DOWNLOADED_DICT = RT_MSA_DICT.dbt_model_downloads

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
        DOWNLOADED_DICT.route_geom,
    )

    # this is new trip updates table
    # TODO: merge with monthly_schedule_rt_route_direction_summary model
    download_monthly_route_direction(
        [operator_report_month], DOWNLOADED_DICT.weekday_route_direction_grain
    )

    end = datetime.datetime.now()
