"""
Create rt_operator_metrics.yml
"""

from pathlib import Path

import pandas as pd
import report_utils
from calitp_portfolio.models import load_site
from calitp_portfolio.mutations import generate_parts_flat
from shared_vars import exclude_operators


def check_route_counts(one_month: str):
    """
    Filter the dfs the same way in the operator report,
    and grab the operators that can be populated for both
    percentiles chart and route map.
    """
    filtering = [
        [
            ("month_first_day", "==", pd.to_datetime(one_month)),
            ("schedule_name", "not in", exclude_operators),
            ("tu_name", "not in", exclude_operators),
        ]
    ]

    route_df = (
        report_utils.import_route_df(
            filters=filtering,
            columns=[
                "schedule_name",
                "tu_name",
            ],
        )
        .drop_duplicates()
        .dropna()
        .reset_index(drop=True)
    )

    operator_df = (
        report_utils.import_operator_df(
            filters=filtering, columns=["schedule_name", "tu_name"]
        )
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Use inner merge - charts and maps need both dfs to work
    count_df = pd.merge(
        operator_df, route_df, on=["schedule_name", "tu_name"], how="inner"
    )

    return count_df


def create_rt_operator_metrics_yml(site_path: Path, month: str):
    print(month)
    df = check_route_counts(month)

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
    from shared_vars import operator_report_month

    create_rt_operator_metrics_yml(
        Path("./rt_operator_metrics.yml"), operator_report_month
    )
