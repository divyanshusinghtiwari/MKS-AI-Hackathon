"""Benchmark forecasting models: Seasonal Naive, Croston's Method, and SBA."""

import numpy as np
import pandas as pd
from typing import Dict, Tuple


def forecast_seasonal_naive(
    history_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str = "Units_Unconstrained",
) -> np.ndarray:
    """Seasonal Naive baseline: forecasts month m using the exact same calendar month of the prior year.
    
    If prior year month is unavailable (e.g. series started < 12 months ago), fall back to overall series mean.
    """
    # Build lookup of (SKU_ID, Region, Month) -> last observed value for that calendar month
    sorted_hist = history_df.sort_values("Date")
    last_seasonal_val = (
        sorted_hist.groupby(["SKU_ID", "Region", "Month"])[target_col]
        .last()
        .to_dict()
    )
    overall_mean = (
        sorted_hist.groupby(["SKU_ID", "Region"])[target_col]
        .mean()
        .to_dict()
    )

    preds = []
    for idx, row in test_df.iterrows():
        sku = row["SKU_ID"]
        reg = row["Region"]
        m = int(row["Month"])
        val = last_seasonal_val.get((sku, reg, m))
        if val is None or pd.isnull(val):
            val = overall_mean.get((sku, reg), 0.0)
        preds.append(max(0.0, float(val)))

    return np.array(preds)


def forecast_croston_sba(
    history_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str = "Units_Unconstrained",
    method: str = "sba",
    alpha: float = 0.1,
) -> np.ndarray:
    """Croston and Syntetos-Boylan Approximation (SBA) baseline for intermittent demand.
    
    - Croston: rate = z / p (smoothed size / smoothed interval)
    - SBA: de-biased rate = (1 - alpha/2) * (z / p)
    """
    rates = {}
    for (sku, reg), grp in history_df.groupby(["SKU_ID", "Region"]):
        series = grp[target_col].values
        non_zero = series[series > 0]
        if len(non_zero) == 0:
            rates[(sku, reg)] = 0.0
        else:
            mean_z = np.mean(non_zero)
            adi = len(series) / len(non_zero)
            croston_rate = mean_z / adi if adi > 0 else 0.0
            if method.lower() == "sba":
                rates[(sku, reg)] = (1.0 - alpha / 2.0) * croston_rate
            else:
                rates[(sku, reg)] = croston_rate

    preds = []
    for idx, row in test_df.iterrows():
        rate = rates.get((row["SKU_ID"], row["Region"]), 0.0)
        preds.append(max(0.0, float(rate)))

    return np.array(preds)


def forecast_composite_baseline(
    history_df: pd.DataFrame,
    test_df: pd.DataFrame,
    intermittency_df: pd.DataFrame,
    target_col: str = "Units_Unconstrained",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate Seasonal Naive, Croston/SBA, and Hybrid Composite Baseline.
    
    Selection Logic:
    - If series is Intermittent or Lumpy (ADI >= 1.32): select SBA.
    - If series is Smooth or Erratic (ADI < 1.32): select Seasonal Naive.
    """
    s_naive = forecast_seasonal_naive(history_df, test_df, target_col)
    sba = forecast_croston_sba(history_df, test_df, target_col, method="sba")

    # Composite based on intermittency class
    inter_map = intermittency_df.set_index(["SKU_ID", "Region"])["intermittency_class"].to_dict()
    
    composite = []
    for idx, row in test_df.iterrows():
        sku = row["SKU_ID"]
        reg = row["Region"]
        iclass = inter_map.get((sku, reg), "Smooth")
        if iclass in ["Intermittent", "Lumpy"]:
            composite.append(sba[idx])
        else:
            composite.append(s_naive[idx])

    return s_naive, sba, np.array(composite)
