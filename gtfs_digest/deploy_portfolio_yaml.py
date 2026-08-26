"""
Create the GTFS Digest yaml that
sets the parameterization for the analysis site.
"""
from pathlib import Path

import gcsfs
import pandas as pd
from calitp_portfolio.models import load_site
from calitp_portfolio.mutations import generate_parts_grouped

from update_vars import DIGEST_DICT, PROCESSED_GCS, abbrev_month

def generate_operator_report_yaml(
    site_path: Path,
    abbrev_month: str
) -> pd.DataFrame:
    """
    Generate the yaml for our Operator grain portfolio.
    """
    table = DIGEST_DICT.schedule_rt_route_direction
    site = load_site(site_path)

    # Keep only organizations with RT and schedule OR only schedule.
    df = (
        pd.read_parquet(
            f"{PROCESSED_GCS}{table}_{abbrev_month}.parquet", 
            columns=["caltrans_district", "analysis_name"],
            filesystem = gcsfs.GCSFileSystem()
        ).drop_duplicates()
        .dropna(subset=["caltrans_district"])
        .reset_index(drop=True)
    )

    # To get this to the format groups = {"D1": [1, 2, 3], "D2": [4, 5, 6]}
    operators_grouped_by_district = {
        one_district: sorted(df[df.caltrans_district==d].analysis_name.unique())
        for one_district in sorted(df.caltrans_district.unique())
    }
    
    site = generate_parts_grouped(
        site,
        param_key="analysis_name",
        groups= operators_grouped_by_district
    })

    site.write_yaml(site_path)

    print(f"yaml generated at {site_path}")

    return 

if __name__ == "__main__":

    SITE_YAML = Path("./gtfs_digest.yml")
    generate_operator_grain_yaml(SITE_YAML, abbrev_month)
    
