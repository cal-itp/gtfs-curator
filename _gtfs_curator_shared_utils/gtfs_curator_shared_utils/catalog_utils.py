"""
Functions for opening yaml catalogs in shared_utils.
"""

from pathlib import Path

import intake
from omegaconf import OmegaConf  # this is yaml parser


def get_catalog(catalog_path: str, use_intake: bool = True) -> Path:
    """ """
    if use_intake:
        return intake.open_catalog(catalog_path)
    else:
        return OmegaConf.load(catalog_path)
