"""Aggregator to create one clean row per Date-SKU-Region and handle missing rows vs zeros."""

import logging
import pandas as pd
import numpy as np
from itertools import product
from src.config import CANONICAL_REGIONS

logger = logging.getLogger(__name__)


def aggregate_to_date_sku_region(cleaned_train: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cleaned transaction data to one clean row per Date-SKU-Region.
    
    Workstream 1 Core:
    'One clean row per Date-SKU-Region'
    """
    logger.info("Aggregating cleaned transactions to Date-SKU-Region...")

    # Group by Date, SKU_ID, Region
    grouped = (
        cleaned_train.groupby(["Date", "SKU_ID", "Region"], as_index=False)
        .agg(
            Units_Sold=("Units_Sold", "sum"),
            Revenue_USD=("Revenue_USD", "sum"),
            Transaction_Count=("Record_ID", "count"),
            Return_Count=("is_return", "sum"),
            Zero_Order_Count=("is_zero_order", "sum"),
        )
    )

    # Derive Year and Month
    grouped["Year"] = grouped["Date"].str[:4].astype(int)
    grouped["Month"] = grouped["Date"].str[5:7].astype(int)

    # Compute effective Unit_Price_USD
    grouped["Unit_Price_USD"] = np.where(
        grouped["Units_Sold"] > 0,
        (grouped["Revenue_USD"] / grouped["Units_Sold"]).round(2),
        0.0,
    )

    # Join metadata from sku_master
    sku_meta = sku_master[["SKU_ID", "Product_Family", "Business_Unit", "SKU_Description"]].drop_duplicates()
    merged = grouped.merge(sku_meta, on="SKU_ID", how="left")

    # If any price is 0, lookup from cleaned_train reference price
    ref_prices = (
        cleaned_train[cleaned_train["Unit_Price_USD"] > 0]
        .groupby(["SKU_ID", "Year"])["Unit_Price_USD"]
        .median()
        .to_dict()
    )
    
    zero_price_mask = merged["Unit_Price_USD"] <= 0
    if zero_price_mask.sum() > 0:
        for idx in merged[zero_price_mask].index:
            sku = merged.at[idx, "SKU_ID"]
            yr = merged.at[idx, "Year"]
            merged.at[idx, "Unit_Price_USD"] = ref_prices.get((sku, yr), 100.0)

    # Ensure clean non-negative net units for physical sales
    merged["Units_Sold_Net"] = merged["Units_Sold"]
    merged["Units_Sold"] = merged["Units_Sold"].clip(lower=0)

    logger.info(f"Aggregated monthly dataset shape: {merged.shape}")
    return merged


def build_regularized_panel_grid(
    monthly_df: pd.DataFrame,
    sku_master: pd.DataFrame,
    start_date: str = "2019-01",
    end_date: str = "2026-10",
) -> pd.DataFrame:
    """Build a complete balanced panel grid (Date x SKU x Region) respecting product lifecycles.
    
    Workstream 1 Advanced:
    'Handle missing rows vs zeros'
    """
    logger.info("Constructing regularized panel grid to distinguish missing rows from zeros...")

    # Generate all monthly dates
    dates = pd.date_range(start=f"{start_date}-01", end=f"{end_date}-01", freq="MS").strftime("%Y-%m").tolist()
    
    # Active SKUs
    skus = sku_master["SKU_ID"].unique().tolist()
    regions = CANONICAL_REGIONS

    # Build full grid
    grid = pd.DataFrame(product(dates, skus, regions), columns=["Date", "SKU_ID", "Region"])
    grid["Year"] = grid["Date"].str[:4].astype(int)
    grid["Month"] = grid["Date"].str[5:7].astype(int)

    # Merge sku lifecycle rules (Launch_Date, EOL_Date)
    sku_life = sku_master[["SKU_ID", "Product_Family", "Business_Unit", "Launch_Date", "EOL_Date"]].drop_duplicates()
    grid = grid.merge(sku_life, on="SKU_ID", how="left")

    # Filter out dates before launch or after EOL (Rule 5)
    valid_mask = True
    if "Launch_Date" in grid.columns:
        valid_mask = valid_mask & ((grid["Launch_Date"].isnull()) | (grid["Launch_Date"] == "") | (grid["Date"] >= grid["Launch_Date"]))
    if "EOL_Date" in grid.columns:
        valid_mask = valid_mask & ((grid["EOL_Date"].isnull()) | (grid["EOL_Date"] == "") | (grid["Date"] <= grid["EOL_Date"]))

    grid_active = grid[valid_mask].copy()

    # Merge monthly transactions
    tx_cols = ["Date", "SKU_ID", "Region", "Units_Sold", "Revenue_USD", "Unit_Price_USD", "Transaction_Count", "Zero_Order_Count"]
    merged = grid_active.merge(monthly_df[tx_cols], on=["Date", "SKU_ID", "Region"], how="left")

    # Distinguish:
    # 1. Had transactions: Transaction_Count > 0
    # 2. Had explicit zero order: Zero_Order_Count > 0 and Units_Sold == 0
    # 3. Missing row in ERP: Transaction_Count is null -> filled with 0 demand, flagged as is_missing_row
    merged["is_missing_row"] = merged["Transaction_Count"].isnull()
    merged["Units_Sold"] = merged["Units_Sold"].fillna(0).astype(int)
    merged["Revenue_USD"] = merged["Revenue_USD"].fillna(0.0).round(2)
    merged["Transaction_Count"] = merged["Transaction_Count"].fillna(0).astype(int)
    merged["Zero_Order_Count"] = merged["Zero_Order_Count"].fillna(0).astype(int)

    logger.info(f"Regularized panel grid constructed: {len(merged):,} rows. Missing rows resolved to zero: {merged['is_missing_row'].sum():,}")
    return merged
