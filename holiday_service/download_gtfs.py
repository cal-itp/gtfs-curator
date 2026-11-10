import gcsfs
import pandas as pd
from gtfs_curator_utils import bq_utils

GCS_FILE_PATH = "gs://calitp-analytics-data/data-analyses/holiday_service/"

# https://github.com/cal-itp/data-analyses/blob/main/holiday_service_research/holiday_service_mismatch.sql#L81
holiday_dates = [
    "2025-11-11",
    "2025-11-15",  # Sat
    "2025-11-16",  # Sun
    "2025-11-19",  # Wed the week before thanksgiving
    "2025-11-27",
    "2025-11-28",
    "2025-12-13",  # Sat
    "2025-12-14",  # Sun
    "2025-12-17",  # Wed the week before Christmas
    "2025-12-24",
    "2025-12-25",
    "2025-12-31",
    "2026-01-01",
]


if __name__ == "__main__":
    year = "2025"
    '''
    bq_utils.download_table(
        sql_query = """
            SELECT 
                service_date,
                feed_key,
                name AS schedule_gtfs_dataset_name,
                _feed_valid_from,
                trip_id,
                iteration_num,
                trip_instance_key,
                route_id,
                direction_id,
                shape_id,
                shape_array_key,
                service_hours,
            FROM `cal-itp-data-infra.mart_gtfs.fct_scheduled_trips`
        """,
        filter_dict = {"service_date": holiday_dates},
        output_path = f"{GCS_FILE_PATH}holidays_{year}.parquet"
    )
    '''
    feeds_df = pd.read_parquet(
        f"{GCS_FILE_PATH}holidays_{year}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        columns=["feed_key", "_feed_valid_from"],
    ).drop_duplicates()

    feed_valid_list = [
        pd.to_datetime(c).date().isoformat() for c in feeds_df._feed_valid_from.unique()
    ]

    bq_utils.download_table(
        sql_query="""
            SELECT 
                feed_key,
                _feed_valid_from,
                shape_id,
                key AS shape_array_key,
                pt_array
            FROM `cal-itp-data-infra.mart_gtfs.dim_shapes_arrays`
        """,
        filter_dict={
            "_feed_valid_from": [feed_valid_list],
            "feed_key": feeds_df.feed_key.unique().tolist(),
        },
        output_path=f"{GCS_FILE_PATH}dim_shapes_arrays_{year}.parquet",
    )
