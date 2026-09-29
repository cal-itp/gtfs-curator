"""
Consolidate the prep needed for route-direction summary
and stops.

Leave the filtering for proximity and special routes later.
"""

import C4_event_helpers as C4
import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
import world_cup_vars as wc_vars
from gtfs_curator_utils.geography_utils import METERS_PER_MI, WGS84, CA_NAD83Albers_m

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH

credentials, _ = google.auth.default()


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


def categorize_proximity_to_poi(
    route_gdf: gpd.GeoDataFrame,
    poi_gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """
    For bus, keep within 3 miles.
    For rail, keep within 10 miles.
    """
    bus_gdf = filter_to_routes_near_poi(
        route_gdf[route_gdf.route_type == "3"], poi_gdf, METERS_PER_MI * 3
    )

    rail_gdf = filter_to_routes_near_poi(
        route_gdf[route_gdf.route_type.isin(["0", "1", "2"])],
        poi_gdf,
        METERS_PER_MI * 10,
    )

    route_gdf2 = pd.merge(
        route_gdf,
        bus_gdf,
        on=["schedule_name", "route_name", "direction_id", "shape_array_key"],
        how="left",
        indicator="merge_bus",
    ).merge(
        rail_gdf,
        on=["schedule_name", "route_name", "direction_id", "shape_array_key"],
        how="left",
        indicator="merge_rail",
    )

    # now overwrite the _merge columns
    route_gdf2 = route_gdf2.assign(
        is_near=route_gdf2.apply(
            lambda x: (
                True if x.merge_bus == "both" or x.merge_rail == "both" else False
            ),
            axis=1,
        )
    )

    return route_gdf2


def prep_fct_daily_schedule_rt_route_direction_summary(
    event_name: str = wc_vars.event_name,
    operator_list: list = [],
    event_time_of_day_dict: dict = {},
) -> gpd.GeoDataFrame:
    """
    Tag event info on all operators,
    so aggregation can occur for all operators.
    Include operator list, because World Cup had 2 locations,
    and we don't want to look at transit operators in Bay Area for SoFi.
    """

    route_gdf = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}fct_daily_schedule_rt_route_direction_summary_{event_name}.parquet",
            filesystem=gcsfs.GCSFileSystem(),
            columns=[
                "service_date",
                "schedule_name",
                "feed_key",
                "route_id",
                "route_id_cleaned",
                "route_name",
                "direction_id",
                "route_type",
                "shape_id",
                "shape_array_key",
                "n_trips",
                "num_stop_times",
            ],
            filters=[[("schedule_name", "in", operator_list)]],
        )
        .pipe(C4.merge_routes_with_shape_geom)
        .pipe(C4.tag_event_days_and_times, event_time_of_day_dict)
    )

    return route_gdf


if __name__ == "__main__":
    route_gdf = prep_fct_daily_schedule_rt_route_direction_summary(
        event_name=wc_vars.event_name,
        operator_list=wc_vars.socal_names,
        event_time_of_day_dict=wc_vars.sofi_match_times,
    )

    # can take sofi_trips or route_gdf!
    trips_by_event = (
        C4.aggregate_by_event_type(
            route_gdf,
            group_cols=[
                "schedule_name",
                "route_name",
                "direction_id",
                "event_day",
                "day_type",
            ],
            metric_cols=["n_trips"],
        )
        .rename(
            columns={
                "n_trips": "daily_trips",
            }
        )
        .pipe(
            C4.make_wide,
            index_cols=["schedule_name", "route_name", "direction_id"],
            pivot_cols=["day_type", "event_day"],
            value_cols=["daily_trips"],
        )
        .pipe(C4.merge_routes_with_shape_geom)
        .pipe(categorize_proximity_to_poi)
    )

    # but before this, maybe add a geospatial function to see if it's "near"
    sofi_trips = C4.filter_to_special_routes(
        route_gdf, route_name_dict=wc_vars.special_socal_routes_dict
    )
