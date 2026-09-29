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

import C4_event_helpers as C4
import E1_new_prep as E1
import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
from gtfs_curator_utils.geography_utils import METERS_PER_MI
from world_cup_vars import GCS_FILE_PATH, event_name

credentials, _ = google.auth.default()


if __name__ == "__main__":
    stadium_gdf = gpd.read_parquet(
        f"{GCS_FILE_PATH}points_of_interest_{event_name}.parquet",
        storage_options={"token": credentials},
    )

    # Read in fct_daily_schedule_rt_route_direction_summary, merge in shape geometry
    route_gdf = pd.read_parquet(
        f"{GCS_FILE_PATH}fct_daily_schedule_rt_route_direction_summary_{event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    ).pipe(C4.merge_routes_with_shape_geom)

    # Keep only routes within 3 miles for bus and 10 miles for rail, save these out
    bus_gdf = E1.filter_to_routes_near_poi(
        route_gdf[route_gdf.route_type == "3"], stadium_gdf, METERS_PER_MI * 3
    )

    rail_gdf = E1.filter_to_routes_near_poi(
        route_gdf[route_gdf.route_type.isin(["0", "1", "2"])],
        stadium_gdf,
        METERS_PER_MI * 10,
    )

    routes_near_stadium = pd.concat([bus_gdf, rail_gdf], axis=0, ignore_index=True)

    routes_near_stadium.to_parquet(
        f"{GCS_FILE_PATH}routes_near_poi.parquet", filesystem=gcsfs.GCSFileSystem()
    )
