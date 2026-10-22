"""
GTFS Diagnostics
"""

from datetime import datetime, timedelta

import gcsfs
import google.auth
import pandas as pd
from cookbook_vars import DATE_PERIODS_DICT, GCS_FILE_PATH
from google.cloud import bigquery

credentials, _ = google.auth.default()
client = bigquery.Client(project="cal-itp-data-infra-staging", credentials=credentials)


def download_quartet_by_feed_key(
    table_name: str,
) -> pd.DataFrame:

    sql_query = """
        SELECT
            *
        FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.quartet_by_feed_key`
    """

    query_job = client.query(sql_query)
    df = query_job.result().to_arrow().to_pandas()

    df.to_parquet(
        f"{GCS_FILE_PATH}{table_name}.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    print(f"exported: {table_name}")
    return


def calculate_time_overlap(
    t1_start: datetime,
    t1_end: datetime,
    t2_start: datetime,
    t2_end: datetime,
) -> float:
    """
    Be able to find the overlap (in days) between
    ridership_start/end and GTFS schedule feed_key's service_date_start/end.
        https://medium.com/@sebastianof/how-pyto-find-the-overlap-between-two-time-intervals-93904c401120
    """
    overlap_timedelta = max(timedelta(0), min(t1_end, t2_end) - max(t1_start, t2_start))

    overlap_days = overlap_timedelta.total_seconds() / (3_600 * 24)

    return overlap_days


def add_date_period_filtering(df: pd.DataFrame, date_periods: dict) -> pd.DataFrame:
    """
    Add a column to tag whether the record is part of each date period.
    Use 2 halves of year. is_2026_H2, is_2026_H1, etc.
    If itables can handle larger tables, do it by year.
    """
    for label, one_date_period in date_periods.items():
        start_date = pd.to_datetime(one_date_period[0])
        end_date = pd.to_datetime(one_date_period[1])

        df[f"is_{label}"] = df.apply(
            lambda x: (
                True
                if calculate_time_overlap(
                    start_date, end_date, x.service_date_start, x.service_date_end
                )
                > 0
                else False
            ),
            axis=1,
        )

    return df


if __name__ == "__main__":
    # download_quartet_by_feed_key("quartet_by_feed_key")

    df = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}quartet_by_feed_key.parquet",
            filesystem=gcsfs.GCSFileSystem(),
        )
        .astype(
            {
                "service_date_start": "datetime64[ns]",
                "service_date_end": "datetime64[ns]",
            }
        )
        .pipe(add_date_period_filtering, DATE_PERIODS_DICT)
    )

    df.to_parquet(
        f"{GCS_FILE_PATH}quartet_by_feed_key_categorized.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )
