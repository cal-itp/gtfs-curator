import pandas as pd

event_name = "world_cup"

GCS_FILE_PATH = (
    f"gs://calitp-analytics-data/data-analyses/transit_event_analysis/{event_name}/"
)

# 2026-06-12 starts -5 ; 2026-07-10 ends + 5
event_start_end = ("2026-06-07", "2026-07-15")

event_date_range = pd.date_range(
    start=event_start_end[0],
    end=event_start_end[1],
)

# add this to get date filtering to work, unsure how to use STRUCT in parameter
# bigquery.ArrayParameter has error if not values and array_type in {"RECORD", "STRUCT"}:
event_date_range = [pd.to_datetime(c) for c in event_date_range]

sofi_dates = [
    "2026-06-12",
    "2026-06-15",
    "2026-06-18",
    "2026-06-21",
    "2026-06-25",
    "2026-06-28",
    "2026-07-02",
    "2026-07-10",
]

sofi_match_times = {
    **{
        d: "midday"
        for d in ["2026-06-18", "2026-06-21", "2026-06-28", "2026-07-02", "2026-07-10"]
    },
    **{d: "pm_peak" for d in ["2026-06-12", "2026-06-15", "2026-06-25"]},
    # night matches are a bit tricky, can span pm_peak to evening, but use the start time to determine
}

socal_names = [
    "LA Metro Events Schedule",
    "LA Metro Bus Schedule",
    "LA Metro Rail Schedule",
    "LA DOT Schedule",
    "G Trans Schedule",
    "Torrance Schedule",
    "Inglewood Schedule",
    "Beach Cities GMV Schedule",
    "Big Blue Bus Schedule",
    "Big Blue Bus Swiftly Schedule",
    "Culver City Schedule",
    "Metrolink Schedule",
]

levi_dates = [
    "2026-06-13",
    "2026-06-16",
    "2026-06-19",
    "2026-06-22",
    "2026-06-25",
    "2026-07-01",
]

levi_match_times = {
    **{d: "midday" for d in ["2026-06-13"]},
    **{d: "pm_peak" for d in ["2026-06-25", "2026-07-01"]},
    **{d: "evening" for d in ["2026-06-16", "2026-06-19", "2026-06-22"]},
}

bay_area_names = [
    "SCVTA Schedule",
    "Bay Area 511 Santa Clara Transit Schedule",
    "BART Schedule",
    "Bay Area 511 BART Schedule",
    "Caltrain Schedule",
    "Bay Area 511 Caltrain Schedule",
    "San Joaquin Schedule",  # is this needed?
    "ACE Schedule",
    "Bay Area 511 ACE Schedule",
    "Capitol Corridor Schedule",
    "Bay Area 511 Capitol Corridor Schedule",
    "Amtrak Schedule",
]

"""
# special LA Metro WC feed
# gtfs_dataset_name: LA Metro Events Schedule
# _valid_from 2026-07-07 UTC

tiffany_mart_gtfs.event_fct_daily_feeds_la_metro

SELECT
  *
FROM `cal-itp-data-infra.mart_gtfs.fct_daily_schedule_feeds` AS t1
WHERE t1.date >= "2026-07-05" AND t1.date <= "2026-07-20" AND t1.gtfs_dataset_name = "LA Metro Events Schedule"
"""
