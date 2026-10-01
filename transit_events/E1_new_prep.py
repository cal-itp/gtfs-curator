"""
Consolidate the prep needed for route-direction summary
and stops.

Leave the filtering for proximity and special routes later.
"""

import C4_event_helpers as C4
import C5_proximity as C5
import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
import world_cup_vars as wc_vars
from gtfs_curator_utils import utils

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH
credentials, _ = google.auth.default()


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


def dedupe_route_geom(
    route_gdf: gpd.GeoDataFrame,
    route_cols: list = ["schedule_name", "route_name", "directon_id"],
) -> gpd.GeoDataFrame:
    """
    Once route is aggregated, we lose
    combinations of service_date-[route_cols]-shape_array_key.
    Keep one shape_array_key to use for geom from dim_shapes_arrays.
    """
    route_gdf2 = (
        route_gdf.sort_values(route_cols + ["shape_array_key"])
        .drop_duplicates(subset=route_cols)
        .reset_index()
    )[route_cols + ["shape_array_key", "geometry"]]

    return route_gdf2


def full_route_cleaning(event_name: str, point_of_interest: str) -> gpd.GeoDataFrame:
    if point_of_interest == "sofi":
        point_of_interest_full_name = "SoFi Stadium"
        operator_list = wc_vars.socal_names
        event_time_of_day_dict = wc_vars.sofi_match_times
        route_name_dict = wc_vars.special_socal_routes_dict

    elif point_of_interest == "levi":
        point_of_interest_full_name = "Levi's Stadium"
        operator_list = wc_vars.bay_area_names
        event_time_of_day_dict = wc_vars.levi_match_times
        route_name_dict = wc_vars.special_bayarea_routes_dict

    stadium_gdf = gpd.read_parquet(
        f"{GCS_FILE_PATH}points_of_interest_{event_name}.parquet",
        storage_options={"token": credentials},
        filters=[[("point_of_interest", "==", point_of_interest_full_name)]],
    )

    route_gdf = prep_fct_daily_schedule_rt_route_direction_summary(
        event_name=event_name,
        operator_list=operator_list,
        event_time_of_day_dict=event_time_of_day_dict,
    )

    route_cols = ["schedule_name", "route_name", "direction_id", "route_type"]

    trips_by_event = (
        C4.aggregate_by_event_type(
            route_gdf,
            group_cols=route_cols
            + [
                "event_day",
                "day_type",
            ],
            metric_cols=["n_trips"],
        )
        .rename(columns={"n_trips": "daily_trips"})
        .pipe(
            C4.make_wide,
            index_cols=route_cols,
            pivot_cols=["day_type", "event_day"],
            value_cols=["daily_trips"],
        )
    )

    # Attach deduped route geom to trips_by_event
    route_geom = dedupe_route_geom(route_gdf, route_cols)
    trips_wide_gdf = pd.merge(route_geom, trips_by_event, on=route_cols, how="inner")

    trips_wide_gdf_near = C5.categorize_route_proximity_to_poi(
        trips_wide_gdf, stadium_gdf
    ).pipe(C4.categorize_special_routes, route_name_dict)

    print(f"daily route-direction summary aggregated for {point_of_interest}")

    return trips_wide_gdf_near


def import_routes_near_poi(event_name: str, point_of_interest: str):
    # import the route summary prepared for sofi / levi, use those dummy variables for route
    # and attach to stop data
    route_summary_flagged = pd.read_parquet(
        f"{GCS_FILE_PATH}route_summary_{point_of_interest}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        columns=[
            "schedule_name",
            "route_name",
            "direction_id",
            "is_route_near",
            "is_special_route",
        ],
    ).drop_duplicates()

    # this is the original route_df, has feed_key, which fct_daily_scheduled_stops needs
    full_route_df = pd.read_parquet(
        f"{GCS_FILE_PATH}fct_daily_schedule_rt_route_direction_summary_{event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        columns=["feed_key", "schedule_name", "route_id", "route_name", "direction_id"],
    ).drop_duplicates()

    df = pd.merge(
        full_route_df,
        route_summary_flagged,
        on=["schedule_name", "route_name", "direction_id"],
        how="inner",
    )

    return df


def flag_if_stop_on_near_or_special_route(
    stop_gdf: gpd.GeoDataFrame, route_summary_df: pd.DataFrame
) -> gpd.GeoDataFrame:
    """
    route_summary_df has flags whether route is is_route_near, is_special_route.
    Compare those routes to the stop's route_id_array,
    and tag whether the stop falls on a route that got near stadium, on a route that is special route.
    """
    # For each schedule_name, get a list of the route_ids that were near or special
    near_routes_df = (
        route_summary_df[route_summary_df.is_route_near == True]
        .groupby(["schedule_name"])
        .agg(near_route_ids=("route_id", lambda x: list(set(x))))
        .reset_index()
    )

    special_routes_df = (
        route_summary_df[route_summary_df.is_special_route == True]
        .groupby(["schedule_name"])
        .agg(special_route_ids=("route_id", lambda x: list(set(x))))
        .reset_index()
    )

    stop_gdf2 = pd.merge(
        stop_gdf, near_routes_df, on="schedule_name", how="inner"
    ).merge(special_routes_df, on="schedule_name", how="inner")

    stop_gdf2 = stop_gdf2.assign(
        is_route_near=stop_gdf2.apply(
            lambda x: (
                True
                if any(one_id in x.route_id_array for one_id in x.near_route_ids)
                else False
            ),
            axis=1,
        ),
        is_special_route=stop_gdf2.apply(
            lambda x: (
                True
                if any(one_id in x.route_id_array for one_id in x.special_route_ids)
                else False
            ),
            axis=1,
        ),
    )

    return stop_gdf2


def prep_fct_daily_scheduled_stops(event_name: str, event_time_of_day_dict: dict = {}):
    metric_cols = [
        # "n_hours_in_service",
        "arrivals_per_hour_owl",
        "arrivals_per_hour_early_am",
        "arrivals_per_hour_am_peak",
        "arrivals_per_hour_midday",
        "arrivals_per_hour_pm_peak",
        "arrivals_per_hour_evening",
        "arrivals_owl",
        "arrivals_early_am",
        "arrivals_am_peak",
        "arrivals_midday",
        "arrivals_pm_peak",
        "arrivals_evening",
        "route_id_array",
        "route_type_array",
        # "wheelchair_boarding", "location_type"
    ]

    # stop gdf doesn't have schedule_name, merge that in before we aggregate
    stop_gdf = gpd.read_parquet(
        f"{GCS_FILE_PATH}fct_daily_scheduled_stops_{event_name}.parquet",
        storage_options={"token": credentials},
        columns=[
            "service_date",
            "feed_key",
            "stop_id",
            "stop_name",
            "daily_arrivals",
            "geometry",
        ]
        + metric_cols,
    ).pipe(C4.tag_event_days_and_times, event_time_of_day_dict)

    return stop_gdf


def full_stop_cleaning(event_name: str, point_of_interest: str):
    if point_of_interest == "sofi":
        point_of_interest_full_name = "SoFi Stadium"
        event_time_of_day_dict = wc_vars.sofi_match_times

    elif point_of_interest == "levi":
        point_of_interest_full_name = "Levi's Stadium"
        event_time_of_day_dict = wc_vars.levi_match_times

    stadium_gdf = gpd.read_parquet(
        f"{GCS_FILE_PATH}points_of_interest_{event_name}.parquet",
        storage_options={"token": credentials},
        filters=[[("point_of_interest", "==", point_of_interest_full_name)]],
    )

    routes_df = import_routes_near_poi(event_name, point_of_interest)

    stop_gdf = prep_fct_daily_scheduled_stops(event_name, event_time_of_day_dict).merge(
        routes_df[["feed_key", "schedule_name"]].drop_duplicates(),
        how="inner",
    )

    arrivals_by_event_df = (
        C4.aggregate_by_event_type(
            stop_gdf,
            group_cols=[
                "schedule_name",
                "stop_id",
                "stop_name",
                "event_day",
                "day_type",
            ],
            metric_cols=["daily_arrivals"],
        )
        .pipe(
            C4.make_wide,
            index_cols=["schedule_name", "stop_id", "stop_name"],
            pivot_cols=["day_type", "event_day"],
            value_cols=["daily_arrivals"],
        )
        .pipe(C4.merge_in_stop_geom, stop_gdf)
    )

    arrivals_by_event_df = (
        arrivals_by_event_df.assign(
            combined_change_daily_arrivals=arrivals_by_event_df.change_daily_arrivals_weekday
            + arrivals_by_event_df.change_daily_arrivals_weekend
        )
        .pipe(flag_if_stop_on_near_or_special_route, routes_df)
        .pipe(C5.categorize_stop_proximity_to_poi, stadium_gdf)
    )

    print(f"daily stops aggregated for {point_of_interest}")

    return arrivals_by_event_df


if __name__ == "__main__":
    for p in ["sofi", "levi"]:
        route_gdf = full_route_cleaning(wc_vars.event_name, p)
        utils.geoparquet_gcs_export(route_gdf, GCS_FILE_PATH, f"route_summary_{p}")
        del route_gdf

        stop_gdf = full_stop_cleaning(wc_vars.event_name, p)
        utils.geoparquet_gcs_export(stop_gdf, GCS_FILE_PATH, f"stop_summary_{p}")
        del stop_gdf
