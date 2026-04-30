"""
Download tables for creating Marin's RT operator report.
"""

import gcsfs
import google.auth
from gtfs_curator_shared_utils import bq_utils

credentials, project = google.auth.default()

PREDICTIONS_GCS = "gs://calitp-analytics-data/data-analyses/rt_predictions/"

if __name__ == "__main__":

    monthly_operator_summary = bq_utils.download_table(
        project_name="cal-itp-data-infra-staging",
        dataset_name="tiffany_mart_gtfs",  # these are not in tiffany_mart_gtfs_rollup
        table_name="fct_monthly_operator_summary_marin",
        date_col="month_first_day",
        start_date="2026-02-01",
        end_date="2026-02-01",
    )

    monthly_operator_summary.to_parquet(
        f"{PREDICTIONS_GCS}monthly_operator_summary_marin.parquet", filesystem=gcsfs.GCSFileSystem()
    )
