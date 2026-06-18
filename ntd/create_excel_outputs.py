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
import pandas as pd


def monthly_report_by_rtpa(
    df,
    cover_sheet_path = "cover_sheet_template.xlsx",
    cover_sheet_index_col = "**NTD Monthly Ridership by RTPA**"
    indiv_excel_filename = f"{update_vars.YEAR}_{update_vars.MONTH}",
):
    time_cols = ["period_year", "period_month", "period_year_month", "month_first_day"]
    previous_upt_col = "previous_y_m_upt"
    # do something to rtpa? one of these has to change
    geography_cols = ["rtpa_name_split"]

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
        by_agency = aggregate_by_agency(df[df.rtpa==one_rtpa], previous_upt_col, time_cols, geography_cols)
        by_mode = aggregate_by_mode(df[df.rtpa==one_rtpa], previous_upt_col, time_cols, geography_cols)
        by_tos = aggregate_by_tos(df[df.rtpa==one_rtpa], previous_upt_col, time_cols, geography_cols)
      
        with pd.ExcelWriter(f"./{indiv_excel_filename}/{rtpa_snakecase}.xlsx", mode="a") as writer:
            df[df.rtpa==one_rtpa].to_excel(writer, sheet_name="RTPA Ridership", index=False)
            by_agency.to_excel(writer, sheet_name="Aggregated by Agency", index=False)
            by_mode.to_excel(writer, sheet_name="Aggregated by Mode", index=False)
            by_tos.to_excel(writer, sheet_name="Aggregated by TOS", index=False)
    
	zip_excel(output_file_name)
    upload_to_gcs()
    publish_to_public_gcs()   
	remove_local_outputs()
    
    return

def annual_report_by_rtpa(
    df,
    cover_sheet_path = "annual_cover_sheet_template.xlsx",
    cover_sheet_index_col = "**NTD Annual Ridership by RTPA**"
    indiv_excel_filename = f"{update_vars.YEAR}_{update_vars.MONTH}",
):
    time_cols = ["year"]
    previous_upt_col = "previous_y_upt"
    # do something to rtpa? one of these has to change
    geography_cols = ["rtpa_name_split"]

    excel_output_foldername = f"{indiv_excel_filename}_annual_report_data"

    for one_rtpa in df.rtpa.unique():
        rtpa_snakecase = 
        by_agency = aggregate_by_agency(df[df.rtpa==one_rtpa], previous_upt_col, time_cols, geography_cols)
        by_mode = aggregate_by_mode(df[df.rtpa==one_rtpa], previous_upt_col, time_cols, geography_cols)
        by_tos = aggregate_by_tos(df[df.rtpa==one_rtpa], previous_upt_col, time_cols, geography_cols)
      
        with pd.ExcelWriter(f"./{indiv_excel_filename}/{rtpa_snakecase}.xlsx", mode="a") as writer:
            df[df.rtpa==one_rtpa].to_excel(writer, sheet_name="RTPA Ridership", index=False)
            by_agency.to_excel(writer, sheet_name="Aggregated by Agency", index=False)
            by_mode.to_excel(writer, sheet_name="Aggregated by Mode", index=False)
            by_tos.to_excel(writer, sheet_name="Aggregated by TOS", index=False)
            by_reporter_type.to_excel(writer, sheet_name="Aggregated by Reporter Type", index=False)
    
    zip_excel(output_file_name)
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
   