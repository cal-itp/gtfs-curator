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
from google.cloud import bigquery, bigquery_storage
from gtfs_curator_utils import geography_utils, utils
from world_cup_vars import GCS_FILE_PATH

# from google.cloud import storage
# gcs_client = storage.Client()
# bucket = gcs_client.bucket("calitp-analytics-data")

credentials, project = google.auth.default()
client = bigquery.Client(project=project, credentials=credentials)
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def filter_dim_shapes(feed_valid_value: str, feed_key_list: list) -> pd.DataFrame:

    # Figure out how to parameterize this, make sure date list works
    # this is staging project right now
    # client = bigquery.Client(project=project, credentials=credentials)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("feed_valid_value", "DATE", feed_valid_value),
            bigquery.ArrayQueryParameter("feed_key_list", "STRING", feed_key_list),
        ]
    )

    dim_gtfs_query = """
        SELECT
            feed_key,
            key AS shape_array_key,
            shape_id,
            pt_array,
        FROM `cal-itp-data-infra.mart_gtfs.dim_shapes_arrays`
        WHERE DATE(_feed_valid_from) IN UNNEST(@feed_valid_value) AND feed_key IN UNNEST(@feed_key_list)
    """
    query_job = client.query(dim_gtfs_query, job_config=job_config)

    # df = query_job.result().to_geodataframe(
    #    bqstorage_client=bqstorage_client,
    #    geography_column="pt_array"
    # )
    t1 = datetime.datetime.now()

    df = query_job.result().to_arrow(bqstorage_client=bqstorage_client).to_pandas()

    t2 = datetime.datetime.now()
    print(f"export query to arrow, to pandas: {t2 - t1}")

    df = geography_utils.convert_to_gdf(df, "pt_array", "line")

    t3 = datetime.datetime.now()
    print(f"convert to gdf: {t3 - t2}")

    return df


def filter_dim_stops(feed_valid_value: str, feed_key_list: list) -> pd.DataFrame:

    # Figure out how to parameterize this, make sure date list works
    # this is staging project right now
    # client = bigquery.Client(project=project, credentials=credentials)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("feed_valid_value", "DATE", feed_valid_value),
            bigquery.ArrayQueryParameter("feed_key_list", "STRING", feed_key_list),
        ]
    )

    dim_gtfs_query = """
        SELECT
            feed_key,
            stop_id,
            pt_geom,
        FROM `cal-itp-data-infra.mart_gtfs.dim_stops`
        WHERE DATE(_feed_valid_from) IN UNNEST(@feed_valid_value) AND feed_key IN UNNEST(@feed_key_list)
    """
    query_job = client.query(dim_gtfs_query, job_config=job_config)

    t1 = datetime.datetime.now()

    df = (
        query_job.result()
        .to_geodataframe(bqstorage_client=bqstorage_client, geography_column="pt_geom")
        .rename(columns={"pt_geom": "geometry"})
    )

    t2 = datetime.datetime.now()
    print(f"export query to geodataframe: {t2 - t1}")

    return df


if __name__ == "__main__":
    from world_cup_vars import event_name

    subset_feeds = pd.read_parquet(
        f"{GCS_FILE_PATH}feeds_{event_name}.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    # the dtype for the _feed_valid_from query parameter is confusing to set
    # this works, date coerced as datetime, but looks like string, but it's actually date(2026, 1, 1)
    subset_feeds = subset_feeds.assign(
        _feed_valid_from=subset_feeds._feed_valid_from.dt.date
    )
    # ._feed_valid_from.dt.normalize() can set it back to UTC midnight, but this doesn't work for query param either

    subset_feed_valid_from = subset_feeds._feed_valid_from.unique().tolist()
    subset_feed_keys = subset_feeds.feed_key.unique().tolist()

    dim_shape_arrays = filter_dim_shapes(subset_feed_valid_from, subset_feed_keys)

    utils.geoparquet_gcs_export(
        dim_shape_arrays, GCS_FILE_PATH, f"dim_shape_arrays_{event_name}"
    )

    # dim_stops = filter_dim_stops(subset_feed_valid_from, subset_feed_keys)
    # utils.geoparquet_gcs_export(dim_stops, GCS_FILE_PATH, f"dim_stops_{event_name}")
