# NTD scripts to dbt models

**Goal**: describe what each script does, then replicate with streamlined and consolidated dbt models.
Make sure models adhere to grains in the warehouse and capture as much of the needed columns as possible.
* monthly ridership: https://github.com/cal-itp/data-analyses/blob/main/ntd/monthly_ridership_report/monthly_ridership_by_rtpa.py
* annual ridership: https://github.com/cal-itp/data-analyses/blob/main/ntd/annual_ridership_report/annual_ridership_script.py
* UCLA performance metrics: https://github.com/cal-itp/data-analyses/blob/main/ntd/new_transit_metrics/new_transit_metrics_utils.py
* utils: https://github.com/cal-itp/data-analyses/blob/main/ntd/ridership_report_utils/_01_ntd_ridership_utils.py
* annual tables (annual ridership + UCLA performance metrics) came from different time-series sheets, so from `stg -> int`, these are separate models for each metric.
   * `fct` doesn't need to maintain the fanout, it can be brought together, so metrics can be calculated with needed columns side-by-side.
   * currently, `fct` just merges in `dim_agency_information` and filters out bad keys, and does this repeatedly, across 10 models. the `int` models can be brought in together to 1 `fct` table, eliminate sprawl.
   * `fct` tables constructed this way wasn't a request based on use, so this can get refactored to match how it's used.

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

### Sanity Check Notes
* Use `rtpa_name_split` + a bit extra to get annual RTPA list set up (this list is different than monthly RTPA list, LACDPW (LA County Dept of Public Works) is split out from LA Metro / LA County overall)
* One NTD that needed to be included in LACDPW wasn't in there before, and was still sorted into LA Metro, this is the difference from existing, but this is correct
   * `Los Angeles County - Department of Public Works, Transit Operations, East Los Angeles MB and DR`
   * due to variety of how these strings show up, use 2 different ways to tag LADPW rows and re-categorize.
   * **validated all other results**, upt values for indiv agencies match, sum of upt by RTPA, sum of agencies by RTPA match
* Use new bridge table to be crosswalk - do not start with GTFS operators, because this will filter out NTD agencies if they don't have GTFS
   * Use very similar crosswalk as `bridge_gtfs_analysis_name_x_ntd` (universe of GTFS operators, bring in NTD IDs for those). Adapt it.
   * NTD bridge will be universe of NTD ID agencies, label it with necessary columns, add as much RTPA cleaning as possible
* **TODO**
   * add macros and get the columns that are needed into dbt model ahead of time - columns are either created or renamed 3 or 4 times, streamline this and remove need for dictionary to map full names
   * identify which columns belong to annual report vs UCLA report, these share same model now

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
* couldn't find NTD API for this

**operating expenses** (TS1.2 Operating and Capital Funding Time Series)
* Excel: https://www.transit.dot.gov/ntd/data-product/ts12-operating-funding-time-series-3
* NTD API tables, found 2022-2024 only
   * Federal, 3 years worth: https://data.transportation.gov/Public-Transit/2022-2024-NTD-Annual-Data-Funding-Sources-Federal-/qpjk-b3zw/about_data

6. `mart_ntd_assets`

### References
* [2024 Publication Guide](https://www.transit.dot.gov/sites/fta.dot.gov/files/2025-10/2024%20Annual%20NTD%20Data%20Publications%20Guide.pdf)
   * Section on `Reconciling Operating Funds Time Series 1.2 and 2.1/2.2` on why operating fund amounts might differ
