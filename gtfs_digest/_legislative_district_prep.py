"""
Crosswalk of transit operators to legislative districts.

Spatial join fct_monthly_routes to legislative district
boundaries. Any intersection means that operator's data
will be included for that legislative district.
"""

from pathlib import Path

import gcsfs
import geopandas as gpd
import google.auth
import pandas as pd
from calitp_portfolio.models import load_site
from calitp_portfolio.mutations import generate_parts_flat
from gtfs_curator_utils import utils
from update_vars import DIGEST_DICT, PROCESSED_GCS, RAW_GCS, SHARED_GCS, abbrev_month

credentials, _ = google.auth.default()


def sjoin_shapes_legislative_districts(abbrev_month: str) -> pd.DataFrame:
    """
    Grab shapes (fct_monthly_routes) and do a spatial join
    with legislative district.
    Keep 1 row for every operator-legislative_district combination.
    """
    monthly_routes = gpd.read_parquet(
        f"{RAW_GCS}{DIGEST_DICT.route_map}_{abbrev_month}.parquet",
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

    utils.geoparquet_gcs_export(crosswalk, PROCESSED_GCS, f"{DIGEST_DICT.crosswalk_legislative}_{abbrev_month}")

    print(f"{abbrev_month}: exported legislative districts to operators crosswalk")

    return


def legislative_district_yaml(site_path: Path):
    """
    There are 120 districts, 80 assembly districts, 40 senate districts
    118 show up here in this publication month (Apr 2026).
    Is it consistently these 118? Will this fluctuate?
    """
    site = load_site(site_path)

    crosswalk_url = f"{PROCESSED_GCS}{DIGEST_DICT.crosswalk_legislative}_{abbrev_month}.parquet"

    legislative_districts_list = (
        pd.read_parquet(crosswalk_url, columns=["legislative_district"], filesystem=gcsfs.GCSFileSystem())
        .legislative_district.unique()
        .tolist()
    )

    site = generate_parts_flat(
        site,
        param_key="district",
        values=sorted(legislative_districts_list),
    )

    site.write_yaml(site_path)

    print(f"yaml generated at {site_path}")

    return


if __name__ == "__main__":

    sjoin_shapes_legislative_districts(abbrev_month)

    # write out the portfolio yaml - TOC does not need all 120 districts necessarily
    legislative_district_yaml(Path("./legislative_district_digest.yml"))
