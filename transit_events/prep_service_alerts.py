"""
Service alerts.

1. downloaded all the service alerts for the event date range
   - fct_daily_service_alerts_trip_summaries (use message column?)
      - is trip_id useful to map onto routes?
   - fct_daily_service_alerts (use this one?)
2. need to subset to the sa_base64_urls we want for event
   - this is not entirely known until we can map based on schedule_name
   - attach sa_name too, so that we can better make sense of service_alerts
3. data processing
   - categorize service_alerts into broad categories to see what types of alerts show up
   - figure out if trip_ids can help us narrow down to routes of interest, or whether we'll miss alerts we want
"""

import gcsfs
import pandas as pd
import world_cup_vars as wc_vars

GCS_FILE_PATH = wc_vars.GCS_FILE_PATH
DIAG_GCS = "gs://calitp-analytics-data/data-analyses/gtfs_diagnostics/"


def import_and_filter(
    service_alerts_filename: str, event_date_range: list, list_of_operators: list
) -> pd.DataFrame:
    """
    Use the diagnostics quartet_by_feed df here.
    Filter to the operators we want for World Cup,
    filter to service_dates that are in the event date range,
    attach sa_name to it too.
    """

    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{service_alerts_filename}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    ).rename(columns={"base64_url": "sa_base64_url"})

    if "service_date" in df.columns:
        df = df.assign(
            service_date=pd.to_datetime(df.service_date),
        )
    # fct_daily_service_alerts uses active_date
    elif "active_date" in df.columns:
        df = df.assign(service_date=pd.to_datetime(df.active_date))

    df_keys = (
        pd.read_parquet(
            f"{DIAG_GCS}quartet_by_feed_key_categorized.parquet",
            filesystem=gcsfs.GCSFileSystem(),
            columns=["schedule_name", "sa_name", "sa_base64_url", "service_date_range"],
            filters=[
                [
                    ("schedule_name", "in", list_of_operators),
                ]
            ],
        )
        .dropna(subset="sa_base64_url")
        .explode("service_date_range")
        .rename(columns={"service_date_range": "service_date"})
        .astype({"service_date": "datetime64[ns]"})
    )

    df_keys2 = df_keys[df_keys.service_date.isin(event_date_range)][
        ["service_date", "schedule_name", "sa_name", "sa_base64_url"]
    ].drop_duplicates()

    df2 = pd.merge(df, df_keys2, on=["service_date", "sa_base64_url"], how="inner")

    return df2


def tag_based_on_keywords(text_col: str, list_of_words: list):
    """
    For service_alerts, might look at header column or message column.
    Look to see if any of the keywords exist, flag dummy variable as True if
    the word shows up.
    Use this to help sort all the different types of service_alerts there are.
    """
    if any(word in text_col.lower() for word in list_of_words):
        return True
    else:
        return False


def tag_service_alerts_header(df: pd.DataFrame):
    WORLD_CUP_WORDS = ["world cup", "wc", "fifa", "additional service", "special event"]
    DELAY_WORDS = [
        "delay",
        "suspended",
        "temporarily",
        "temporary",
        "stopped",
    ]
    CANCEL_WORDS = [
        "close",
        "closed",
        "closure",
        "cancel",
        "no service",
        "miss",
        "missed stop",
        "missed trip",
    ]
    SAFETY_WORDS = ["safety", "mechanical issue", "police", "police activity"]
    SERVICE_RELOCATE_WORDS = [
        "construction",
        "reroute",
        "detour",
        "plan ahead",
        "missed stops",
        "moved",
        "bay change",
        "platform change",
        "relocation",
        "stop relocation",
        "stop moved",
    ]

    ELEVATOR_WORDS = ["accessibility", "elevator", "out of service", "escalator"]

    TEST_IGNORE_WORDS = ["test", "test alert", "disregard"]

    df = df.assign(header_desc=df.header.str.cat(df.description, sep=" ", na_rep=""))

    df = df.assign(
        flag_wc=df.apply(
            lambda x: tag_based_on_keywords(x.header_desc, WORLD_CUP_WORDS), axis=1
        ),
        flag_delay=df.apply(
            lambda x: tag_based_on_keywords(x.header_desc, DELAY_WORDS), axis=1
        ),
        flag_cancel=df.apply(
            lambda x: tag_based_on_keywords(x.header_desc, CANCEL_WORDS), axis=1
        ),
        flag_safety=df.apply(
            lambda x: tag_based_on_keywords(x.header_desc, SAFETY_WORDS), axis=1
        ),
        flag_service_change=df.apply(
            lambda x: tag_based_on_keywords(x.header_desc, SERVICE_RELOCATE_WORDS),
            axis=1,
        ),
        flag_elevator=df.apply(
            lambda x: tag_based_on_keywords(x.header_desc, ELEVATOR_WORDS), axis=1
        ),
        flag_test=df.apply(
            lambda x: tag_based_on_keywords(x.header_desc, TEST_IGNORE_WORDS), axis=1
        ),
    )

    flag_cols = [c for c in df.columns if "flag_" in c]
    df["n_flags"] = df[flag_cols].sum(axis=1)

    return df


if __name__ == "__main__":
    """
    service_alerts_trip_summaries = import_and_filter(
        f"fct_daily_service_alerts_trip_summaries_{wc_vars.event_name}",
        wc_vars.event_date_range,
        wc_vars.socal_names + wc_vars.bay_area_names,
    )
    service_alerts_trip_summaries.to_parquet(
        f"{GCS_FILE_PATH}fct_daily_service_alerts_trip_summaries_filtered.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )
    print("exported fct_daily_service_alerts_trip_summaries")
    """
    daily_service_alerts = import_and_filter(
        f"fct_daily_service_alerts_{wc_vars.event_name}",
        wc_vars.event_date_range,
        wc_vars.socal_names + wc_vars.bay_area_names,
    ).pipe(tag_service_alerts_header)

    daily_service_alerts.to_parquet(
        f"{GCS_FILE_PATH}fct_daily_service_alerts_filtered.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    print("exported fct_daily_service_alerts")
