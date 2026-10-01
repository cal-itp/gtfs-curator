import geopandas as gpd
import google.auth
import pandas as pd
import world_cup_vars as wc_vars
from gtfs_curator_utils.geography_utils import METERS_PER_MI, WGS84, CA_NAD83Albers_m

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH
credentials, _ = google.auth.default()


def filter_to_near_poi(
    route_or_stop_gdf: gpd.GeoDataFrame, poi_gdf: gpd.GeoDataFrame, buffer_meters: float
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
            route_or_stop_gdf,
            poi_buffered,
            how="inner",
            predicate="intersects",
        )
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return gdf_near_poi


def categorize_route_proximity_to_poi(
    route_gdf: gpd.GeoDataFrame,
    poi_gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """
    For bus, keep within 3 miles.
    For rail, keep within 10 miles.
    """
    route_cols = ["schedule_name", "route_name", "direction_id", "shape_array_key"]

    bus_gdf = filter_to_near_poi(
        route_gdf[route_gdf.route_type == "3"], poi_gdf, METERS_PER_MI * 3
    )[route_cols + ["point_of_interest"]].drop_duplicates()

    rail_gdf = filter_to_near_poi(
        route_gdf[route_gdf.route_type.isin(["0", "1", "2"])],
        poi_gdf,
        METERS_PER_MI * 10,
    )[route_cols + ["point_of_interest"]].drop_duplicates()

    route_gdf2 = pd.merge(
        route_gdf,
        bus_gdf,
        on=route_cols,
        how="left",
        indicator="merge_bus",
    ).merge(
        rail_gdf,
        on=route_cols,
        how="left",
        indicator="merge_rail",
    )

    # now overwrite the _merge columns
    route_gdf2 = route_gdf2.assign(
        is_route_near=route_gdf2.apply(
            lambda x: (
                True if x.merge_bus == "both" or x.merge_rail == "both" else False
            ),
            axis=1,
        ),
        point_of_interest=route_gdf2.point_of_interest_x.fillna(
            route_gdf2.point_of_interest_y
        ),
    ).drop(
        columns=[
            "merge_bus",
            "merge_rail",
            "point_of_interest_x",
            "point_of_interest_y",
        ]
    )

    return route_gdf2


def categorize_stop_proximity_to_poi(
    stop_gdf: gpd.GeoDataFrame,
    poi_gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """
    For bus, keep within 3 miles.
    For rail, keep within 10 miles.
    """
    stop_cols = ["schedule_name", "stop_id", "stop_name"]

    bus_gdf = filter_to_near_poi(
        stop_gdf[stop_gdf.route_type_array.str.contains("3")],
        poi_gdf,
        METERS_PER_MI * 3,
    )[stop_cols + ["point_of_interest"]].drop_duplicates()

    rail_gdf = filter_to_near_poi(
        stop_gdf[
            (stop_gdf.route_type_array.str.contains("0"))
            | (stop_gdf.route_type_array.str.contains("1"))
            | (stop_gdf.route_type_array.str.contains("2"))
        ],
        poi_gdf,
        METERS_PER_MI * 10,
    )[stop_cols + ["point_of_interest"]].drop_duplicates()

    stop_gdf2 = pd.merge(
        stop_gdf,
        bus_gdf,
        on=stop_cols,
        how="left",
        indicator="merge_bus",
    ).merge(
        rail_gdf,
        on=stop_cols,
        how="left",
        indicator="merge_rail",
    )

    # now overwrite the _merge columns
    stop_gdf2 = stop_gdf2.assign(
        is_stop_near=stop_gdf2.apply(
            lambda x: (
                True if x.merge_bus == "both" or x.merge_rail == "both" else False
            ),
            axis=1,
        ),
        point_of_interest=stop_gdf2.point_of_interest_x.fillna(
            stop_gdf2.point_of_interest_y
        ),
    ).drop(
        columns=[
            "merge_bus",
            "merge_rail",
            "point_of_interest_x",
            "point_of_interest_y",
        ]
    )

    return stop_gdf2
