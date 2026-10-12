"""
GTFS Diagnostics

use cases:
- one operator, which feed? which feed_keys?
- Culver City missing
- Santa Barbara arrivals look too high
- OCTA incorrectly parsed

dim_shapes_arrays

export query to arrow, to pandas: 0:01:05.259273
convert to gdf and export: 0:09:07.664431
"""

import datetime

import gcsfs
import google.auth
import pandas as pd
import world_cup_vars as wc_vars
from google.cloud import bigquery_storage
from gtfs_curator_utils import bq_utils, geography_utils, utils

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH

credentials, _ = google.auth.default()
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def filter_dim_shapes(feed_valid_value: str, feed_key_list: list) -> pd.DataFrame:

    dim_gtfs_query = """
        SELECT
            feed_key,
            key AS shape_array_key,
            shape_id,
            pt_array,
        FROM `cal-itp-data-infra.mart_gtfs.dim_shapes_arrays`
    """

    FILENAME = f"dim_shape_arrays_{wc_vars.event_name}.parquet"
    t0 = datetime.datetime.now()

    bq_utils.download_table(
        dim_gtfs_query,
        filter_dict={"_feed_valid_from": feed_valid_value, "feed_key": feed_key_list},
        output_path=f"{GCS_FILE_PATH}{FILENAME}",
        bqstorage_client=bqstorage_client,
    )

    t1 = datetime.datetime.now()
    print(f"export query to arrow, to pandas: {t1 - t0}")

    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{FILENAME}", filesystem=gcsfs.GCSFileSystem()
    ).pipe(geography_utils.convert_to_gdf, "pt_array", "line")

    utils.geoparquet_gcs_export(df, GCS_FILE_PATH, FILENAME)

    t2 = datetime.datetime.now()
    print(f"convert to gdf and export: {t2 - t1}")

    return


if __name__ == "__main__":
    subset_feeds = pd.read_parquet(
        f"{GCS_FILE_PATH}feeds_{wc_vars.event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    # the dtype for the _feed_valid_from query parameter is confusing to set
    # this works, date coerced as datetime, but looks like string, but it's actually date(2026, 1, 1)
    subset_feeds = subset_feeds.assign(
        _feed_valid_from=subset_feeds._feed_valid_from.dt.date
    )
    # ._feed_valid_from.dt.normalize() can set it back to UTC midnight, but this doesn't work for query param either

    subset_feed_valid_from = subset_feeds._feed_valid_from.unique().tolist()
    subset_feed_keys = subset_feeds.feed_key.unique().tolist()

    filter_dim_shapes(subset_feed_valid_from, subset_feed_keys)
