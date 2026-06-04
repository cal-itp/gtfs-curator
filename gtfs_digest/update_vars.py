from gtfs_curator_utils import catalog_utils

CATALOG_DICT = catalog_utils.get_catalog("catalog.yml", use_intake=False)
DIGEST_DICT = CATALOG_DICT.gtfs_digest_rollup

analysis_month = "2026-01-01"
last_year = "2025-01-01"
previous_month = "2025-12-01"

abbrev_month = analysis_month.replace("-", "_")[0:7]

DIGEST_GCS = DIGEST_DICT.dir
RAW_GCS = f"{DIGEST_GCS}raw/"
PROCESSED_GCS = f"{DIGEST_GCS}processed/"
