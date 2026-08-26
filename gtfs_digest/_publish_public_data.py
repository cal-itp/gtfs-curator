"""
Export the tables we used in the notebook
to create GTFS Digest to our public bucket.
"""
from pathlib import Path
from typing import Literal

import geopandas as gpd
import gcsfs
import google.auth

from gtfs_curator_utils import publish_utils, utils
from update_vars import DIGEST_DICT, PROCESSED_GCS, abbrev_month, PUBLIC_GCS

credentials, _ = google.auth.default()


def grab_filepaths(
    file_keys: list, abbrev_month: str
) -> list:
    """
    For each file in catalog.yml, construct the GCS file path to upload.
    
    Ex: the key-value pair
    schedule_rt_route_direction: "fct_monthly_schedule_rt_route_direction_summary"
    - raw file is {RAW_GCS}fct_monthly_schedule_rt_route_direction_summary_{abbrev_month}.parquet
    - processed file is {PROCESSED_GCS}fct_monthly_schedule_rt_route_direction_summary_{abbrev_month}.parquet
    """
    file_paths = [DIGEST_DICT[f] for f in file_keys]

    return [f"{PROCESSED_GCS}{f}_{abbrev_month}.parquet" for f in file_paths]


def export_parquet_as_csv_or_geojson(
    filename: str,
    filetype: Literal["df", "gdf"],
):
    """
    For parquets, we want to export as csv.
    For geoparquets, we want to export as geojson.
    """
    if filetype == "df":
        df = pd.read_parquet(filename, filesystem = gcsfs.GCSFileSystem())
        df.to_csv(f"{PUBLIC_GCS}gtfs_digest/{Path(filename).stem}.csv", index=False)

    elif filetype == "gdf":
        df = gpd.read_parquet(
            filename,
            storage_options={"token": credentials.token},
        )
        utils.geojson_gcs_export(
            df, f"{PUBLIC_GCS}gtfs_digest/", Path(filename).stem, geojson_type="geojson"
        )


if __name__ == "__main__":
    digest_gdf_keys = ["route_map"]

    digest_df_keys = [
        "schedule_rt_route_direction",
        "operator_summary",
        "hourly_day_type_summary",
    ]

    df_filepaths = grab_filepaths(digest_df_keys, abbrev_month)

    gdf_filepaths = grab_filepaths(digest_gdf_keys, abbrev_month)

    # copy our private files to public GCS
    # for df ones, export as csv too
    # for gdf ones, export as geojson
    for f in df_filepaths + gdf_filepaths:
        publish_utils.write_to_public_gcs(f, f"gtfs_digest/{Path(f).name}", PUBLIC_GCS)

    for f in df_filepaths:
        export_parquet_as_csv_or_geojson(f, filetype="df")

    for f in gdf_filepaths:
        export_parquet_as_csv_or_geojson(f, filetype="gdf")
