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
from google.cloud import bigquery, bigquery_storage
from gtfs_curator_utils import utils
from world_cup_vars import GCS_FILE_PATH

# from google.cloud import storage
# gcs_client = storage.Client()
# bucket = gcs_client.bucket("calitp-analytics-data")

credentials, _ = google.auth.default()
client = bigquery.Client(project="cal-itp-data-infra-staging", credentials=credentials)
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def filter_fct_daily_schedule_rt_route_direction_summary(
    service_date_list: list,
) -> pd.DataFrame:

    # Figure out how to parameterize this, make sure date list works
    # this is staging project right now
    client = bigquery.Client(
        project="cal-itp-data-infra-staging", credentials=credentials
    )

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "service_date_list", "DATETIME", service_date_list
            ),
        ]
    )

    daily_route_query = """
        SELECT
            *
        FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.fct_daily_schedule_rt_route_direction_summary`
        WHERE service_date IN UNNEST(@service_date_list)
    """

    query_job = client.query(daily_route_query, job_config)
    df = query_job.result().to_arrow(bqstorage_client=bqstorage_client).to_pandas()

    return df


def filter_fct_daily_scheduled_stops(
    service_date_list: list, feed_key_list: list
) -> pd.DataFrame:

    # Figure out how to parameterize this, make sure date list works
    # this is staging project right now
    client = bigquery.Client(project="cal-itp-data-infra", credentials=credentials)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "service_date_list", "DATETIME", service_date_list
            ),
            bigquery.ArrayQueryParameter("feed_key_list", "STRING", feed_key_list),
        ]
    )

    daily_stops_query = """
        SELECT
            *
        FROM `cal-itp-data-infra.mart_gtfs.fct_daily_scheduled_stops`
        WHERE service_date IN UNNEST(@service_date_list) AND feed_key IN UNNEST(@feed_key_list)
    """

    query_job = client.query(daily_stops_query, job_config)
    df = (
        query_job.result()
        .to_geodataframe(bqstorage_client=bqstorage_client, geography_column="pt_geom")
        .rename(columns={"pt_geom": "geometry"})
    )

    return df


if __name__ == "__main__":
    import world_cup_vars as wc_vars

    # (3) `fct_daily_schedule_rt_route_direction_summary` and explore and figure out routes

    daily_route_summary = filter_fct_daily_schedule_rt_route_direction_summary(
        wc_vars.event_date_range
    )

    daily_route_summary = daily_route_summary.assign(
        service_date=pd.to_datetime(daily_route_summary.service_date)
    )

    daily_route_summary.to_parquet(
        f"{GCS_FILE_PATH}fct_daily_schedule_rt_route_direction_summary_{wc_vars.event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    # (4) fct_daily_scheduled_stops
    # filter by service_date and feed_key
    # Big Query prod job ID: 43ee39af-cbd2-44a1-ad24-48e97828eb6c ~2GB
    # what is the size to use bqstorage_client vs not use it?
    subset_feed_keys = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}feeds_{wc_vars.event_name}.parquet",
            filesystem=gcsfs.GCSFileSystem(),
        )
        .feed_key.unique()
        .tolist()
    )

    daily_stops = filter_fct_daily_scheduled_stops(
        wc_vars.event_date_range, subset_feed_keys
    )

    daily_stops = daily_stops.assign(
        service_date=pd.to_datetime(daily_stops.service_date)
    )

    utils.geoparquet_gcs_export(
        daily_stops, GCS_FILE_PATH, f"fct_daily_scheduled_stops_{wc_vars.event_name}"
    )
