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


def filter_fct_daily_scheduled_stops_to_special_routes_keep_far_stops(
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

    # only use this to bring schedule_name in for each feed_key
    stops_near_sofi = pd.read_parquet(
        f"{GCS_FILE_PATH}stops_near_poi.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        filters=[[("schedule_name", "in", operator_list)]],
        columns=["feed_key", "schedule_name"],
    ).drop_duplicates()

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
    ).merge(
        stops_near_sofi,
        on=["feed_key"],  # "stop_id", "stop_name"],
        how="inner",
    )

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


def aggregate_by_event_type(
    gdf: gpd.GeoDataFrame, arrivals_col: str = "daily_arrivals"
) -> pd.DataFrame:
    # See how this function can accommodate the aggregation here by time-of-day
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
                arrivals_col: "sum",
                "service_date": "nunique",
            }
        )
        .reset_index()
        .rename(
            columns={
                arrivals_col: "total_arrivals",  # rename for clarity here
                "service_date": "n_days",
            }
        )
    )

    arrivals_by_event_type = arrivals_by_event_type.assign(
        daily_arrivals=arrivals_by_event_type.total_arrivals.divide(
            arrivals_by_event_type.n_days
        ).round(2),
    ).rename(columns={"daily_arrivals": arrivals_col})

    return arrivals_by_event_type


def make_wide(
    df: pd.DataFrame,
    index_cols: list = ["schedule_name", "stop_id", "stop_name"],
    pivot_cols: list = ["day_type", "event_day"],
    value_cols: list = ["daily_arrivals"],
) -> pd.DataFrame:
    """
    Make wide, so that a stop can show weekday event, weekday non_event, and change (event - non_event).
    Fix column names after pivoting, flatten into 1 column name with underscore.
    https://stackoverflow.com/questions/14507794/how-to-flatten-a-hierarchical-index-in-columns
    https://www.reddit.com/r/learnpython/comments/fddx9k/column_names_after_pivot/
    """
    # Map this to event, non_event string values, so that the post-pivot column flattening
    # happens without error
    df = df.assign(event_day=df.event_day.map({True: "event", False: "non_event"}))

    df_wide = df.pivot(
        index=index_cols, columns=pivot_cols, values=value_cols
    ).reset_index()

    # df_wide.columns.get_level_values(0)
    df_wide.columns = [
        "_".join(col).rstrip("_").strip() for col in df_wide.columns.values
    ]

    df_wide = df_wide.assign(
        change_daily_arrivals_weekday=(
            df_wide.daily_arrivals_weekday_event
            - df_wide.daily_arrivals_weekday_non_event
        ).round(1),
        change_daily_arrivals_weekend=(
            df_wide.daily_arrivals_weekend_event
            - df_wide.daily_arrivals_weekend_non_event
        ).round(1),
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


def stop_arrival_change_from_baseline_wide(stop_arrivals: gpd.GeoDataFrame):
    """
    Aggregate stop arrival changes by day_type / event_day.
    Normalize metrics so it's daily arrivals (averaged across days available).
    Make wide, easier to select which column to plot on map or chart.
    Metrics added:
        - weekday event, weekday non-event, weekday change from baseline
        - weekend event, weekend non-event, weekend change from baseline
        - total change from baseline (weekday + weekend)
    """
    arrivals_by_event_df = aggregate_by_event_type(
        stop_arrivals, arrivals_col="daily_arrivals"
    )

    arrivals_wide = make_wide(
        arrivals_by_event_df,
        index_cols=["schedule_name", "stop_id", "stop_name"],
        pivot_cols=["day_type", "event_day"],
        value_cols=["daily_arrivals"],
    ).pipe(merge_in_stop_geom, stop_arrivals)

    arrivals_wide = arrivals_wide.assign(
        combined_change_daily_arrivals=arrivals_wide.change_daily_arrivals_weekday
        + arrivals_wide.change_daily_arrivals_weekend
    )

    return arrivals_wide


def stop_arrival_change_from_baseline_wide_time_of_day(
    stop_arrivals_gdf: gpd.GeoDataFrame, time_of_day: str
) -> gpd.GeoDataFrame:
    """
    Set up comparison of arrivals_per_hour_{time_of_day} for event vs
    non-event.
    event_df is filtered with event_day = True and event_time_of_day, since events can occur in any time-of-day.
    non_event_df is filtered to event_day = False and selecting the arrivals_per_hour_{time_of_day}
    """
    keep_cols = [
        "service_date",
        "schedule_name",
        "stop_id",
        "stop_name",
        "event_day",
        "day_type",
    ]

    # look at arrivals_per_hour_pm_peak for event, keep both day_types
    event_df = stop_arrivals_gdf[
        (stop_arrivals_gdf.event_day == True)
        & (stop_arrivals_gdf.event_time_of_day == time_of_day)
    ][keep_cols + [f"arrivals_per_hour_{time_of_day}"]].reset_index(drop=True)

    # comparison is the same day-type, compare arrivals_per_hour_pm_peak
    nonevent_df = stop_arrivals_gdf[(stop_arrivals_gdf.event_day == False)][
        keep_cols + [f"arrivals_per_hour_{time_of_day}"]
    ].reset_index(drop=True)

    # do something similar as arrivals_wide
    time_of_day_df = pd.concat([event_df, nonevent_df], axis=0, ignore_index=True)

    arrivals_by_event_df = aggregate_by_event_type(
        time_of_day_df, f"arrivals_per_hour_{time_of_day}"
    )

    arrivals_wide = make_wide(
        arrivals_by_event_df,
        index_cols=["schedule_name", "stop_id", "stop_name"],
        value_cols=[f"arrivals_per_hour_{time_of_day}"],
    ).pipe(merge_in_stop_geom, stop_arrivals_gdf)

    arrivals_wide = arrivals_wide.assign(
        combined_change=arrivals_wide[
            [
                f"change_arrivals_per_hour_{time_of_day}_weekday",
                f"change_arrivals_per_hour_{time_of_day}_weekend",
            ]
        ].sum(axis=1)
    ).rename(
        columns={"combined_change": f"combined_change_arrivals_per_hour_{time_of_day}"}
    )

    return arrivals_wide
