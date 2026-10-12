"""
GTFS Diagnostics

use cases:
- one operator, which feed? which feed_keys?
- Culver City missing
- Santa Barbara arrivals look too high
- OCTA incorrectly parsed


dim_shapes_arrays

# (a) filter on all dates, grab only feed_keys needed, extra WHERE statement to narrow down feed_keys

# (b) filter on all service dates, more dates now, filter down feed_keys
# Big Query prod job ID: 9c0d9e51-21e2-40d7-81e0-783b834cf731
export query to arow, to pandas: 0:00:52.880121
convert to gdf: 0:07:06.507688 # this keeps around 1.5MB for memory, low, but takes awhile for ____ rows
.to_geodataframe() didn't work because we keep this as array of WKT?

# (c) add additional dates around event start / end
export query to arrow, to pandas: 0:01:12.100387
convert to gdf: 0:09:10.803260


dim_stops
# (a) filter on all event dates, use .to_geodataframe, since this one seems like it'd work
export query to geodataframe: 0:00:03.023190
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
