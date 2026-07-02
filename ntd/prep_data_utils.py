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
            group_cols=["ntd_id", "source_agency"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
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
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
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
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
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
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(time_cols + geography_cols + ["reporter_type"])
        .reset_index(drop=True)
    )


def extra_annual_rtpa_splitting(row):
    """
    Replace LA County Public Works agencies with their own RTPA
    For SCAG, use rtpa_name_split that mirrors each county.
    """
    # previously, used list to tag, but one NTD ID: 90271 was missing
    # use string to tag instead for resiliency
    # Los Angeles County - Department of Public Works, Transit Operations, East Los Angeles MB and DR
    # this was previously part of LACMTA, so now counts willl differ
    # lacdpw_list = [
    #    "90269", "90270", "90272", "90273", "90274",
    #    "90275", "90276", "90277", "90278", "90279",
    # ]

    # use 2 conditions to tag, since string can show with LACDPW before hyphen
    if ("Los Angeles County - Department of Public Works" in row.source_agency) or ("LACDPW" in row.source_agency):
        return "Los Angeles County Department of Public Works"
    elif row.rtpa_name == "Southern California Association of Governments":
        return row.rtpa_name_split
    else:
        return row.rtpa_name
