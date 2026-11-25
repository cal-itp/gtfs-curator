"""
GTFS Diagnostics

use cases:
- one operator, which feed? which feed_keys?
- Culver City missing
- Santa Barbara arrivals look too high
- OCTA incorrectly parsed
"""

import gcsfs
import google.auth
import pandas as pd
import world_cup_vars as wc_vars
from google.cloud import bigquery, bigquery_storage
from gtfs_curator_utils import bq_utils

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH
credentials, _ = google.auth.default()
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def filter_fct_daily_schedule_rt_route_direction_summary(
    service_date_list: list,
) -> pd.DataFrame:

    daily_route_query = """
        SELECT
            *
        FROM `cal-itp-data-infra.mart_gtfs.fct_daily_schedule_rt_route_direction_summary`
    """

    bq_utils.download_table(
        daily_route_query,
        filter_dict={"service_date": service_date_list},
        output_path=f"{GCS_FILE_PATH}fct_daily_schedule_rt_route_direction_summary_{wc_vars.event_name}.parquet",
        bqstorage_client=bqstorage_client,
    )

    return


def filter_fct_daily_scheduled_stops(
    service_date_list: list, feed_key_list: list
) -> pd.DataFrame:

    daily_stops_query = """
        SELECT
            *
        FROM `cal-itp-data-infra.mart_gtfs.fct_daily_scheduled_stops`
    """

    bq_utils.download_table(
        daily_stops_query,
        filter_dict={"service_date": service_date_list, "feed_key": feed_key_list},
        geography_column="pt_geom",
        output_path=f"{GCS_FILE_PATH}fct_daily_scheduled_stops_{wc_vars.event_name}.parquet",
        bqstorage_client=bqstorage_client,
    )

    return


def filter_fct_service_alerts_trip_summaries(
    service_date_list: list,
    # sa_base64_url_list: list # this has to be known ahead of time
) -> pd.DataFrame:

    client = bigquery.Client(project="cal-itp-data-infra", credentials=credentials)

    # table is clustered by base64_url
    # has service_date, but service_date isn't partition or cluster column, so move it after base64_url filter
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            # bigquery.ArrayQueryParameter("sa_base64_url_list", "STRING", sa_base64_url_list),
            bigquery.ArrayQueryParameter(
                "service_date_list", "DATETIME", service_date_list
            ),
        ]
    )

    query = """
        SELECT
            *
        FROM `cal-itp-data-infra.mart_gtfs.fct_service_alerts_trip_summaries`
        WHERE service_date IN UNNEST(@service_date_list)
    """
    # maybe put UNNEST(@sa_base64_url_list) once we know

    query_job = client.query(query, job_config)
    df = query_job.result().to_arrow().to_pandas()

    return df


def filter_fct_daily_service_alerts(
    active_date_list: list,  # sa_base64_url_list: list
) -> pd.DataFrame:

    # Figure out how to parameterize this, make sure date list works
    # this is staging project right now
    client = bigquery.Client(project="cal-itp-data-infra", credentials=credentials)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "active_date_list", "DATETIME", active_date_list
            ),
            # clustered on base64_url, but we have to know these ahead of time
            # set up dim_provider_gtfs_data?
            # bigquery.ArrayQueryParameter("sa_base64_url_list", "STRING", sa_base64_url_list),
        ]
    )

    query = """
        SELECT
            *
        FROM `cal-itp-data-infra.mart_gtfs.fct_daily_service_alerts`
        WHERE active_date IN UNNEST(@active_date_list)
    """

    query_job = client.query(query, job_config)
    df = query_job.result().to_arrow().to_pandas()

    return df


if __name__ == "__main__":
    # (3) `fct_daily_schedule_rt_route_direction_summary` and explore and figure out routes

    filter_fct_daily_schedule_rt_route_direction_summary(wc_vars.event_date_range)

    # (4) fct_daily_scheduled_stops
    # filter by service_date and feed_key
    subset_feed_keys = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}feeds_{wc_vars.event_name}.parquet",
            filesystem=gcsfs.GCSFileSystem(),
        )
        .feed_key.unique()
        .tolist()
    )

    filter_fct_daily_scheduled_stops(wc_vars.event_date_range, subset_feed_keys)

    """
    # (5) fct_service_alerts_trip_summaries
    # filter by service_date and sa_base64_url
    daily_sa_trip_summary = filter_fct_service_alerts_trip_summaries(
        # subset_sa_urls,
        wc_vars.event_date_range
    ).pipe(bq_utils.exclude_interval_columns)

    daily_sa_trip_summary.to_parquet(
        f"{GCS_FILE_PATH}fct_daily_service_alerts_trip_summaries_{wc_vars.event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    # (6) fct_daily_service_alerts
    # filter by service_date and sa_base64_url
    daily_service_alerts = filter_fct_daily_service_alerts(
        # subset_sa_urls,
        wc_vars.event_date_range
    )

    daily_service_alerts.to_parquet(
        f"{GCS_FILE_PATH}fct_daily_service_alerts_{wc_vars.event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )
    """
