"""
Merge annual NTD data with RTPA crosswalk.

Aggregate by agency, mode, type of service, reporter_type
and save out parquets.
Filter these parquets in zipped Excel files.
"""

import gcsfs
import pandas as pd
import prep_data_utils
from update_vars import ANNUAL_GCS, GCS_FILE_PATH


def extra_annual_rtpa_splitting(row):
    """
    Replace LA County Public Works agencies with their own RTPA
    For SCAG, use rtpa_name_split that mirrors each county.
    """
    # use 2 conditions to tag, since string can show with LACDPW before hyphen
    if ("Los Angeles County - Department of Public Works" in row.source_agency) or ("LACDPW" in row.source_agency):
        return "Los Angeles County Department of Public Works"
    elif row.rtpa_name == "Southern California Association of Governments":
        return row.rtpa_name_split
    else:
        return row.rtpa_name


def merge_annual_ntd_with_rtpa_crosswalk(report_aggregation: str = "annual") -> pd.DataFrame:
    """
    General function to prep NTD data from
    - script downloads dbt model and saves as monthly.parquet or annual.parquet
    - same crosswalk downloaded
    - merge NTD df with crosswalk
    - monthly and annual have slightly different RTPA mapping, so handle those individually after merge
    - save as monthly_with_crosswalk.parquet or annual_with_crosswalk.parquet
    """
    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{report_aggregation}.parquet",
        # should only certain columns be read in? now this table is much larger
        filesystem=gcsfs.GCSFileSystem(),
    ).pipe(prep_data_utils.merge_with_crosswalk)

    # for annual, use rtpa_name_split
    # for publishing Excel, some columns get renamed, do it all here
    df = (
        df.assign(rtpa=df.apply(extra_annual_rtpa_splitting, axis=1))
        .rename(
            columns={
                "unlinked_passenger_trips": "upt",
                "source_agency": "agency",
            }
        )
        .drop(columns=["rtpa_name", "rtpa_name_split"])
    )
    # can drop rtpa_name_split now, function above gets rtpa_name to split out LA into LACDPW and LA Metro

    df.to_parquet(f"{GCS_FILE_PATH}{report_aggregation}_with_crosswalk.parquet", filesystem=gcsfs.GCSFileSystem())

    return df


def aggregate_annual_and_export(
    df: pd.DataFrame,
):
    """
    For annual NTD data, need aggregations:
    - by agency
    - by mode
    - by type of service
    - by reporter_type (not in monthly)

    Save exports in GCS bucket.
    - annual aggregations saved in GCS_FILE_PATH/annual
    - overwrite these aggregations each time, since they're cumulative (latest date always includes all previous dates)
    - aggregations are used for easier visualizations and Excel outputs (can filter by RTPA)
    """
    prep_data_utils.aggregate_by_agency(
        df, previous_upt_col="upt_prior_year", time_cols=["year"], geography_cols=["rtpa"]
    ).to_parquet(f"{ANNUAL_GCS}agency.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_mode(
        df, previous_upt_col="upt_prior_year", time_cols=["year"], geography_cols=["rtpa"]
    ).to_parquet(f"{ANNUAL_GCS}mode.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_tos(
        df,
        previous_upt_col="upt_prior_year",
        time_cols=["year"],
        geography_cols=["rtpa"],
    ).to_parquet(f"{ANNUAL_GCS}type_of_service.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_reporter_type(
        df, previous_upt_col="upt_prior_year", time_cols=["year"], geography_cols=["rtpa"]
    ).to_parquet(f"{ANNUAL_GCS}reporter_type.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"saved aggregations in {ANNUAL_GCS}")


if __name__ == "__main__":

    # Since annual and monthly NTD pipelines are run at different cadences
    # set up different scripts.
    # Share structure with `prep_data_utils`
    df = merge_annual_ntd_with_rtpa_crosswalk("annual")
    aggregate_annual_and_export(df)
