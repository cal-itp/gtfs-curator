# NTD scripts to dbt models

**Goal**: describe what each script does, then replicate with streamlined and consolidated dbt models.
Make sure models adhere to grains in the warehouse and capture as much of the needed columns as possible.
* monthly ridership: TODO URL
* annual ridership: TODO URL
* UCLA performance metrics: TODO URL

## Monthly Ridership by RTPA
1. monthly ridership agency-mode-tos grain data: `mart_ntd_ridership.fct_complete_monthly_ridership_with_adjustments_and_estimates`
   * filter for years (2018-), state (CA), non-nulls
   * crosswalk (SCAG is split out by county) - use new bridge table
1. TODO define grain for operating expenses: `mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode_upt`
   * filter for years (2018-), state (CA) using UZA
1. Merge ridership with operator expenses
1. Merge in crosswalk
   * Note: Merging on too many columns can create problems because csvs and dtypes aren't stable / consistent for NTD ID, Legacy NTD ID, and UZA
1. Add columns for report viz
   * Add change columns - compare to same month_one_year_ago, get change and percent change
   * Mode and TOS get full names
1. Save Excel outputs
   * Prepare some subtotals (Aggregated by Agency / Mode / TOS) as individual sheets
   * Attach cover sheet
   * Loop through RTPAs to create Excel worksheet for each
1. Upload to public GCS

## Annual Ridership by RTPA
1. annual ridership and operating expenses (agency-mode-tos grain data): `mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode_upt`
   * filter for years (2018-), state (CA) using UZA
   * there is a group by to sum, so this aggregated grain is what we want
   * check why columns are not named the same, do values differ? tos vs type_of_service; mode vs mode_name vs _3_mode
   * make crosswalk (same as monthly)
1. Merge in crosswalk
   * There is a separate handling of ntd_ids that belong to LA County Dept of Public Works, they get mapped to a different RTPA? Or they just get flagged as being merged?
1. Add columns for report viz
   * Add change columns - compare to same one_year_ago, get change and percent change
   * Mode and TOS get full names
1. Save Excel outputs
   * Prepare some subtotals (Aggregated by Agency / Mode / TOS / Reporter Type) as individual sheets
   * Attach cover sheet
   * Loop through RTPAs to create Excel worksheet for each
1. Upload to public GCS

## UCLA NTD Performance Metrics
1. annual operating expenses (agency-mode grain data): `mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode_opexp_total`
   * filter for years (2018-), state (CA) using UZA, non-nulls
   * check mode vs mode_status? agency_status? reporter_type? is that used in annual ridership?
   * upt, vrh, vrm tables have a clear lineage, but feels really repetitive
1. annual **upt** agency-mode grain data:  `mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode_upt`
1. annual **vrh** agency-mode grain data: `mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode_vrh`
1. annual **vrm** agency-mode grain data: `mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode_vrm`
1. Merge in crosswalk
1. Add columns for report viz
   * Mode, service (why isn't this called tos) -> TOS get full names
   * dtypes wrangling: integrify
   * These were used in notebook:
   ```
   rename_cols={
        'upt':"Unlinked Passenger Trips",
        'vrm':"Vehicle Revenue Miles",
        'vrh':"Vehicle Revenue Hours",
        'opexp_total':"Operating Expense Total",
        'opex_per_vrh':"Operating Expense per Vehicle Revenue Hours",
        'opex_per_vrm':"Operating Expense per Vehicle Revenue Miles",
        'opex_per_upt':"Operating Expense per Unlinked Passenger Trips",
        'upt_per_vrh':"Unlinked Passenger Trips per Vehicle Revenue Hours",
        'upt_per_vrm':"Unlinked Passenger Trips per Vehicle Revenue Miles",
    }
   ```
