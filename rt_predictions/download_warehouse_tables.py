"""
Download tables for creating RT stop, route, operator report.
"""

import datetime
import sys

from gtfs_curator_utils import bq_utils, geography_utils, utils
from loguru import logger
from shared_vars import PREDICTIONS_GCS, operator_report_month


def download_stops_stuff():
    """
    TODO: see if these can get added to monthly stops table
    monthly_stops = bq_utils.download_table(
        project_name="cal-itp-data-infra-staging",
        dataset_name="tiffany_mart_gtfs_rollup",
        table_name="test_monthly_schedule_rt_stops",
        date_col="month_first_day",
        start_date="2025-12-01",
        end_date="2026-01-01",
        geom_col="pt_geom",
        geom_type="point",
    )

    utils.geoparquet_gcs_export(
        monthly_stops, PREDICTIONS_GCS, "monthly_schedule_rt_stops"
    )

    stop_order = bq_utils.download_table(
        project_name=PRODUCTION_PROJECT,
        dataset_name="staging",
        table_name="int_gtfs_schedule__stop_order_by_route",
        date_col="_valid_from_service_date",
        start_date="2025-12-01",
        end_date="2026-03-01",
    ).drop(columns=["_valid_to_service_date"])

    stop_order.to_parquet(
        f"{PREDICTIONS_GCS}int_gtfs_schedule__stop_order_by_route.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )
    """
    return


def download_monthly_route_direction():
    """
    # TODO: see if these columns can get added to table
    monthly_tu_route_direction_summary = bq_utils.download_table(
        project_name="cal-itp-data-infra-staging",
        dataset_name="tiffany_mart_gtfs_rollup",
        table_name="fct_monthly_trip_updates_route_direction_summary",
        date_col="month_first_day",
        start_date="2025-12-01",
        end_date="2026-01-01",
    )

    monthly_tu_route_direction_summary.to_parquet(
        f"{PREDICTIONS_GCS}monthly_tu_route_direction_summary.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )
    """
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

    # these would be shared with GTFS digest, so may not have to download operator summary or monthly routes
    operator_summary_query = """
        SELECT * FROM `cal-itp-data-infra.mart_gtfs_rollup.fct_monthly_operator_summary`
    """
    bq_utils.download_table(
        operator_summary_query,
        filter_dict={"month_first_day": operator_report_month},
        output_path=f"{PREDICTIONS_GCS}monthly_operator_summary.parquet",
    )

    routes_query = """
        SELECT * FROM `cal-itp-data-infra.mart_gtfs_rollup.fct_monthly_routes`
    """

    routes_gdf = bq_utils.download_table(
        routes_query,
        filter_dict={"month_first_day": operator_report_month},
        output_path=None,
    )

    routes_gdf = geography_utils.convert_to_gdf(routes_gdf, "pt_array", "line")

    utils.geoparquet_gcs_export(
        routes_gdf,
        PREDICTIONS_GCS,
        "monthly_routes",
    )

    end = datetime.datetime.now()
