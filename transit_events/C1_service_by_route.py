"""
(1) Define World Cup variables
   - event days
   - non-event days, 1 week before, in between days + 1 week after?
(2) Define points of interest
   - Sofi + Levi Stadium points -> swap for any other points of interest, neighborhoods, etc
   - this could be set up as a gdf that gets input
(3) Plot gtfs_dataset_name-feed_key-route-direction near POI
   - fct_daily_schedule_rt_route_direction_summary
      - tiffany_mart_gtfs has shape_id + shape_array_key
      - merge this in and filter by distance
   - 2 mile or 3 mile for bus
   - 10 mile for rail
   - get list of routes per operator that get near
(4) Metrics that show modified event service
   - routes operating on day / event window that visit stops near event (dim_stop_arrivals)
   - trips on event days vs non-event days (fct_daily_schedule_rt_route_direction_summary)

https://github.com/cal-itp/data-analyses/issues/2043
"""

import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
from gtfs_curator_utils import utils
from gtfs_curator_utils.geography_utils import METERS_PER_MI, WGS84, CA_NAD83Albers_m
from world_cup_vars import GCS_FILE_PATH, event_name

credentials, _ = google.auth.default()


def create_stadiums_poi_gdf(points_dict: dict) -> gpd.GeoDataFrame:
    df = pd.DataFrame(
        {
            "point_of_interest": [label for label, xy_point in points_dict.items()],
            "latitude": [xy_point[1] for label, xy_point in points_dict.items()],
            "longitude": [xy_point[0] for label, xy_point in points_dict.items()],
        }
    )

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=WGS84
    ).drop(columns=["longitude", "latitude"])

    return gdf


def merge_routes_with_shape_geom(
    route_df: pd.DataFrame,
):
    shape_geom = gpd.read_parquet(
        f"{GCS_FILE_PATH}dim_shape_arrays_{event_name}.parquet",
        storage_options={"token": credentials},
        columns=["shape_array_key", "geometry"],
    )

    gdf = pd.merge(shape_geom, route_df, on="shape_array_key", how="inner")

    return gdf


def filter_to_routes_near_poi(
    route_gdf: gpd.GeoDataFrame, poi_gdf: gpd.GeoDataFrame, buffer_meters: float
) -> pd.DataFrame:
    """
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
            route_gdf,
            poi_buffered,
            how="inner",
            predicate="intersects",
        )[
            [
                "schedule_name",
                "route_name",
                "direction_id",
                "shape_array_key",
                "point_of_interest",
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return gdf_near_poi


if __name__ == "__main__":
    # Set the stadium points
    stadium_points_dict = {
        "SoFi Stadium": (-118.338635, 33.953304),
        "Levi's Stadium": (-121.969342, 37.403294),
    }
    stadium_gdf = create_stadiums_poi_gdf(stadium_points_dict)

    utils.geoparquet_gcs_export(
        stadium_gdf, GCS_FILE_PATH, f"points_of_interest_{event_name}"
    )

    # Read in fct_daily_schedule_rt_route_direction_summary, merge in shape geometry
    route_gdf = pd.read_parquet(
        f"{GCS_FILE_PATH}fct_daily_schedule_rt_route_direction_summary_{event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    ).pipe(merge_routes_with_shape_geom)

    # Keep only routes within 3 miles for bus and 10 miles for rail, save these out
    bus_gdf = filter_to_routes_near_poi(
        route_gdf[route_gdf.route_type == "3"], stadium_gdf, METERS_PER_MI * 3
    )

    rail_gdf = filter_to_routes_near_poi(
        route_gdf[route_gdf.route_type.isin(["0", "1", "2"])],
        stadium_gdf,
        METERS_PER_MI * 10,
    )

    routes_near_stadium = pd.concat([bus_gdf, rail_gdf], axis=0, ignore_index=True)

    routes_near_stadium.to_parquet(
        f"{GCS_FILE_PATH}routes_near_poi.parquet", filesystem=gcsfs.GCSFileSystem()
    )
