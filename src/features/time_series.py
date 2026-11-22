"""Time series lag, rolling window, EWMA, and growth rate feature generation."""

import numpy as np
import pandas as pd


def create_time_series_features(
    df: pd.DataFrame,
    target_col: str = "Units_Unconstrained",
    group_cols: list = ["SKU_ID", "Region"],
) -> pd.DataFrame:
    """Generate strictly backward-looking time-series lag and rolling statistics.
    
    Task 2:
    - Lag 1, 2, 3, 6, 9, 12, 18, 24 months
    - Rolling mean and standard deviation (3, 6, 12 months)
    - Rolling min and max (6, 12 months)
    - Exponentially weighted moving averages (EWMA span 3, span 12)
    - Demand growth rates (MoM, YoY, 3M momentum)
    
    CRITICAL: All rolling and EWMA features are computed strictly on shifted (past)
    values to guarantee ZERO target leakage into month t.
    """
    out = df.copy()

    # Ensure strictly sorted by group and date
    out = out.sort_values(by=group_cols + ["Date"]).reset_index(drop=True)
    grouped = out.groupby(group_cols)[target_col]

    # 1. Historical Lags (1, 2, 3, 6, 9, 12, 18, 24)
    lags = [1, 2, 3, 6, 9, 12, 18, 24]
    for lag in lags:
        out[f"lag_{lag}"] = grouped.shift(lag)

    # 2. Rolling Statistics (computed on lag_1 to ensure past-only values)
    # Using shift(1) as the base series guarantees no current-month information is included
    lag1_grouped = out.groupby(group_cols)["lag_1"]

    # Rolling Means
    for w in [3, 6, 12]:
        out[f"rolling_mean_{w}"] = (
            lag1_grouped.rolling(window=w, min_periods=1).mean().reset_index(level=group_cols, drop=True).round(2)
        )

    # Rolling Standard Deviations
    for w in [3, 6, 12]:
        out[f"rolling_std_{w}"] = (
            lag1_grouped.rolling(window=w, min_periods=2).std().reset_index(level=group_cols, drop=True).fillna(0.0).round(2)
        )

    # Rolling Minimum and Maximum (6, 12 months)
    for w in [6, 12]:
        out[f"rolling_min_{w}"] = (
            lag1_grouped.rolling(window=w, min_periods=1).min().reset_index(level=group_cols, drop=True)
        )
        out[f"rolling_max_{w}"] = (
            lag1_grouped.rolling(window=w, min_periods=1).max().reset_index(level=group_cols, drop=True)
        )

    # 3. Exponentially Weighted Moving Averages (EWMA)
    # Computed on lag_1
    out["ewma_span_3"] = (
        lag1_grouped.transform(lambda s: s.ewm(span=3, min_periods=1).mean()).round(2)
    )
    out["ewma_span_12"] = (
        lag1_grouped.transform(lambda s: s.ewm(span=12, min_periods=1).mean()).round(2)
    )

    # 4. Demand Growth Rates & Momentum
    # MoM Growth: (lag_1 - lag_2) / (lag_2 + 1)
    out["mom_growth_rate"] = (
        (out["lag_1"] - out["lag_2"]) / (out["lag_2"] + 1.0)
    ).clip(lower=-2.0, upper=5.0).round(4)

    # YoY Growth: (lag_1 - lag_12) / (lag_12 + 1)
    out["yoy_growth_rate"] = (
        (out["lag_1"] - out["lag_12"]) / (out["lag_12"] + 1.0)
    ).clip(lower=-2.0, upper=5.0).round(4)

    # 3-Month Momentum: (lag_1 - lag_3) / (lag_3 + 1)
    out["momentum_3m"] = (
        (out["lag_1"] - out["lag_3"]) / (out["lag_3"] + 1.0)
    ).clip(lower=-2.0, upper=5.0).round(4)

    return out
