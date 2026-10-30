-----------------------------------------------------------------------
-- tiffany_mart_gtfs_rollup.fct_monthly_trip_updates_route_direction_summary
-- for now, let's get the percentile metrics to monthly and use this
-- TODO: what's shared and can make it into a separate model
-- try to set up microbatch, how to add 1 month at a time with lookback configured
-- but event_time set with service_date from upstream? 1 table, 2 incremental
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
-- if this works here, move it into the fct_monthly_operator_summary
-- (https://stackoverflow.com/questions/55905251/how-to-set-a-condition-for-arrays-in-where-clause-bigquery)
pos_prediction_errors AS (
	SELECT 
		month_first_day,
		day_type,
		base64_url,
		schedule_base64_url,
		route_name,
		direction_id,
	    ARRAY(SELECT pe FROM UNNEST(prediction_error_by_minute_array) AS pe WHERE pe > 0) AS prediction_error
	FROM trip_join
),

pos_prediction_errors2 AS (
    {{ get_percentiles_by_group(
        'pos_prediction_errors', 
        ('month_first_day', 'day_type',
        'base64_url', 'schedule_base64_url', 
        'route_name', 'direction_id'), 
        array_col='prediction_error',
        decimals=1) 
    }}
),

	
-- select only negative values for array
neg_prediction_errors AS (
	SELECT 
		month_first_day,
		day_type,
		base64_url,
		schedule_base64_url,
		route_name,
		direction_id,
	    ARRAY(SELECT pe FROM UNNEST(prediction_error_by_minute_array) AS pe WHERE pe < 0) AS prediction_error
	FROM trip_join
),

neg_prediction_errors2 AS (
    {{ get_percentiles_by_group(
        'neg_prediction_errors', 
        ('month_first_day', 'day_type',
        'base64_url', 'schedule_base64_url', 
        'route_name', 'direction_id'), 
        array_col='prediction_error',
        decimals=1) 
    }}
),

route_direction_summary AS (
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

fct_tu_route_direction_summary AS (
    SELECT
        route_direction_summary.*,
 
        pe.value_array AS prediction_error_sec_array,
        pe.value_percentile_array AS prediction_error_sec_percentile_array,
    
        pe.pos_value_array AS positive_prediction_error_sec_array,
        pe.pos_value_percentile_array AS positive_percentile_array,
        pe.neg_value_array AS negative_prediction_error_sec_array,
        pe.neg_value_percentile_array AS negative_percentile_array,

        spe.value_array AS scaled_prediction_error_sec_array,
        spe.value_percentile_array AS scaled_prediction_error_sec_percentile_array,
        
        spe.pos_value_array AS scaled_positive_prediction_error_sec_array,
        spe.pos_value_percentile_array AS scaled_positive_percentile_array,
        spe.neg_value_array AS scaled_negative_prediction_error_sec_array,
        spe.neg_value_percentile_array AS scaled_negative_percentile_array,
    
    FROM route_direction_summary        
    INNER JOIN prediction_error_by_route_direction AS pe 
        USING (month_first_day, day_type, base64_url, schedule_base64_url, route_name, direction_id)
    INNER JOIN scaled_prediction_error_by_route_direction AS spe
        USING (month_first_day, day_type, base64_url, schedule_base64_url, route_name, direction_id)
)
    
SELECT * FROM fct_tu_route_direction_summary