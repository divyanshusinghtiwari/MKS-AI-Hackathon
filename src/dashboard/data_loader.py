"""Data loader and caching module for Streamlit Control Tower Dashboard."""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
import streamlit as st

# Path configuration relative to repository root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
REPORTS_DIR = BASE_DIR / "reports"
SUBMISSION_PATH = BASE_DIR / "submission.csv"


@st.cache_data(show_spinner=False)
def load_historical_demand() -> pd.DataFrame:
    """Load cleaned unconstrained demand history (2019-01 to 2026-10)."""
    path = CLEANED_DIR / "demand_reconstructed.parquet"
    if not path.exists():
        st.error(f"Missing historical demand dataset at {path}")
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def load_forecast_data() -> pd.DataFrame:
    """Load 19-month forecast predictions with P10/P50/P90 intervals (2026-11 to 2028-05)."""
    path = ARTIFACTS_DIR / "forecasts_with_intervals.parquet"
    if not path.exists():
        st.error(f"Missing forecast dataset at {path}")
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def load_submission_data() -> pd.DataFrame:
    """Load official submission.csv (58,219 rows)."""
    if not SUBMISSION_PATH.exists():
        st.error(f"Missing official submission file at {SUBMISSION_PATH}")
        return pd.DataFrame()
    return pd.read_csv(SUBMISSION_PATH)


@st.cache_data(show_spinner=False)
def load_sku_master() -> pd.DataFrame:
    """Load SKU master reference data."""
    path = CLEANED_DIR / "sku_master_cleaned.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_macro_indicators() -> pd.DataFrame:
    """Load cleaned macroeconomic indicators (2019-01 to 2028-05)."""
    path = CLEANED_DIR / "macro_indicators_cleaned.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_anomaly_data() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load anomaly register and anomaly summary metrics."""
    reg_path = REPORTS_DIR / "anomaly_register.csv"
    sum_path = REPORTS_DIR / "anomaly_summary.json"

    df = pd.read_csv(reg_path) if reg_path.exists() else pd.DataFrame()
    summary = {}
    if sum_path.exists():
        with open(sum_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
    return df, summary


@st.cache_data(show_spinner=False)
def load_data_quality_report() -> Dict[str, Any]:
    """Load Phase 1 data quality report JSON."""
    path = REPORTS_DIR / "data_quality_report.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_backtest_data() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load 19-month rolling backtest evaluation records and summary metrics."""
    res_path = REPORTS_DIR / "backtest_results.csv"
    sum_path = REPORTS_DIR / "backtest_summary.json"

    df = pd.read_csv(res_path) if res_path.exists() else pd.DataFrame()
    summary = {}
    if sum_path.exists():
        with open(sum_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
    return df, summary


@st.cache_data(show_spinner=False)
def load_feature_importance() -> pd.DataFrame:
    """Load global LightGBM feature importance rankings."""
    path = REPORTS_DIR / "feature_importance.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def get_sku_prices() -> Dict[str, float]:
    """Extract authoritative unit price per SKU from historical data for revenue forecasting."""
    hist = load_historical_demand()
    if hist.empty or "Unit_Price_USD" not in hist.columns:
        return {}
    # Use most recent observed price per SKU
    latest_prices = (
        hist.sort_values("Date")
        .groupby("SKU_ID")["Unit_Price_USD"]
        .last()
        .to_dict()
    )

    # Transfer prices to cold-start replacement SKUs from their predecessors
    pred_map = {
        "PMP-020": "PMP-003",
        "PTC-029": "PTC-005",
        "THM-012": "THM-001",
    }
    for l_sku, p_sku in pred_map.items():
        if p_sku in latest_prices and l_sku not in latest_prices:
            latest_prices[l_sku] = latest_prices[p_sku]

    return latest_prices


def build_continuous_portfolio_timeline(
    hist_df: pd.DataFrame,
    fc_df: pd.DataFrame,
    prices_map: Dict[str, float] = None,
) -> pd.DataFrame:
    """Combine historical unconstrained demand and forward forecasts into a unified continuous timeline."""
    if hist_df.empty:
        return pd.DataFrame()

    # 1. Monthly Historical Aggregation
    hist_monthly = (
        hist_df.groupby("Date")
        .agg({
            "Units_Shipped": "sum",
            "Units_Unconstrained": "sum",
            "Revenue_Unconstrained": "sum",
        })
        .reset_index()
    )
    hist_monthly["P10_Forecast"] = np.nan
    hist_monthly["P50_Forecast"] = np.nan
    hist_monthly["P90_Forecast"] = np.nan
    hist_monthly["Units_Sold_Forecast"] = np.nan
    hist_monthly["Revenue_Forecast"] = np.nan
    hist_monthly["is_forecast"] = False

    # 2. Monthly Forecast Aggregation
    if not fc_df.empty:
        # Approximate forecasted revenue if price map provided
        fc_copy = fc_df.copy()
        if prices_map:
            median_p = float(np.median(list(prices_map.values()))) if prices_map else 731.34
            fc_copy["Est_Price"] = fc_copy["SKU_ID"].map(prices_map).fillna(median_p)
            fc_copy["Est_Revenue"] = fc_copy["Units_Sold_Forecast"] * fc_copy["Est_Price"]
        else:
            fc_copy["Est_Revenue"] = 0.0

        fc_monthly = (
            fc_copy.groupby("Date")
            .agg({
                "P10_Forecast": "sum",
                "P50_Forecast": "sum",
                "P90_Forecast": "sum",
                "Units_Sold_Forecast": "sum",
                "Est_Revenue": "sum",
            })
            .reset_index()
            .rename(columns={"Est_Revenue": "Revenue_Forecast"})
        )
        fc_monthly["Units_Shipped"] = np.nan
        fc_monthly["Units_Unconstrained"] = np.nan
        fc_monthly["Revenue_Unconstrained"] = np.nan
        fc_monthly["is_forecast"] = True

        combined = pd.concat([hist_monthly, fc_monthly], ignore_index=True)
    else:
        combined = hist_monthly

    return combined.sort_values("Date").reset_index(drop=True)
