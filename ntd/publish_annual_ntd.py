"""
Publish NTD annual ridership by RTPA (this has multiple files?)
"""

import os

import create_excel_outputs as excel_utils
import gcsfs
import pandas as pd
from gtfs_curator_utils import publish_utils
from update_vars import GCS_FILE_PATH

PUBLIC_GCS = "gs://calitp-publish-data-analysis/"
fs = gcsfs.GCSFileSystem()

# list columns to keep for Excel, in order they should appear
ANNUAL_COLS = [
    # NTD identifier columns
    "source_agency",
    "ntd_id",
    "year",
    "mode",
    "mode_full_name",
    "type_of_service",
    "type_of_service_full_name",
    "reporter_type",
    "agency_status",
    "primary_uza_name",
    # metric cols
    "upt",
    "upt_prior_year",
    "upt_change_1yr",
    "upt_pct_change_1yr",
    # RTPA
    "rtpa_name_split",
]

"""
this is the order in Excel
    agency_name
    agency_status
    ntd_id
    primary_uza_name
    reporter_type
    mode
    service
    year
    upt
    RTPA
    previous_y_upt
    change_1yr
    pct_change_1yr
    mode_full
    service_full
"""


def annual_data_to_publish(report_aggregation: str = "annual"):
    """
    Prep annual data for publishing.
    Subset columns, rename, etc.
    Annual ridership and UCLA performance metrics both use the same warehouse table,
    but not every column needs to be published for Excel. Only the relevant upt columns should be published.
    """
    df = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}{report_aggregation}_with_crosswalk.parquet",
            filesystem=gcsfs.GCSFileSystem(),
            columns=ANNUAL_COLS,
        )
        .reindex(columns=ANNUAL_COLS)
        .dropna(subset="rtpa_name")
    )

    # TODO: if this is what columns should be, then we should rename in downloaded table, when it's merged with crosswalk
    # whatever is downloaded here should be renamed already
    annual_col_dict = {"source_agency": "agency", "type_of_service": "tos"}

    df = df.rename(columns=annual_col_dict)  # .sort_values() sorting should be handled within aggregation

    return df


def annual_report_by_rtpa(
    report_aggregation="annual",
    indiv_excel_filename=2024,  # use year?
):
    df = annual_data_to_publish(report_aggregation)
    excel_output_foldername = f"{indiv_excel_filename}_{report_aggregation}_report_data"

    for one_rtpa in df.rtpa_name.unique():
        rtpa_excel_filename = excel_utils.insert_excel_cover_sheet(
            report_aggregation, excel_output_foldername, one_rtpa
        )
        excel_utils.export_aggregations_as_excel_sheets(report_aggregation, rtpa_excel_filename, one_rtpa)

    excel_utils.zip_excel(excel_output_foldername)

    fs.put(f"{excel_output_foldername}.zip", f"{GCS_FILE_PATH}publish/{excel_output_foldername}.zip")

    os.remove(f"./{excel_output_foldername}.zip")

    # in public GCS, can we just overwrite file, since it's always cumulative?
    publish_utils.write_to_public_gcs(
        f"{GCS_FILE_PATH}publish/{excel_output_foldername}.zip",
        f"ntd_annual_ridership/{excel_output_foldername}",  # what is the name of this file in public bucket?
        PUBLIC_GCS,
    )

    return


if __name__ == "__main__":

    ntd_year = 2024

    annual_report_by_rtpa(
        report_aggregation="annual",
        indiv_excel_filename=ntd_year,
    )
