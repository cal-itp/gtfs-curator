""" """

import B3_ntd_utils as ntd_utils
import gcsfs
import pandas as pd
from update_vars import GCS_FILE_PATH


def merge_with_crosswalk(
    ntd_df: pd.DataFrame,
):
    crosswalk = pd.read_parquet(
        f"{GCS_FILE_PATH}crosswalk2.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        columns=["ntd_id_2022", "rtpa_name", "rtpa_name_split"],
    ).rename(columns={"ntd_id_2022": "ntd_id"})

    df = pd.merge(ntd_df, crosswalk, on="ntd_id", how="left")

    return df


def merge_ntd_annual_with_rtpa_crosswalk(filename: str):

    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{filename}.parquet",
        # should only certain columns be read in? now this table is much larger
        filesystem=gcsfs.GCSFileSystem(),
    ).pipe(merge_with_crosswalk)

    # for annual, use rtpa_name_split
    df = df.assign(rtpa_name=df.apply(ntd_utils.extra_annual_rtpa_splitting, axis=1)).rename(
        columns={"unlinked_passenger_trips": "upt"}
    )

    df.to_parquet(f"{GCS_FILE_PATH}{filename}_with_crosswalk.parquet", filesystem=gcsfs.GCSFileSystem())
    aggregate_stuff_and_export(df, report_aggregation="annual")

    return


def merge_ntd_monthly_with_rtpa_crosswalk(filename: str):
    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{filename}.parquet",
        # should only certain columns be read in? now this table is much larger
        filesystem=gcsfs.GCSFileSystem(),
    ).pipe(merge_with_crosswalk)

    # for monthly, use rtpa_name?

    df.to_parquet(f"{GCS_FILE_PATH}{filename}_with_crosswalk.parquet", filesystem=gcsfs.GCSFileSystem())

    return


def aggregate_stuff_and_export(df: pd.DataFrame, report_aggregation: str):
    """ """
    OUTPUT_FOLDER = f"{GCS_FILE_PATH}{report_aggregation}/"

    if report_aggregation == "annual":
        time_cols = ["year"]
    elif report_aggregation == "monthly":
        time_cols = ["month_first_day", "mnonth", "year"]

    by_agency = ntd_utils.aggregate_by_agency(
        df, previous_upt_col="upt_prior_year", time_cols=time_cols, geography_cols=["rtpa_name"]
    )

    by_agency.to_parquet(f"{OUTPUT_FOLDER}agency.parquet", filesystem=gcsfs.GCSFileSystem())

    by_mode = ntd_utils.aggregate_by_mode(
        df, previous_upt_col="upt_prior_year", time_cols=time_cols, geography_cols=["rtpa_name"]
    )

    by_mode.to_parquet(f"{OUTPUT_FOLDER}mode.parquet", filesystem=gcsfs.GCSFileSystem())

    by_tos = ntd_utils.aggregate_by_tos(
        df,
        previous_upt_col="upt_prior_year",  # this groupby uses type_of_service_full_name and type_of_service
        time_cols=time_cols,
        geography_cols=["rtpa_name"],
    )

    by_tos.to_parquet(f"{OUTPUT_FOLDER}type_of_service.parquet", filesystem=gcsfs.GCSFileSystem())

    by_reporter_type = ntd_utils.aggregate_by_reporter_type(
        df, previous_upt_col="upt_prior_year", time_cols=time_cols, geography_cols=["rtpa_name"]
    )

    by_reporter_type.to_parquet(f"{OUTPUT_FOLDER}reporter_type.parquet", filesystem=gcsfs.GCSFileSystem())

    print(f"saved aggregations in {OUTPUT_FOLDER}")

    return


if __name__ == "__main__":

    merge_ntd_annual_with_rtpa_crosswalk("annual")

    # TODO: since these are different cadences,
    # how should these scripts be set up so that we can share structure
    # but only once every 12 months do we have to run both
    # merge_ntd_annual_with_rtpa_crosswalk("monthly")
