import geopandas as gpd
import gcsfs
import google.auth
import pandas as pd
from gtfs_curator_utils import geography_utils, utils
from update_vars import DIGEST_DICT, RAW_GCS, PROCESSED_GCS, abbrev_month

# Initialize credentials
credentials, _ = google.auth.default()

def prep_schedule_rt_route_direction_summary(abbrev_month: str) -> pd.DataFrame:
    filename = DIGEST_DICT.schedule_rt_route_direction
    df = pd.read_parquet(
        f"{RAW_GCS}{filename}_{abbrev_month}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    # Select relevant columns
    df2 = (
        df[
            [
                "month_first_day",
                "analysis_name",
                "route_name",
                "direction_id",
                "frequency_all_day",
                "frequency_offpeak",
                "frequency_peak",
                "daily_trips_peak",
                "daily_trips_offpeak",
                "daily_trips_all_day",
                "day_type",
                "route_type",
                "daily_service_hours",
                "route_typology",
            ]
        ]
        .drop_duplicates()
        .reset_index()
    )

    # Clean columns
    df2.route_typology = df2.route_typology.str.title()
    df2.columns = df2.columns.str.replace("_", " ").str.title()
    df2["Month First Day"] = pd.to_datetime(df2["Month First Day"]).dt.strftime("%m/%Y")
    df2 = df2.rename(
        columns={
            "Direction Id": "Direction",
            "Month First Day": "Date",
            "Route Name": "Route",
        }
    )

    # Add calculated columns
    df2["Daily Service Minutes"] = df2["Daily Service Hours"] * 60
    df2["Average Scheduled Minutes"] = (
        df2["Daily Service Minutes"] / df2["Daily Trips All Day"]
    )
    df2["Headway All Day"] = 60 / df2["Frequency All Day"]
    df2["Headway Peak"] = 60 / df2["Frequency Peak"]
    df2["Headway Offpeak"] = 60 / df2["Frequency Offpeak"]

    # Save processed file
    df2.to_parquet(
        f"{PROCESSED_GCS}{filename}_{abbrev_month}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print("export processed {filename}")
    return 


def prep_operator_summary(abbrev_month: str) -> pd.DataFrame:
    filename = DIGEST_DICT.operator_summary

    df = pd.read_parquet(
        f"{RAW_GCS}{filename}_{abbrev_month}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    # Select relevant columns
    df2 = df[
        [
            "month_first_day",
            "analysis_name",
            "caltrans_district",
            "vp_name",
            "tu_name",
            "n_trips",
            "day_type",
            "daily_trips",
            "ttl_service_hours",  # "daily_service_hours",
            "n_routes",
            "n_days",
            "n_shapes",
            "n_stops",
            "daily_arrivals",
            "vp_messages_per_minute",
            "n_vp_trips",
            "daily_vp_trips",
            "pct_vp_trips",
            "tu_messages_per_minute",
            "n_tu_trips",
            "daily_tu_trips",
            "pct_tu_trips",
        ]
    ]

    # Multiply percetnage columns by 100. Clip any values above 100.
    df2.pct_tu_trips = df2.pct_tu_trips * 100
    df2.pct_vp_trips = df2.pct_vp_trips * 100
    df2.pct_tu_trips = df2.pct_tu_trips.clip(upper=100.0)
    df2.pct_vp_trips = df2.pct_vp_trips.clip(upper=100.0)

    # Clean columns
    df2.columns = df2.columns.str.replace("_", " ").str.title()
    df2 = df2.rename(columns={"Month First Day": "Date"})
    df2.columns = df2.columns.str.replace("Vp", "VP").str.replace("Tu", "TU")

    # Save processed file
    df2.to_parquet(
        f"{PROCESSED_GCS}{filename}_{abbrev_month}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    print("export processed {filename}")

    return 


def prep_fct_monthly_routes(abbrev_month: str) -> pd.DataFrame:
    filename = DIGEST_DICT.route_map

    gdf = gpd.read_parquet(
        f"{RAW_GCS}{filename}_{abbrev_month}.parquet",
        storage_options={"token": credentials.token},
    )

    # Keep most recent route geography
    gdf2 = gdf.sort_values(
        by=["month_first_day", "analysis_name", "route_name"],
        ascending=[False, True, True],
    ).drop_duplicates(subset=["analysis_name", "route_name"])

    # Drop unnecessary columns
    gdf2 = gdf2.drop(columns=["shape_id", "shape_array_key", "n_trips", "direction_id"])

    # Convert to miles
    gdf2["route_length_miles"] = (
        gdf2.geometry.to_crs(geography_utils.CA_NAD83Albers_ft).length / 5_280
    )

    # Clean column names
    gdf2.columns = gdf2.columns.str.replace("_", " ").str.title()

    # Export to GCS
    utils.geoparquet_gcs_export(
        gdf2,
        PROCESSED_GCS,
        {filename}_{abbrev_month},
    )

    print("export processed {filename}")

    return 


def prep_fct_operator_hourly_summary(abbrev_month: str) -> pd.DataFrame:
    filename = DIGEST_DICT.hourly_day_type_summary
    
    df = pd.read_parquet(
        f"{RAW_GCS}{filename}_{abbrev_month}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )

    # Prepare data
    df2 = (
        df.groupby(["analysis_name", "month_first_day", "day_type", "departure_hour"])
        .agg({"n_trips": "sum"})
        .reset_index()
    )

    df2.columns = df2.columns.str.replace("_", " ").str.title()

    df2 = df2.rename(columns={"Month First Day": "Date"})

    df2["Date"] = df2["Date"].dt.strftime("%m-%Y")

    df2.to_parquet(
        f"{PROCESSED_GCS}{filename}_{abbrev_month}.parquet",
        filesystem = gcsfs.GCSFileSystem()
    )    
    
    print("export processed {filename}")

    return 


if __name__ == "__main__":
    
    prep_schedule_rt_route_direction_summary(abbrev_month)
    prep_operator_summary(abbrev_month)
    prep_fct_monthly_routes(abbrev_month)
    prep_fct_operator_hourly_summary(abbrev_month)
    print("done running")
