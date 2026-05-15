from . import (  # magics,
    _color_palette,
    bq_utils,
    catalog_utils,
    geography_utils,
    portfolio_utils,
    publish_utils,
    sql,
    utils,
)

__all__ = [
    "bq_utils",
    "catalog_utils",
    "geography_utils",
    "magics",
    "portfolio_utils",
    "publish_utils",
    "sql",
    "utils",
    "_color_palette",
]

import sys

if "ipykernel" in sys.modules:
    from . import magics
