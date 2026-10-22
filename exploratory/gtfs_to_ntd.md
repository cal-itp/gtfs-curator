## NTD agency profile 
* current use case: for each `analysis_name`, label the relevant NTD agency information
   * for LA Metro, since `analysis_name` is 1 agency, we should be able to link to the single NTD ID
   * should be 1:1 matching based on `bridge_gtfs_analysis_name_x_ntd`
   * the need to dedupe dimension tables here might lead to inconsistent labeling with more use cases added.
   * already with 2 tables, 3 steps to use, there are 3 levels of deduping, before we even see the label used. likely, if we switch up order of operations, we won't get the same results.
* future use case: combine this with NTD agency grain tables (`mart_ntd_annual_reporting` or NTD Transit Supply and Demand work Shweta is working on)

**download 2 NTD tables, merge together**

1. `load_ntd`
`mart_ntd.dim_annual_agency_information`

* dedupe (with sorting) by `agency_name`
* still need to dedupe, this one `_is_current` flag is not on, it is dim table. 

2. `load_mobility`

`mart_ntd.dim_mobility_mart_providers`
* dedupe (with sorting) by `agency_name`
* still need to dedupe, even though `_is_current` flag is on within parent tables of `dim_mobility_mart_providers`.
* dimension tables get handled differently throughout analysis.

3. merge the 2 tables together.

* merge on `agency_name` still results in needing to dedupe. why?

**NTD columns used in GTFS Digest, grouped by dbt parent**

4. `dim_annual_agency_information`
* `agency_name`: used to dedupe
* `service_area_sq_miles`, `service_area_pop`, `primary_uza_name`

5. `dim_mobility_mart_providers`
* `agency_name`: used to dedupe and also join with `dim_annual_agency_information`
* `hq_county`: this column is actually just `county_geography_name`, which is already present in `bridge_gtfs_analysis_name_x_ntd`

    ```
    orgs_x_hq AS (
       SELECT * FROM {{ ref('bridge_organizations_x_headquarters_county_geography') }}
       WHERE _is_current
    
    `orgs_x_hq.county_geography_name AS hq_county`
    ```