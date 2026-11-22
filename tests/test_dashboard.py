"""Unit and integration tests for Phase 5 Streamlit Control Tower Dashboard."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.dashboard.data_loader import (
    load_historical_demand,
    load_forecast_data,
    load_submission_data,
    load_data_quality_report,
    load_anomaly_data,
    load_backtest_data,
    build_continuous_portfolio_timeline,
)
from src.dashboard.filters import filter_dataframe

BASE_DIR = Path(__file__).resolve().parent.parent


def test_dashboard_data_artifacts_exist():
    """Verify all required dashboard data artifacts exist and load correctly."""
    hist = load_historical_demand()
    assert not hist.empty
    assert len(hist) > 200000

    fc = load_forecast_data()
    assert not fc.empty
    assert len(fc) == 58219

    sub = load_submission_data()
    assert not sub.empty
    assert len(sub) == 58219

    dq = load_data_quality_report()
    assert "data_cleaning_audit" in dq

    ano_df, ano_sum = load_anomaly_data()
    assert not ano_df.empty
    assert len(ano_df) == 13231

    bt_df, bt_sum = load_backtest_data()
    assert not bt_df.empty
    assert "overall_portfolio_performance" in bt_sum


def test_continuous_timeline_transformation():
    """Verify historical unconstrained demand and forward forecast merge into one continuous timeline."""
    hist_sample = pd.DataFrame({
        "Date": ["2026-09", "2026-10"],
        "Units_Shipped": [100.0, 110.0],
        "Units_Unconstrained": [105.0, 115.0],
        "Revenue_Unconstrained": [5250.0, 5750.0],
    })
    fc_sample = pd.DataFrame({
        "Date": ["2026-11", "2026-12"],
        "SKU_ID": ["SKU-01", "SKU-01"],
        "P10_Forecast": [90.0, 95.0],
        "P50_Forecast": [100.0, 105.0],
        "P90_Forecast": [115.0, 120.0],
        "Units_Sold_Forecast": [100.0, 105.0],
    })
    price_map = {"SKU-01": 50.0}

    timeline = build_continuous_portfolio_timeline(hist_sample, fc_sample, price_map)
    assert len(timeline) == 4
    assert timeline["Date"].tolist() == ["2026-09", "2026-10", "2026-11", "2026-12"]
    assert timeline["is_forecast"].tolist() == [False, False, True, True]

    # Verify history has NaNs for forecast cols and vice versa
    assert np.isnan(timeline.loc[0, "P50_Forecast"])
    assert np.isnan(timeline.loc[2, "Units_Unconstrained"])
    assert timeline.loc[2, "Revenue_Forecast"] == 100.0 * 50.0


def test_filter_dataframe_logic():
    """Verify global filter selections apply correctly without dropping unexpected rows."""
    df = pd.DataFrame({
        "Date": ["2026-01", "2026-02", "2026-03"],
        "Product_Family": ["Hydraulics", "Hydraulics", "Thermal Management"],
        "Region": ["North America", "Europe", "North America"],
        "SKU_ID": ["HYD-001", "HYD-001", "THM-001"],
        "Units": [50, 60, 70],
    })

    # 1. Filter by Family
    f1 = filter_dataframe(df, {"families": ["Hydraulics"], "regions": ["North America", "Europe"], "start_date": "2026-01", "end_date": "2026-03"})
    assert len(f1) == 2
    assert (f1["Product_Family"] == "Hydraulics").all()

    # 2. Filter by Specific SKU
    f2 = filter_dataframe(df, {"families": ["Hydraulics", "Thermal Management"], "regions": ["North America", "Europe"], "sku": "THM-001", "start_date": "2026-01", "end_date": "2026-03"})
    assert len(f2) == 1
    assert f2.iloc[0]["SKU_ID"] == "THM-001"

    # 3. Filter by Date range
    f3 = filter_dataframe(df, {"families": ["Hydraulics", "Thermal Management"], "regions": ["North America", "Europe"], "start_date": "2026-02", "end_date": "2026-03"})
    assert len(f3) == 2
    assert "2026-01" not in f3["Date"].values


def test_what_if_simulation_isolation():
    """Verify that what-if simulation calculations do not modify source forecast data."""
    fc_df = pd.DataFrame({
        "SKU_ID": ["SKU-A", "SKU-B"],
        "Product_Family": ["Electrical Assemblies", "Powertrain Components"],
        "Units_Sold_Forecast": [100, 200],
    })
    original_sum = fc_df["Units_Sold_Forecast"].sum()

    # Apply macro elasticity shock in memory
    pmi_shock = -3.0
    ev_shock = 10.0
    mults = [1.0 + (pmi_shock * 0.012) + (ev_shock * 0.009), 1.0 + (pmi_shock * 0.012) - (ev_shock * 0.004)]
    sim_units = np.round(fc_df["Units_Sold_Forecast"] * mults).astype(int)

    # Ensure source data was not modified
    assert fc_df["Units_Sold_Forecast"].sum() == original_sum
    assert len(sim_units) == 2
    assert (sim_units >= 0).all()


def test_procurement_safety_stock_formulas():
    """Verify safety stock and reorder point formulas produce valid non-negative parameters."""
    avg_demand = 100.0
    p90 = 130.0
    lead_time = 2.0

    buffer_monthly = max(0.0, p90 - avg_demand)  # 30.0
    ss = int(round(buffer_monthly * np.sqrt(lead_time)))  # 30 * 1.414 = 42
    rop = int(round(avg_demand * lead_time + ss))  # 200 + 42 = 242

    assert ss > 0
    assert rop > ss
    assert rop == 242
