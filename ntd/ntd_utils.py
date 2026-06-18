"""
Separate out the utility functions needed for aggregation or visualization.
"""

import pandas as pd


def sum_by_group_new(
    df: pd.DataFrame,
    group_cols: list,
    sum_cols: list,
    prior_col: str,
) -> pd.DataFrame:
    """ """
    grouped_df = df.groupby(group_cols, dropna=False).agg({**{c: "sum" for c in sum_cols}}).reset_index()

    # calculate percent change. Turn decimal (0-1) to number (0-100) for easier display in charts.
    # must make sure that the sorting is intact for monthly or annual (sort by year or month_first_day)
    grouped_df = grouped_df.assign(
        pct_change_1_yr=(grouped_df.upt - grouped_df[prior_col]).divide(grouped_df[prior_col]).round(4) * 100
    )

    return grouped_df


def aggregate_by_agency(df, previous_upt_col, time_cols, geography_cols):
    return (
        sum_by_group_new(
            df,
            group_cols=["ntd_id", "agency"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(time_cols + geography_cols + ["ntd_id"])
        .reset_index(drop=True)
    )


def aggregate_by_mode(df, previous_upt_col, time_cols, geography_cols):
    return (
        sum_by_group_new(
            df,
            group_cols=["mode", "mode_full_name"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(time_cols + geography_cols + ["mode"])
        .reset_index(drop=True)
    )


def aggregate_by_tos(df, previous_upt_col, time_cols, geography_cols):
    return (
        sum_by_group_new(
            df,
            group_cols=["type_of_service", "type_of_service_full_name"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(time_cols + geography_cols + ["type_of_service"])
        .reset_index(drop=True)
    )


def aggregate_by_reporter_type(df, previous_upt_col, time_cols, geography_cols):
    return (
        sum_by_group_new(
            df,
            group_cols=["reporter_type"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(time_cols + geography_cols + ["reporter_type"])
        .reset_index(drop=True)
    )
