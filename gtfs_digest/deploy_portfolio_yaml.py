"""
Write out how site.yaml would be generated for 3 GTFS Digests.
"""

from pathlib import Path

import gcsfs
import pandas as pd
from calitp_portfolio.models import load_site
from calitp_portfolio.mutations import generate_parts_flat
from update_vars import DIGEST_DICT, PROCESSED_GCS, abbrev_month


def legislative_district_yaml(site_path: Path = Path("./digestif.yml")):
    """
    There are 120 districts, 80 assembly districts, 40 senate districts
    118 show up here in this publication month (Apr 2026).
    Is it consistently these 118? Will this fluctuate?
    """
    site = load_site(site_path)
    # site = load_site(Path("../gtfs_digest/digestif.yml"))

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

    legislative_district_yaml(Path("./digestif.yml"))
