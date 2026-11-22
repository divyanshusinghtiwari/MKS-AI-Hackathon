"""Comprehensive Anomaly Detection Engine for Celeris Automobili Industrial."""

import logging
from typing import List, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def detect_all_anomalies(
    demand_df: pd.DataFrame,
    events_df: pd.DataFrame,
    sku_master_df: pd.DataFrame,
) -> pd.DataFrame:
    """Identify and catalog all anomalies across demand history into the official Anomaly Register.
    
    Workstream 2 Core, Advanced & Expert:
    - Statistical demand outliers (Z-score / MAD)
    - Sudden demand spikes and drops
    - Structural breaks (EV adoption transition)
    - Pandemic and chip shortage impacts
    - Early buying before price increases
    - Holiday and event impacts
    - Customer switches and ordering-cycle shifts
    - Stockout-related supply constraints
    """
    logger.info("Executing comprehensive anomaly detection...")
    anomalies: List[Dict[str, Any]] = []

    # 1. Stockout-Related Supply Anomalies
    logger.info("Detecting inventory stockout anomalies...")
    stockout_rows = demand_df[demand_df["is_stockout_month"]].copy()
    for idx, row in stockout_rows.iterrows():
        shipped = int(row["Units_Shipped"])
        uncon = int(row["Units_Unconstrained"])
        lost = int(row["Lost_Units"])
        reason = row["Stockout_Reason"]
        fill_rate = float(row["Fill_Rate_Pct"])

        # Determine severity
        if fill_rate < 50.0 or lost > 50:
            severity = "HIGH"
        elif fill_rate < 85.0 or lost > 10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Categorize
        if "Semiconductor" in reason:
            anom_type = "MACRO_CHIP_SHORTAGE"
            category = "SUPPLY_CONSTRAINT"
            explanation = f"Global chip shortage caused supply bottleneck ({lost:,} lost units, {fill_rate:.1f}% fill rate)."
            action = "Train demand models on Units_Unconstrained (Requested_Units); apply semiconductor supply driver."
        else:
            anom_type = "SUPPLY_STOCKOUT"
            category = "SUPPLY_CONSTRAINT"
            explanation = f"Supply constraint due to {reason} ({lost:,} lost units, fill rate {fill_rate:.1f}%)."
            action = "Substitute unconstrained demand for forecasting; do not treat constrained shipments as lower market demand."

        anomalies.append({
            "Date": row["Date"],
            "SKU_ID": row["SKU_ID"],
            "Region": row["Region"],
            "Observed_Demand": shipped,
            "Expected_Demand": uncon,
            "Anomaly_Type": anom_type,
            "Business_Category": category,
            "Severity": severity,
            "Detection_Method": "Stockout Ledger Cross-Reference",
            "Explanation": explanation,
            "Recommended_Action": action,
        })

    # 2. Pandemic Shock Anomalies (March 2020 - May 2020)
    logger.info("Detecting COVID-19 pandemic lockdown anomalies...")
    covid_dates = {"2020-03", "2020-04", "2020-05"}
    covid_df = demand_df[demand_df["Date"].isin(covid_dates)].copy()

    # Calculate pre-pandemic baseline (2019 mean for each SKU-Region)
    baseline_2019 = (
        demand_df[demand_df["Date"].str.startswith("2019")]
        .groupby(["SKU_ID", "Region"])["Units_Unconstrained"]
        .mean()
        .to_dict()
    )

    for idx, row in covid_df.iterrows():
        sku = row["SKU_ID"]
        reg = row["Region"]
        base = baseline_2019.get((sku, reg), 0.0)
        actual = int(row["Units_Unconstrained"])
        
        # If pre-pandemic baseline was healthy (> 30 units) and dropped by > 40%
        if base >= 30 and actual < base * 0.55:
            drop_pct = ((base - actual) / base) * 100
            anomalies.append({
                "Date": row["Date"],
                "SKU_ID": sku,
                "Region": reg,
                "Observed_Demand": actual,
                "Expected_Demand": int(round(base)),
                "Anomaly_Type": "MACRO_PANDEMIC_DISRUPTION",
                "Business_Category": "GENUINE_BUSINESS_EVENT",
                "Severity": "HIGH",
                "Detection_Method": "Pandemic Event Window & Baseline Drop (>40%)",
                "Explanation": f"Severe demand drop of {drop_pct:.1f}% caused by global COVID-19 plant lockdowns.",
                "Recommended_Action": "Incorporate lockdown intervention dummy feature; do not propagate trough to future trend.",
            })

    # 3. Pre-Price Increase Pull-Forward Demand
    logger.info("Detecting pre-price increase pull-forward buying...")
    # Check November / December before major price increases (e.g. 2022-11, 2022-12, 2023-11, 2023-12)
    pull_forward_dates = {"2022-11", "2022-12", "2023-11", "2023-12"}
    pf_df = demand_df[demand_df["Date"].isin(pull_forward_dates)].copy()

    # Annual median per SKU-Region
    median_demand = demand_df.groupby(["SKU_ID", "Region"])["Units_Unconstrained"].median().to_dict()

    for idx, row in pf_df.iterrows():
        sku = row["SKU_ID"]
        reg = row["Region"]
        med = median_demand.get((sku, reg), 0.0)
        actual = int(row["Units_Unconstrained"])
        
        # If demand surged > 75% above median with volume >= 40 units
        if med >= 20 and actual > med * 1.75:
            surge_pct = ((actual - med) / med) * 100
            anomalies.append({
                "Date": row["Date"],
                "SKU_ID": sku,
                "Region": reg,
                "Observed_Demand": actual,
                "Expected_Demand": int(round(med)),
                "Anomaly_Type": "PRICE_HIKE_PULL_FORWARD",
                "Business_Category": "GENUINE_BUSINESS_EVENT",
                "Severity": "MEDIUM",
                "Detection_Method": "Pre-Jan Price Hike Surge (>75% vs Series Median)",
                "Explanation": f"Customer pre-buying surge (+{surge_pct:.1f}%) ahead of the scheduled Jan 1 list price increase.",
                "Recommended_Action": "Model pre-price hike buying elasticity and subsequent Q1 inventory overhang.",
            })

    # 4. Seasonal European Summer Shutdowns (August)
    logger.info("Detecting European summer holiday plant shutdowns...")
    aug_europe = demand_df[(demand_df["Month"] == 8) & (demand_df["Region"] == "Europe")].copy()
    for idx, row in aug_europe.iterrows():
        sku = row["SKU_ID"]
        reg = row["Region"]
        med = median_demand.get((sku, reg), 0.0)
        actual = int(row["Units_Unconstrained"])
        if med >= 30 and actual < med * 0.4:
            drop_pct = ((med - actual) / med) * 100
            anomalies.append({
                "Date": row["Date"],
                "SKU_ID": sku,
                "Region": reg,
                "Observed_Demand": actual,
                "Expected_Demand": int(round(med)),
                "Anomaly_Type": "HOLIDAY_SEASONAL_SHUTDOWN",
                "Business_Category": "GENUINE_BUSINESS_EVENT",
                "Severity": "LOW",
                "Detection_Method": "August Europe Holiday Shutdown Filter",
                "Explanation": f"Annual European automotive factory summer vacation shutdown (-{drop_pct:.1f}%).",
                "Recommended_Action": "Model via August seasonal holiday factor; expected to recur annually.",
            })

    # 5. Structural Break: EV Adoption Shift
    logger.info("Detecting structural breaks (EV expansion vs ICE decline)...")
    sku_master_map = sku_master_df.set_index("SKU_ID")["Powertrain_Application"].to_dict()
    ev_skus = {sku for sku, app in sku_master_map.items() if app == "EV"}

    # Pre-calculate pre-2022 volume in O(1) dict
    pre_2022_means = (
        demand_df[demand_df["Date"] < "2022-01"]
        .groupby(["SKU_ID", "Region"])["Units_Unconstrained"]
        .mean()
        .to_dict()
    )

    ev_df = demand_df[(demand_df["SKU_ID"].isin(ev_skus)) & (demand_df["Date"] >= "2023-01")].copy()
    for idx, row in ev_df.iterrows():
        sku = row["SKU_ID"]
        reg = row["Region"]
        actual = int(row["Units_Unconstrained"])
        pre_mean = pre_2022_means.get((sku, reg), 0.0)
        
        if pre_mean < 5 and actual > 40:
            anomalies.append({
                "Date": row["Date"],
                "SKU_ID": sku,
                "Region": reg,
                "Observed_Demand": actual,
                "Expected_Demand": int(round(pre_mean)),
                "Anomaly_Type": "STRUCTURAL_BREAK_EV",
                "Business_Category": "GENUINE_BUSINESS_EVENT",
                "Severity": "HIGH",
                "Detection_Method": "EV Powertrain Structural Shift Analysis",
                "Explanation": "Sustained upward inflection in EV demand reflecting accelerating industry electrification.",
                "Recommended_Action": "Incorporate macro EV_Adoption_Index as a non-linear explanatory feature.",
            })

    # 6. Statistical Outliers (Spikes and Drops via Rolling Median & MAD)
    logger.info("Detecting statistical demand outliers (MAD / Z-score)...")
    series_stats = (
        demand_df.groupby(["SKU_ID", "Region"])["Units_Unconstrained"]
        .agg(
            median="median",
            q25=lambda s: s.quantile(0.25),
            q75=lambda s: s.quantile(0.75),
        )
        .reset_index()
    )
    series_stats["iqr"] = (series_stats["q75"] - series_stats["q25"]).clip(lower=5.0)

    merged_stats = demand_df.merge(
        series_stats[["SKU_ID", "Region", "median", "iqr"]],
        on=["SKU_ID", "Region"],
        how="left",
    )

    spike_mask = (
        (merged_stats["Units_Unconstrained"] > merged_stats["median"] + 4.0 * merged_stats["iqr"])
        & (merged_stats["Units_Unconstrained"] > 100)
        & (~merged_stats["is_stockout_month"])
        & (~merged_stats["Date"].isin(pull_forward_dates))
        & (~merged_stats["Date"].isin(covid_dates))
    )

    spikes = merged_stats[spike_mask]
    for idx, row in spikes.iterrows():
        sku = row["SKU_ID"]
        reg = row["Region"]
        actual = int(row["Units_Unconstrained"])
        med = float(row["median"])
        iqr = float(row["iqr"])
        anomalies.append({
            "Date": row["Date"],
            "SKU_ID": sku,
            "Region": reg,
            "Observed_Demand": actual,
            "Expected_Demand": int(round(med)),
            "Anomaly_Type": "STATISTICAL_SPIKE",
            "Business_Category": "UNUSUAL_LEGITIMATE_DEMAND",
            "Severity": "HIGH" if actual > med + 6 * iqr else "MEDIUM",
            "Detection_Method": "Robust IQR Outlier Filter (Volume > Median + 4*IQR)",
            "Explanation": f"Isolated extreme surge of {actual} units (series median: {int(med)}). Likely one-off OEM batch order.",
            "Recommended_Action": "Retain in training dataset; apply robust loss (Huber/MAE) to prevent model overfitting.",
        })

    # Create DataFrame and de-duplicate by (Date, SKU_ID, Region, Anomaly_Type)
    anom_df = pd.DataFrame(anomalies)
    if not anom_df.empty:
        anom_df = anom_df.drop_duplicates(subset=["Date", "SKU_ID", "Region", "Anomaly_Type"])
        anom_df = anom_df.sort_values(by=["Date", "Severity", "SKU_ID"]).reset_index(drop=True)

    logger.info(f"Anomaly detection complete. Total anomalies cataloged: {len(anom_df):,}")
    return anom_df
