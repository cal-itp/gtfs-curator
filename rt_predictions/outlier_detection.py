"""
Data prep related to removing outliers.
Thresholds here are based on exploratory work
from 2 week June 2025 period to find 1% tails.
"""

import pandas as pd

MIN_ERROR_SEC_5MIN = -60 * 5
MAX_ERROR_SEC_5MIN = 60 * 5


def drop_outliers(df: pd.DataFrame, min_cutoff: int, max_cutoff: int) -> pd.DataFrame:
    """
    Drop outliers based on avg_prediction_error_sec for now.
    Use 250 seconds on either end, this is roughly 1% of either tail.
    In the future, we might expand to other columns.
    """
    return df[
        (df.avg_prediction_error_sec >= min_cutoff)
        & (df.avg_prediction_error_sec <= max_cutoff)
    ].reset_index(drop=True)
