"""
Crosswalk
"""

import gcsfs
import pandas as pd
from gtfs_curator_utils import bq_utils
from update_vars import DIGEST_DICT, PROCESSED_GCS, abbrev_month


def load_crosswalk(
    project_name: str,
    dataset_name: str,
    table_name: str = "bridge_gtfs_analysis_name_x_ntd",
) -> pd.DataFrame:
    crosswalk_cols = [
        "schedule_gtfs_dataset_name",
        "analysis_name",
        "county_name",
        "caltrans_district",
        "caltrans_district_full",
        "ntd_id",
        "ntd_id_2022",
    ]

    df = bq_utils.download_table(
        project_name=project_name,
        dataset_name=dataset_name,
        table_name=table_name,
        date_col=None,
        columns=crosswalk_cols,
    )

    df2 = (
        df.dropna(subset=["ntd_id", "ntd_id_2022"])
        .drop_duplicates(
            subset=["analysis_name", "organization_name", "schedule_gtfs_dataset_name"]
        )
        .rename(
            columns={
                "schedule_gtfs_dataset_name": "name",
                "caltrans_district": "caltrans_district_int",
                "caltrans_district_full": "caltrans_district",
            }
        )
        .reset_index(drop=True)
    )

    # there's a leading space. TODO: remove in warehouse
    df2 = df2.assign(caltrans_district=df2.caltrans_district.str.strip())

    df2.to_parquet(
        f"{PROCESSED_GCS}{DIGEST_DICT.crosswalk}_{abbrev_month}.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    return


if __name__ == "__main__":
    PROD_PROJECT = "cal-itp-data-infra"
    PROD_MART = "mart_transit_database"

    load_crosswalk(
        project_name=PROD_PROJECT,
        dataset_name=PROD_MART,
    )
