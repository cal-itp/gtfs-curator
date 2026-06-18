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

def one_get_rtpa_list_to_use_as_excel_sheets():
    print("creating individual RTPA excel files")

    for i in df["rtpa_name"].unique():

        print(f"creating excel file for: {i}")

        # Filename should be snakecase
        rtpa_snakecase = i.replace(" ", "_").replace("/", "_").lower()

        # insertng readme cover sheet,
        cover_sheet = pd.read_excel(cover_sheet_path, index_col=cover_sheet_index_col)
        cover_sheet.to_excel(f"./{year}_{month}/{rtpa_snakecase}.xlsx", sheet_name="README")

        rtpa_data = (
            df[df["rtpa_name"] == i].sort_values("ntd_id")
            # got error from excel not recognizing timezone, made list to include dropping "execution_ts" column
            .drop(columns="_merge")
        )

        if col_dict:
            rtpa_data = rtpa_data.rename(columns=col_dict)

        agency_cols = ["ntd_id", "agency", "rtpa_name"]
        mode_cols = ["mode", "rtpa_name"]
        tos_cols = ["tos", "rtpa_name"]
        reporter_type = ["reporter_type", "rtpa_name"]
    return

def two_monthly_output():
     # column lists for aggregations

    monthly_group_col_2 = ["period_year", "period_month", "period_year_month"]

    monthly_agg_col = {"upt": "sum", "previous_y_m_upt": "sum", "change_1yr": "sum"}
    monthly_change_col = "previous_y_m_upt"

    by_agency_long = sum_by_group(
        df=rtpa_data,
        group_cols=agency_cols,
        group_col2=monthly_group_col_2,  # look into combingin with base grou_cols
        agg_cols=monthly_agg_col,
        change_col=monthly_change_col,
    )

    by_mode_long = sum_by_group(
        df=rtpa_data,
        group_cols=mode_cols,
        group_col2=monthly_group_col_2,  # look into combingin with base grou_cols
        agg_cols=monthly_agg_col,
        change_col=monthly_change_col,
    )

    by_tos_long = sum_by_group(
        df=rtpa_data,
        group_cols=tos_cols,
        group_col2=monthly_group_col_2,  # look into combingin with base grou_cols
        agg_cols=monthly_agg_col,
        change_col=monthly_change_col,
    )
    # writing pages to excel fil
    with pd.ExcelWriter(f"./{year}_{month}/{rtpa_snakecase}.xlsx", mode="a") as writer:
        rtpa_data.to_excel(writer, sheet_name="RTPA Ridership Data", index=False)
        by_agency_long.to_excel(writer, sheet_name="Aggregated by Agency", index=False)
        by_mode_long.to_excel(writer, sheet_name="Aggregated by Mode", index=False)
        by_tos_long.to_excel(writer, sheet_name="Aggregated by TOS", index=False)
    
    return

def three_annual_output():
    annual_group_col_2 = ["year"]

    annual_agg_col = {
        "upt": "sum",
        "previous_y_upt": "sum",
        "change_1yr": "sum",
    }
    annual_change_col = "previous_y_upt"

    by_agency_long = sum_by_group(
        df=rtpa_data,
        group_cols=agency_cols,
        group_col2=annual_group_col_2,  # look into combingin with base grou_cols
        agg_cols=annual_agg_col,
        change_col=annual_change_col,
    )

    by_mode_long = sum_by_group(
        df=rtpa_data,
        group_cols=mode_cols,
        group_col2=annual_group_col_2,  # look into combingin with base grou_cols
        agg_cols=annual_agg_col,
        change_col=annual_change_col,
    )

    by_tos_long = sum_by_group(
        df=rtpa_data,
        group_cols=tos_cols,
        group_col2=annual_group_col_2,  # look into combingin with base grou_cols
        agg_cols=annual_agg_col,
        change_col=annual_change_col,
    )
    by_reporter_type_long = sum_by_group(
        df=rtpa_data,
        group_cols=reporter_type,
        group_col2=annual_group_col_2,  # look into combingin with base grou_cols
        agg_cols=annual_agg_col,
        change_col=annual_change_col,
    )

    # writing pages to excel fil
    with pd.ExcelWriter(f"./{year}_{month}/{rtpa_snakecase}.xlsx", mode="a") as writer:
        rtpa_data.to_excel(writer, sheet_name="RTPA Ridership Data", index=False)
        by_agency_long.to_excel(writer, sheet_name="Aggregated by Agency", index=False)
        by_mode_long.to_excel(writer, sheet_name="Aggregated by Mode", index=False)
        by_tos_long.to_excel(writer, sheet_name="Aggregated by TOS", index=False)
        by_reporter_type_long.to_excel(writer, sheet_name="Aggregate by Reporter Type", index=False)

    return

def four_zip_and_upload_to_public_gcs():
    print("zipping all excel files")

    shutil.make_archive(f"./{output_file_name}", "zip", f"{year}_{month}")

    print("Zipped folder")

    fs.upload(f"./{output_file_name}.zip", f"{update_vars.GCS_FILE_PATH}{year}_{month}.zip")

    if monthly_upload_to_public:
        fs.upload(f"./{output_file_name}.zip", f"{PUBLIC_GCS}ntd_monthly_ridership/{year}_{month}.zip")
        print("Uploaded to public GCS - monthly report")

    if annual_upload_to_public:
        fs.upload(
            f"./{output_file_name}.zip", f"{PUBLIC_GCS}ntd_annual_ridership/{year}_{month}_annual_report_data.zip"
        )

        print("Uploaded to public GCS - annual report")

    print("complete")
    return 

def current_monthly_workflow():
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
    
    monthly_cover_sheet_path = "cover_sheet_template.xlsx"
    monthly_index_col = "**NTD Monthly Ridership by RTPA**"
    monthly_data_file_name = f"{update_vars.YEAR}_{update_vars.MONTH}_monthly_report_data"
    
    df = _01_ntd_ridership_utils.produce_ntd_monthly_ridership_by_rtpa(update_vars.YEAR, update_vars.MONTH)
    gcs_pandas().data_frame_to_parquet(
        df, f"{GCS_FILE_PATH}ca_monthly_ridership_{update_vars.YEAR}_{update_vars.MONTH}.parquet"
    )
    
    # For each RTPA, we'll produce a single excel and save it to a local folder
    os.makedirs(f"./{update_vars.YEAR}_{update_vars.MONTH}/")
    
    df = gcs_pandas().read_parquet(
        f"{GCS_FILE_PATH}ca_monthly_ridership_{update_vars.YEAR}_{update_vars.MONTH}.parquet"
    )
    _01_ntd_ridership_utils.save_rtpa_outputs(
        df=df,
        year=update_vars.YEAR,
        month=update_vars.MONTH,
        # col_dict = monthly_col_dict,
        cover_sheet_path=monthly_cover_sheet_path,
        cover_sheet_index_col=monthly_index_col,
        output_file_name=monthly_data_file_name,
        report_type="monthly",
        monthly_upload_to_public=True,
    )
    
    _01_ntd_ridership_utils.remove_local_outputs(update_vars.YEAR, update_vars.MONTH)
    return 
    