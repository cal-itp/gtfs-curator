""" """

import geopandas as gpd
import google.auth
import pandas as pd
from update_vars import DIGEST_DICT, RAW_GCS, abbrev_month

credentials, _ = google.auth.default()
SHARED_GCS = "gs://calitp-analytics-data/data-analyses/shared_data/"


def sjoin_shapes_legislative_districts(shapes_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Grab shapes (fct_monthly_routes) and do a spatial join
    with legislative district.
    Keep 1 row for every operator-legislative_district combination.
    """
    legislative_districts = gpd.read_parquet(
        f"{SHARED_GCS}legislative_districts.parquet", storage_options={"token": credentials.token}
    )

    crosswalk = (
        gpd.sjoin(shapes_gdf, legislative_districts, how="inner", predicate="intersects")[
            ["schedule_name", "analysis_name", "legislative_district"]
        ]
        .drop_duplicates()
        .sort_values(["schedule_name", "legislative_district"])
        .reset_index(drop=True)
    )

    return crosswalk


if __name__ == "__main__":

    # how should args be set up so that when this month is run, the crosswalk is made,
    # and portfolio yaml can be generated off of it?
    filename = f"{RAW_GCS}{DIGEST_DICT.route_map}_{abbrev_month}.parquet"

    gdf = gpd.read_parquet(
        filename, storage_options={"token": credentials.token}, columns=["schedule_name", "analysis_name", "geometry"]
    )

    crosswalk = sjoin_shapes_legislative_districts(gdf)
