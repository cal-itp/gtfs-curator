"""
Publish NTD monthly ridership by RTPA.
Publish NTD annual ridership by RTPA (this has multiple files?)

https://github.com/tiffanychu90/curator/blob/test-ntd-data-products/ntd/ntd_utils.py
save_rtpa_outputs():
   - handles monthly or annual
   - both: need RTPA indiv Excel sheets
   - monthly: 4 sheets: full df, by_agency, by_mode, by_tos (does this upload a year grain? the download step implies it)
   - annual: 5 sheets: full df, by_agency, by_mode, by_tos, by_reporter_type
   - both: zip Excel workbook, need public_filename, cover_sheet, upload, remove_local_outputs
"""
import gcsfs
import pandas as pd


def monthly_report_by_rtpa(
    cover_sheet_path = "cover_sheet_template.xlsx",
    cover_sheet_index_col = "**NTD Monthly Ridership by RTPA**"
    indiv_excel_filename = f"{update_vars.YEAR}_{update_vars.MONTH}",
):

    excel_output_foldername = f"{indiv_excel_filename}_monthly_report_data"

    monthly_col_dict = {
        "Uace Cd": "UACE Code",
        "Dt": "Date",
        "Tos": "Type of Service",
        "Legacy Ntd Id": "Legacy NTD ID",
        "Vrm": "VRM",
        "Vrh": "VRH",
        "Voms": "VOMS",
        "Rtpa": "RTPA",
        "Pct Change 1Yr": "Percent Change in 1 Year UPT",
        "Tos Full": "Type of Service Full Name",
    }

	for one_rtpa in df.rtpa.unique():
        rtpa_snakecase =
        
        with pd.ExcelWriter(f"./{indiv_excel_filename}/{rtpa_snakecase}.xlsx", mode="a") as writer:
            import_filtered_rtpa_file("monthly_with_crosswalk.parquet", one_rtpa).to_excel(writer, sheet_name="RTPA Ridership", index=False)
            import_filtered_rtpa_file("monthly/agency.parquet", one_rtpa).to_excel(writer, sheet_name="Aggregated by Agency", index=False)
            import_filtered_rtpa_file("monthly/mode.parquet", one_rtpa).to_excel(writer, sheet_name="Aggregated by Mode", index=False)
            import_filtered_rtpa_file("monthly/type_of_service.parquet", one_rtpa).to_excel(writer, sheet_name="Aggregated by TOS", index=False)

    zip_excel(excel_output_foldername)
    upload_to_gcs()
    publish_to_public_gcs()
    remove_local_outputs()
    return

def import_filtered_rtpa_file(
    gcs_file_name: str = "",
    one_rtpa: str
) -> pd.DataFrame:
    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{gcs_file_name}", 
        filesystem = gcsfs.GCSFileSystem(),
        filters = [[("rtpa_name", "==", one_rtpa)]]
    ).reset_index(drop=True)
    
    return df

def annual_report_by_rtpa(
    cover_sheet_path = "annual_cover_sheet_template.xlsx",
    cover_sheet_index_col = "**NTD Annual Ridership by RTPA**"
    indiv_excel_filename = f"{update_vars.YEAR}_{update_vars.MONTH}",
):
    
    excel_output_foldername = f"{indiv_excel_filename}_annual_report_data"
    # TODO: if this is what columns should be, then we should rename in downloaded table, when it's merged with crosswalk 
    # whatever is downloaded here should be renamed already
	annual_col_dict = {
        "source_agency": "agency", 
        "type_of_service": "tos"
    }

	for one_rtpa in df.rtpa.unique():
        rtpa_snakecase =
        
        with pd.ExcelWriter(f"./{indiv_excel_filename}/{rtpa_snakecase}.xlsx", mode="a") as writer:
            import_filtered_rtpa_file("annual_with_crosswalk.parquet", one_rtpa).to_excel(writer, sheet_name="RTPA Ridership", index=False)
            import_filtered_rtpa_file("annual/agency.parquet", one_rtpa).to_excel(writer, sheet_name="Aggregated by Agency", index=False)
            import_filtered_rtpa_file("annual/mode.parquet", one_rtpa).to_excel(writer, sheet_name="Aggregated by Mode", index=False)
            import_filtered_rtpa_file("annual/type_of_service.parquet", one_rtpa).to_excel(writer, sheet_name="Aggregated by TOS", index=False)
            import_filtered_rtpa_file("annual/reporter_type.parquet", one_rtpa).to_excel(writer, sheet_name="Aggregated by Reporter Type", index=False)
            
    zip_excel(excel_output_foldername)
    upload_to_gcs()
    publish_to_public_gcs()
    remove_local_outputs()
    return


def zip_excel(output_file_name):
    shutil.make_archive(f"./{output_file_name}", "zip", output_file_name)
    return

def upload_to_gcs():
    fs.upload(f"./{output_file_name}.zip", f"{update_vars.GCS_FILE_PATH}{year}_{month}.zip")
    return

def publish_to_public_gcs():
    fs.upload(f"./{output_file_name}.zip", f"{PUBLIC_GCS}ntd_monthly_ridership/{year}_{month}.zip")
    return
