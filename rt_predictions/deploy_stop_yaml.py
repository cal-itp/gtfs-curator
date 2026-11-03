"""
Create rt_stop_metrics.yml
"""

from pathlib import Path

import pandas as pd
import report_utils
from calitp_portfolio.models import load_site
from calitp_portfolio.mutations import generate_parts_flat
from shared_vars import exclude_operators


def check_stop_and_route_counts(one_month: str):
    """
    Filter the dfs the same way in the stop report,
    and grab the operators that can be populated .
    """
    filtering = [
        [
            ("month_first_day", "==", pd.to_datetime(one_month)),
            ("schedule_name", "not in", exclude_operators),
            ("tu_name", "not in", exclude_operators),
            ("day_type", "==", "Weekday"),  # for operator report, show day_types
        ]
    ]

    stop_df = (
        report_utils.import_stop_df(
            filters=filtering, columns=["schedule_name", "route_name", "geometry"]
        )
        .dropna(subset=["route_name", "geometry"])
        .drop(columns="geometry")
        .drop_duplicates()
    )

    route_df = (
        report_utils.import_route_df(
            filters=filtering,
            columns=[
                "schedule_name",
                "tu_name",
                "route_name",
            ],
        )
        .dropna(subset="route_name")
        .drop_duplicates()
    )

    # Use inner merge - charts and maps need both dfs to work
    count_df = (
        pd.merge(route_df, stop_df, on=["schedule_name", "route_name"], how="inner")
        .groupby(["schedule_name", "tu_name"])
        .agg({"route_name": "count"})
        .reset_index()
    )

    return count_df


def create_rt_stop_metrics_yml(site_path: Path, month: str):
    print(month)
    df = check_stop_and_route_counts(month)

    site = load_site(site_path)
    site = generate_parts_flat(
        site,
        param_key="name",
        values=sorted(df.tu_name.unique()),
    )

    site.write_yaml(site_path)
    print(f"yaml generated at {site_path}")
    return


if __name__ == "__main__":
    from shared_vars import stop_report_month

    create_rt_stop_metrics_yml(Path("./rt_stop_metrics.yml"), stop_report_month)
