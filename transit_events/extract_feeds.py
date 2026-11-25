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
import pandas as pd
import world_cup_vars as wc_vars
from google.cloud import bigquery
from gtfs_curator_utils import bq_utils

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH


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

    bq_utils.download_table_with_job_config(
        daily_feeds_query,
        job_config=job_config,
        output_path=f"{GCS_FILE_PATH}fct_daily_schedule_feeds_{wc_vars.event_name}.parquet",
    )

    return


def filter_to_last_n_feeds(one_operator_name: str, feed_type: str, n: int):
    """
    order this by _feed_valid_from and key into it
    can't just use dim_gtfs_datasets_latest
    -- 1st part: get date range, feeds that were relevant in that range
    -- 2nd part: filter to names we want
    -- Inglewood Schedule: doing the partition by name and base64_url means we might keep some older feeds, which had different base64_url
    but if we don't do it, some names might not be continuous, like some change names slightly, and we'd miss them
    """

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

    bq_utils.download_table_with_job_config(
        daily_feeds_query, job_config=job_config, output_path=""
    )

    return


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


def filter_fct_daily_schedule_rt_operator_summary(
    service_date_list: list,
    # schedule_name_list: list = None
):
    """
    Need to save out schedule feed_key, quartet_gtfs_dataset_keys, and quartet base4_urls.
    Future TODO: see how service_alerts can fit into this dbt model
    """

    query = """
        SELECT 
            service_date,
            feed_key,
            _feed_valid_from,
            schedule_gtfs_dataset_key,
            schedule_name,
            schedule_base64_url,
            vp_name,
            vp_gtfs_dataset_key,
            vp_base64_url,
            tu_name,
            tu_gtfs_dataset_key,
            tu_base64_url,
  
    FROM `cal-itp-data-infra.mart_gtfs.fct_daily_schedule_rt_operator_summary`
    """

    bq_utils.download_table(
        query,
        filter_dict={"service_date": service_date_list},
        output_path=f"{GCS_FILE_PATH}fct_daily_schedule_rt_operator_summary_{wc_vars.event_name}.parquet",
    )

    print("fct_daily_schedule_rt_operator_summary feeds")

    return


if __name__ == "__main__":
    # (1) fct_daily_schedule_feeds for entire date range
    filter_fct_daily_schedule_feeds_by_date(wc_vars.event_date_range)

    # (2) filter down to operators for those feeds
    filter_to_operators_for_event(
        wc_vars.event_name, wc_vars.socal_names + wc_vars.bay_area_names
    )

    # (3) filter to fct_daily_schedule_rt_operator_summary for event_date range
    filter_fct_daily_schedule_rt_operator_summary(wc_vars.event_date_range)
