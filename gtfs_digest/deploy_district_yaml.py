"""
Create the yaml for district GTFS Digest.
"""

from pathlib import Path

from calitp_portfolio.models import load_site
from calitp_portfolio.mutations import generate_parts_flat

if __name__ == "__main__":
    SITE_YAML = Path("./district_digest.yml")

    site = load_site(SITE_YAML)
    site = generate_parts_flat(
        site,
        param_key="district",
        values=[
            "01 - Eureka",
            "02 - Redding",
            "03 - Marysville / Sacramento",
            "04 - Bay Area / Oakland",
            "05 - San Luis Obispo / Santa Barbara",
            "06 - Fresno / Bakersfield",
            "07 - Los Angeles / Ventura",
            "08 - San Bernardino / Riverside",
            "09 - Bishop",
            "10 - Stockton",
            "11 - San Diego",
            "12 - Orange County",
        ],
    )

    site.write_yaml(SITE_YAML)
