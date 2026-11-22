"""Build leakage-free features for the 19-month test horizon (2026-11 to 2028-05)."""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Predecessor mapping for cold start launch SKUs
PREDECESSOR_MAP = {
    "PMP-020": "PMP-003",
    "PTC-029": "PTC-005",
    "THM-012": "THM-001",
}


def build_test_features(
    test_df: pd.DataFrame,
    features_hist: pd.DataFrame,
    macro_df: pd.DataFrame,
    sku_master_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate all required features for test.csv without future information leakage."""
    logger.info("Constructing test feature set for 19-month forecast horizon...")
    test_feat = test_df.copy()

    # 1. Calendar & Cyclical
    test_feat["Quarter"] = ((test_feat["Month"] - 1) // 3) + 1
    test_feat["month_sin"] = np.sin(2 * np.pi * test_feat["Month"] / 12)
    test_feat["month_cos"] = np.cos(2 * np.pi * test_feat["Month"] / 12)
    test_feat["quarter_sin"] = np.sin(2 * np.pi * test_feat["Quarter"] / 4)
    test_feat["quarter_cos"] = np.cos(2 * np.pi * test_feat["Quarter"] / 4)
    test_feat["is_europe_summer_shutdown"] = (test_feat["Month"] == 8).astype(int)
    test_feat["is_golden_week_month"] = (test_feat["Month"] == 10).astype(int)
    test_feat["is_cny_month"] = test_feat["Month"].isin([1, 2]).astype(int)
    test_feat["is_year_end_holiday"] = (test_feat["Month"] == 12).astype(int)
    test_feat["is_pre_price_hike_month"] = (test_feat["Month"] == 12).astype(int)
    test_feat["is_post_price_hike_month"] = (test_feat["Month"] == 1).astype(int)

    # 2. Macroeconomic Indicators (contemporaneous + lags)
    macro_sorted = macro_df.sort_values("Date").copy()
    for col in [
        "ISM_Manufacturing_PMI",
        "Auto_Production_YoY_Pct",
        "Vehicle_Inventory_Days",
        "Raw_Material_Cost_Index",
        "New_Vehicle_Orders_Index",
        "Industrial_Util_Rate_Pct",
        "Fuel_Price_Index",
        "EV_Adoption_Index",
    ]:
        macro_sorted[f"{col}_lag1"] = macro_sorted[col].shift(1)
        macro_sorted[f"{col}_lag2"] = macro_sorted[col].shift(2)
        macro_sorted[f"{col}_lag3"] = macro_sorted[col].shift(3)

    macro_cols = [c for c in macro_sorted.columns if c not in ["Year", "Month"]]
    test_feat = test_feat.merge(macro_sorted[macro_cols], on="Date", how="left")

    # 3. Series-level Intermittency & Historical Baselines
    series_stats = (
        features_hist.groupby(["SKU_ID", "Region"])
        .agg({
            "adi": "last",
            "cv2": "last",
            "intermittency_class": "last",
            "croston_baseline_rate": "last",
            "sba_baseline_rate": "last",
            "historical_stockout_rate": "last",
            "historical_active_customers": "last",
        })
        .reset_index()
    )

    test_feat = test_feat.merge(series_stats, on=["SKU_ID", "Region"], how="left")

    # Impute cold-start SKUs from predecessors
    for sku, pred_sku in PREDECESSOR_MAP.items():
        mask = test_feat["SKU_ID"] == sku
        if mask.sum() > 0:
            pred_stats = series_stats[series_stats["SKU_ID"] == pred_sku].set_index("Region")
            for reg in test_feat.loc[mask, "Region"].unique():
                if reg in pred_stats.index:
                    row = pred_stats.loc[reg]
                    for col in [
                        "adi",
                        "cv2",
                        "intermittency_class",
                        "croston_baseline_rate",
                        "sba_baseline_rate",
                        "historical_stockout_rate",
                        "historical_active_customers",
                    ]:
                        test_feat.loc[mask & (test_feat["Region"] == reg), col] = row[col]

    # Fill default values for any missing series stats
    test_feat["adi"] = test_feat["adi"].fillna(1.0)
    test_feat["cv2"] = test_feat["cv2"].fillna(0.2)
    test_feat["intermittency_class"] = test_feat["intermittency_class"].fillna("Smooth")
    test_feat["croston_baseline_rate"] = test_feat["croston_baseline_rate"].fillna(0.0)
    test_feat["sba_baseline_rate"] = test_feat["sba_baseline_rate"].fillna(0.0)
    test_feat["historical_stockout_rate"] = test_feat["historical_stockout_rate"].fillna(0.0)
    test_feat["historical_active_customers"] = test_feat["historical_active_customers"].fillna(1.0)

    # 4. Product Master & Lifecycle Features
    sku_feat = sku_master_df[
        ["SKU_ID", "Powertrain_Application", "Launch_Date", "EOL_Date", "Replaces_SKU"]
    ].drop_duplicates()
    test_feat = test_feat.merge(sku_feat, on="SKU_ID", how="left")

    def diff_months(d1: str, d2: str) -> int:
        y1, m1 = int(d1[:4]), int(d1[5:7])
        y2, m2 = int(d2[:4]), int(d2[5:7])
        return (y1 - y2) * 12 + (m1 - m2)

    test_feat["months_since_launch"] = [
        diff_months(d, l) if pd.notnull(l) else 999.0
        for d, l in zip(test_feat["Date"], test_feat["Launch_Date"])
    ]
    test_feat["months_until_eol"] = [
        diff_months(e, d) if pd.notnull(e) else 999.0
        for d, e in zip(test_feat["Date"], test_feat["EOL_Date"])
    ]
    test_feat["is_pre_launch"] = (test_feat["Date"] < test_feat["Launch_Date"]).astype(int)
    test_feat["is_post_eol"] = (test_feat["Date"] > test_feat["EOL_Date"]).astype(int)
    test_feat["has_replacement_sku"] = test_feat["Replaces_SKU"].notnull().astype(int)

    # 5. Seasonal Anchor: lag_12 and rolling_mean_12
    seasonal_val = (
        features_hist.groupby(["SKU_ID", "Region", "Month"])["Units_Unconstrained"]
        .last()
        .to_dict()
    )
    overall_mean = (
        features_hist.groupby(["SKU_ID", "Region"])["Units_Unconstrained"]
        .mean()
        .to_dict()
    )

    # Map predecessor seasonal patterns to cold-start SKUs
    for (pred_sku, reg, m), val in list(seasonal_val.items()):
        for launch_sku, p_sku in PREDECESSOR_MAP.items():
            if pred_sku == p_sku:
                seasonal_val[(launch_sku, reg, m)] = val

    for (pred_sku, reg), val in list(overall_mean.items()):
        for launch_sku, p_sku in PREDECESSOR_MAP.items():
            if pred_sku == p_sku:
                overall_mean[(launch_sku, reg)] = val

    lag12 = []
    roll12 = []
    for idx, r in test_feat.iterrows():
        s, reg, m = r["SKU_ID"], r["Region"], r["Month"]
        l_val = seasonal_val.get((s, reg, m))
        m_val = overall_mean.get((s, reg))
        lag12.append(l_val if l_val is not None else (m_val if m_val is not None else 0.0))
        roll12.append(m_val if m_val is not None else 0.0)

    test_feat["lag_12"] = lag12
    test_feat["rolling_mean_12"] = roll12

    logger.info(f"Test feature construction complete: {test_feat.shape[0]:,} rows, {test_feat.shape[1]:,} features.")
    return test_feat
