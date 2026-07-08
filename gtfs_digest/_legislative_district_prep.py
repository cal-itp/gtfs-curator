"""
Crosswalk of transit operators to legislative districts.

Spatial join fct_monthly_routes to legislative district
boundaries. Any intersection means that operator's data
will be included for that legislative district.
"""

import geopandas as gpd
import google.auth
import pandas as pd
from gtfs_curator_utils import utils
from update_vars import DIGEST_DICT, PROCESSED_GCS, RAW_GCS, SHARED_GCS, abbrev_month

credentials, _ = google.auth.default()


def sjoin_shapes_legislative_districts(file_name: str) -> pd.DataFrame:
    """
    Grab shapes (fct_monthly_routes) and do a spatial join
    with legislative district.
    Keep 1 row for every operator-legislative_district combination.
    """
    monthly_routes = gpd.read_parquet(
        f"{RAW_GCS}{DIGEST_DICT.route_map}_{file_name}.parquet",
        storage_options={"token": credentials.token},
        columns=["analysis_name", "geometry"],
    )

    legislative_districts = gpd.read_parquet(
        f"{SHARED_GCS}legislative_districts.parquet",
        storage_options={"token": credentials.token},
    )

    crosswalk = (
        gpd.sjoin(monthly_routes, legislative_districts, how="inner", predicate="intersects")[
            ["analysis_name", "legislative_district"]
        ]
        .drop_duplicates()
        .sort_values(["analysis_name", "legislative_district"])
        .reset_index(drop=True)
    )

    utils.geoparquet_gcs_export(crosswalk, PROCESSED_GCS, f"{DIGEST_DICT.crosswalk_legislative}_{file_name}")

    print("exported legislative districts to operators crosswalk")

    return


if __name__ == "__main__":

    sjoin_shapes_legislative_districts(abbrev_month)
