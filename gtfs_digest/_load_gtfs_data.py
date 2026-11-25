"""
Download mart_gtfs_rollup tables for GTFS Digest
"""

from typing import Literal

import pandas as pd
from gtfs_curator_utils import bq_utils, geography_utils, utils
from update_vars import (
    DIGEST_DICT,
    RAW_GCS,
    abbrev_month,
    last_year,
    previous_month,
)


def load_table(
    catalog_table_name: Literal[
        "schedule_rt_route_direction", "operator_summary", "hourly_day_type_summary"
    ],
    start_date: str,
):
    """
    Download the tables listed in catalog.yml.
    Those catalog maps those table_names to the warehouse's dbt model name.
    The dbt models are within the mart_gtfs_rollup dataset
    project.dataset.table = `cal-itp-data.mart_gtfs_rollup.one_table`
    """
    table = DIGEST_DICT[catalog_table_name]

    sql_query = f"""
        SELECT *
        FROM `cal-itp-data-infra.mart_gtfs_rollup.{table}`
    """

    bq_utils.download_table(
        sql_query,
        filter_dict={"month_first_day": start_date},
        output_path=f"{RAW_GCS}{table}_{abbrev_month}.parquet",
    )

    return


def load_fct_monthly_routes(
    start_date: str,
) -> pd.DataFrame:
    table = DIGEST_DICT.route_map

    sql_query = f"""
        SELECT *
        FROM `cal-itp-data-infra.mart_gtfs_rollup.{table}`
    """
    df = bq_utils.download_table(
        sql_query, filter_dict={"month_first_day": start_date}, output_path=None
    )

    df = geography_utils.convert_to_gdf(df, "pt_array", "line")

    utils.geoparquet_gcs_export(
        df,
        f"{RAW_GCS}",
        f"{table}_{abbrev_month}",
    )

    print(f"exported {RAW_GCS}{table}_{abbrev_month}")

    return


if __name__ == "__main__":
    load_table("schedule_rt_route_direction", start_date=last_year)
    load_table("operator_summary", start_date=previous_month)
    load_table("hourly_day_type_summary", start_date=last_year)

    # this one can't do .to_geodataframe(), it's an array of points, not geography type
    # this takes a couple minutes, but doesn't bump up the memory beyond 2MB
    load_fct_monthly_routes(start_date=previous_month)
