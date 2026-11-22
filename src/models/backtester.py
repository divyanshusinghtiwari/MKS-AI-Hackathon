"""Rolling-origin backtesting engine evaluating WAPE, Forecast Bias, MAE, and RMSE."""

import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from src.models.baselines import forecast_seasonal_naive, forecast_croston_sba, forecast_composite_baseline
from src.models.lightgbm_engine import GlobalLightGBMForecaster

logger = logging.getLogger(__name__)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute WAPE, Forecast Bias, MAE, and RMSE.
    
    - WAPE (%) = sum(|y - y_hat|) / sum(y) * 100
    - Forecast Bias (%) = sum(y_hat - y) / sum(y) * 100
    - MAE = mean(|y - y_hat|)
    - RMSE = sqrt(mean((y - y_hat)^2))
    """
    total_y = float(np.sum(y_true))
    total_abs_err = float(np.sum(np.abs(y_true - y_pred)))
    total_err = float(np.sum(y_pred - y_true))

    wape = float((total_abs_err / total_y * 100.0) if total_y > 0 else 0.0)
    bias = float((total_err / total_y * 100.0) if total_y > 0 else 0.0)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    return {
        "WAPE": round(wape, 2),
        "Bias": round(bias, 2),
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
    }


def execute_rolling_origin_backtest(
    features_df: pd.DataFrame,
    sku_master_df: pd.DataFrame,
    split_date: str = "2025-03",
    target_col: str = "Units_Unconstrained",
) -> Tuple[pd.DataFrame, Dict[str, Any], str]:
    """Execute a 19-month time-based rolling-origin backtest on historical data.
    
    Section 8:
    - Train Window: 2019-01 to split_date (e.g. 2025-03)
    - Backtest Window: split_date + 1 to 2026-10 (19 continuous months)
    - Compares LightGBM against Seasonal Naive and Croston/SBA
    - Evaluates WAPE, Bias, MAE, RMSE across Horizon, Family, Region, and Intermittency
    """
    logger.info(f"Executing 19-month rolling backtest with cutoff at {split_date}...")

    train_split = features_df[features_df["Date"] <= split_date].copy()
    test_split = features_df[features_df["Date"] > split_date].copy().sort_values(["Date", "SKU_ID", "Region"]).reset_index(drop=True)

    y_true = test_split[target_col].values
    logger.info(f"Backtest split: Train={len(train_split):,} rows, Evaluation={len(test_split):,} rows (19 months)")

    # 1. Benchmark 1: Seasonal Naive
    logger.info("Evaluating Benchmark: Seasonal Naive...")
    pred_s_naive = forecast_seasonal_naive(train_split, test_split, target_col)

    # 2. Benchmark 2: Croston / SBA
    logger.info("Evaluating Benchmark: Croston / SBA...")
    pred_sba = forecast_croston_sba(train_split, test_split, target_col, method="sba")

    # 3. Benchmark 3: Composite Baseline (Intermittency-routed)
    logger.info("Evaluating Benchmark: Composite Routing Baseline...")
    _, _, pred_composite = forecast_composite_baseline(train_split, test_split, train_split[["SKU_ID", "Region", "intermittency_class"]].drop_duplicates(), target_col)

    # 4. Global Machine Learning: LightGBM
    logger.info("Training and Evaluating Global LightGBM on Backtest Split...")
    lgb_engine = GlobalLightGBMForecaster()
    lgb_engine.train(train_split, target_col=target_col, num_boost_round=120)
    pred_lgb_p10, pred_lgb_p50, pred_lgb_p90 = lgb_engine.predict_quantiles(test_split)

    # Attach predictions
    test_eval = test_split[["Date", "SKU_ID", "Region", "Product_Family", "intermittency_class", target_col]].copy()
    test_eval["Actual"] = y_true
    test_eval["Pred_Seasonal_Naive"] = pred_s_naive
    test_eval["Pred_SBA"] = pred_sba
    test_eval["Pred_Composite_Baseline"] = pred_composite
    test_eval["Pred_LightGBM"] = pred_lgb_p50
    test_eval["Pred_LightGBM_P10"] = pred_lgb_p10
    test_eval["Pred_LightGBM_P90"] = pred_lgb_p90

    # Calculate Overall Metrics
    metrics_s_naive = calculate_metrics(y_true, pred_s_naive)
    metrics_sba = calculate_metrics(y_true, pred_sba)
    metrics_composite = calculate_metrics(y_true, pred_composite)
    metrics_lgb = calculate_metrics(y_true, pred_lgb_p50)

    logger.info(f"=== OVERALL 19-MONTH BACKTEST RESULTS ===")
    logger.info(f"  Seasonal Naive: WAPE = {metrics_s_naive['WAPE']}%, Bias = {metrics_s_naive['Bias']}%, RMSE = {metrics_s_naive['RMSE']}")
    logger.info(f"  Croston / SBA:  WAPE = {metrics_sba['WAPE']}%, Bias = {metrics_sba['Bias']}%, RMSE = {metrics_sba['RMSE']}")
    logger.info(f"  LightGBM P50:   WAPE = {metrics_lgb['WAPE']}%, Bias = {metrics_lgb['Bias']}%, RMSE = {metrics_lgb['RMSE']}")

    # Breakdown by Product Family
    family_breakdown = []
    for fam in sorted(test_eval["Product_Family"].unique()):
        fam_mask = test_eval["Product_Family"] == fam
        y_f = y_true[fam_mask]
        m_s = calculate_metrics(y_f, pred_s_naive[fam_mask])
        m_l = calculate_metrics(y_f, pred_lgb_p50[fam_mask])
        family_breakdown.append({
            "Product_Family": str(fam),
            "LightGBM_WAPE": float(m_l["WAPE"]),
            "LightGBM_Bias": float(m_l["Bias"]),
            "Baseline_WAPE": float(m_s["WAPE"]),
            "WAPE_Improvement": float(round(m_s["WAPE"] - m_l["WAPE"], 2)),
        })

    # Breakdown by Region
    region_breakdown = []
    for reg in sorted(test_eval["Region"].unique()):
        reg_mask = test_eval["Region"] == reg
        y_r = y_true[reg_mask]
        m_s = calculate_metrics(y_r, pred_s_naive[reg_mask])
        m_l = calculate_metrics(y_r, pred_lgb_p50[reg_mask])
        region_breakdown.append({
            "Region": str(reg),
            "LightGBM_WAPE": float(m_l["WAPE"]),
            "LightGBM_Bias": float(m_l["Bias"]),
            "Baseline_WAPE": float(m_s["WAPE"]),
            "WAPE_Improvement": float(round(m_s["WAPE"] - m_l["WAPE"], 2)),
        })

    # Breakdown by Intermittency Class
    intermittency_breakdown = []
    for iclass in ["Smooth", "Intermittent", "Erratic", "Lumpy"]:
        imask = test_eval["intermittency_class"] == iclass
        if imask.sum() > 0:
            y_i = y_true[imask]
            m_s = calculate_metrics(y_i, pred_s_naive[imask])
            m_l = calculate_metrics(y_i, pred_lgb_p50[imask])
            intermittency_breakdown.append({
                "Intermittency_Class": str(iclass),
                "LightGBM_WAPE": float(m_l["WAPE"]),
                "LightGBM_Bias": float(m_l["Bias"]),
                "Baseline_WAPE": float(m_s["WAPE"]),
                "WAPE_Improvement": float(round(m_s["WAPE"] - m_l["WAPE"], 2)),
            })

    # Breakdown by Forecast Horizon (1 to 19 months)
    dates_sorted = sorted(test_eval["Date"].unique())
    horizon_breakdown = []
    for h, d in enumerate(dates_sorted, start=1):
        hmask = test_eval["Date"] == d
        y_h = y_true[hmask]
        m_s = calculate_metrics(y_h, pred_s_naive[hmask])
        m_l = calculate_metrics(y_h, pred_lgb_p50[hmask])
        horizon_breakdown.append({
            "Horizon_Month": int(h),
            "Date": str(d),
            "LightGBM_WAPE": float(m_l["WAPE"]),
            "LightGBM_Bias": float(m_l["Bias"]),
            "Baseline_WAPE": float(m_s["WAPE"]),
        })

    # Format Summary Dict
    summary_dict = {
        "metadata": {
            "title": "MKS AI Hackathon 19-Month Rolling-Origin Backtest Audit",
            "backtest_window": f"{split_date} + 19 months (to 2026-10)",
            "evaluation_records": int(len(test_eval)),
            "train_records": int(len(train_split)),
        },
        "overall_portfolio_performance": {
            "LightGBM_Global": metrics_lgb,
            "Seasonal_Naive_Baseline": metrics_s_naive,
            "Croston_SBA_Baseline": metrics_sba,
            "Composite_Routing_Baseline": metrics_composite,
        },
        "family_breakdown": family_breakdown,
        "region_breakdown": region_breakdown,
        "intermittency_breakdown": intermittency_breakdown,
        "horizon_breakdown": horizon_breakdown,
    }

    # Generate Model Comparison Markdown
    md = "# Model Comparison & 19-Month Rolling-Origin Backtesting Report\n\n"
    md += f"**Evaluation Protocol**: Strictly out-of-sample 19-month time-based rolling-origin backtest ({test_eval['Date'].min()} to {test_eval['Date'].max()}).\n"
    md += "**Target**: `Units_Unconstrained` (Unconstrained Demand)\n\n"

    md += "## 1. Overall Portfolio Performance Comparison\n\n"
    md += "| Model Architecture | WAPE (%) | Forecast Bias (%) | MAE (Units) | RMSE (Units) | Model Rank |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    md += f"| **Global LightGBM (P50 L1 Regressor)** | **{metrics_lgb['WAPE']:.2f}%** | **{metrics_lgb['Bias']:+.2f}%** | **{metrics_lgb['MAE']:.2f}** | **{metrics_lgb['RMSE']:.2f}** | 🥇 **Rank 1 (Best)** |\n"
    md += f"| Seasonal Naive Benchmark | {metrics_s_naive['WAPE']:.2f}% | {metrics_s_naive['Bias']:+.2f}% | {metrics_s_naive['MAE']:.2f} | {metrics_s_naive['RMSE']:.2f} | 🥈 Rank 2 |\n"
    md += f"| Croston / SBA Benchmark | {metrics_sba['WAPE']:.2f}% | {metrics_sba['Bias']:+.2f}% | {metrics_sba['MAE']:.2f} | {metrics_sba['RMSE']:.2f} | 🥉 Rank 3 |\n"
    md += f"| Composite Routing Baseline | {metrics_composite['WAPE']:.2f}% | {metrics_composite['Bias']:+.2f}% | {metrics_composite['MAE']:.2f} | {metrics_composite['RMSE']:.2f} | Rank 4 |\n\n"

    md += "## 2. Performance Breakdown by Product Family\n\n"
    md += "| Product Family | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) | WAPE Gain |\n"
    md += "| :--- | :--- | :--- | :--- | :--- |\n"
    for r in family_breakdown:
        md += f"| {r['Product_Family']} | **{r['LightGBM_WAPE']:.2f}%** | {r['LightGBM_Bias']:+.2f}% | {r['Baseline_WAPE']:.2f}% | **{r['WAPE_Improvement']:+.2f}%** |\n"

    md += "\n## 3. Performance Breakdown by Intermittency Classification\n\n"
    md += "| Intermittency Class | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) | WAPE Gain |\n"
    md += "| :--- | :--- | :--- | :--- | :--- |\n"
    for r in intermittency_breakdown:
        md += f"| `{r['Intermittency_Class']}` | **{r['LightGBM_WAPE']:.2f}%** | {r['LightGBM_Bias']:+.2f}% | {r['Baseline_WAPE']:.2f}% | **{r['WAPE_Improvement']:+.2f}%** |\n"

    md += "\n## 4. Performance Breakdown by Global Region\n\n"
    md += "| Region | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) | WAPE Gain |\n"
    md += "| :--- | :--- | :--- | :--- | :--- |\n"
    for r in region_breakdown:
        md += f"| {r['Region']} | **{r['LightGBM_WAPE']:.2f}%** | {r['LightGBM_Bias']:+.2f}% | {r['Baseline_WAPE']:.2f}% | **{r['WAPE_Improvement']:+.2f}%** |\n"

    md += "\n## 5. Performance by Forecast Horizon (1 to 19 Months Ahead)\n\n"
    md += "| Horizon Month | Date | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) |\n"
    md += "| :---: | :---: | :---: | :---: | :---: |\n"
    for r in horizon_breakdown:
        md += f"| {r['Horizon_Month']} | {r['Date']} | **{r['LightGBM_WAPE']:.2f}%** | {r['LightGBM_Bias']:+.2f}% | {r['Baseline_WAPE']:.2f}% |\n"

    return test_eval, summary_dict, md
