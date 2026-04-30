{{
    config(
        materialized='table',
        cluster_by=['service_date']
    )
}}

SELECT *
FROM `cal-itp-data-infra.mart_gtfs.fct_daily_schedule_rt_route_direction_summary`
WHERE service_date >= "2026-02-01" AND service_date < "2026-03-01" AND
    schedule_gtfs_dataset_key IN ('70278036918ea1640d84a4f7c1d6af66','0089bd1b0a2b78a8590d8749737d7146', '9b4a37e507b9d86a115dbcc6bb764a65')
