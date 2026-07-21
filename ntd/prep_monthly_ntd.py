"""
Merge monthly NTD data with RTPA crosswalk.

Aggregate by agency, mode, type of service
and save out parquets.
Filter these parquets in zipped Excel files.
"""

import gcsfs
import pandas as pd
import prep_data_utils
from update_vars import GCS_FILE_PATH, MONTHLY_GCS


def merge_monthly_ntd_with_rtpa_crosswalk(report_aggregation: str = "monthly") -> pd.DataFrame:
    """
    General function to prep NTD data from
    - script downloads dbt model and saves as monthly.parquet or annual.parquet
    - same crosswalk downloaded
    - merge NTD df with crosswalk
    - monthly and annual have slightly different RTPA mapping, so handle those individually after merge
    - save as monthly_with_crosswalk.parquet or annual_with_crosswalk.parquet
    """
    # more of this makes it into dbt model
    df = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}{report_aggregation}.parquet",
            filesystem=gcsfs.GCSFileSystem(),
        )
        .astype(
            {
                **{
                    c: "Int64"
                    for c in [
                        "upt",
                        "voms",
                        "vrh",
                        "vrm",
                        "upt_prior_month",
                        "upt_change_1mo",
                        "upt_prior_year",
                        "upt_change_1yr",
                    ]
                },
                **{i: "Float64" for i in ["upt_pct_change_1mo", "upt_pct_change_1yr"]},
            }
        )
        .pipe(prep_data_utils.merge_with_crosswalk)
        .drop(columns=["rtpa_name"])
        .rename(columns={"rtpa_name_split": "rtpa"})
    )

    round_me = ["upt_pct_change_1mo", "upt_pct_change_1yr"]
    df[round_me] = df[round_me].round(4)

    # TODO: format month_first_day as date, not datetime

    df.to_parquet(f"{GCS_FILE_PATH}{report_aggregation}_with_crosswalk.parquet", filesystem=gcsfs.GCSFileSystem())

    return df


def aggregate_monthly_and_export(df: pd.DataFrame):
    """
    For monthly NTD data, need aggregations:
    - by agency
    - by mode
    - by type of service

    Save exports in GCS bucket.
    - monthly aggregations saved in GCS_FILE_PATH/monthly
    - overwrite these aggregations each time, since they're cumulative (latest date always includes all previous dates)
    - aggregations are used for easier visualizations and Excel outputs (can filter by RTPA)
    """
    prep_data_utils.aggregate_by_agency(
        df,
        previous_upt_col="upt_prior_year",
        time_cols=["month_first_day", "month", "year"],
        geography_cols=["rtpa"],
    ).to_parquet(f"{MONTHLY_GCS}agency.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_mode(
        df,
        previous_upt_col="upt_prior_year",
        time_cols=["month_first_day", "month", "year"],
        geography_cols=["rtpa"],
    ).to_parquet(f"{MONTHLY_GCS}mode.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_tos(
        df,
        previous_upt_col="upt_prior_year",
        time_cols=["month_first_day", "month", "year"],
        geography_cols=["rtpa"],
    ).to_parquet(f"{MONTHLY_GCS}type_of_service.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"saved aggregations in {MONTHLY_GCS}")

    return


if __name__ == "__main__":

    df = merge_monthly_ntd_with_rtpa_crosswalk("monthly")
    aggregate_monthly_and_export(df)
