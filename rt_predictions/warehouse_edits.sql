-----------------------------------------------------------------------
-- tiffany_mart_gtfs_rollup.fct_monthly_trip_updates_route_direction_summary
-- for now, let's get the percentile metrics to monthly and use this
-- TODO: what's shared and can make it into a separate model
-- try to set up microbatch, how to add 1 month at a time with lookback configured
-- but event_time set with service_date from upstream? 1 table, 2 incremental
-- can this be incremental? how would lookback be set up?
-- incremental, fulll refresh worked
-- job ID: 8f04ee91-ade3-47f4-a1c7-d7586dc33e9a (run for sep); aa0b2f68-bfb6-4454-a07f-393c2bd2d6d9 (run for aug, incremental worked)
-----------------------------------------------------------------------
{{
    config(
        materialized='incremental',
        incremental_strategy='insert_overwrite',
        partition_by = {
            'field': 'month_first_day',
            'data_type': 'date',
            'granularity': 'month',
        },
        cluster_by='base64_url',
    )
}}

-- trip_metrics doesn't have all dates
WITH trip_metrics AS (
    SELECT 
        trip_summaries.service_date,
        trip_summaries.base64_url,
        trip_summaries.schedule_base64_url,
        trip_summaries.trip_instance_key,
        
        trip_metrics.* EXCEPT(service_date, base64_url, trip_key),
    
    FROM `cal-itp-data-infra.mart_gtfs.fct_trip_updates_trip_metrics` AS trip_metrics--{{ ref('fct_trip_updates_trip_metrics') }}
    INNER JOIN `cal-itp-data-infra.mart_gtfs.fct_trip_updates_trip_summaries` AS trip_summaries
        ON trip_summaries.service_date = trip_metrics.service_date
        AND trip_summaries.base64_url = trip_metrics.base64_url
        AND trip_summaries.key = trip_metrics.trip_key
    WHERE trip_metrics.service_date >= "2026-08-01" AND trip_metrics.service_date < "2026-09-01"  
),

scheduled_trips AS (
    SELECT
        service_date,
        trip_instance_key,
        name,
        base64_url,
        route_id,
        route_short_name,
        route_long_name,
        direction_id
    FROM `cal-itp-data-infra.mart_gtfs.fct_scheduled_trips` --{{ ref('fct_scheduled_trips') }}
    WHERE service_date >= "2026-08-01" AND service_date < "2026-09-01"
),

-- we may not have a full month for these metrics to be calculated
-- however, we will want to average for the month for the n_days we do have
-- when we go from route_id->route_name, similar to how other monthly rollup tables are set up,
trip_join AS (
    SELECT
        DATE_TRUNC(trip_metrics.service_date, MONTH) AS month_first_day,
        {{ generate_day_type('trip_metrics.service_date') }} AS day_type,

        trip_metrics.base64_url,
        trip_metrics.trip_instance_key,
        scheduled_trips.name AS schedule_name,
        trip_metrics.schedule_base64_url,
        {{ get_combined_route_name('scheduled_trips.name', 'route_id', 'route_short_name', 'route_long_name') }} AS route_name,
        scheduled_trips.direction_id,

        trip_metrics.* EXCEPT(service_date, base64_url, trip_instance_key, schedule_base64_url)
    
    FROM trip_metrics
    INNER JOIN scheduled_trips
        ON trip_metrics.trip_instance_key = scheduled_trips.trip_instance_key
        AND trip_metrics.service_date = scheduled_trips.service_date
        AND trip_metrics.schedule_base64_url = scheduled_trips.base64_url
),

prediction_error_by_route_direction AS (
    {{ get_percentiles_by_group(
        'trip_join', 
        ('month_first_day', 'day_type',
        'base64_url', 'schedule_base64_url', 
        'route_name', 'direction_id'), 
        array_col='prediction_error_by_minute_array',
        decimals=1) 
    }}
),

scaled_prediction_error_by_route_direction AS (
    {{ get_percentiles_by_group(
        'trip_join', 
        ('month_first_day', 'day_type',
        'base64_url', 'schedule_base64_url', 
        'route_name', 'direction_id'), 
        array_col='scaled_prediction_error_by_minute_array',
        decimals=3) 
    }}
),

-- select only positive values for array (only do it on unscaled)
prediction_errors_subset AS ( -- noqa: L045
	SELECT
		month_first_day,
		day_type,
		base64_url,
		schedule_base64_url,
        route_name,
        direction_id,
	    ARRAY(
            SELECT pe FROM UNNEST(prediction_error_by_minute_array) AS pe WHERE pe > 0
        ) AS pos_prediction_error,
	    ARRAY(
            SELECT pe FROM UNNEST(prediction_error_by_minute_array) AS pe WHERE pe < 0
        ) AS neg_prediction_error,
	FROM trip_join
),

pos_prediction_errors AS (
    {{ get_percentiles_by_group(
        'prediction_errors_subset',
        ('month_first_day', 'day_type',
        'base64_url', 'schedule_base64_url', 
        'route_name', 'direction_id'),
        array_col='pos_prediction_error',
        decimals=1)
    }}
),

neg_prediction_errors AS (
    {{ get_percentiles_by_group(
        'prediction_errors_subset',
        ('month_first_day', 'day_type',
        'base64_url', 'schedule_base64_url', 
        'route_name', 'direction_id'),
        array_col='neg_prediction_error',
        decimals=1)
    }}
),

prediction_array_results AS (
    SELECT
        pe.month_first_day,
        pe.day_type,
        pe.base64_url,
        pe.schedule_base64_url,
        pe.route_name,
        pe.direction_id,

        pe.value_array AS prediction_error_sec_array,
        pe.value_percentile_array AS prediction_error_sec_percentile_array,
        spe.value_array AS scaled_prediction_error_sec_array,

        -- there seems to be some null elements in the pos/neg ones, why? isolating this join to where data is complete hasn't made this go away
        ARRAY(
            SELECT
                COALESCE(pe, 0) AS pe
                FROM UNNEST(pos_pe.value_array) AS pe
        ) AS pos_prediction_error_sec_array,
        ARRAY(
            SELECT
                COALESCE(pe, 0) AS pe
                FROM UNNEST(neg_pe.value_array) AS pe
        ) AS neg_prediction_error_sec_array,
		-- do this because the Newmark paper plots these arrays
		-- to create the charts where smaller errors (closer to zero) are better,
		-- the larger positive errors reverse the percentiles them so that the 10th percentile has larger values
		ARRAY_REVERSE(pos_pe.value_percentile_array) AS pos_prediction_error_sec_percentile_array

    FROM prediction_error_by_route_direction AS pe
    INNER JOIN scaled_prediction_error_by_route_direction AS spe
        ON pe.month_first_day = spe.month_first_day
        AND pe.day_type = spe.day_type
        AND pe.base64_url = spe.base64_url
        AND pe.schedule_base64_url = spe.schedule_base64_url
        AND pe.route_name = spe.route_name
        AND COALESCE(pe.direction_id, -1) = COALESCE(spe.direction_id, -1)    
    LEFT JOIN pos_prediction_errors AS pos_pe --not sure if filtering impacts rows disappearing, use left join for now
        ON pe.month_first_day = pos_pe.month_first_day
        AND pe.day_type = pos_pe.day_type
        AND pe.base64_url = pos_pe.base64_url
        AND pe.schedule_base64_url = pos_pe.schedule_base64_url
        AND pe.route_name = pos_pe.route_name
        AND COALESCE(pe.direction_id, -1) = COALESCE(pos_pe.direction_id, -1) 
    LEFT JOIN neg_prediction_errors AS neg_pe
        ON pe.month_first_day = neg_pe.month_first_day
        AND pe.day_type = neg_pe.day_type
        AND pe.base64_url = neg_pe.base64_url
        AND pe.schedule_base64_url = neg_pe.schedule_base64_url
        AND pe.route_name = neg_pe.route_name
        AND COALESCE(pe.direction_id, -1) = COALESCE(neg_pe.direction_id, -1)  
),
	
tu_route_direction_aggregation AS (
    SELECT
        month_first_day,
        day_type,
        base64_url,
        schedule_base64_url,
        schedule_name,
        route_name,
        direction_id,
    
        ROUND(AVG(avg_prediction_error_sec), 2) AS avg_prediction_error_sec,

        SUM(n_tu_accurate_minutes) AS n_tu_accurate_minutes,
        SUM(n_tu_complete_minutes) AS n_tu_complete_minutes,

        SUM(n_tu_minutes_available) AS n_tu_minutes_available,
        ROUND(AVG(avg_prediction_spread_minutes), 2) AS avg_prediction_spread_minutes,
        SUM(n_predictions) AS n_predictions,

        SUM(n_predictions_early) AS n_predictions_early,
        SUM(n_predictions_ontime) AS n_predictions_ontime,
        SUM(n_predictions_late) AS n_predictions_late,

        SUM(n_tu_stops) AS n_tu_stops,
        COUNT(DISTINCT trip_instance_key) AS n_tu_trips,
    
    FROM trip_join
    GROUP BY 1, 2, 3, 4, 5, 6, 7
),

-- join all calculated trip update metrics
tu_route_dir_metrics AS (
    SELECT
        tu_route_direction_aggregation.*,

        prediction_array_results.* EXCEPT(month_first_day, day_type, base64_url, schedule_base64_url, route_name, direction_id)

    FROM tu_route_direction_aggregation
    LEFT JOIN prediction_array_results
        ON tu_route_direction_aggregation.month_first_day = prediction_array_results.month_first_day
        AND tu_route_direction_aggregation.day_type = prediction_array_results.day_type
        AND tu_route_direction_aggregation.base64_url = prediction_array_results.base64_url
        AND tu_route_direction_aggregation.schedule_base64_url = prediction_array_results.schedule_base64_url
        AND tu_route_direction_aggregation.route_name = prediction_array_results.route_name
        AND COALESCE(tu_route_direction_aggregation.direction_id, -1) = COALESCE(prediction_array_results.direction_id, -1)
)
   
SELECT * FROM tu_route_dir_metrics