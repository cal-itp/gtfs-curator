-- use fct_vehicle_locations and aggregate to trip or trip-stop

----------------------------------------------------------
-- (1) metrics that pertain to stop
----------------------------------------------------------
WITH vehicle_locations AS (
    SELECT
		service_date,
		base64_url,
		gtfs_dataset_name,
		schedule_feed_key,
		schedule_base64_url,
		schedule_name,
		trip_instance_key,
		stop_id,
		current_stop_sequence,
		current_status,

		key,
		_header_message_age,
		_vehicle_message_age,
		position_bearing,
		position_odometer,
		position_speed,

		congestion_level,
		occupancy_status,
		occupancy_percentage,

    FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.fct_vehicle_locations`
    WHERE dt IN ('2026-01-01', '2026-01-02')
),

stop_metrics AS (
	SELECT
	    service_date,
	    base64_url,
		gtfs_dataset_name,
		schedule_feed_key,
		schedule_base64_url,
		schedule_name,
	    trip_instance_key,
	    stop_id,
		current_stop_sequence,
		current_status,

		AVG(_header_message_age) AS avg_header_message_age, -- farhad does more percentiles, but get this column
		AVG(_vehicle_message_age) AS avg_vehicle_message_age,

		MIN(position_speed) AS min_speed,
		MAX(position_speed) AS max_speed,
		AVG(position_speed) AS avg_speed,
		MAX(position_odometer) AS max_odometer,
		MIN(position_odometer) AS min_odometer,
		ARRAY_AGG(DISTINCT position_bearing IGNORE NULLS) AS position_bearing_array,
		ARRAY_AGG(DISTINCT congestion_level IGNORE NULLS),
		COUNT(congestion_level) AS count_congestion_level,
		COUNT(occupancy_status) AS count_occupancy_status,
		ARRAY_AGG(occupancy_percentage IGNORE NULLS) AS occupancy_percentage_array,
		COUNT(key) AS n_vp,

	FROM vehicle_locations
	GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
)

SELECT * FROM stop_metrics


----------------------------------------------------------
-- (2) metrics that pertain to fct_vp_trip_summaries
-- other columns we haven't used yet
----------------------------------------------------------
WITH trip_metrics AS (
    SELECT
        service_date,
        base64_url,
        schedule_base64_url,
		trip_id,
		iteration_num,
        trip_instance_key,

		trip_route_ids,
		trip_direction_ids,
		trip_schedule_relationships,

		-- does this show 1?
		num_distinct_header_timestamps,
    	-- these 2 are used in fct_daily_schedule_rt_route_direction_summary for messages per minute
		num_distinct_extract_ts,
    	extract_duration_minutes,
    FROM `cal-itp-data-infra-staging.tiffany_mart_gtfs.fct_vehicle_positions_trip_summaries`
    WHERE service_date = '2026-01-01'
)

SELECT * FROM trip_metrics
