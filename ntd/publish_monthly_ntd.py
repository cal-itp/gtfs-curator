"""
Publish NTD monthly ridership by RTPA.
"""

import os

import create_excel_outputs as excel_utils
import gcsfs
import pandas as pd
from gtfs_curator_utils import publish_utils
from update_vars import GCS_FILE_PATH

fs = gcsfs.GCSFileSystem()


def monthly_data_to_publish(report_aggregation: str):
    """
    Prep monthly data for publishing.
    Subset columns, rename, etc.
    When multiple data products share the same table, use this to decide which columns
    are relevant to be used.
    """
    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{report_aggregation}_with_crosswalk.parquet", filesystem=gcsfs.GCSFileSystem()
    ).dropna(subset="rtpa_name")
    monthly_col_dict = {
        "Uace Cd": "UACE Code",
        # "Dt": "Date",
        "Tos": "Type of Service",
        "Legacy Ntd Id": "Legacy NTD ID",
        "Vrm": "VRM",
        "Vrh": "VRH",
        "Voms": "VOMS",
        "Rtpa": "RTPA",
        "Pct Change 1Yr": "Percent Change in 1 Year UPT",
        "Tos Full": "Type of Service Full Name",
    }
    df = df.rename(columns=monthly_col_dict)
    return df


def monthly_report_by_rtpa(
    report_aggregation: str = "monthly",
    indiv_excel_filename="2026_02",  # update_vars.YEAR, update_vars.MONTH
):
    df = monthly_data_to_publish(report_aggregation)

    excel_output_foldername = f"{indiv_excel_filename}_{report_aggregation}_report_data"

    for one_rtpa in df.rtpa_name.unique():

        rtpa_excel_filename = excel_utils.insert_excel_cover_sheet(
            report_aggregation, excel_output_foldername, one_rtpa
        )
        excel_utils.export_aggregations_as_excel_sheets(report_aggregation, rtpa_excel_filename, one_rtpa)

    excel_utils.zip_excel(excel_output_foldername)

    fs.put(f"{excel_output_foldername}.zip", f"{GCS_FILE_PATH}publish/{excel_output_foldername}.zip")

    os.remove(f"{excel_output_foldername}.zip")

    publish_utils.write_to_public_gcs(
        f"{GCS_FILE_PATH}publish/{excel_output_foldername}.zip",
        f"ntd_monthly_ridership/{excel_output_foldername}",  # what is the name of this file in public bucket?
        excel_utils.PUBLIC_GCS,
    )
    return


if __name__ == "__main__":

    monthly_report_by_rtpa(
        report_aggregation="monthly",
        indiv_excel_filename="2026_02",  # this is year_month? 2026_Feb?
    )
