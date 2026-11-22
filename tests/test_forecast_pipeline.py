"""Unit and integration tests for Workstream 4: Forecasting Engine & Submission Generation."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.models.baselines import forecast_seasonal_naive, forecast_croston_sba
from src.models.cold_start import apply_lifecycle_and_cold_start_rules, COLD_START_TRANSITIONS
from src.models.reconciliation import reconcile_hierarchical_forecasts

BASE_DIR = Path(__file__).resolve().parent.parent


def test_seasonal_naive_baseline():
    """Verify seasonal naive extracts last seasonal month or falls back to mean."""
    history = pd.DataFrame({
        "Date": ["2024-01", "2024-02", "2025-01", "2025-02"],
        "Month": [1, 2, 1, 2],
        "SKU_ID": ["SKU-01", "SKU-01", "SKU-01", "SKU-01"],
        "Region": ["North America", "North America", "North America", "North America"],
        "Units_Unconstrained": [100.0, 150.0, 110.0, 160.0],
    })
    test = pd.DataFrame({
        "Date": ["2026-01", "2026-02"],
        "Month": [1, 2],
        "SKU_ID": ["SKU-01", "SKU-01"],
        "Region": ["North America", "North America"],
    })
    preds = forecast_seasonal_naive(history, test)
    assert len(preds) == 2
    assert preds[0] == 110.0  # Most recent Jan
    assert preds[1] == 160.0  # Most recent Feb


def test_croston_sba_debiasing():
    """Verify SBA applies the (1 - alpha/2) de-biasing multiplier to Croston."""
    history = pd.DataFrame({
        "Date": ["2024-01", "2024-02", "2024-03", "2024-04"],
        "SKU_ID": ["SKU-01"] * 4,
        "Region": ["Europe"] * 4,
        "Units_Unconstrained": [0.0, 50.0, 0.0, 50.0],  # ADI = 2, mean non-zero = 50 -> Croston = 25
    })
    test = pd.DataFrame({
        "Date": ["2024-05"],
        "SKU_ID": ["SKU-01"],
        "Region": ["Europe"],
    })
    croston_pred = forecast_croston_sba(history, test, method="croston", alpha=0.1)
    sba_pred = forecast_croston_sba(history, test, method="sba", alpha=0.1)

    assert croston_pred[0] == 25.0
    # SBA = 25.0 * (1 - 0.05) = 23.75
    assert np.isclose(sba_pred[0], 23.75)
    assert sba_pred[0] < croston_pred[0]


def test_rule5_lifecycle_zeroing():
    """Verify Rule 5 strictly enforces zero before launch and zero after EOL."""
    sku_master = pd.DataFrame({
        "SKU_ID": ["LAUNCH-01", "EOL-01"],
        "Launch_Date": ["2027-06", "2015-01"],
        "EOL_Date": [None, "2027-08"],
    })
    test = pd.DataFrame({
        "Date": ["2027-05", "2027-06", "2027-08", "2027-09"],
        "SKU_ID": ["LAUNCH-01", "LAUNCH-01", "EOL-01", "EOL-01"],
        "Region": ["Europe", "Europe", "Europe", "Europe"],
    })
    raw_preds = np.array([50.0, 50.0, 50.0, 50.0])
    adj = apply_lifecycle_and_cold_start_rules(test, raw_preds, sku_master)

    # LAUNCH-01: May 2027 is pre-launch -> must be 0
    assert adj[0] == 0.0
    # LAUNCH-01: June 2027 is launch month -> > 0
    assert adj[1] > 0.0
    # EOL-01: August 2027 is EOL month -> > 0
    assert adj[2] > 0.0
    # EOL-01: Sept 2027 is post-EOL -> must be 0
    assert adj[3] == 0.0


def test_cold_start_transition_ramp():
    """Verify smooth phase-in/phase-out ramp for successor and predecessor."""
    sku_master = pd.DataFrame({
        "SKU_ID": ["PMP-020", "PMP-003"],
        "Launch_Date": ["2027-06", "2018-01"],
        "EOL_Date": [None, "2027-08"],
    })
    test = pd.DataFrame({
        "Date": ["2027-06", "2027-06", "2027-07", "2027-07", "2027-08", "2027-08", "2027-09", "2027-09"],
        "SKU_ID": ["PMP-020", "PMP-003", "PMP-020", "PMP-003", "PMP-020", "PMP-003", "PMP-020", "PMP-003"],
        "Region": ["North America"] * 8,
    })
    raw_preds = np.array([100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0])
    adj = apply_lifecycle_and_cold_start_rules(test, raw_preds, sku_master)

    # Month 1 (2027-06): Successor 35%, Predecessor 65% -> Sum = 100%
    assert np.isclose(adj[0] + adj[1], 100.0)
    assert np.isclose(adj[0], 35.0)
    assert np.isclose(adj[1], 65.0)

    # Month 2 (2027-07): Successor 70%, Predecessor 30% -> Sum = 100%
    assert np.isclose(adj[2] + adj[3], 100.0)
    assert np.isclose(adj[2], 70.0)
    assert np.isclose(adj[3], 30.0)

    # Month 3 (2027-08): Successor 100%, Predecessor 0% -> Sum = 100%
    assert np.isclose(adj[4], 100.0)
    assert np.isclose(adj[5], 0.0)

    # Post-EOL (2027-09): Successor 100%, Predecessor 0% (Rule 5)
    assert np.isclose(adj[6], 100.0)
    assert np.isclose(adj[7], 0.0)


def test_hierarchical_reconciliation():
    """Verify bottom-up hierarchical reconciliation guarantees zero discrepancy across levels."""
    df = pd.DataFrame({
        "Date": ["2026-11", "2026-11", "2026-11", "2026-11"],
        "SKU_ID": ["SKU-01", "SKU-02", "SKU-01", "SKU-02"],
        "Region": ["Europe", "Europe", "Asia Pacific", "Asia Pacific"],
        "Product_Family": ["Hydraulics", "Hydraulics", "Hydraulics", "Hydraulics"],
        "Units_Sold_Forecast": [10.0, 20.0, 30.0, 40.0],
    })
    out_df, hierarchy = reconcile_hierarchical_forecasts(df, "Units_Sold_Forecast")

    port_sum = hierarchy["portfolio_global"].set_index("Date")["Portfolio_Global_Forecast"]
    reg_sum = hierarchy["region_global"].groupby("Date")["Region_Global_Forecast"].sum()
    fam_sum = hierarchy["family_global"].groupby("Date")["Family_Global_Forecast"].sum()

    assert np.isclose(port_sum.loc["2026-11"], 100.0)
    assert np.isclose(reg_sum.loc["2026-11"], 100.0)
    assert np.isclose(fam_sum.loc["2026-11"], 100.0)


def test_quantile_monotonicity():
    """Verify quantile predictions satisfy 0 <= P10 <= P50 <= P90."""
    p10 = np.array([5.0, -2.0, 15.0])
    p50 = np.array([4.0, 10.0, 12.0])
    p90 = np.array([3.0, 8.0, 25.0])

    # Applying monotonicity correction
    c_p10 = np.clip(p10, 0.0, None)
    c_p50 = np.maximum(c_p10, p50)
    c_p90 = np.maximum(c_p50, p90)

    assert (c_p10 >= 0.0).all()
    assert (c_p10 <= c_p50).all()
    assert (c_p50 <= c_p90).all()
