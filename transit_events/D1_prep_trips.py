""" """

import C1_service_by_route as C1
import C4_event_helpers as C4
import gcsfs
import geopandas as gpd
import google.auth
import numpy as np
import pandas as pd
import world_cup_vars as wc_vars

credentials, _ = google.auth.default()

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH


def filter_fct_daily_schedule_rt_route_direction_summary_to_special_routes(
    event_name: str = wc_vars.event_name,
    operator_list: list = [],
    route_name_dict: dict = {},
    event_time_of_day_dict: dict = {},
) -> gpd.GeoDataFrame:

    subset_routes = np.concatenate(
        [i for i in route_name_dict.values() if i is not None]
    ).ravel()

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
            filters=[
                [
                    ("schedule_name", "in", operator_list),
                    ("route_name", "in", subset_routes),
                ]
            ],
        )
        .pipe(C1.merge_routes_with_shape_geom)
        .pipe(C4.tag_event_days_and_times, event_time_of_day_dict)
    )

    return route_gdf


def aggregate_daily_trips_by_operator(df: pd.DataFrame):
    df2 = (
        df.groupby(["service_date", "schedule_name"])
        .agg({"n_trips": "sum"})
        .reset_index()
    )

    # Make sure these show up in the same place as the dotted lines
    df2 = df2.assign(service_date=pd.to_datetime(df2.service_date).dt.normalize())
    return df2