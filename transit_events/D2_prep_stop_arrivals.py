"""
A bunch of prep work is needed to prepare fct_daily_scheduled_stops
to be tagged as event / non-event, and aggregate to be ready for viz.
- filtering to stops within vicinity
- filtering to stops along routes that had detected service changes
- aggregate by event / non-event and day_type
- make wide or long for viz, depends on GT or altair


TODO: this needs to be refactored to make more sense conceptually.
It goes back and forth with routes. What is known at each stage, what is the right order?
"""

import C4_event_helpers as C4
import gcsfs
import geopandas as gpd
import google.auth
import numpy as np
import pandas as pd
import world_cup_vars as wc_vars

credentials, _ = google.auth.default()

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH


def filter_to_routes_with_service_changes(
    event_name: str,
    operator_list: list,
    route_name_dict: dict,
    event_time_of_day_dict: dict,
) -> list:

    subset_routes = np.concatenate(
        [i for i in route_name_dict.values() if i is not None]
    ).ravel()

    route_gdf = pd.read_parquet(
        f"{GCS_FILE_PATH}fct_daily_schedule_rt_route_direction_summary_{event_name}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        columns=["schedule_name", "route_name", "route_id"],
        filters=[
            [
                ("schedule_name", "in", operator_list),
                ("route_name", "in", subset_routes),
            ]
        ],
    )

    subset_route_ids = route_gdf.route_id.unique()

    return subset_route_ids


def get_stops_along_special_routes(
    stop_gdf: gpd.GeoDataFrame, list_of_routes: list
) -> pd.DataFrame:
    # filter stops to ones that travel along the routes we want
    # explode to see which route_ids, then drop the ones that aren't found in our list of service changes
    keep_cols = ["feed_key", "stop_id", "stop_name"]

    stops_for_special_routes = (
        stop_gdf[keep_cols + ["route_id_array"]]
        .explode("route_id_array")
        .query("route_id_array in @list_of_routes")[keep_cols]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return stops_for_special_routes


def filter_fct_daily_scheduled_stops_to_special_routes(
    event_name: str = wc_vars.event_name,
    operator_list: list = [],
    route_name_dict: dict = {},
    event_time_of_day_dict: dict = {},
) -> gpd.GeoDataFrame:

    routes_with_changes = filter_to_routes_with_service_changes(
        event_name=event_name,
        operator_list=operator_list,
        route_name_dict=route_name_dict,
        event_time_of_day_dict=event_time_of_day_dict,
    )

    stops_near_sofi = pd.read_parquet(
        f"{GCS_FILE_PATH}stops_near_poi.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        filters=[[("schedule_name", "in", operator_list)]],
    )

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
        "route_id_array",  # "route_type_array",
        # "wheelchair_boarding", "location_type"
    ]

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
    ).merge(stops_near_sofi, on=["feed_key", "stop_id", "stop_name"], how="inner")

    stops_for_special_routes = get_stops_along_special_routes(
        stop_gdf, routes_with_changes
    )

    stop_gdf2 = pd.merge(
        stop_gdf,
        stops_for_special_routes,
        on=["feed_key", "stop_id", "stop_name"],
        how="inner",
    ).pipe(C4.tag_event_days_and_times, event_time_of_day_dict)

    return stop_gdf2


def aggregate_by_event_type(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    arrivals_by_event_type = (
        gdf.groupby(
            [
                "schedule_name",  # "feed_key",
                "stop_id",
                "stop_name",
                "event_day",
                "day_type",
            ]
        )
        .agg(
            {
                "daily_arrivals": "sum",
                "service_date": "nunique",
            }
        )
        .reset_index()
        # rename columns here for clarity
        .rename(
            columns={
                "daily_arrivals": "total_arrivals",
                "service_date": "n_days",
            }
        )
    )

    arrivals_by_event_type = arrivals_by_event_type.assign(
        daily_arrivals=arrivals_by_event_type.total_arrivals.divide(
            arrivals_by_event_type.n_days
        ).round(2),
    )

    return arrivals_by_event_type


def make_wide(
    df: pd.DataFrame,
    group_cols: list = ["schedule_name", "stop_id", "stop_name"],
    metric_cols: list = ["daily_arrivals"],
) -> pd.DataFrame:

    non_event_df = df[df.event_day == False][group_cols + metric_cols].rename(
        columns={**{c: f"{c}_non_event" for c in metric_cols}}
    )

    event_df = df[df.event_day == True][group_cols + metric_cols].rename(
        columns={**{c: f"{c}_event" for c in metric_cols}}
    )

    df_wide = pd.merge(event_df, non_event_df, on=group_cols, how="inner")

    for c in metric_cols:
        df_wide[f"change_{c}"] = round(
            df_wide[f"{c}_event"] - df_wide[f"{c}_non_event"], 1
        )

    return df_wide


def merge_in_stop_geom(
    df: pd.DataFrame, stop_gdf: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:

    stop_geom = stop_gdf[
        ["schedule_name", "stop_id", "stop_name", "route_id_array", "geometry"]
    ]

    stop_geom = (
        stop_geom.assign(route_id_array=stop_geom.route_id_array.str.join(", "))
        .sort_values(["schedule_name", "stop_id"])
        .drop_duplicates(subset=["schedule_name", "stop_id", "stop_name"])
        .reset_index(drop=True)
    )

    df2 = pd.merge(
        stop_geom, df, on=["schedule_name", "stop_id", "stop_name"], how="inner"
    )

    return df2
