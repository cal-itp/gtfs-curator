"""
GTFS Diagnostics

(1) start from a service date range, which feeds were relevant?
   - grab all, then filter to operators
   - for feeds, be able to get _feed_valid_from, to key into dimension tables

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
from world_cup_vars import GCS_FILE_PATH

# from google.cloud import storage
# gcs_client = storage.Client()
# bucket = gcs_client.bucket("calitp-analytics-data")

credentials, project = google.auth.default()
client = bigquery.Client(project=project, credentials=credentials)
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def filter_fct_daily_schedule_feeds_by_date(
    service_date_list: list,
) -> pd.DataFrame:

    # Figure out how to parameterize this, make sure date list works
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "service_date_list", "DATETIME", service_date_list
            ),
        ]
    )

    daily_feeds_query = """
        SELECT
            feed_key,
            _feed_valid_from,
            gtfs_dataset_name,
            ARRAY_AGG(date ORDER BY date) AS service_date_list,

        FROM `cal-itp-data-infra.mart_gtfs.fct_daily_schedule_feeds`
        WHERE date IN UNNEST(@service_date_list)
        GROUP BY 1, 2, 3
    """

    query_job = client.query(daily_feeds_query, job_config)
    df = query_job.result().to_arrow(bqstorage_client=bqstorage_client).to_pandas()

    return df


def filter_to_last_n_feeds(one_operator_name: str, feed_type: str, n: int):
    """
    order this by _feed_valid_from and key into it
    can't just use dim_gtfs_datasets_latest
    -- 1st part: get date range, feeds that were relevant in that range
    -- 2nd part: filter to names we want
    -- Inglewood Schedule: doing the partition by name and base64_url means we might keep some older feeds, which had different base64_url
    but if we don't do it, some names might not be continuous, like some change names slightly, and we'd miss them
    """
    client = bigquery.Client(project="cal-itp-data-infra", credentials=credentials)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("feed_type", "STRING", feed_type),
            bigquery.ScalarQueryParameter("n_feeds", "INT64", n),
        ]
    )

    daily_feeds_query = """
        WITH filtered_gtfs_datasets AS (
            SELECT
                name AS gtfs_dataset_name,
                base64_url,
                _valid_from,
                _valid_to,
                ROW_NUMBER() OVER(PARTITION BY name, base64_url ORDER BY _valid_from DESC) AS rn
            
            FROM `cal-itp-data-infra.mart_transit_database.dim_gtfs_datasets`
            WHERE CONTAINS_SUBSTR(name, @one_operator_name) AND type = @feed_type 
            ORDER BY name ASC, _valid_from DESC
        ),

        filtered_n_datasets AS (
            SELECT * FROM filtered_gtfs_datasets
            WHERE rn <= @n_feeds
        )
    """

    query_job = client.query(daily_feeds_query, job_config)
    df = query_job.result().to_arrow(bqstorage_client=bqstorage_client).to_pandas()

    return df


def filter_to_operators_for_event(event_name: str, schedule_gtfs_name_list: list):
    """
    fct_daily_schedule_feeds kept entire date range, all operators.

    Names for feeds aren't easy to remember / some we pull multiple feeds,
    so save all the feeds we have
    and filter down by (schedule)_gtfs_dataset_name here.
    """
    subset_feeds = pd.read_parquet(
        f"{GCS_FILE_PATH}fct_daily_schedule_feeds_{event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        filters=[
            [
                ("gtfs_dataset_name", "in", schedule_gtfs_name_list),
            ]
        ],
    )

    subset_feeds.to_parquet(
        f"{GCS_FILE_PATH}feeds_{event_name}.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    print(f"subset feeds for {event_name}")
    return


if __name__ == "__main__":
    import world_cup_vars as wc_vars

    # (1) fct_daily_schedule_feeds for entire date range
    daily_feeds = filter_fct_daily_schedule_feeds_by_date(wc_vars.event_date_range)

    daily_feeds.to_parquet(
        f"{GCS_FILE_PATH}fct_daily_schedule_feeds_{wc_vars.event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    # (2) filter down to operators for those feeds
    filter_to_operators_for_event(
        wc_vars.event_name, wc_vars.socal_names + wc_vars.bay_area_names
    )
