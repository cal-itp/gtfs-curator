"""
A bunch of prep work is needed to prepare fct_daily_scheduled_stops
to be tagged as event / non-event, and aggregate to be ready for viz.
- filtering to stops within vicinity
- filtering to stops along routes that had detected service changes
- aggregate by event / non-event and day_type
- make wide or long for viz, depends on GT or altair


TODO: this needs to be refactored to make more sense conceptually.
It goes back and forth with routes. What is known at each stage, what is the right order?
Can the aggregations be done earlier, then filter for the special routes or stops near stadium?
explode stop's route_id_array and use that to filter
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

    stops_for_special_routes = C4.get_stops_along_special_routes(
        stop_gdf, routes_with_changes
    )

    stop_gdf2 = pd.merge(
        stop_gdf,
        stops_for_special_routes,
        on=["feed_key", "stop_id", "stop_name"],
        how="inner",
    ).pipe(C4.tag_event_days_and_times, event_time_of_day_dict)

    return stop_gdf2


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

    return


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

    arrivals_by_event_df = C4.aggregate_by_event_type(
        time_of_day_df,
        group_cols=["schedule_name", "stop_id", "stop_name", "event_day", "day_type"],
        metric_cols=[f"arrivals_per_hour_{time_of_day}"],
    )

    arrivals_wide = C4.make_wide(
        arrivals_by_event_df,
        index_cols=["schedule_name", "stop_id", "stop_name"],
        value_cols=[f"arrivals_per_hour_{time_of_day}"],
    ).pipe(C4.merge_in_stop_geom, stop_arrivals_gdf)

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
