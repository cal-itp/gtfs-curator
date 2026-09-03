# NTD scripts to dbt models
**Goal**: describe what each script does, then replicate with streamlined and consolidated dbt models.
Make sure models adhere to grains in the warehouse and capture as much of the needed columns as possible.
* monthly ridership [query](https://github.com/cal-itp/data-analyses/blob/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/ridership_report_utils/_01_ntd_ridership_utils.py#L407-L505) and [archived folder](https://github.com/cal-itp/data-analyses/tree/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/monthly_ridership_report)
* annual ridership [query](https://github.com/cal-itp/data-analyses/blob/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/ridership_report_utils/_01_ntd_ridership_utils.py#L295-L404) and [archived folder](https://github.com/cal-itp/data-analyses/tree/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/annual_ridership_report)
* UCLA performance metrics [query](https://github.com/cal-itp/data-analyses/blob/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/new_transit_metrics/new_transit_metrics_utils.py#L16-L179) and [archived folder](https://github.com/cal-itp/data-analyses/tree/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/new_transit_metrics)

## Monthly Ridership by RTPA
1. monthly ridership agency-mode-tos grain data: `mart_ntd_ridership.fct_complete_monthly_ridership_with_adjustments_and_estimates`
   * filter for years (2018-), state (CA), non-nulls
   * [crosswalk](https://github.com/cal-itp/data-analyses/blob/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/ridership_report_utils/_01_ntd_ridership_utils.py#L442C53-L442C57) needed (SCAG is split out by county) - use new bridge table
1. merge in last year's upt: agency-year-mode-tos-upt: `mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode_upt`
   * filter for years (2018-), state (CA) using UZA
1. last year's upt is exported to be second file saved in public GCS
   * It also needs to merge in crosswalk
1. Merge in crosswalk for monthly ridership
   * Note: Merging on too many columns can create problems because csvs and dtypes aren't stable / consistent for NTD ID, Legacy NTD ID, and UZA
1. Add columns for report viz
   * Add [change columns](https://github.com/cal-itp/data-analyses/blob/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/ridership_report_utils/_01_ntd_ridership_utils.py#L34-L54) - compare to same month_one_year_ago, get change and percent change (check that this is done correctly, is it Sep 2026 vs Sep 2025?)
   * Mode and TOS get full names
1. Save [Excel outputs](https://github.com/cal-itp/data-analyses/blob/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/ridership_report_utils/_01_ntd_ridership_utils.py#L138)
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
1. Save [Excel outputs](https://github.com/cal-itp/data-analyses/blob/ac532e3da4b46593efb4468c3204f8f2196fd359/ntd/ridership_report_utils/_01_ntd_ridership_utils.py#L138)
   * Prepare some subtotals (Aggregated by Agency / Mode / TOS / Reporter Type) as individual sheets
   * Attach cover sheet
   * Loop through RTPAs to create Excel worksheet for each
1. Upload to public GCS

### Sanity Check
* check downloaded files
* filter down to which columns to keep, both annual / UCLA report now share same upstream model and all columns are present
   * need to remove some of the other keys in the existing Excel, those aren't meaningful for others
* 2018 is the first year for Python script, but in dbt model, we have earlier years?
   * Python script leaves the 2018 cell blank, but since dbt model can capture everything, and then we subset it, then we have 2018 populated
* Other values for Butte look good
* Sorting in `prep_data_utils` (*done*):
   * Aggregated mode: sort by mode, then year (right now, it sorts by year, mode)
   * Aggregated TOS: sort by TOS then year
* Column naming needs to be standardized, easier to trace lineage when debugging:
   * in monthly, `tos` renamed to `Type of Service`, `tos_full` renamed to `Type of Service Full Name`
     * in monthly Excel cover sheet: data dictionary refers to `TOS`
   * in annual: `tos` renamed to `service`, dbt column is now `type_of_service`.
      * in annual Excel cover sheet: data dictionary refers to `TOS`,
   * **decision: standardize based on monthly**.
      * use `type_of_service`, `type_of_service_full_name`, `mode_full_name` and update Excel cover sheets and columns used for publishing.
      * Err on the side of being more descriptive in column names.
      * For Excel sheets, keep snakecase for now, so just 1 set of renaming in `prep_*_ntd.py` scripts.
      * For cover sheet, remove refs to monthly in the annual coversheet, remove leading spaces, update column names, make sure spacing is the same across both.
* Go with more descriptive column names, monthly dbt models use `vrm`, `voms`, etc
* Monthly ridership, check 2017 to make sure 2018 values are correctly calculated, since queries always filter for 2018-present. Checked Butte, looks good.

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
        'opex_per_vrh':"Operating Expense per Vehicle Revenue Hours", #cost-efficiency
        'opex_per_vrm':"Operating Expense per Vehicle Revenue Miles", #cost-efficiency
        #opex_per_vehicle_trip (denominator is GTFS trips) # cost-efficiency
        'opex_per_upt':"Operating Expense per Unlinked Passenger Trips",
        'upt_per_vrh':"Unlinked Passenger Trips per Vehicle Revenue Hours", #service-effectiveness
        'upt_per_vrm':"Unlinked Passenger Trips per Vehicle Revenue Miles", #service-effectiveness
         #farebox recovery ratio = fares_revenue/opex
    }
   ```

## Our Warehouse
A bunch of these, but can't really distinguish the difference beyond topics, which one is annual and are all the rest monthly?:

1. `mart_ntd`
2. `mart_ntd_ridership`(monthly ridership)

* Excel sheet, updated monthly: https://www.transit.dot.gov/ntd/data-product/monthly-module-adjusted-data-release
* NTD API, updated weekly: https://data.transportation.gov/Public-Transit/Complete-Monthly-Ridership-with-Adjustments-and-Es/8bui-9xvu/data_preview

3. `mart_ntd_annual_reporting`

Covers annual summaries, how does this fit in with the service tables in `mart_ntd_funding_and_expenses`?

4. `mart_ntd_safety_and_security`

5. `mart_ntd_funding_and_expenses`

Based on the prefixes, there are at least 3 main time-series datasets covered.

**service and funding** (TS2.1 - Service Data and Operating Expenses Time Series by Mode)
* Excel : https://www.transit.dot.gov/ntd/data-product/ts21-service-data-and-operating-expenses-time-series-mode-2
* Each sheet is upt, vrm, vrh, etc, and reflected in own intermediate and fct table
* https://data.transportation.gov/Public-Transit/NTD-Annual-Data-View-Operating-Expenses-by-Functio/i5ki-dc58/about_data
* Expenses by function:
  * `vo` = vehicle_operations
  * `vm` = vehicle_maintenance
  * `fm` = facilities_maintenance
  * `ga` = general_administration
  * `nvm` = non_vehicle_maintenance?
  * `fares`
  * `total`

**capital expenditures** (TS3.1 - Capital Expenditures Time Series)
* Excel: https://www.transit.dot.gov/ntd/data-product/ts31-capital-expenditures-time-series-2

**operating expenses** (TS1.2 Operating and Capital Funding Time Series)
* Excel: https://www.transit.dot.gov/ntd/data-product/ts12-operating-funding-time-series-3
* NTD API tables, found 2022-2024 only
   * Federal, 3 years worth: https://data.transportation.gov/Public-Transit/2022-2024-NTD-Annual-Data-Funding-Sources-Federal-/qpjk-b3zw/about_data

6. `mart_ntd_assets`

### References
* [2024 Publication Guide](https://www.transit.dot.gov/sites/fta.dot.gov/files/2025-10/2024%20Annual%20NTD%20Data%20Publications%20Guide.pdf)
   * Section on `Reconciling Operating Funds Time Series 1.2 and 2.1/2.2` on why operating fund amounts might differ
