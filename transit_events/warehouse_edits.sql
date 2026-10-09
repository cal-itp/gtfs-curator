--------------------------------------------------------------------------
-- mart_transit_database.dim_provider_gtfs_data
-- add columns that give us service_date start/end
--------------------------------------------------------------------------
WITH dim_provider_gtfs_data AS (
    SELECT 
      schedule_gtfs_dataset_key,
      vehicle_positions_gtfs_dataset_key,
      trip_updates_gtfs_dataset_key,
      _valid_from,
      _valid_to,
      -- DAG runs at 4pm Pacific. We use schedule from noon Pacific, so extracting dates this way
      -- gives us a service_date range
      -- otherwise, a feed that ends 2026-07-12 UTC, starts 2026-07-13 UTC
      -- corresponds to 4pm Pacific on 2026-07-12. service_date on 2026-07-12 would then have 2 feeds to choose from,
      -- but we want to choose the earlier one. On 2026-07-13, we are choosing the feed that started at 4pm the previous day.
      EXTRACT(DATE FROM _valid_from) AS _valid_from_service_date,
      EXTRACT(DATE FROM _valid_to) AS _valid_to_service_date,
      --IF(vehicle_positions_gtfs_dataset_key = "07c6c0760475ad0633d6a70b3e059fea", 1, 0) AS keep_me -- this one gets used, which is what we want
    FROM `cal-itp-data-infra.mart_transit_database.dim_provider_gtfs_data`
    --WHERE schedule_gtfs_dataset_key = "7ada6c55e4a29f4535e84c504a994b14"
    --ORDER BY _valid_from
  )
    
  SELECT * FROM dim_provider_gtfs_data
