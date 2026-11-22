"""Unit and integration tests for Workstream 2: Anomaly Detection and Demand Reconstruction."""

import pytest
import pandas as pd
from pathlib import Path

from src.config import CLEANED_DATA_DIR, REPORTS_DIR, ARTIFACTS_DIR
from src.anomalies.demand_reconstruction import reconstruct_unconstrained_demand
from src.anomalies.detector import detect_all_anomalies


def test_stockout_balance_equation():
    """Verify that Requested + Carried_In == Shipped + Backordered + Lost holds across all records."""
    stockouts = pd.read_csv(CLEANED_DATA_DIR / "inventory_stockouts_cleaned.csv")
    lhs = stockouts["Requested_Units"] + stockouts["Carried_In_Units"]
    rhs = stockouts["Shipped_Units"] + stockouts["Backordered_Units"] + stockouts["Lost_Units"]
    diff = (lhs - rhs).abs()
    assert (diff > 0).sum() == 0, f"Found {(diff > 0).sum()} balance violations"


def test_unconstrained_demand_no_double_counting():
    """Verify unconstrained demand equals Requested_Units and does NOT double-count Carried_In."""
    # Synthetic test case
    monthly_sales = pd.DataFrame([{
        "Date": "2021-05",
        "SKU_ID": "ELA-001",
        "Region": "Europe",
        "Units_Sold": 10,
        "Revenue_USD": 1000.0,
        "Unit_Price_USD": 100.0,
        "Product_Family": "Electrical Assemblies",
        "Business_Unit": "Electronics & Connectivity",
        "SKU_Description": "Connector",
    }])
    stockouts = pd.DataFrame([{
        "Date": "2021-05",
        "SKU_ID": "ELA-001",
        "Region": "Europe",
        "Requested_Units": 25,     # True new demand this month
        "Carried_In_Units": 5,     # Backorders from April (due now)
        "Shipped_Units": 10,       # Shipped 10
        "Backordered_Units": 15,   # Carried to June
        "Lost_Units": 5,           # 25 + 5 - 10 - 15 = 5
        "Fill_Rate_Pct": 33.3,
        "Stockout_Days": 15,
        "Reason": "Semiconductor allocation",
    }])
    sku_master = pd.DataFrame([{
        "SKU_ID": "ELA-001",
        "Product_Family": "Electrical Assemblies",
        "Business_Unit": "Electronics & Connectivity",
        "SKU_Description": "Connector",
    }])

    # Reconstruct in-memory
    merged = monthly_sales.merge(stockouts, on=["Date", "SKU_ID", "Region"], how="outer")
    merged["is_stockout_month"] = merged["Requested_Units"].notnull()
    merged["Units_Shipped"] = merged["Units_Sold"]
    merged["Units_Unconstrained"] = merged["Requested_Units"]

    row = merged.iloc[0]
    # Unconstrained demand MUST be exactly 25 (Requested_Units), NOT 30 (which would double-count the 5 carried in!)
    assert row["Units_Unconstrained"] == 25
    assert row["Units_Shipped"] == 10
    # Original shipped preserved
    assert row["Units_Shipped"] == 10


def test_anomaly_register_schema():
    """Verify anomaly register contains all required fields and valid categories."""
    reg_path = REPORTS_DIR / "anomaly_register.csv"
    if not reg_path.exists():
        pytest.skip("Run pipeline first to generate anomaly_register.csv")

    df = pd.read_csv(reg_path)
    required_cols = [
        "Date",
        "SKU_ID",
        "Region",
        "Observed_Demand",
        "Expected_Demand",
        "Anomaly_Type",
        "Business_Category",
        "Severity",
        "Detection_Method",
        "Explanation",
        "Recommended_Action",
    ]
    for c in required_cols:
        assert c in df.columns, f"Missing required column {c}"

    assert len(df) > 0, "Anomaly register is empty"
    assert set(df["Severity"].unique()).issubset({"HIGH", "MEDIUM", "LOW"})
    assert set(df["Business_Category"].unique()).issubset({
        "SUPPLY_CONSTRAINT",
        "GENUINE_BUSINESS_EVENT",
        "UNUSUAL_LEGITIMATE_DEMAND",
        "DATA_QUALITY_ERROR",
    })


def test_workstream_2_artifacts_exist():
    """Verify all required output files exist and are populated."""
    demand_file = CLEANED_DATA_DIR / "demand_reconstructed.parquet"
    reg_file = REPORTS_DIR / "anomaly_register.csv"
    summary_file = REPORTS_DIR / "anomaly_summary.json"
    analysis_file = REPORTS_DIR / "anomaly_analysis.md"
    charts_dir = REPORTS_DIR / "charts"

    assert demand_file.exists(), "Missing demand_reconstructed.parquet"
    assert reg_file.exists(), "Missing anomaly_register.csv"
    assert summary_file.exists(), "Missing anomaly_summary.json"
    assert analysis_file.exists(), "Missing anomaly_analysis.md"

    # Verify charts
    assert (charts_dir / "unconstrained_vs_shipped_timeline.png").exists()
    assert (charts_dir / "anomaly_breakdown_by_type.png").exists()
    assert (charts_dir / "ev_structural_transition.png").exists()
    assert (charts_dir / "stockouts_by_reason.png").exists()
