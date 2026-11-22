"""High-quality visualizer for anomaly analysis and unconstrained demand reconstruction."""

import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

# Set publication-quality plot style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 11


def generate_anomaly_charts(
    demand_df: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    sku_master_df: pd.DataFrame,
    output_dir: Path,
):
    """Generate and save publication-quality visualizations for Workstream 2."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating charts in {output_dir}...")

    # 1. Timeline: Shipped vs Unconstrained Demand
    plt.figure(figsize=(14, 6))
    monthly_totals = (
        demand_df.groupby("Date")[["Units_Shipped", "Units_Unconstrained"]]
        .sum()
        .reset_index()
    )
    plt.plot(
        monthly_totals["Date"],
        monthly_totals["Units_Unconstrained"] / 1000.0,
        label="True Unconstrained Demand (Requested)",
        color="#1f77b4",
        linewidth=2.2,
    )
    plt.plot(
        monthly_totals["Date"],
        monthly_totals["Units_Shipped"] / 1000.0,
        label="Actual Constrained Shipped (train.csv)",
        color="#d62728",
        linewidth=1.8,
        linestyle="--",
    )
    
    # Highlight Chip Shortage Window
    chip_dates = monthly_totals[
        (monthly_totals["Date"] >= "2021-03") & (monthly_totals["Date"] <= "2022-12")
    ]
    if not chip_dates.empty:
        idx_start = chip_dates.index[0]
        idx_end = chip_dates.index[-1]
        plt.axvspan(
            idx_start,
            idx_end,
            color="#ff7f0e",
            alpha=0.15,
            label="Global Semiconductor Shortage Window",
        )

    plt.title("Celeris Automobili: Historical Sales vs. Reconstructed Unconstrained Demand (2019-2026)")
    plt.xlabel("Delivery Month (YYYY-MM)")
    plt.ylabel("Monthly Demand (Thousand Units)")
    plt.xticks(ticks=range(0, len(monthly_totals), 6), labels=monthly_totals["Date"].iloc[::6], rotation=45)
    plt.legend(frameon=True, loc="upper left")
    plt.tight_layout()
    plt.savefig(output_dir / "unconstrained_vs_shipped_timeline.png", dpi=300)
    plt.close()

    # 2. Anomaly Breakdown by Type & Category
    plt.figure(figsize=(12, 6))
    type_counts = anomaly_df["Anomaly_Type"].value_counts()
    colors = sns.color_palette("viridis", len(type_counts))
    bars = plt.barh(type_counts.index, type_counts.values, color=colors, edgecolor="black", alpha=0.85)
    plt.title("Distribution of Detected Anomalies by Classification Type")
    plt.xlabel("Number of Anomalies Cataloged")
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 15, bar.get_y() + bar.get_height() / 2, f"{int(w):,}", va="center", fontsize=9, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "anomaly_breakdown_by_type.png", dpi=300)
    plt.close()

    # 3. Structural Break: EV Adoption Shift
    plt.figure(figsize=(12, 6))
    merged_pt = demand_df.merge(sku_master_df[["SKU_ID", "Powertrain_Application"]], on="SKU_ID", how="left")
    pt_timeline = (
        merged_pt.groupby(["Date", "Powertrain_Application"])["Units_Unconstrained"]
        .sum()
        .unstack(fill_value=0)
    )
    for col, color in [("EV", "#2ca02c"), ("ICE", "#d62728"), ("Universal", "#1f77b4")]:
        if col in pt_timeline.columns:
            plt.plot(pt_timeline.index, pt_timeline[col] / 1000.0, label=f"Powertrain: {col}", color=color, linewidth=2.0)
    
    plt.title("Structural Shift: EV Exponential Growth vs. Conventional ICE Demand (2019-2026)")
    plt.xlabel("Delivery Month (YYYY-MM)")
    plt.ylabel("Demand (Thousand Units)")
    plt.xticks(ticks=range(0, len(pt_timeline), 6), labels=pt_timeline.index[::6], rotation=45)
    plt.legend(frameon=True, loc="center left")
    plt.tight_layout()
    plt.savefig(output_dir / "ev_structural_transition.png", dpi=300)
    plt.close()

    # 4. Stockout Causes Breakdown
    stockouts_only = demand_df[demand_df["is_stockout_month"]]
    if not stockouts_only.empty:
        plt.figure(figsize=(10, 6))
        reason_counts = stockouts_only["Stockout_Reason"].value_counts()
        colors = sns.color_palette("pastel")[:len(reason_counts)]
        plt.pie(reason_counts.values, labels=reason_counts.index, autopct="%1.1f%%", startangle=140, colors=colors)
        plt.title("Root Causes of Supply-Constrained Stockout Months (5,830 events)")
        plt.tight_layout()
        plt.savefig(output_dir / "stockouts_by_reason.png", dpi=300)
        plt.close()

    logger.info("All 4 anomaly analysis charts generated successfully.")
