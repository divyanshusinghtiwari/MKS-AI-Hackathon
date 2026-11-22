"""Unconstrained Demand Reconstruction Engine for Celeris Automobili Industrial."""

import logging
from pathlib import Path
import pandas as pd
import numpy as np

from src.config import CLEANED_DATA_DIR, CANONICAL_REGIONS

logger = logging.getLogger(__name__)


def reconstruct_unconstrained_demand(
    monthly_sales_path: Path = CLEANED_DATA_DIR / "train_monthly_cleaned.parquet",
    stockouts_path: Path = CLEANED_DATA_DIR / "inventory_stockouts_cleaned.csv",
    sku_master_path: Path = CLEANED_DATA_DIR / "sku_master_cleaned.csv",
    output_path: Path = CLEANED_DATA_DIR / "demand_reconstructed.parquet",
) -> pd.DataFrame:
    """Integrate inventory stockouts with cleaned monthly sales to reconstruct true unconstrained market demand.
    
    Workstream 2 Advanced & Rule 7:
    - Verifies balance: Requested + Carried_In = Shipped + Backordered + Lost
    - Prevents double-counting: Requested_Units isolates true new demand for this month
    - Preserves original shipped quantities in Units_Shipped
    - Produces demand_reconstructed.parquet
    """
    logger.info("Loading cleaned monthly sales, stockouts, and SKU master...")
    monthly = pd.read_parquet(monthly_sales_path)
    stockouts = pd.read_csv(stockouts_path)
    sku_master = pd.read_csv(sku_master_path)

    # 1. Verify Stockout Balance Equation
    lhs = stockouts["Requested_Units"] + stockouts["Carried_In_Units"]
    rhs = stockouts["Shipped_Units"] + stockouts["Backordered_Units"] + stockouts["Lost_Units"]
    balance_diff = (lhs - rhs).abs()
    assert (balance_diff > 1).sum() == 0, f"Found {balance_diff.sum()} stockout balance violations!"
    logger.info("Stockout balance equation verified: Requested + Carried_In == Shipped + Backordered + Lost.")

    # 2. Outer merge to capture both active shipments and 100% stockout months
    logger.info("Merging monthly sales with inventory stockout records...")
    stockout_cols = [
        "Date",
        "SKU_ID",
        "Region",
        "Requested_Units",
        "Carried_In_Units",
        "Shipped_Units",
        "Backordered_Units",
        "Lost_Units",
        "Fill_Rate_Pct",
        "Stockout_Days",
        "Reason",
    ]
    merged = monthly.merge(stockouts[stockout_cols], on=["Date", "SKU_ID", "Region"], how="outer")

    # 3. Identify Stockout Months
    merged["is_stockout_month"] = merged["Requested_Units"].notnull()

    # 4. Units_Shipped: Shipped quantity (preserving original train units)
    # If in train, use train Units_Sold; else use stockouts Shipped_Units
    merged["Units_Shipped"] = merged["Units_Sold"].fillna(merged["Shipped_Units"]).fillna(0).astype(int)

    # 5. Units_Unconstrained:
    # If stockout month: Requested_Units (true unconstrained demand asked by customers this month)
    # Note: Carried_In_Units was backordered from the prior month; using Requested_Units strictly avoids double counting!
    # If non-stockout month: Units_Shipped
    merged["Units_Unconstrained"] = (
        merged["Requested_Units"].fillna(merged["Units_Shipped"]).astype(int)
    )

    # Fill stockout metrics for non-stockout months
    merged["Carried_In_Units"] = merged["Carried_In_Units"].fillna(0).astype(int)
    merged["Backordered_Units"] = merged["Backordered_Units"].fillna(0).astype(int)
    merged["Lost_Units"] = merged["Lost_Units"].fillna(0).astype(int)
    merged["Fill_Rate_Pct"] = merged["Fill_Rate_Pct"].fillna(100.0).round(1)
    merged["Stockout_Days"] = merged["Stockout_Days"].fillna(0).astype(int)
    merged["Stockout_Reason"] = merged["Reason"].fillna("None")
    merged = merged.drop(columns=["Reason", "Shipped_Units", "Requested_Units"], errors="ignore")

    # 6. Fill missing metadata for any pure stockout rows (27 rows)
    sku_lookup = sku_master.set_index("SKU_ID").to_dict(orient="index")
    
    # Fill Year and Month if null
    merged["Year"] = merged["Date"].str[:4].astype(int)
    merged["Month"] = merged["Date"].str[5:7].astype(int)

    # Price lookup reference
    price_ref = (
        monthly[monthly["Unit_Price_USD"] > 0]
        .groupby(["SKU_ID", "Year"])["Unit_Price_USD"]
        .median()
        .to_dict()
    )

    for idx in merged[merged["Product_Family"].isnull()].index:
        sku = merged.at[idx, "SKU_ID"]
        yr = merged.at[idx, "Year"]
        info = sku_lookup.get(sku, {})
        merged.at[idx, "Product_Family"] = info.get("Product_Family", "Unknown")
        merged.at[idx, "Business_Unit"] = info.get("Business_Unit", "Unknown")
        merged.at[idx, "SKU_Description"] = info.get("SKU_Description", "")
        merged.at[idx, "Unit_Price_USD"] = price_ref.get((sku, yr), 100.0)

    # 7. Compute Revenues
    merged["Unit_Price_USD"] = merged["Unit_Price_USD"].fillna(100.0).round(2)
    merged["Revenue_Shipped"] = (merged["Units_Shipped"] * merged["Unit_Price_USD"]).round(2)
    merged["Revenue_Unconstrained"] = (merged["Units_Unconstrained"] * merged["Unit_Price_USD"]).round(2)

    # 8. Sort and Organize Columns
    cols_order = [
        "Date",
        "Year",
        "Month",
        "SKU_ID",
        "Region",
        "Product_Family",
        "Business_Unit",
        "SKU_Description",
        "Units_Shipped",
        "Units_Unconstrained",
        "Unit_Price_USD",
        "Revenue_Shipped",
        "Revenue_Unconstrained",
        "is_stockout_month",
        "Stockout_Reason",
        "Fill_Rate_Pct",
        "Stockout_Days",
        "Carried_In_Units",
        "Backordered_Units",
        "Lost_Units",
    ]
    # Keep any additional columns
    remaining_cols = [c for c in merged.columns if c not in cols_order]
    final_df = merged[cols_order + remaining_cols].sort_values(by=["Date", "SKU_ID", "Region"]).reset_index(drop=True)

    # Export to Parquet
    logger.info(f"Saving reconstructed demand dataset to {output_path} ({len(final_df):,} rows)...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(output_path, index=False)

    shipped_sum = final_df["Units_Shipped"].sum()
    uncon_sum = final_df["Units_Unconstrained"].sum()
    lost_sum = final_df["Lost_Units"].sum()
    logger.info(
        f"Reconstruction Complete:\n"
        f"  Total Rows: {len(final_df):,}\n"
        f"  Total Shipped: {shipped_sum:,} units\n"
        f"  Total Unconstrained: {uncon_sum:,} units\n"
        f"  Recovered Demand Gap: {uncon_sum - shipped_sum:,} units (Lost Units: {lost_sum:,})"
    )
    return final_df
