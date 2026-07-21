"""
Download mart_gtfs_rollup tables for GTFS Digest
"""

import gcsfs
import pandas as pd
from gtfs_curator_utils import bq_utils, utils
from update_vars import (
    DIGEST_DICT,
    PROCESSED_GCS,
    RAW_GCS,
    abbrev_month,
    analysis_month,
    last_year,
    previous_month,
)

crosswalk_url = f"{PROCESSED_GCS}{DIGEST_DICT.crosswalk}_{abbrev_month}.parquet"


def load_schedule_rt_route_direction_summary(
    project_name: str,
    date_col: str,
    dataset_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    df = bq_utils.download_table(
        project_name=project_name,
        dataset_name=dataset_name,
        table_name=DIGEST_DICT.schedule_rt_route_direction,
        date_col=date_col,
        start_date=start_date,
        end_date=end_date,
    )

    # Merge with crosswalk
    crosswalk_df = pd.read_parquet(
        crosswalk_url,
        columns=["name", "analysis_name"],
        filesystem=gcsfs.GCSFileSystem(),
    ).drop_duplicates()

    m1 = pd.merge(df, crosswalk_df, on="name", how="inner")

    utils.geoparquet_gcs_export(
        m1, f"{RAW_GCS}", f"{DIGEST_DICT.schedule_rt_route_direction}_{abbrev_month}"
    )

    return


def load_operator_summary(
    project_name: str,
    date_col: str,
    dataset_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    df = bq_utils.download_table(
        project_name=project_name,
        dataset_name=dataset_name,
        table_name=DIGEST_DICT.operator_summary,
        date_col=date_col,
        start_date=start_date,
        end_date=end_date,
    )

    crosswalk_df = pd.read_parquet(
        crosswalk_url,
        columns=["name", "analysis_name", "caltrans_district"],
        filesystem=gcsfs.GCSFileSystem(),
    ).drop_duplicates()

    m1 = pd.merge(
        df, crosswalk_df, left_on=["schedule_name"], right_on=["name"], how="inner"
    )

    utils.geoparquet_gcs_export(
        m1, f"{RAW_GCS}", f"{DIGEST_DICT.operator_summary}_{abbrev_month}"
    )

    return


def load_fct_monthly_routes(
    project_name: str,
    date_col: str,
    dataset_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    gdf = bq_utils.download_table(
        project_name=project_name,
        dataset_name=dataset_name,
        table_name=DIGEST_DICT.route_map,
        date_col=date_col,
        start_date=start_date,
        end_date=end_date,
        geom_col="pt_array",
        geom_type="line",
    )

    crosswalk_df = pd.read_parquet(
        crosswalk_url,
        columns=["name", "analysis_name"],
        filesystem=gcsfs.GCSFileSystem(),
    ).drop_duplicates()

    m1 = pd.merge(gdf, crosswalk_df, on="name", how="inner")

    utils.geoparquet_gcs_export(
        m1,
        f"{RAW_GCS}",
        f"{DIGEST_DICT.route_map}_{abbrev_month}",
    )

    return


def load_fct_operator_hourly_summary(
    project_name: str,
    date_col: str,
    dataset_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    df = bq_utils.download_table(
        project_name=project_name,
        dataset_name=dataset_name,
        table_name=DIGEST_DICT.hourly_day_type_summary,
        date_col=date_col,
        start_date=start_date,
        end_date=end_date,
    )

    # Merge with crosswalk
    crosswalk_df = pd.read_parquet(
        crosswalk_url,
        columns=["name", "analysis_name"],
        filesystem=gcsfs.GCSFileSystem(),
    ).drop_duplicates()

    m1 = (
        pd.merge(df, crosswalk_df, on="name", how="inner")
        .drop_duplicates()
        .reset_index()
    )

    utils.geoparquet_gcs_export(
        m1,
        f"{RAW_GCS}",
        f"{DIGEST_DICT.hourly_day_type_summary}_{abbrev_month}",
    )

    return


if __name__ == "__main__":
    PROD_PROJECT = "cal-itp-data-infra"
    PROD_MART = "mart_gtfs_rollup"
    MONTH_DATE_COL = "month_first_day"

    load_schedule_rt_route_direction_summary(
        project_name=PROD_PROJECT,
        date_col=MONTH_DATE_COL,
        dataset_name=PROD_MART,
        start_date=last_year,
        end_date=analysis_month,
    )

    load_operator_summary(
        project_name=PROD_PROJECT,
        date_col=MONTH_DATE_COL,
        dataset_name=PROD_MART,
        start_date=last_year,
        end_date=analysis_month,
    )

    load_fct_monthly_routes(
        project_name=PROD_PROJECT,
        date_col=MONTH_DATE_COL,
        dataset_name=PROD_MART,
        start_date=previous_month,
        end_date=analysis_month,
    )

    load_fct_operator_hourly_summary(
        project_name=PROD_PROJECT,
        date_col=MONTH_DATE_COL,
        dataset_name=PROD_MART,
        start_date=last_year,
        end_date=analysis_month,
    )
