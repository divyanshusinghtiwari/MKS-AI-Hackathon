"""Demand intermittency analysis and Syntetos-Boylan / Croston classification."""

import numpy as np
import pandas as pd


def compute_intermittency_metrics(
    df: pd.DataFrame,
    target_col: str = "Units_Unconstrained",
    group_cols: list = ["SKU_ID", "Region"],
) -> pd.DataFrame:
    """Calculate ADI, CV², and classify series into Smooth, Intermittent, Erratic, or Lumpy.
    
    Task 3:
    - Average Demand Interval (ADI): total periods / periods with non-zero demand
    - Squared Coefficient of Variation (CV²): (std / mean)² of non-zero demand sizes
    - Classification cutoffs (Syntetos & Boylan, 2005):
        - Smooth:       ADI < 1.32 and CV² < 0.49
        - Intermittent: ADI >= 1.32 and CV² < 0.49
        - Erratic:      ADI < 1.32 and CV² >= 0.49
        - Lumpy:        ADI >= 1.32 and CV² >= 0.49
    - Croston and SBA baseline demand rate estimation.
    """
    records = []
    alpha = 0.1  # Standard Croston smoothing parameter

    for (sku, reg), grp in df.groupby(group_cols):
        series = grp[target_col].values
        total_n = len(series)
        non_zero = series[series > 0]
        n_non_zero = len(non_zero)

        if n_non_zero == 0:
            adi = 99.0
            cv2 = 0.0
            cat = "Intermittent"
            croston_rate = 0.0
            sba_rate = 0.0
        else:
            adi = total_n / n_non_zero
            mean_nz = np.mean(non_zero)
            std_nz = np.std(non_zero, ddof=1) if n_non_zero > 1 else 0.0
            cv2 = (std_nz / mean_nz) ** 2 if mean_nz > 0 else 0.0

            # Syntetos-Boylan categorization
            if adi < 1.32:
                cat = "Smooth" if cv2 < 0.49 else "Erratic"
            else:
                cat = "Intermittent" if cv2 < 0.49 else "Lumpy"

            # Croston & SBA smoothed rates
            # z: demand size, p: demand interval
            z = mean_nz
            p = adi
            croston_rate = z / p if p > 0 else 0.0
            sba_rate = (1.0 - alpha / 2.0) * croston_rate

        records.append({
            "SKU_ID": sku,
            "Region": reg,
            "adi": round(float(adi), 2),
            "cv2": round(float(cv2), 3),
            "intermittency_class": cat,
            "croston_baseline_rate": round(float(croston_rate), 2),
            "sba_baseline_rate": round(float(sba_rate), 2),
        })

    intermittency_df = pd.DataFrame(records)
    return intermittency_df
