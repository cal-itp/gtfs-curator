"""
Merge downloaded route summary table with route geom.

Light data cleaning, remove outliers,
explode arrays to get percentiles for charts.
"""

import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
import report_utils
from gtfs_curator_utils import utils
from shared_vars import PREDICTIONS_GCS, RT_MSA_DICT

credentials, _ = google.auth.default()


def clean_route_file(filename: str) -> pd.DataFrame:
    """
    Clean route metrics.

    Derive more metrics, drop outliers, handle unit conversions, rounding.
        - bus catch likelihood - sum of early + on-time predictions,
        - prediction error categorized (we can adjust this for viz)
        - unpack percentile arrays for ones to visualize (IQR, prediction_padding, can adjust to have more too)

    Removing outliers (stops removed 1% on each tail, cutoff was 5 min).
    for routes, use same 5 min cutoff, and this removes less than 1% on each tail.
    1% on each tail is around 3.5 min.
    """
    # this table is a left join with prediction accuracy, so drop rows that don't have tu metrics calculated
    # also dropna with vp_name, because vp can be missing while still having tu
    route_df = (
        pd.read_parquet(
            f"{PREDICTIONS_GCS}{filename}.parquet",
            filesystem=gcsfs.GCSFileSystem(),
        )
        .dropna(subset="n_tu_trips_prediction_accuracy")
        .dropna(subset="vp_name")
    )

    route_df = (
        route_df.assign(
            bus_catch_likelihood=route_df[
                ["pct_predictions_early", "pct_predictions_ontime"]
            ].sum(axis=1),
        )
        .pipe(
            report_utils.drop_outliers,
            report_utils.MIN_ERROR_SEC_5MIN,
            report_utils.MAX_ERROR_SEC_5MIN,
        )
        .pipe(report_utils.convert_seconds_to_minutes, "avg_prediction_error_sec")
        .pipe(
            report_utils.categorize_prediction_error,
            "avg_prediction_error_minutes",
            upper_cutoff=5,
            middle_cutoff=3,
            lower_cutoff=1,
        )
        .pipe(report_utils.add_route_direction_column)
    )

    # Add prediction padding, 25th percentile, 75th percentile, and calculate IQR
    group_cols = [
        "month_first_day",
        "day_type",
        "tu_base64_url",
        "tu_name",
        "schedule_base64_url",
        "schedule_name",
        "route_dir_name",
    ]

    # percentiles are scaled or unscaled
    # For scaled, explode and get percentiles to keep, pivot
    PTILES_TO_DISPLAY = [5, 25, 75]
    scaled_df = report_utils.explode_percentiles(
        route_df,
        group_cols,
        array_col="scaled_prediction_error_sec_array",
        ptile_array_col="prediction_error_sec_percentile_array",
        ptiles_to_keep=[25, 75],
    ).rename(
        columns={
            **{f"p{i}": f"scaled_p{i}" for i in [25, 75]},
            "iqr": "scaled_iqr",
        }
    )

    # For unscaled, explode and get the percentiles to keep, pivot, then convert to minutes
    unscaled_df = (
        report_utils.explode_percentiles(
            route_df,
            group_cols,
            array_col="prediction_error_sec_array",
            ptile_array_col="prediction_error_sec_percentile_array",
            ptiles_to_keep=PTILES_TO_DISPLAY,
        )
        .rename(
            columns={
                **{f"p{i}": f"p{i}" for i in PTILES_TO_DISPLAY},
                "p5": "prediction_padding",
            }
        )
        .pipe(report_utils.convert_seconds_to_minutes, "p25")
        .pipe(report_utils.convert_seconds_to_minutes, "p75")
        .pipe(report_utils.convert_seconds_to_minutes, "prediction_padding")
        .pipe(report_utils.convert_seconds_to_minutes, "iqr")
    )

    # prediction padding is absolute value of 5th percentile, make that explicit here
    percentiles_df = pd.merge(
        scaled_df,
        unscaled_df.assign(prediction_padding=unscaled_df.prediction_padding.abs()),
        on=group_cols,
        how="inner",
    )

    route_df2 = pd.merge(route_df, percentiles_df, on=group_cols, how="inner")

    return route_df2


def merge_in_route_geom(
    route_df: pd.DataFrame, route_geom_filename: str
) -> gpd.GeoDataFrame:
    """
    Merge route metrics with fct_monthly_routes to get the line geometry.
    """
    route_geom = (
        gpd.read_parquet(
            f"{PREDICTIONS_GCS}{route_geom_filename}.parquet",
            storage_options={"token": credentials.token},
            columns=[
                "month_first_day",
                "name",
                "route_name",
                "direction_id",
                "geometry",
            ],
        )
        .pipe(report_utils.add_route_direction_column)
        .drop(columns=["route_name", "direction_id"])
    )

    route_gdf = pd.merge(
        route_geom.rename(columns={"name": "schedule_name"}),
        route_df,
        on=["month_first_day", "schedule_name", "route_dir_name"],
        how="inner",
    )

    return route_gdf


if __name__ == "__main__":
    DOWNLOADED_DICT = RT_MSA_DICT.dbt_model_downloads
    PROCESSED_DICT = RT_MSA_DICT.rt_schedule_models

    route_cleaned = clean_route_file(
        DOWNLOADED_DICT.weekday_route_direction_grain,
    ).pipe(merge_in_route_geom, DOWNLOADED_DICT.route_geom)

    utils.geoparquet_gcs_export(
        route_cleaned, PREDICTIONS_GCS, PROCESSED_DICT.weekday_route_direction
    )
