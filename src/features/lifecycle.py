"""Product lifecycle, launch/EOL tenure, replacement mappings, and customer ordering features."""

import pandas as pd
import numpy as np


def create_product_and_business_features(
    df: pd.DataFrame,
    sku_master_df: pd.DataFrame,
    raw_train_cleaned_df: pd.DataFrame,
) -> pd.DataFrame:
    """Engineer product lifecycle, launch/EOL status, replacement SKU links, and ordering features.
    
    Task 5:
    - Product family & business unit
    - Product lifecycle status (Active, Discontinued, EOL Announced, Planned Launch)
    - Months since launch (product maturity)
    - Months until EOL (phase-out window)
    - is_pre_launch, is_post_eol flags (strict Rule 5 compliance)
    - Replaces_SKU relationships & predecessor transfer indicators
    - Powertrain application (EV, ICE, Universal)
    - Historical stockout vulnerability metrics
    - Historical active customer count per SKU-Region
    """
    out = df.copy()

    # Join master product attributes if not already present
    master_cols = [
        "SKU_ID",
        "Size_Class",
        "Powertrain_Application",
        "Launch_Date",
        "EOL_Date",
        "Replaces_SKU",
        "Lifecycle_Status",
    ]
    # Drop existing overlap to avoid duplicate columns
    cols_to_join = [c for c in master_cols if c not in out.columns or c == "SKU_ID"]
    if len(cols_to_join) > 1:
        out = out.merge(sku_master_df[cols_to_join], on="SKU_ID", how="left")

    # Helper function to convert YYYY-MM to integer month index
    def to_month_index(date_str):
        if not isinstance(date_str, str) or len(date_str) < 7:
            return None
        try:
            y, m = int(date_str[:4]), int(date_str[5:7])
            return y * 12 + m
        except Exception:
            return None

    out["date_m_idx"] = out["Date"].apply(to_month_index)
    out["launch_m_idx"] = out["Launch_Date"].apply(to_month_index)
    out["eol_m_idx"] = out["EOL_Date"].apply(to_month_index)

    # 1. Product Maturity: Months Since Launch
    out["months_since_launch"] = np.where(
        out["launch_m_idx"].notnull(),
        (out["date_m_idx"] - out["launch_m_idx"]).clip(lower=0),
        120,  # Default mature product if no launch date specified
    ).astype(int)

    # 2. Phase-out Window: Months Until EOL
    out["months_until_eol"] = np.where(
        out["eol_m_idx"].notnull(),
        (out["eol_m_idx"] - out["date_m_idx"]),
        999,  # No EOL planned
    ).astype(int)

    # 3. Strict Rule 5 Boundaries
    out["is_pre_launch"] = np.where(
        out["launch_m_idx"].notnull() & (out["date_m_idx"] < out["launch_m_idx"]),
        1,
        0,
    )
    out["is_post_eol"] = np.where(
        out["eol_m_idx"].notnull() & (out["date_m_idx"] > out["eol_m_idx"]),
        1,
        0,
    )

    # 4. Replacement SKU relationships
    out["has_replacement_sku"] = (
        out["Replaces_SKU"].notnull() & (out["Replaces_SKU"] != "")
    ).astype(int)

    # 5. Historical Stockout Frequency per SKU-Region
    if "is_stockout_month" in out.columns:
        stockout_freq = (
            out.groupby(["SKU_ID", "Region"])["is_stockout_month"]
            .mean()
            .to_dict()
        )
        out["historical_stockout_rate"] = out.set_index(["SKU_ID", "Region"]).index.map(stockout_freq).fillna(0.0).round(3)
    else:
        out["historical_stockout_rate"] = 0.0

    # 6. Customer Ordering Breadth
    # Calculate historical customer count per SKU-Region from raw transaction table
    cust_breadth = (
        raw_train_cleaned_df[raw_train_cleaned_df["Units_Sold"] > 0]
        .groupby(["SKU_ID", "Region"])["Customer_Name"]
        .nunique()
        .to_dict()
    )
    out["historical_active_customers"] = (
        out.set_index(["SKU_ID", "Region"]).index.map(cust_breadth).fillna(1).astype(int)
    )

    # Clean temporary helper columns
    out = out.drop(columns=["date_m_idx", "launch_m_idx", "eol_m_idx"], errors="ignore")
    return out
