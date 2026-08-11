------------------------------------------------------------------
-- (1) fct_daily_schedule_feeds
------------------------------------------------------------------
{{ config(materialized='table') }}

WITH date_spine AS (
    SELECT *
    FROM {{ ref('util_gtfs_schedule_v2_date_spine') }}
),

dim_schedule_feeds AS (
    SELECT *
    FROM {{ ref('dim_schedule_feeds') }}
),

urls_to_gtfs_datasets AS (
    SELECT * FROM {{ ref('int_transit_database__urls_to_gtfs_datasets') }}
),

make_noon_pacific AS (
    SELECT
        date_day,
        TIMESTAMP_ADD(TIMESTAMP(date_day, "America/Los_Angeles"), INTERVAL 12 HOUR) AS noon_pacific
    FROM date_spine
),

fct_daily_schedule_feeds AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['t1.date_day', 't2.key']) }} AS key,
        t1.date_day AS date,
        t2.key AS feed_key,
        t2.feed_timezone,
        t2.base64_url,
        t2._valid_from AS _feed_valid_from,
        urls_to_gtfs_datasets.gtfs_dataset_key AS gtfs_dataset_key,
        urls_to_gtfs_datasets.gtfs_dataset_name AS gtfs_dataset_name,

    FROM make_noon_pacific AS t1
    INNER JOIN dim_schedule_feeds AS t2
        ON t1.noon_pacific BETWEEN t2._valid_from AND t2._valid_to
    LEFT JOIN urls_to_gtfs_datasets
        ON t2.base64_url = urls_to_gtfs_datasets.base64_url
        -- TODO: this fails to join if there is a lag where a feed was extracted the day that its dataset record was deleted
        -- this issue is rare and basically leads to a rounding error in terms of date coverage
        -- we could either try to leverage the _config_extract_ts attribute, or artificially backdate this join (ex., subtract a millisecond after casting)
        AND CAST(date_day AS TIMESTAMP) BETWEEN urls_to_gtfs_datasets._valid_from AND urls_to_gtfs_datasets._valid_to
    WHERE t1.date_day <= CURRENT_DATE("America/Los_Angeles")
)

SELECT * FROM fct_daily_schedule_feeds

------------------------------------------------------------------
-- (2) fct_daily_feed_scheduled_service_summary
------------------------------------------------------------------
{{
    config(
        materialized='table',
        cluster_by = ['service_date']
    )
}}

WITH fct_daily_schedule_feeds AS (
    SELECT
        *,
        EXTRACT(DAYOFWEEK FROM date) AS day_num
    FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.fct_daily_schedule_feeds`--{{ ref('fct_daily_schedule_feeds') }}

),

fct_scheduled_trips AS (
    SELECT *
    FROM {{ ref('fct_scheduled_trips') }}
    WHERE service_date < CURRENT_DATE()
),

fct_scheduled_stops AS (
    SELECT
        service_date,
        feed_key,
        stop_id,
    FROM {{ ref('fct_daily_scheduled_stops') }}
    WHERE service_date < CURRENT_DATE()
),

trip_summary AS (
    SELECT
        service_date,
        feed_key,
        gtfs_dataset_key,
        SUM(service_hours) AS ttl_service_hours,
        SUM(flex_service_hours) AS ttl_flex_service_hours,
        COUNT(DISTINCT trip_id) AS n_trips,
        MIN(trip_first_departure_sec) AS first_departure_sec,
        MAX(trip_last_arrival_sec) AS last_arrival_sec,
        SUM(num_stop_times) AS num_stop_times,
        COUNT(DISTINCT route_id) AS n_routes,
        COUNT(DISTINCT shape_id) AS n_shapes,
        LOGICAL_OR(
            contains_warning_duplicate_stop_times_primary_key
        ) AS contains_warning_duplicate_stop_times_primary_key,
        LOGICAL_OR(
            contains_warning_duplicate_trip_primary_key
        ) AS contains_warning_duplicate_trip_primary_key,
        LOGICAL_OR(
            contains_warning_missing_foreign_key_stop_id
        ) AS contains_warning_missing_foreign_key_stop_id
    FROM fct_scheduled_trips
    GROUP BY service_date, feed_key, gtfs_dataset_key
),

stop_summary AS (
    SELECT
        service_date,
        feed_key,
        COUNT(DISTINCT stop_id) AS n_stops
    FROM fct_scheduled_stops
    GROUP BY service_date, feed_key
),

-- left join with feeds to include information about feeds with no service scheduled
fct_daily_feed_scheduled_service_summary AS (

    SELECT
        DATE(feeds.date) AS service_date,
        feeds.feed_key,
        feeds.gtfs_dataset_key,
        feeds.gtfs_dataset_name,
        feeds._feed_valid_from,
        COALESCE(trips.ttl_service_hours, 0) AS ttl_service_hours,
        COALESCE(trips.ttl_flex_service_hours, 0) AS ttl_flex_service_hours,
        COALESCE(trips.n_trips, 0) AS n_trips,
        trips.first_departure_sec,
        trips.last_arrival_sec,
        COALESCE(trips.num_stop_times, 0) AS num_stop_times,
        COALESCE(trips.n_routes, 0) AS n_routes,
        COALESCE(trips.n_shapes, 0) AS n_shapes,
        COALESCE(stops.n_stops, 0) AS n_stops,
        trips.contains_warning_duplicate_stop_times_primary_key,
        trips.contains_warning_duplicate_trip_primary_key,
        trips.contains_warning_missing_foreign_key_stop_id
    FROM fct_daily_schedule_feeds AS feeds
    LEFT JOIN trip_summary AS trips
        ON feeds.feed_key = trips.feed_key
        AND feeds.date = trips.service_date
    LEFT JOIN stop_summary AS stops
        ON feeds.feed_key = stops.feed_key
        AND feeds.date = stops.service_date
)

SELECT * FROM fct_daily_feed_scheduled_service_summary

------------------------------------------------------------------
-- (3) add shapes to fct_daily_schedule_rt_route_direction_summary
------------------------------------------------------------------
{{
    config(
        materialized='table',
        cluster_by=['service_date']
    )
}}

WITH schedule_trips AS (
    SELECT * FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.fct_scheduled_trips_testing`--{{ ref('fct_scheduled_trips') }}
),

observed_trips AS (
    SELECT * FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.fct_observed_trips_testing`--{{ ref('fct_observed_trips') }}
),

-- add this to make sure we correctly link quartets
dim_provider_gtfs_data AS (
    SELECT
        schedule_gtfs_dataset_key,
        vehicle_positions_gtfs_dataset_key,
        trip_updates_gtfs_dataset_key
    FROM `cal-itp-data-infra.mart_transit_database.dim_provider_gtfs_data`--{{ ref('dim_provider_gtfs_data') }}
    GROUP BY 1, 2, 3
),

gtfs_join AS (
    SELECT
        schedule.service_date,
        COALESCE(schedule.base64_url, rt.schedule_base64_url) AS schedule_base64_url,
        COALESCE(schedule.name, rt.schedule_name) AS schedule_gtfs_dataset_name,
        COALESCE(schedule.gtfs_dataset_key, rt.schedule_gtfs_dataset_key) AS schedule_gtfs_dataset_key,
        schedule.trip_instance_key,

        schedule.* EXCEPT(service_date, base64_url, name, gtfs_dataset_key, trip_instance_key),
        rt.* EXCEPT(service_date, schedule_base64_url, schedule_name, schedule_gtfs_dataset_key, trip_instance_key),
        {{ generate_time_of_day_hours('time_of_day') }} AS n_hours,

    FROM schedule_trips AS schedule
    LEFT JOIN observed_trips AS rt
        ON schedule.service_date = rt.service_date
        AND schedule.base64_url = rt.schedule_base64_url
        AND schedule.trip_instance_key = rt.trip_instance_key
),

time_of_day_counts AS (
    SELECT
        service_date,
        schedule_gtfs_dataset_key,
        time_of_day,
        route_id,
        direction_id,

        COUNT(DISTINCT trip_instance_key) AS n_trips,
        MAX(n_hours) AS n_hours,
    FROM gtfs_join
    GROUP BY 1, 2, 3, 4, 5
),

pivoted_timeofday AS (
    SELECT *
    FROM (
        SELECT
            schedule_gtfs_dataset_key,
            service_date,
            route_id,
            direction_id,

            time_of_day,
            n_trips,
            n_hours
        FROM time_of_day_counts
    )
    PIVOT(
        MIN(n_trips) AS trips,
        MIN(n_trips / n_hours) AS frequency
        FOR time_of_day IN
        ("owl", "early_am", "am_peak", "midday", "pm_peak", "evening")
    )
),

common_shape AS (
    SELECT
        service_date,
        feed_key,
        route_id,
        direction_id,
        shape_id,
        shape_array_key,
        COUNT(DISTINCT trip_instance_key) AS n_trips

    FROM gtfs_join
    GROUP BY 1, 2, 3, 4, 5, 6
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY
            service_date, feed_key, route_id, direction_id
        ORDER BY n_trips DESC) = 1
),

schedule_aggregation AS (
    SELECT
        service_date,
        schedule_base64_url,
        schedule_gtfs_dataset_name,
        schedule_gtfs_dataset_key,
        feed_key,

        route_id,
        {{ parse_route_id('schedule_gtfs_dataset_name', 'route_id') }} AS route_id_cleaned,
        {{ get_combined_route_name(
            'schedule_gtfs_dataset_name',
            'route_id', 'route_short_name', 'route_long_name'
        ) }} AS route_name,
        direction_id,
        route_type,

        COUNT(DISTINCT trip_instance_key) AS n_trips,
        COUNT(DISTINCT route_id) AS n_routes,
        COUNT(DISTINCT shape_id) AS n_shapes,
        ROUND(AVG(num_distinct_stops_served), 1) AS avg_stops_served,
        SUM(num_stop_times) AS num_stop_times,
        COALESCE(ROUND(SUM(service_hours), 2), 0) AS service_hours,
        COALESCE(ROUND(SUM(flex_service_hours), 2), 0) AS flex_service_hours,
    FROM gtfs_join
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
),

tu_aggregation AS (
    SELECT
        service_date,
        schedule_base64_url,
        tu_base64_url,
        tu_name,
        tu_gtfs_dataset_key,

        {{ get_combined_route_name(
            'schedule_gtfs_dataset_name',
            'route_id', 'route_short_name', 'route_long_name'
        ) }} AS route_name,
        route_id,
        direction_id,

        -- trip updates
        COALESCE(SUM(tu_num_distinct_extract_ts), 0) AS tu_num_distinct_updates,
        COUNT(*) AS n_tu_trips,
        COALESCE(SUM(tu_extract_duration_minutes), 0) AS tu_extract_duration_minutes,
        COALESCE(ROUND(
            SAFE_DIVIDE(SUM(tu_num_distinct_extract_ts),
            SUM(tu_extract_duration_minutes)
        ), 2), 0) AS tu_messages_per_minute,
    FROM gtfs_join
    WHERE tu_base64_url IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
),

vp_aggregation AS (
    SELECT
        service_date,
        schedule_base64_url,
        vp_base64_url,
        vp_name,
        vp_gtfs_dataset_key,

        {{ get_combined_route_name(
            'schedule_gtfs_dataset_name',
            'route_id', 'route_short_name', 'route_long_name'
        ) }} AS route_name,
        route_id,
        direction_id,

        -- vehicle positions
        COALESCE(SUM(vp_num_distinct_extract_ts), 0) AS vp_num_distinct_updates,
        COUNT(*) AS n_vp_trips,
        COALESCE(SUM(vp_extract_duration_minutes), 0) AS vp_extract_duration_minutes,
        COALESCE(ROUND(
            SAFE_DIVIDE(SUM(vp_num_distinct_extract_ts),
            SUM(vp_extract_duration_minutes)
        ), 2), 0) AS vp_messages_per_minute,
    FROM gtfs_join
    WHERE vp_base64_url IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
),

schedule_with_quartet AS (
    SELECT
        schedule_aggregation.*,
        common_shape.shape_id,
        common_shape.shape_array_key,
        dim_provider_gtfs_data.trip_updates_gtfs_dataset_key,
        dim_provider_gtfs_data.vehicle_positions_gtfs_dataset_key,
    FROM schedule_aggregation
    INNER JOIN common_shape USING (service_date, feed_key, route_id, direction_id)
    INNER JOIN dim_provider_gtfs_data USING (schedule_gtfs_dataset_key)
),

route_direction_aggregation AS (
    SELECT
        schedule.service_date,
        schedule.schedule_base64_url,
        schedule.schedule_gtfs_dataset_name AS schedule_name,
        schedule.schedule_gtfs_dataset_key,
        schedule.feed_key,

        schedule.route_id,
        schedule.route_id_cleaned,
        schedule.route_name,
        schedule.direction_id,
        schedule.route_type,
        schedule.shape_id,
        schedule.shape_array_key,

        tu.tu_gtfs_dataset_key,
        tu.tu_name,
        tu.tu_base64_url,
        vp.vp_gtfs_dataset_key,
        vp.vp_name,
        vp.vp_base64_url,

        schedule.n_trips,
        schedule.n_routes,
        schedule.n_shapes,
        schedule.avg_stops_served,
        schedule.num_stop_times,
        schedule.service_hours,
        schedule.flex_service_hours,

        -- from pivoted
        COALESCE(trips_owl, 0) AS daily_trips_owl,
		COALESCE(trips_early_am, 0) AS daily_trips_early_am,
		COALESCE(trips_am_peak, 0) AS daily_trips_am_peak,
		COALESCE(trips_midday, 0) AS daily_trips_midday,
		COALESCE(trips_pm_peak, 0) AS daily_trips_pm_peak,
		COALESCE(trips_evening, 0) AS daily_trips_evening,
		COALESCE(trips_am_peak, 0) + COALESCE(trips_pm_peak, 0) AS daily_trips_peak,
		n_trips - (COALESCE(trips_am_peak, 0) + COALESCE(trips_pm_peak, 0)) AS daily_trips_offpeak,

		COALESCE(ROUND(frequency_owl, 2), 0) AS frequency_owl,
		COALESCE(ROUND(frequency_early_am, 2), 0) AS frequency_early_am,
		COALESCE(ROUND(frequency_am_peak, 2), 0) AS frequency_am_peak,
		COALESCE(ROUND(frequency_midday, 2), 0) AS frequency_midday,
		COALESCE(ROUND(frequency_pm_peak, 2), 0) AS frequency_pm_peak,
		COALESCE(ROUND(frequency_evening, 2), 0) AS frequency_evening,

        -- calculate frequency for peak/offpeak this way by weighting the hours present in each category, add frequency for all_day
		ROUND(
			(COALESCE(frequency_am_peak, 0) * 3 + COALESCE(frequency_pm_peak, 0) * 5) / 8,
		2) AS frequency_peak,
		ROUND(
			(COALESCE(frequency_owl, 0) * 4 + COALESCE(frequency_early_am, 0) * 3
			+ COALESCE(frequency_midday, 0) * 5 + COALESCE(frequency_evening, 0) * 4) / 16,
		2) AS frequency_offpeak,
        ROUND(n_trips / 24) AS frequency_all_day,

        -- follow pattern in fct_observed_trips
        tu_base64_url IS NOT NULL AS appeared_in_tu,
        vp_base64_url IS NOT NULL AS appeared_in_vp,

        -- add this to detect rows that are nulls that are double counting schedule data
        COUNT(tu_base64_url) OVER(
            PARTITION BY schedule.service_date, schedule_gtfs_dataset_name, schedule.route_id, schedule.direction_id
        ) AS has_tu,
        COUNT(vp_base64_url) OVER(
            PARTITION BY schedule.service_date, schedule_gtfs_dataset_name, schedule.route_id, schedule.direction_id
        ) AS has_vp,

        -- vehicle positions
        vp.vp_num_distinct_updates,
        vp.n_vp_trips,
        vp.vp_extract_duration_minutes,
        vp.vp_messages_per_minute,

        -- trip updates
        tu.tu_num_distinct_updates,
        tu.n_tu_trips,
        tu.tu_extract_duration_minutes,
        tu.tu_messages_per_minute,

    FROM schedule_with_quartet AS schedule
    INNER JOIN pivoted_timeofday AS pivoted
        ON schedule.service_date = pivoted.service_date
        AND schedule.schedule_gtfs_dataset_key = pivoted.schedule_gtfs_dataset_key
        AND schedule.route_id = pivoted.route_id
        AND COALESCE(schedule.direction_id, -1) = COALESCE(pivoted.direction_id, -1)
    LEFT JOIN tu_aggregation AS tu
        ON schedule.service_date = tu.service_date
        AND schedule.schedule_base64_url = tu.schedule_base64_url
        AND schedule.trip_updates_gtfs_dataset_key = tu.tu_gtfs_dataset_key
        AND schedule.route_name = tu.route_name
        AND COALESCE(schedule.direction_id, -1) = COALESCE(tu.direction_id, -1)
    LEFT JOIN vp_aggregation AS vp
        ON schedule.service_date = vp.service_date
        AND schedule.schedule_base64_url = vp.schedule_base64_url
		AND schedule.vehicle_positions_gtfs_dataset_key = vp.vp_gtfs_dataset_key
        AND schedule.route_name = vp.route_name
        AND COALESCE(schedule.direction_id, -1) = COALESCE(vp.direction_id, -1)
    WHERE n_trips > 0
),

route_direction_aggregation2 AS (
    SELECT
        * EXCEPT(has_vp, has_tu)
    FROM route_direction_aggregation
    -- distinguish between rows that have no RT for that operator at all vs
    -- particular row didn't have RT for that route-dir combo but had RT observed that day
    -- for a day, there can be several combos from the left join:
    -- day1  schedule1  no_tu_route_dir  yes_vp_route_dir
    -- day1  schedule1  yes_tu_route_dir yes_vp_route_dir
    -- day1  schedule1  no_tu_route_dir  no_vp_route_dir (drop row)
    -- day1  schedule2  no_tu_route_dir  no_vp_route_dir (keep row)
    WHERE (appeared_in_tu AND has_tu >= 1) OR (appeared_in_vp AND has_vp >= 1)
)

SELECT * FROM route_direction_aggregation2


------------------------------------------------------------------
-- (4) TODO run in data-infra: fct_daily_schedule_rt_operator_summary 
-- add _feed_valid_from that's now in fct_daily_feed_scheduled_service_summary
------------------------------------------------------------------
{{
    config(
        materialized='table',
        cluster_by=['service_date']
    )
}}

WITH daily_schedule AS (
    SELECT *
    FROM {{ ref('fct_daily_feed_scheduled_service_summary') }}
),

daily_rt AS (
    SELECT *
    FROM {{ ref('fct_daily_rt_service_summary') }}
),

-- these will not be present for each date,
-- so use left join when bringing it in with daily schedule / daily RT
daily_tu_stop_metrics AS (
    SELECT *
    FROM {{ ref('fct_trip_updates_stop_metrics') }}
),

tu_operator_aggregation AS (
    SELECT
        service_date,
        base64_url,
        schedule_base64_url,

        ROUND(SUM(n_tu_complete_minutes) / SUM(n_tu_minutes_available), 3) AS pct_tu_complete_minutes,
        ROUND(SUM(n_tu_accurate_minutes) / SUM(n_tu_minutes_available), 3) AS pct_tu_accurate_minutes,
        ROUND(AVG(avg_prediction_spread_minutes), 2) AS avg_prediction_spread_minutes,
        SUM(n_predictions) AS n_predictions,
        ROUND(SUM(n_predictions_early) / SUM(n_predictions), 2) AS pct_predictions_early,
        ROUND(SUM(n_predictions_ontime) / SUM(n_predictions), 2) AS pct_predictions_ontime,
        ROUND(SUM(n_predictions_late) / SUM(n_predictions), 2) AS pct_predictions_late,

    FROM daily_tu_stop_metrics
    GROUP BY service_date, base64_url, schedule_base64_url
),

prediction_error_by_operator AS (
    {{ get_percentiles_by_group(
        'daily_tu_stop_metrics',
        ('service_date', 'base64_url', 'schedule_base64_url'),
        array_col='prediction_error_by_minute_array',
        decimals=1)
    }}
),

scaled_prediction_error_by_operator AS (
    {{ get_percentiles_by_group(
        'daily_tu_stop_metrics',
        ('service_date', 'base64_url', 'schedule_base64_url'),
        array_col='scaled_prediction_error_by_minute_array',
        decimals=3)
    }}
),

-- join all calculated trip update metrics
tu_operator_metrics AS (
    SELECT
        tu_operator_aggregation.*,

        pe.value_array AS prediction_error_sec_array,
        pe.value_percentile_array AS prediction_error_sec_percentile_array,

        spe.value_array AS scaled_prediction_error_sec_array,
        spe.value_percentile_array AS scaled_prediction_error_sec_percentile_array,

    FROM tu_operator_aggregation
    INNER JOIN prediction_error_by_operator AS pe
        USING (service_date, base64_url, schedule_base64_url)
    INNER JOIN scaled_prediction_error_by_operator AS spe
        USING (service_date, base64_url, schedule_base64_url)
),

daily_summary AS (
    SELECT
        COALESCE(daily_schedule.service_date, daily_rt.service_date) AS service_date,
        daily_schedule.feed_key,
        COALESCE(daily_schedule.gtfs_dataset_key, daily_rt.schedule_gtfs_dataset_key) AS schedule_gtfs_dataset_key,
        COALESCE(daily_schedule.gtfs_dataset_name, daily_rt.schedule_name) AS schedule_name,
        daily_rt.schedule_base64_url,
        daily_schedule._feed_valid_from,
    
        ROUND(daily_schedule.ttl_service_hours, 2) AS ttl_service_hours,
        ROUND(daily_schedule.ttl_flex_service_hours, 2) AS ttl_flex_service_hours,
        COALESCE(daily_schedule.n_trips, 0) AS n_trips,
        daily_schedule.first_departure_sec,
        daily_schedule.last_arrival_sec,
        daily_schedule.num_stop_times,
        daily_schedule.n_routes,
        daily_schedule.n_shapes,
        daily_schedule.n_stops,
        daily_schedule.contains_warning_duplicate_stop_times_primary_key,
        daily_schedule.contains_warning_duplicate_trip_primary_key,
        daily_schedule.contains_warning_missing_foreign_key_stop_id,

        daily_rt.vp_gtfs_dataset_key,
        daily_rt.vp_name,
        daily_rt.vp_base64_url,
        daily_rt.tu_gtfs_dataset_key,
        daily_rt.tu_name,
        daily_rt.tu_base64_url,

        -- trip updates
        COALESCE(daily_rt.n_tu_trips, 0) AS n_tu_trips,
        ROUND(SAFE_DIVIDE(daily_rt.n_tu_trips, daily_schedule.n_trips), 3) AS pct_tu_trips,
        daily_rt.n_tu_routes,
        ROUND(SAFE_DIVIDE(daily_rt.n_tu_routes, daily_schedule.n_routes), 3) AS pct_tu_routes,
        daily_rt.tu_extract_duration_minutes,
        daily_rt.tu_messages_per_minute,

        tu_operator_metrics.pct_tu_complete_minutes,
        tu_operator_metrics.pct_tu_accurate_minutes,
        tu_operator_metrics.avg_prediction_spread_minutes,
        tu_operator_metrics.n_predictions,
        tu_operator_metrics.pct_predictions_early,
        tu_operator_metrics.pct_predictions_ontime,
        tu_operator_metrics.pct_predictions_late,
        tu_operator_metrics.prediction_error_sec_array,
        tu_operator_metrics.prediction_error_sec_percentile_array,
        tu_operator_metrics.scaled_prediction_error_sec_array,
        tu_operator_metrics.scaled_prediction_error_sec_percentile_array,

        -- vehicle positions
        daily_rt.vp_num_distinct_updates,
        COALESCE(daily_rt.n_vp_trips, 0) AS n_vp_trips,
        ROUND(SAFE_DIVIDE(daily_rt.n_vp_trips, daily_schedule.n_trips), 3) AS pct_vp_trips,
        daily_rt.n_vp_routes,
        ROUND(SAFE_DIVIDE(daily_rt.n_vp_routes, daily_schedule.n_routes), 3) AS pct_vp_routes,
        daily_rt.vp_extract_duration_minutes,
        daily_rt.vp_messages_per_minute,

        -- figure out which ones are missing
        IF(gtfs_dataset_name IS NULL AND daily_schedule.feed_key IS NULL AND schedule_name IS NOT NULL, 1, 0) AS in_obs_only,

    FROM daily_schedule
    FULL OUTER JOIN daily_rt -- full outer join to see which ones don't match up
        ON daily_schedule.service_date = daily_rt.service_date
        AND daily_schedule.gtfs_dataset_name = daily_rt.schedule_name
        AND daily_schedule.gtfs_dataset_key = daily_rt.schedule_gtfs_dataset_key
    LEFT JOIN tu_operator_metrics
        ON daily_rt.service_date = tu_operator_metrics.service_date
        AND daily_rt.tu_base64_url = tu_operator_metrics.base64_url
        AND daily_rt.schedule_base64_url = tu_operator_metrics.schedule_base64_url
),

daily_summary2 AS (
    SELECT
        *,

        -- saw that some operators had only vp but not tu, so let's differentiate
        CASE
            WHEN n_trips > 0 AND n_tu_trips = 0 AND n_vp_trips = 0 THEN "schedule_only"
            WHEN n_trips > 0 AND n_tu_trips > 0 AND n_vp_trips > 0 THEN "schedule_and_rt"
            WHEN n_trips > 0 AND n_tu_trips > 0 AND n_vp_trips = 0 THEN "schedule_and_tu_only"
            WHEN n_trips > 0 AND n_tu_trips = 0 AND n_vp_trips > 0 THEN "schedule_and_vp_only"
            WHEN n_trips = 0 THEN "no_active_service"
            -- there are rows with active service but quartet hasn't been implemented yet, these cover 2022-10-01 values and before
            WHEN gtfs_dataset_name IS NULL AND feed_key IS NOT NULL THEN "v1_warehouse"
            ELSE "unknown"
        END AS gtfs_availability,
    FROM daily_summary
)

SELECT * FROM daily_summary2