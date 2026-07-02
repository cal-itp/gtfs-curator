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


def merge_with_crosswalk(
    ntd_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge the NTD df with the RTPA crosswalk on ntd_id.
    """
    crosswalk = pd.read_parquet(
        f"{GCS_FILE_PATH}crosswalk.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        columns=["ntd_id_2022", "rtpa_name", "rtpa_name_split"],
    ).rename(columns={"ntd_id_2022": "ntd_id"})

    df = pd.merge(ntd_df, crosswalk, on="ntd_id", how="left")

    return df


def merge_ntd_with_rtpa_crosswalk(report_aggregation: str) -> pd.DataFrame:
    """
    General function to prep NTD data from `mart_ntd` (TODO find annual / monthly names)
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
    ).pipe(merge_with_crosswalk)

    # stuff in this section should move into dbt model
    if report_aggregation == "monthly":
        # source_agency is how annual dbt model refers to agency from dim_agency_information
        # monthly should also follow that naming convention, since it's fewer models
        df = df.rename(columns={"agency": "source_agency"})

    if report_aggregation == "annual":
        # for annual, use rtpa_name_split
        df = df.assign(rtpa_name=df.apply(prep_data_utils.extra_annual_rtpa_splitting, axis=1)).rename(
            columns={"unlinked_passenger_trips": "upt"}
        )

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
    - monthly aggregations saved in GCS_FILE_PATH/monthly
    - overwrite these aggregations each time, since they're cumulative (latest date always includes all previous dates)
    - aggregations are used for easier visualizations and Excel outputs (can filter by RTPA)
    """
    # TODO: make sure groupby includes all the columns that are needed
    # TODO: make sure sorting matches what we want in Excel
    prep_data_utils.aggregate_by_agency(
        df, previous_upt_col="upt_prior_year", time_cols=["year"], geography_cols=["rtpa_name"]
    ).to_parquet(f"{ANNUAL_GCS}agency.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_mode(
        df, previous_upt_col="upt_prior_year", time_cols=["year"], geography_cols=["rtpa_name"]
    ).to_parquet(f"{ANNUAL_GCS}mode.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_tos(
        df,
        previous_upt_col="upt_prior_year",  # this groupby uses type_of_service_full_name and type_of_service
        time_cols=["year"],
        geography_cols=["rtpa_name"],
    ).to_parquet(f"{ANNUAL_GCS}type_of_service.parquet", filesystem=gcsfs.GCSFileSystem())

    prep_data_utils.aggregate_by_reporter_type(
        df, previous_upt_col="upt_prior_year", time_cols=["year"], geography_cols=["rtpa_name"]
    ).to_parquet(f"{ANNUAL_GCS}reporter_type.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"saved aggregations in {ANNUAL_GCS}")


if __name__ == "__main__":

    # Since annual and monthly NTD pipelines are run at different cadences
    # set up different scripts.
    # Share structure with `prep_data_utils`
    df = merge_ntd_with_rtpa_crosswalk("annual")
    aggregate_annual_and_export(df)
