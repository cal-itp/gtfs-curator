"""
(1) Define World Cup variables
   - use same vars as in service_by_route
(2) Define points of interest
   - use same vars as in service_by_route
(3) Plot daily stops near POI
   - fct_daily_scheduled_stops
      - already has pt_geom and arrival counts by route_type
   - 2 mile or 3 mile for bus
   - 10 mile for rail
   - get list of stops per operator that get near
(4) Metrics that show modified event service
 - stop_time visits (use fct_daily_scheduled_stops arrival columns)

   event time window is the time-of-day bucket event falls in, and
   we want to focus on the surrounding windows?
   for non-event days, those same hours will show decreased service, hopefully
"""

import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
import world_cup_vars as wc_vars
from gtfs_curator_utils.geography_utils import METERS_PER_MI, WGS84, CA_NAD83Albers_m

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH
credentials, _ = google.auth.default()


def filter_to_stops_near_poi(
    stop_gdf: gpd.GeoDataFrame, poi_gdf: gpd.GeoDataFrame, buffer_meters: float
) -> pd.DataFrame:
    """
    similar function as routes near poi
    For bus, keep within 3 miles.
    For rail, keep within 10 miles.
    """
    poi_buffered = poi_gdf.assign(
        geometry=poi_gdf.geometry.to_crs(CA_NAD83Albers_m)
        .buffer(buffer_meters)
        .to_crs(WGS84)
    )

    gdf_near_poi = (
        gpd.sjoin(
            stop_gdf,
            poi_buffered,
            how="inner",
            predicate="intersects",
        )[
            [
                "feed_key",
                "stop_id",
                "stop_name",
                "point_of_interest",
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return gdf_near_poi


if __name__ == "__main__":
    daily_stops = gpd.read_parquet(
        f"{GCS_FILE_PATH}fct_daily_scheduled_stops_{wc_vars.event_name}.parquet",
        storage_options={"token": credentials},
        columns=[
            "feed_key",
            "stop_id",
            "stop_name",
            "route_type_0",
            "route_type_1",
            "route_type_2",
            "route_type_3",
            "geometry",
        ],
    )

    stadium_gdf = gpd.read_parquet(
        f"{GCS_FILE_PATH}points_of_interest_{wc_vars.event_name}.parquet",
        storage_options={"token": credentials},
    )

    keep_cols = ["feed_key", "stop_id", "stop_name", "geometry"]

    bus_gdf = daily_stops[daily_stops.route_type_3 > 0][keep_cols]

    rail_gdf = daily_stops[
        daily_stops[["route_type_0", "route_type_1", "route_type_2"]].sum(axis=1) > 0
    ][keep_cols]

    bus_gdf2 = filter_to_stops_near_poi(bus_gdf, stadium_gdf, METERS_PER_MI * 3)

    rail_gdf2 = filter_to_stops_near_poi(
        rail_gdf,
        stadium_gdf,
        METERS_PER_MI * 10,
    )

    stops_near_stadium = pd.concat([bus_gdf2, rail_gdf2], axis=0, ignore_index=True)

    stops_near_stadium.to_parquet(
        f"{GCS_FILE_PATH}stops_near_poi.parquet", filesystem=gcsfs.GCSFileSystem()
    )
