"""Comprehensive pytest test suite for Workstream 1 cleaning and business rules."""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.normalizers import (
    normalize_date,
    normalize_sku,
    normalize_region,
    normalize_channel,
    normalize_customer,
    CANONICAL_REGIONS,
    CANONICAL_CHANNELS,
    CANONICAL_FAMILIES,
)
from src.data.cleaner import clean_train_data, clean_macro_indicators
from src.data.audit import AuditTrail
from src.data.aggregator import aggregate_to_date_sku_region, build_regularized_panel_grid
from src.config import CLEANED_DATA_DIR, REPORTS_DIR


def test_date_normalization():
    """Verify all heterogeneous date patterns convert to canonical YYYY-MM."""
    assert normalize_date("2024-03")[0] == "2024-03"
    assert normalize_date("2024-03-01")[0] == "2024-03"
    assert normalize_date("2024/03")[0] == "2024-03"
    assert normalize_date("03/2024")[0] == "2024-03"
    assert normalize_date("03-2024")[0] == "2024-03"
    assert normalize_date("Oct 2020")[0] == "2020-10"
    assert normalize_date("Sep-2026")[0] == "2026-09"
    # Transposition fix: 2062 -> 2026
    assert normalize_date("2062-01")[0] == "2026-01"


def test_sku_normalization():
    """Verify SKU cleaning handles casing, separators, padding, and family code CHS -> CSS."""
    assert normalize_sku("ela-055") == "ELA-055"
    assert normalize_sku("thm-055") == "THM-055"
    assert normalize_sku("ELA-85") == "ELA-085"
    assert normalize_sku("HYD029") == "HYD-029"
    assert normalize_sku("CSS_041") == "CSS-041"
    assert normalize_sku("CHS-010") == "CSS-010"
    assert normalize_sku("CHS_038") == "CSS-038"
    assert normalize_sku(" THM-034") == "THM-034"
    assert normalize_sku("PMP-84") == "PMP-084"


def test_region_normalization():
    """Verify that region variations map cleanly to 6 canonical regions."""
    assert normalize_region("APAC") == "Asia Pacific"
    assert normalize_region("Asia Pacific ") == "Asia Pacific"
    assert normalize_region("EU") == "Europe"
    assert normalize_region("EUROPE") == "Europe"
    assert normalize_region("INDIA") == "India"
    assert normalize_region("LATAM") == "Latin America"
    assert normalize_region("Latin america") == "Latin America"
    assert normalize_region("ME&A") == "Middle East & Africa"
    assert normalize_region("Middle East and Africa") == "Middle East & Africa"
    assert normalize_region("N. America") == "North America"
    assert normalize_region("NA") == "North America"


def test_channel_normalization():
    """Verify that channel variations map cleanly to 4 canonical channels."""
    assert normalize_channel("After-market") == "Aftermarket"
    assert normalize_channel("DIRECT OEM") == "Direct OEM"
    assert normalize_channel("OEM Direct") == "Direct OEM"
    assert normalize_channel("T1 Distributor") == "Tier-1 Distributor"
    assert normalize_channel("Tier 1 Distributor") == "Tier-1 Distributor"
    assert normalize_channel("Export ") == "Export"


def test_rule_2_deduplication_timestamp():
    """Verify Rule 2: repeated Record_ID retains row with latest Load_Timestamp."""
    audit = AuditTrail()
    df_raw = pd.DataFrame([
        {
            "Record_ID": "REC-001",
            "Date": "2024-01",
            "Year": 2024,
            "Month": 1,
            "Product_Family": "Hydraulic Systems",
            "Business_Unit": "Fluid Control Group",
            "SKU_ID": "HYD-001",
            "SKU_Description": "Hydraulic Valve",
            "Customer_Name": "Solaris Automotive",
            "Sales_Channel": "Direct OEM",
            "Region": "Europe",
            "Units_Sold": 10,
            "Unit_Price_USD": 100.0,
            "Revenue_USD": 1000.0,
            "Load_Timestamp": "2024-02-01 01:00:00",
        },
        {
            "Record_ID": "REC-001",
            "Date": "2024-01",
            "Year": 2024,
            "Month": 1,
            "Product_Family": "Hydraulic Systems",
            "Business_Unit": "Fluid Control Group",
            "SKU_ID": "HYD-001",
            "SKU_Description": "Hydraulic Valve",
            "Customer_Name": "Solaris Automotive",
            "Sales_Channel": "Direct OEM",
            "Region": "Europe",
            "Units_Sold": 50,  # Updated newer load
            "Unit_Price_USD": 100.0,
            "Revenue_USD": 5000.0,
            "Load_Timestamp": "2024-02-02 01:00:00",  # Latest timestamp
        },
    ])
    sku_master = pd.DataFrame([{
        "SKU_ID": "HYD-001",
        "Product_Family": "Hydraulic Systems",
        "Business_Unit": "Fluid Control Group",
        "SKU_Description": "Hydraulic Valve",
    }])

    cleaned = clean_train_data(df_raw, sku_master, audit)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["Units_Sold"] == 50
    assert cleaned.iloc[0]["Revenue_USD"] == 5000.0
    assert audit.summary_counts.get("RULE_2_DEDUP_TIMESTAMP") == 1


def test_rule_1_date_authority():
    """Verify Rule 1: Date is authoritative over disagreeing Year or Month."""
    audit = AuditTrail()
    df_raw = pd.DataFrame([{
        "Record_ID": "REC-002",
        "Date": "2024-05",  # Authoritative month 5
        "Year": 2023,       # Disagreeing Year
        "Month": 12,        # Disagreeing Month
        "Product_Family": "Hydraulic Systems",
        "Business_Unit": "Fluid Control Group",
        "SKU_ID": "HYD-001",
        "SKU_Description": "Hydraulic Valve",
        "Customer_Name": "Solaris Automotive",
        "Sales_Channel": "Direct OEM",
        "Region": "Europe",
        "Units_Sold": 20,
        "Unit_Price_USD": 100.0,
        "Revenue_USD": 2000.0,
        "Load_Timestamp": "2024-06-01 01:00:00",
    }])
    sku_master = pd.DataFrame([{
        "SKU_ID": "HYD-001",
        "Product_Family": "Hydraulic Systems",
        "Business_Unit": "Fluid Control Group",
        "SKU_Description": "Hydraulic Valve",
    }])

    cleaned = clean_train_data(df_raw, sku_master, audit)
    assert cleaned.iloc[0]["Date"] == "2024-05"
    assert cleaned.iloc[0]["Year"] == 2024
    assert cleaned.iloc[0]["Month"] == 5
    assert audit.summary_counts.get("RULE_1_DATE_AUTHORITY") == 1


def test_revenue_and_price_reconciliation():
    """Verify 100x price scaling fix and recovery of missing Units_Sold."""
    audit = AuditTrail()
    df_raw = pd.DataFrame([
        # Row 1: 100x price error (67308.0 -> 673.08)
        {
            "Record_ID": "REC-003",
            "Date": "2024-01",
            "Year": 2024,
            "Month": 1,
            "Product_Family": "Hydraulic Systems",
            "Business_Unit": "Fluid Control Group",
            "SKU_ID": "HYD-001",
            "SKU_Description": "Hydraulic Valve",
            "Customer_Name": "Solaris Automotive",
            "Sales_Channel": "Direct OEM",
            "Region": "Europe",
            "Units_Sold": 150,
            "Unit_Price_USD": 67308.0,
            "Revenue_USD": 100962.0,
            "Load_Timestamp": "2024-02-01 01:00:00",
        },
        # Row 2: Missing Units_Sold recovered from Revenue / Price
        {
            "Record_ID": "REC-004",
            "Date": "2024-02",
            "Year": 2024,
            "Month": 2,
            "Product_Family": "Hydraulic Systems",
            "Business_Unit": "Fluid Control Group",
            "SKU_ID": "HYD-001",
            "SKU_Description": "Hydraulic Valve",
            "Customer_Name": "Solaris Automotive",
            "Sales_Channel": "Direct OEM",
            "Region": "Europe",
            "Units_Sold": np.nan,  # Missing
            "Unit_Price_USD": 500.0,
            "Revenue_USD": 25000.0,
            "Load_Timestamp": "2024-03-01 01:00:00",
        },
    ])
    sku_master = pd.DataFrame([{
        "SKU_ID": "HYD-001",
        "Product_Family": "Hydraulic Systems",
        "Business_Unit": "Fluid Control Group",
        "SKU_Description": "Hydraulic Valve",
    }])

    cleaned = clean_train_data(df_raw, sku_master, audit)
    # Check 100x fix
    row1 = cleaned[cleaned["Record_ID"] == "REC-003"].iloc[0]
    assert row1["Unit_Price_USD"] == 673.08
    assert row1["Revenue_USD"] == 150 * 673.08

    # Check recovered units
    row2 = cleaned[cleaned["Record_ID"] == "REC-004"].iloc[0]
    assert row2["Units_Sold"] == 50
    assert audit.summary_counts.get("RECONCILE_UNITS_FROM_REVENUE") == 1


def test_aggregation_one_row_per_date_sku_region():
    """Verify Workstream 1 Core requirement: one clean row per Date-SKU-Region."""
    cleaned_train = pd.DataFrame([
        {
            "Record_ID": "REC-005",
            "Date": "2024-01",
            "Year": 2024,
            "Month": 1,
            "SKU_ID": "HYD-001",
            "Region": "Europe",
            "Units_Sold": 30,
            "Unit_Price_USD": 100.0,
            "Revenue_USD": 3000.0,
            "is_return": False,
            "is_zero_order": False,
        },
        {
            "Record_ID": "REC-006",
            "Date": "2024-01",
            "Year": 2024,
            "Month": 1,
            "SKU_ID": "HYD-001",
            "Region": "Europe",
            "Units_Sold": 20,
            "Unit_Price_USD": 100.0,
            "Revenue_USD": 2000.0,
            "is_return": False,
            "is_zero_order": False,
        },
    ])
    sku_master = pd.DataFrame([{
        "SKU_ID": "HYD-001",
        "Product_Family": "Hydraulic Systems",
        "Business_Unit": "Fluid Control Group",
        "SKU_Description": "Hydraulic Valve",
    }])

    monthly = aggregate_to_date_sku_region(cleaned_train, sku_master)
    assert len(monthly) == 1
    assert monthly.iloc[0]["Units_Sold"] == 50
    assert monthly.iloc[0]["Revenue_USD"] == 5000.0
    assert monthly.iloc[0]["Transaction_Count"] == 2


def test_macro_indicators_clean_no_nulls():
    """Verify macro indicators linear interpolation leaves zero nulls."""
    audit = AuditTrail()
    df_macro = pd.DataFrame({
        "Date": ["2024-01", "2024-02", "2024-03"],
        "Year": [2024, 2024, 2024],
        "Month": [1, 2, 3],
        "ISM_Manufacturing_PMI": [50.0, np.nan, 52.0],  # Middle null
        "Auto_Production_YoY_Pct": [2.0, 2.5, 3.0],
        "Vehicle_Inventory_Days": [40.0, 42.0, 44.0],
        "Raw_Material_Cost_Index": [100.0, 101.0, 102.0],
        "New_Vehicle_Orders_Index": [95.0, 96.0, 97.0],
        "Industrial_Util_Rate_Pct": [80.0, 80.5, 81.0],
        "Fuel_Price_Index": [110.0, 112.0, 114.0],
        "EV_Adoption_Index": [15.0, 16.0, 17.0],
    })

    cleaned = clean_macro_indicators(df_macro, audit)
    assert cleaned["ISM_Manufacturing_PMI"].isnull().sum() == 0
    assert cleaned.loc[1, "ISM_Manufacturing_PMI"] == 51.0


def test_pipeline_output_integrity():
    """Integration test verifying all saved files in data/cleaned and reports."""
    assert (CLEANED_DATA_DIR / "train_cleaned.parquet").exists()
    assert (CLEANED_DATA_DIR / "train_monthly_cleaned.parquet").exists()
    assert (CLEANED_DATA_DIR / "train_panel_grid.parquet").exists()
    assert (CLEANED_DATA_DIR / "macro_indicators_cleaned.csv").exists()
    assert (CLEANED_DATA_DIR / "sku_master_cleaned.csv").exists()
    assert (CLEANED_DATA_DIR / "inventory_stockouts_cleaned.csv").exists()
    assert (CLEANED_DATA_DIR / "events_calendar_cleaned.csv").exists()
    assert (CLEANED_DATA_DIR / "test_cleaned.csv").exists()
    assert (REPORTS_DIR / "data_quality_report.json").exists()
    assert (REPORTS_DIR / "data_quality_report.md").exists()
    assert (REPORTS_DIR / "audit_records.parquet").exists()

    # Load cleaned monthly and verify 1 row per Date-SKU-Region
    monthly = pd.read_parquet(CLEANED_DATA_DIR / "train_monthly_cleaned.parquet")
    dups = monthly.duplicated(subset=["Date", "SKU_ID", "Region"]).sum()
    assert dups == 0, f"Found {dups} duplicates in train_monthly_cleaned"
    assert (monthly["Units_Sold"] >= 0).all(), "Found negative units in physical Units_Sold"
    assert monthly["Region"].isin(CANONICAL_REGIONS).all()

    # Verify macro indicators has exactly 114 rows and no nulls
    macro = pd.read_csv(CLEANED_DATA_DIR / "macro_indicators_cleaned.csv")
    assert len(macro) == 114
    assert macro.isnull().sum().sum() == 0
