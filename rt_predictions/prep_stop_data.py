"""
Merge downloaded stop and stop order tables.

Light data cleaning, remove outliers,
explode arrays to get percentiles for charts.
Get stop order by route merged in.
"""

import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
import report_utils
from gtfs_curator_utils import utils
from shared_vars import PREDICTIONS_GCS, RT_MSA_DICT

credentials, _ = google.auth.default()


def import_stop_order_by_route(**kwargs) -> pd.DataFrame:
    """
    Import int_gtfs_schedule__stop_order_by_route.

    This is feed-route-direction-stop grain.
    It is possible for multiple feed_keys to be active for the month.

    For viz, the stops should roughly be plotted by the order they appear
    for each route-direction.
    Take average across feed_keys for avg(stop_sequence) (not meaningful beyond sorting)
    and assign a stop_rank (whole number).
    """
    df = pd.read_parquet(
        f"{PREDICTIONS_GCS}{RT_MSA_DICT.dbt_model_downloads.stop_order}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        **kwargs,
    )

    df = df.assign(
        stop_rank=df.groupby(
            ["gtfs_dataset_name", "route_name", "direction_id"]
        ).avg_stop_seq.rank(),
    )

    return df


def merge_stops_with_route_info(filename: str) -> gpd.GeoDataFrame:
    """
    Stop metrics should have route-direction + stop_rank attached.
    Merge stop metrics with result returned from import_stop_order_by_route().

    Derive several more metrics, drop outliers, handle unit conversions, rounding.
        - bus catch likelihood - sum of early + on-time predictions,
        - prediction error categorized (we can adjust this for viz)
    Note: Since stops can serve multiple routes, the same metrics will show up for both routes.
    """
    stop_gdf = gpd.read_parquet(
        f"{PREDICTIONS_GCS}{filename}.parquet",
        storage_options={"token": credentials.token},
    )
    stop_gdf = (
        stop_gdf.assign(
            bus_catch_likelihood=(
                stop_gdf.n_predictions_early + stop_gdf.n_predictions_ontime
            )
            .divide(stop_gdf.n_predictions)
            .round(3),
            pct_tu_complete_minutes=stop_gdf.n_tu_complete_minutes.divide(
                stop_gdf.n_tu_minutes_available
            ).round(3),
        )
        .pipe(report_utils.convert_seconds_to_minutes, "avg_prediction_error_sec")
        .pipe(
            report_utils.drop_outliers,
            report_utils.MIN_ERROR_SEC_5MIN,
            report_utils.MAX_ERROR_SEC_5MIN,
        )
        .pipe(
            report_utils.categorize_prediction_error,
            "avg_prediction_error_minutes",
            upper_cutoff=5,
            middle_cutoff=3,
            lower_cutoff=1,
        )
    )

    stop_order = import_stop_order_by_route()

    stop_with_route_gdf = pd.merge(
        stop_gdf,
        stop_order.rename(columns={"gtfs_dataset_name": "schedule_name"}),
        on=["schedule_name", "stop_id"],
        how="left",
    ).pipe(report_utils.add_route_direction_column)

    return stop_with_route_gdf


if __name__ == "__main__":
    DOWNLOADED_DICT = RT_MSA_DICT.dbt_model_downloads
    PROCESSED_DICT = RT_MSA_DICT.rt_schedule_models

    stop_with_route_gdf = merge_stops_with_route_info(
        DOWNLOADED_DICT.weekday_stop_grain
    )

    utils.geoparquet_gcs_export(
        stop_with_route_gdf, PREDICTIONS_GCS, PROCESSED_DICT.weekday_stop_with_route
    )
