from pathlib import Path

from omegaconf import OmegaConf

PREDICTIONS_GCS = "gs://calitp-analytics-data/data-analyses/rt_predictions/"
VP_GCS = "gs://calitp-analytics-data/data-analyses/rt_vehicle_positions/"


def get_catalog(catalog_name="catalog") -> Path:
    """
    Grab GTFS RT MSA catalog (uses OmegaConf yaml parser).
    """
    catalog_path = Path.cwd().joinpath(f"{catalog_name}.yml")

    return OmegaConf.load(catalog_path)


RT_MSA_DICT = get_catalog("catalog")
stop_report_month = "2026-01-01"
operator_report_month = "2026-01-01"

"""
execute:
  echo: false
jupyter:
  jupytext:
    text_representation:
      extension: .qmd
      format_name: quarto
      format_version: '1.0'
      jupytext_version: 1.19.1
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
"""
