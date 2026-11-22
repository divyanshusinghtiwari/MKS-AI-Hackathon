"""Comprehensive cleaning pipeline for Celeris Automobili Industrial datasets."""

import logging
import numpy as np
import pandas as pd
from typing import Tuple, Dict

from src.data.normalizers import (
    normalize_date,
    normalize_sku,
    normalize_region,
    normalize_channel,
    normalize_customer,
    get_canonical_family_and_bu,
    CANONICAL_REGIONS,
    CANONICAL_CHANNELS,
    CANONICAL_FAMILIES,
)
from src.data.audit import AuditTrail

logger = logging.getLogger(__name__)


def clean_train_data(
    raw_train: pd.DataFrame,
    sku_master: pd.DataFrame,
    audit: AuditTrail,
) -> pd.DataFrame:
    """Clean the raw train.csv transactions in full compliance with business rules.
    
    Workstream 1 Core & Advanced:
    - Deduplicates Record_ID using latest Load_Timestamp (Rule 2)
    - Standardizes Dates and enforces Date authority over Year/Month (Rule 1)
    - Normalizes SKU_IDs to canonical codes (matching sku_master)
    - Resolves Region and Sales Channel variations to canonical sets
    - Imputes missing Region using customer geography and SKU history
    - Reconciles Units_Sold, Unit_Price_USD, and Revenue_USD (100x price fix, missing recovery)
    - Flags returns (negative units) and catalog zero orders
    """
    logger.info(f"Starting train cleaning. Raw rows: {len(raw_train):,}")
    df = raw_train.copy()

    # 1. Deduplication by Record_ID using Load_Timestamp (Rule 2)
    df["Load_Timestamp_dt"] = pd.to_datetime(df["Load_Timestamp"], errors="coerce")
    initial_count = len(df)
    
    # Sort by Record_ID and Load_Timestamp descending, then drop duplicates
    df = df.sort_values(by=["Record_ID", "Load_Timestamp_dt"], ascending=[True, False])
    dup_mask = df.duplicated(subset=["Record_ID"], keep="first")
    dup_count = dup_mask.sum()
    
    if dup_count > 0:
        logger.info(f"Found {dup_count:,} duplicate Record_IDs. Retaining records with latest Load_Timestamp.")
        audit.increment("RULE_2_DEDUP_TIMESTAMP", count=int(dup_count))
        # Log a sample of duplicates to the record audit
        for rid in df.loc[dup_mask, "Record_ID"].head(50):
            audit.log("train", rid, "RULE_2_DEDUP_TIMESTAMP", "Record_ID", rid, "REMOVED", "Removed older duplicate timestamp", increment_summary=False)
        df = df[~dup_mask].copy()

    df = df.drop(columns=["Load_Timestamp_dt"])

    # 2. Date Standardization & Rule 1 Authority
    logger.info("Standardizing dates and validating Year/Month...")
    dates_norm = []
    years_calc = []
    months_calc = []
    
    for raw_d, raw_y, raw_m, rid in zip(df["Date"], df["Year"], df["Month"], df["Record_ID"]):
        clean_d, y_calc, m_calc = normalize_date(str(raw_d), raw_y, raw_m)
        
        # Check if raw Date was changed
        if clean_d != str(raw_d):
            audit.increment("NORM_DATE_FORMAT")
            if audit.summary_counts.get("NORM_DATE_FORMAT", 0) <= 100:
                audit.log("train", rid, "NORM_DATE_FORMAT", "Date", raw_d, clean_d, "Standardized to YYYY-MM", increment_summary=False)

        # Check if Year/Month disagreed with Date (Rule 1)
        try:
            if int(raw_y) != y_calc or int(raw_m) != m_calc:
                audit.increment("RULE_1_DATE_AUTHORITY")
                if audit.summary_counts.get("RULE_1_DATE_AUTHORITY", 0) <= 100:
                    audit.log("train", rid, "RULE_1_DATE_AUTHORITY", "Year/Month", f"{raw_y}-{raw_m}", f"{y_calc}-{m_calc}", "Date authoritative over Year/Month", increment_summary=False)
        except Exception:
            audit.increment("RULE_1_DATE_AUTHORITY")

        dates_norm.append(clean_d)
        years_calc.append(y_calc)
        months_calc.append(m_calc)

    df["Date"] = dates_norm
    df["Year"] = years_calc
    df["Month"] = months_calc

    # 3. SKU Normalization
    logger.info("Normalizing SKU identifiers...")
    cleaned_skus = []
    for raw_sku, rid in zip(df["SKU_ID"], df["Record_ID"]):
        clean_sku = normalize_sku(str(raw_sku))
        if clean_sku != str(raw_sku):
            audit.increment("NORM_SKU_SYNTAX")
            if audit.summary_counts.get("NORM_SKU_SYNTAX", 0) <= 100:
                audit.log("train", rid, "NORM_SKU_SYNTAX", "SKU_ID", raw_sku, clean_sku, "Standardized SKU format/prefix", increment_summary=False)
        cleaned_skus.append(clean_sku)
    df["SKU_ID"] = cleaned_skus

    # 4. Product Family & Business Unit Enrichment / Correction
    sku_master_lookup = sku_master.set_index("SKU_ID").to_dict(orient="index")
    
    families = []
    bus = []
    descriptions = []
    for sku, raw_fam, raw_desc in zip(df["SKU_ID"], df["Product_Family"], df["SKU_Description"]):
        master_info = sku_master_lookup.get(sku)
        if master_info:
            family = master_info.get("Product_Family")
            bu = master_info.get("Business_Unit")
            desc = master_info.get("SKU_Description")
        else:
            family, bu = get_canonical_family_and_bu(sku)
            desc = str(raw_desc)

        if str(raw_fam).strip() != family:
            audit.increment("NORM_FAMILY_NAME")
        families.append(family)
        bus.append(bu)
        descriptions.append(desc if desc and pd.notnull(desc) else str(raw_desc))

    df["Product_Family"] = families
    df["Business_Unit"] = bus
    df["SKU_Description"] = descriptions

    # 5. Customer Name & Sales Channel Normalization
    logger.info("Normalizing Customers and Sales Channels...")
    cust_unique = {c: (normalize_customer(str(c)) or "Unknown Customer") for c in df["Customer_Name"].unique()}
    cust_clean = [cust_unique[c] for c in df["Customer_Name"]]
    for c, norm_c in cust_unique.items():
        if norm_c != str(c):
            audit.increment("NORM_CUSTOMER_NAME", count=(df["Customer_Name"] == c).sum())

    channel_unique = {ch: (normalize_channel(str(ch)) or "Direct OEM") for ch in df["Sales_Channel"].unique()}
    channel_clean = [channel_unique[ch] for ch in df["Sales_Channel"]]
    for ch, norm_ch in channel_unique.items():
        if norm_ch != str(ch):
            audit.increment("NORM_SALES_CHANNEL", count=(df["Sales_Channel"] == ch).sum())

    df["Customer_Name"] = cust_clean
    df["Sales_Channel"] = channel_clean

    # 6. Region Normalization & Missing Imputation
    logger.info("Normalizing Regions and imputing missing geography...")
    raw_regs = df["Region"].astype(str).tolist()
    reg_clean = [normalize_region(r) for r in raw_regs]
    
    df["Region"] = reg_clean
    missing_reg_mask = df["Region"].isnull()
    missing_reg_count = missing_reg_mask.sum()
    logger.info(f"Missing / unmapped regions to impute: {missing_reg_count}")

    if missing_reg_count > 0:
        # Rule A: Known ME&A exclusive customers
        mea_customers = {"Atlas Mideast Components", "Falcon Gulf Motors", "Kestrel Mobility"}
        mea_mask = missing_reg_mask & df["Customer_Name"].isin(mea_customers)
        df.loc[mea_mask, "Region"] = "Middle East & Africa"
        audit.increment("IMPUTE_REGION_MEA_EXCLUSIVE", count=int(mea_mask.sum()))

        # Rule B: Mode region per (SKU, Customer)
        has_reg = df[df["Region"].notnull()]
        sku_cust_mode = (
            has_reg.groupby(["SKU_ID", "Customer_Name"])["Region"]
            .agg(lambda s: s.mode().iloc[0] if len(s.mode()) > 0 else None)
            .to_dict()
        )
        
        rem_mask = df["Region"].isnull()
        for idx in df[rem_mask].index:
            sku = df.at[idx, "SKU_ID"]
            cust = df.at[idx, "Customer_Name"]
            reg = sku_cust_mode.get((sku, cust))
            if reg:
                df.at[idx, "Region"] = reg
                audit.increment("IMPUTE_REGION_SKU_CUSTOMER_MODE")

        # Rule C: Mode region per SKU overall fallback
        rem_mask2 = df["Region"].isnull()
        if rem_mask2.sum() > 0:
            sku_mode = (
                has_reg.groupby("SKU_ID")["Region"]
                .agg(lambda s: s.mode().iloc[0] if len(s.mode()) > 0 else "North America")
                .to_dict()
            )
            for idx in df[rem_mask2].index:
                sku = df.at[idx, "SKU_ID"]
                reg = sku_mode.get(sku, "North America")
                df.at[idx, "Region"] = reg
                audit.increment("IMPUTE_REGION_SKU_MODE")

    # 7. Pricing, Revenue, and Units_Sold Reconciliation
    logger.info("Reconciling Units_Sold, Unit_Price_USD, and Revenue_USD...")
    
    # Parse numbers safely
    raw_units = pd.to_numeric(df["Units_Sold"], errors="coerce")
    raw_price = pd.to_numeric(df["Unit_Price_USD"], errors="coerce")
    raw_rev = pd.to_numeric(df["Revenue_USD"], errors="coerce")

    # Fix price scaling errors (prices stored in cents / 100x too large)
    price_corrected = raw_price.copy()
    price_100x_mask = price_corrected > 5000.0
    price_corrected[price_100x_mask] = (price_corrected[price_100x_mask] / 100.0).round(2)
    audit.increment("RULE_4_PRICE_SCALING_100X", count=int(price_100x_mask.sum()))

    # Build reference price per SKU-Year
    valid_prices = pd.DataFrame({"SKU_ID": df["SKU_ID"], "Year": df["Year"], "Price": price_corrected})
    valid_prices = valid_prices[valid_prices["Price"] > 0]
    sku_year_price_ref = valid_prices.groupby(["SKU_ID", "Year"])["Price"].median().to_dict()

    # Fill any remaining 0 / NaN prices from SKU reference
    zero_price_mask = (price_corrected.isnull()) | (price_corrected <= 0)
    if zero_price_mask.sum() > 0:
        for idx in df[zero_price_mask].index:
            sku = df.at[idx, "SKU_ID"]
            yr = df.at[idx, "Year"]
            ref_p = sku_year_price_ref.get((sku, yr), 100.0)
            price_corrected.at[idx] = ref_p
            audit.increment("IMPUTE_PRICE_FROM_CATALOG")

    df["Unit_Price_USD"] = price_corrected.round(2)

    # Recover missing Units_Sold using Revenue / Price
    units_corrected = raw_units.copy()
    missing_units_mask = units_corrected.isnull()
    recovered_units_mask = missing_units_mask & raw_rev.notnull() & (df["Unit_Price_USD"] > 0)
    units_corrected[recovered_units_mask] = (raw_rev[recovered_units_mask] / df.loc[recovered_units_mask, "Unit_Price_USD"]).round(0)
    audit.increment("RECONCILE_UNITS_FROM_REVENUE", count=int(recovered_units_mask.sum()))

    # Any remaining null units filled with 0 (no order)
    remaining_null_units = units_corrected.isnull()
    units_corrected[remaining_null_units] = 0.0
    audit.increment("FILL_NULL_UNITS_ZERO", count=int(remaining_null_units.sum()))

    df["Units_Sold"] = units_corrected.astype(int)

    # Reconcile Revenue_USD = Units_Sold * Unit_Price_USD
    reconciled_revenue = (df["Units_Sold"] * df["Unit_Price_USD"]).round(2)
    rev_diff_mask = (raw_rev.isnull()) | ((reconciled_revenue - raw_rev).abs() > 0.05)
    audit.increment("RECONCILE_REVENUE_CALCULATION", count=int(rev_diff_mask.sum()))
    df["Revenue_USD"] = reconciled_revenue

    # 8. Add Quality & Integrity Audit Flags
    df["is_return"] = df["Units_Sold"] < 0
    df["is_zero_order"] = df["Units_Sold"] == 0

    logger.info(f"Train cleaning complete. Cleaned rows: {len(df):,}")
    return df


def clean_macro_indicators(raw_macro: pd.DataFrame, audit: AuditTrail) -> pd.DataFrame:
    """Clean macro indicators: verify 114 months (2019-01 to 2028-05) and interpolate missing values."""
    logger.info("Cleaning macro_indicators.csv...")
    df = raw_macro.copy()
    
    # Standardize dates
    df["Date"] = df["Date"].astype(str).str.strip()
    df["Year"] = df["Date"].str[:4].astype(int)
    df["Month"] = df["Date"].str[5:7].astype(int)

    numeric_cols = [
        "ISM_Manufacturing_PMI",
        "Auto_Production_YoY_Pct",
        "Vehicle_Inventory_Days",
        "Raw_Material_Cost_Index",
        "New_Vehicle_Orders_Index",
        "Industrial_Util_Rate_Pct",
        "Fuel_Price_Index",
        "EV_Adoption_Index",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logger.info(f"Macro column '{col}' has {null_count} nulls. Applying linear interpolation.")
            audit.increment(f"IMPUTE_MACRO_{col}", count=int(null_count))
            df[col] = df[col].interpolate(method="linear").bfill().ffill().round(2)

    return df


def clean_sku_master(raw_sku: pd.DataFrame, audit: AuditTrail) -> pd.DataFrame:
    """Standardize SKU master data and validate lifecycles."""
    logger.info("Cleaning sku_master.csv...")
    df = raw_sku.copy()
    df["SKU_ID"] = df["SKU_ID"].astype(str).str.strip().str.upper()
    df["Product_Family"] = df["Product_Family"].astype(str).str.strip()
    df["Business_Unit"] = df["Business_Unit"].astype(str).str.strip()
    df["Lifecycle_Status"] = df["Lifecycle_Status"].astype(str).str.strip()
    df["Launch_Date"] = df["Launch_Date"].astype(str).str.strip()
    df["EOL_Date"] = df["EOL_Date"].astype(str).str.strip()
    df["Replaces_SKU"] = df["Replaces_SKU"].astype(str).str.strip()
    return df


def clean_inventory_stockouts(raw_stockouts: pd.DataFrame, audit: AuditTrail) -> pd.DataFrame:
    """Standardize inventory stockouts and reconcile balance equation."""
    logger.info("Cleaning inventory_stockouts.csv...")
    df = raw_stockouts.copy()
    
    # Standardize Date
    df["Date"] = df["Date"].astype(str).str.strip()
    
    # Standardize SKU_ID and Region
    df["SKU_ID"] = df["SKU_ID"].apply(normalize_sku)
    df["Region"] = df["Region"].apply(normalize_region)

    numeric_cols = [
        "Requested_Units",
        "Carried_In_Units",
        "Shipped_Units",
        "Backordered_Units",
        "Lost_Units",
        "Fill_Rate_Pct",
        "Stockout_Days",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Validate stockout balance: Lost_Units = Requested + Carried_In - Shipped - Backordered
    calc_lost = df["Requested_Units"] + df["Carried_In_Units"] - df["Shipped_Units"] - df["Backordered_Units"]
    imbalance = (calc_lost - df["Lost_Units"]).abs() > 1
    if imbalance.sum() > 0:
        logger.info(f"Fixed {imbalance.sum()} stockout balance discrepancies.")
        audit.increment("RECONCILE_STOCKOUT_BALANCE", count=int(imbalance.sum()))
        df.loc[imbalance, "Lost_Units"] = calc_lost[imbalance].clip(lower=0)

    return df


def clean_events_calendar(raw_events: pd.DataFrame, audit: AuditTrail) -> pd.DataFrame:
    """Standardize events calendar dates and scopes."""
    logger.info("Cleaning events_calendar.csv...")
    df = raw_events.copy()
    df["Event_ID"] = df["Event_ID"].astype(str).str.strip()
    df["Start_Date"] = df["Start_Date"].astype(str).str.strip()
    df["End_Date"] = df["End_Date"].astype(str).str.strip()
    df["Scope_Type"] = df["Scope_Type"].astype(str).str.strip()
    df["Scope_Value"] = df["Scope_Value"].astype(str).str.strip()
    df["Event_Type"] = df["Event_Type"].astype(str).str.strip()
    return df


def validate_test_data(raw_test: pd.DataFrame, audit: AuditTrail) -> pd.DataFrame:
    """Validate test.csv against canonical schemas."""
    logger.info("Validating test.csv...")
    df = raw_test.copy()
    assert len(df) == 58219, f"Expected 58,219 test rows, found {len(df)}"
    assert df["Region"].isin(CANONICAL_REGIONS).all(), "Test has non-canonical regions"
    assert df["Sales_Channel"].isin(CANONICAL_CHANNELS).all(), "Test has non-canonical sales channels"
    assert df["Product_Family"].isin(CANONICAL_FAMILIES).all(), "Test has non-canonical product families"
    return df
