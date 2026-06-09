"""
Download vp tables aggregated to stop / trip for 1 service_date.
"""

import gcsfs
from gtfs_curator_utils import bq_utils

VP_GCS = "gs://calitp-analytics-data/data-analyses/rt_vehicle_positions/"

if __name__ == "__main__":

    analysis_date = "2026-01-01"

    for t in ["stop", "trip"]:
        df = bq_utils.download_table(
            project_name="cal-itp-data-infra-staging",
            dataset_name="tiffany_mart_gtfs",
            table_name=f"vp_additional_{t}_info",
            date_col="service_date",
            start_date=analysis_date,
            end_date=analysis_date,
        )

        df.to_parquet(f"{VP_GCS}vp_{t}_metrics.parquet", filesystem=gcsfs.GCSFileSystem())

        del df
