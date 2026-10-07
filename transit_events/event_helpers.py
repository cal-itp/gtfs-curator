"""
All the event-related work.

Tag whether service_date had event, what event's time-of-day is.
Filter for special routes.
Merge in shape geom and stop geom.
Aggregation by day_type-event_day for route-direction summary and stops.
"""

from typing import Literal

import geopandas as gpd
import google.auth
import numpy as np
import pandas as pd
import world_cup_vars as wc_vars

credentials, _ = google.auth.default()

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH


def tag_event_days_and_times(df: pd.DataFrame, event_day_time_bucket_dict: dict):

    # fix the dict to work with datetime
    # hard to set this dict up correctly with dtypes
    event_day_time_bucket_dict = {
        pd.to_datetime(k): v for k, v in event_day_time_bucket_dict.items()
    }

    df = df.assign(
        event_day=df.apply(
            lambda x: (
                True
                if x.service_date in list(event_day_time_bucket_dict.keys())
                else False
            ),
            axis=1,
        ),
        day_type=df.apply(
            lambda x: "weekend" if x.service_date.dayofweek >= 5 else "weekday", axis=1
        ),
        event_time_of_day=df.service_date.map(event_day_time_bucket_dict).fillna(
            "non_event_day"
        ),
    )

    return df


def grab_matches_by_day_type(
    event_time_of_day_dict: dict,
    time_of_day: Literal["early_am", "am_peak", "midday", "pm_peak", "evening", "owl"],
    day_type: Literal["weekday", "weekend"],
) -> dict:
    """
    Or create a new dict that can key into weekday or weekend?
    """
    WEEKDAY_LIST = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    filtered_events = {
        **{
            d: tod
            for d, tod in wc_vars.sofi_match_times.items()
            if (tod == time_of_day)
            and (
                pd.to_datetime(d).day_name() in ["Saturday", "Sunday"]
                if day_type == "weekend"
                else pd.to_datetime(d).day_name() in WEEKDAY_LIST
            )
        }
    }

    return filtered_events


def merge_routes_with_shape_geom(
    route_df: pd.DataFrame,
):
    shape_geom = gpd.read_parquet(
        f"{GCS_FILE_PATH}dim_shape_arrays_{wc_vars.event_name}.parquet",
        storage_options={"token": credentials},
        columns=["shape_array_key", "geometry"],
    )

    gdf = pd.merge(shape_geom, route_df, on="shape_array_key", how="inner")

    return gdf


def merge_in_stop_geom(
    df: pd.DataFrame, stop_gdf: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:

    stop_geom = stop_gdf[
        [
            "schedule_name",
            "stop_id",
            "stop_name",
            "route_id_array",
            "route_type_array",
            "geometry",
        ]
    ]

    stop_geom = (
        stop_geom.assign(
            route_id_array=stop_geom.route_id_array.str.join(", "),
            route_type_array=stop_geom.apply(
                lambda x: ", ".join(map(str, x.route_type_array)), axis=1
            ),
        )
        .sort_values(["schedule_name", "stop_id"])
        .drop_duplicates(subset=["schedule_name", "stop_id", "stop_name"])
        .reset_index(drop=True)
    )

    df2 = pd.merge(
        stop_geom, df, on=["schedule_name", "stop_id", "stop_name"], how="inner"
    )

    return df2


def categorize_special_routes(
    route_gdf: gpd.GeoDataFrame,
    route_name_dict: dict = {},
) -> gpd.GeoDataFrame:
    """
    Should this be filter or add dummy variable?
    """
    subset_routes = np.concatenate(
        [i for i in route_name_dict.values() if i is not None]
    ).ravel()

    route_gdf = route_gdf.assign(
        is_special_route=route_gdf.apply(
            lambda x: True if x.route_name in subset_routes else False, axis=1
        )
    )

    return route_gdf


def aggregate_daily_trips(df: pd.DataFrame, group_cols: list):
    df2 = df.groupby(group_cols).agg({"n_trips": "sum"}).reset_index()

    # Make sure these show up in the same place as the dotted lines
    df2 = df2.assign(service_date=pd.to_datetime(df2.service_date).dt.normalize())
    return df2


def aggregate_by_event_type(
    gdf: gpd.GeoDataFrame,
    group_cols: list = [
        "schedule_name",
        "stop_id",
        "stop_name",
        "event_day",
        "day_type",
    ],
    sum_cols: list = ["daily_arrivals"],
    mean_cols: list = [],
) -> pd.DataFrame:
    """
    Can be used for stop arrivals and trips
    """

    df = (
        gdf.groupby(group_cols)
        .agg(
            {
                **{c: "sum" for c in sum_cols},
                **{c: "mean" for c in mean_cols},
                "service_date": "nunique",
            }
        )
        .reset_index()
        .rename(columns={"service_date": "n_days"})
    )

    # rounding
    for c in sum_cols:
        df[c] = df[c].divide(df.n_days).round(2)

    df[mean_cols] = df[mean_cols].round(2)

    return df


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

    # the pivot will create all the combinations available
    # however, for time-of-day comparisons, we might be missing combinations
    # ex: event is only weekday; weekend has no event vs non-event comparison
    # in these cases, create the columns and fill with zeros? should the function end earlier so it's explicit where this is done?
    for c in value_cols:
        df_wide[f"change_{c}_weekday"] = change_from_nonevent_column(
            df_wide, f"{c}_weekday"
        ).round(1)
        df_wide[f"change_{c}_weekend"] = change_from_nonevent_column(
            df_wide, f"{c}_weekend"
        ).round(1)

    return df_wide


def change_from_nonevent_column(df: pd.DataFrame, col_prefix: str) -> pd.Series:
    """
    Calculate change column.
    Columns take pattern: {metric}_{day_type}_{event_type}
    - daily_arrivals_weekday_event - daily_arrivals_weekday_non_event
    - daily_trips_weekend_event - daily_trips_weekend_non_event
    - arrivals_per_hour_pm_peak_event - arrivals_per_hour_pm_peak_non_event
    """
    df[f"{col_prefix}_event"] = df[f"{col_prefix}_event"].fillna(0)
    df[f"{col_prefix}_non_event"] = df[f"{col_prefix}_non_event"].fillna(0)
    return (df[f"{col_prefix}_event"] - df[f"{col_prefix}_non_event"]).fillna(0)
