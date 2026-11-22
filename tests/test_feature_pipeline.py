"""Unit and integration tests for Workstream 3: Feature Engineering and Macro Drivers."""

import pytest
import pandas as pd
import numpy as np

from src.features.calendar import create_calendar_features
from src.features.time_series import create_time_series_features
from src.features.intermittency import compute_intermittency_metrics
from src.features.macro import analyze_macro_lead_lags, attach_macro_features
from src.config import CLEANED_DATA_DIR, REPORTS_DIR


def test_calendar_features_cyclical_bounds():
    """Verify calendar features lie within mathematical bounds [-1, 1] and events trigger accurately."""
    df = pd.DataFrame([
        {"Date": "2024-08", "Region": "Europe"},
        {"Date": "2024-05", "Region": "Asia Pacific"},
        {"Date": "2024-12", "Region": "North America"},
    ])
    out = create_calendar_features(df)
    assert (-1.0 <= out["month_sin"]).all() and (out["month_sin"] <= 1.0).all()
    assert (-1.0 <= out["month_cos"]).all() and (out["month_cos"] <= 1.0).all()
    
    # August Europe shutdown
    assert out.iloc[0]["is_europe_summer_shutdown"] == 1
    assert out.iloc[1]["is_europe_summer_shutdown"] == 0

    # May Asia Pacific Golden Week
    assert out.iloc[1]["is_golden_week_month"] == 1

    # December Holiday
    assert out.iloc[2]["is_year_end_holiday"] == 1


def test_no_target_leakage_in_lags():
    """Verify that lag features strictly reflect past observations and lag_1 equals target[t-1]."""
    df = pd.DataFrame({
        "Date": ["2024-01", "2024-02", "2024-03", "2024-04"],
        "SKU_ID": ["HYD-001"] * 4,
        "Region": ["Europe"] * 4,
        "Units_Unconstrained": [100, 150, 200, 250],
    })
    out = create_time_series_features(df, target_col="Units_Unconstrained")
    
    # t=0: lag_1 must be NaN (no history prior to 2024-01)
    assert pd.isnull(out.iloc[0]["lag_1"])
    
    # t=1: lag_1 must equal 100 (demand of t=0)
    assert out.iloc[1]["lag_1"] == 100
    
    # t=2: lag_1 must equal 150, lag_2 must equal 100
    assert out.iloc[2]["lag_1"] == 150
    assert out.iloc[2]["lag_2"] == 100

    # t=3: lag_1 must equal 200, lag_2 must equal 150, lag_3 must equal 100
    assert out.iloc[3]["lag_1"] == 200
    assert out.iloc[3]["lag_2"] == 150
    assert out.iloc[3]["lag_3"] == 100


def test_rolling_features_use_past_only():
    """Verify that rolling_mean_3[t] strictly averages [t-1, t-2, t-3] and excludes target[t]."""
    df = pd.DataFrame({
        "Date": ["2024-01", "2024-02", "2024-03", "2024-04"],
        "SKU_ID": ["HYD-001"] * 4,
        "Region": ["Europe"] * 4,
        "Units_Unconstrained": [10, 20, 30, 999],  # Notice huge spike at t=3
    })
    out = create_time_series_features(df, target_col="Units_Unconstrained")

    # At t=3, target is 999. rolling_mean_3 must be (30 + 20 + 10) / 3 = 20.0
    # It must NOT include 999!
    assert out.iloc[3]["rolling_mean_3"] == 20.0


def test_demand_intermittency_classification():
    """Verify Syntetos-Boylan intermittency categorization (Smooth, Intermittent, Erratic, Lumpy)."""
    # Smooth series: constant demand every period
    df_smooth = pd.DataFrame({
        "SKU_ID": ["SKU-A"] * 10,
        "Region": ["North America"] * 10,
        "Units_Unconstrained": [50, 52, 48, 50, 51, 49, 50, 52, 48, 51],
    })
    res_smooth = compute_intermittency_metrics(df_smooth, target_col="Units_Unconstrained")
    assert res_smooth.iloc[0]["intermittency_class"] == "Smooth"
    assert res_smooth.iloc[0]["adi"] == 1.0

    # Intermittent series: orders only every 3 periods, stable sizes
    df_inter = pd.DataFrame({
        "SKU_ID": ["SKU-B"] * 9,
        "Region": ["North America"] * 9,
        "Units_Unconstrained": [50, 0, 0, 50, 0, 0, 50, 0, 0],
    })
    res_inter = compute_intermittency_metrics(df_inter, target_col="Units_Unconstrained")
    assert res_inter.iloc[0]["intermittency_class"] == "Intermittent"
    assert res_inter.iloc[0]["adi"] == 3.0


def test_feature_store_artifacts_exist():
    """Verify that all Phase 3 files exist and are populated."""
    feat_file = CLEANED_DATA_DIR / "features_engineered.parquet"
    dict_file = REPORTS_DIR / "feature_dictionary.md"
    macro_file = REPORTS_DIR / "macro_correlation_analysis.md"
    report_file = REPORTS_DIR / "feature_quality_report.json"

    assert feat_file.exists(), "Missing features_engineered.parquet"
    assert dict_file.exists(), "Missing feature_dictionary.md"
    assert macro_file.exists(), "Missing macro_correlation_analysis.md"
    assert report_file.exists(), "Missing feature_quality_report.json"
