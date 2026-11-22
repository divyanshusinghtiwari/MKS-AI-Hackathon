"""Safety Stock & Procurement Planner View: P90 Sizing, Buffer Stock, and Reorder Points."""

from typing import Dict, Any
import streamlit as st
import pandas as pd
import numpy as np

from src.dashboard.filters import filter_dataframe


def render_procurement_planner_view(
    fc_df: pd.DataFrame,
    filters: Dict[str, Any],
):
    """Render the optional Procurement & Safety Stock Planner dashboard view."""
    st.markdown("## 📦 Procurement & Safety Stock Planning Workbench")
    st.markdown(
        "*Leverage probabilistic P90 demand bounds and lead-time assumptions to size safety buffers "
        "and establish component reorder thresholds without stockout exposure.*"
    )

    st.markdown(
        """
        <div class="callout-box">
            <b>📋 Planning Assumptions & Guidance:</b><br>
            • <b>Target Cycle Service Level:</b> 95% (calibrated against P90 quantile predictions).<br>
            • <b>Assumed Supplier Lead Time ($L$):</b> Configurable parameter (Default: 2.0 months for automotive tier-1 supply chains).<br>
            • <b>Notice:</b> Values displayed are <i>calculated planning estimates</i> intended to assist supply chain planners. 
            They do not represent confirmed external purchase orders.
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtered_fc = filter_dataframe(fc_df, filters)
    if filtered_fc.empty:
        st.warning("No forecast data matching current filters.")
        return

    # User Lead Time Selector
    col_lead, col_target = st.columns(2)
    with col_lead:
        lead_time_months = st.slider("Supplier Lead Time (Months):", min_value=1.0, max_value=6.0, value=2.0, step=0.5)
    with col_target:
        service_level_label = st.selectbox("Target Protection Quantile:", options=["P90 Upper Quantile (Recommended)", "P95 Extended Buffer (+15%)"], index=0)

    # Compute SKU-Level Planning Aggregates across the 19-month window
    sku_planning = (
        filtered_fc.groupby(["SKU_ID", "Product_Family", "Region"])
        .agg({
            "P10_Forecast": "mean",
            "P50_Forecast": "mean",
            "P90_Forecast": "mean",
            "Units_Sold_Forecast": "sum",
        })
        .reset_index()
    )

    # Safety StockBuffer = P90 - P50
    buffer_multiplier = 1.15 if "P95" in service_level_label else 1.0
    sku_planning["Avg_Monthly_Demand"] = np.round(sku_planning["P50_Forecast"], 1)
    sku_planning["Monthly_Safety_Buffer"] = np.round(
        np.maximum(0.0, (sku_planning["P90_Forecast"] - sku_planning["P50_Forecast"])) * buffer_multiplier,
        1
    )
    sku_planning["Lead_Time_Demand"] = np.round(sku_planning["Avg_Monthly_Demand"] * lead_time_months, 1)
    sku_planning["Recommended_Safety_Stock"] = np.round(sku_planning["Monthly_Safety_Buffer"] * np.sqrt(lead_time_months), 0).astype(int)
    sku_planning["Reorder_Point_ROP"] = np.round(sku_planning["Lead_Time_Demand"] + sku_planning["Recommended_Safety_Stock"], 0).astype(int)

    # Top KPI Row
    total_safety_stock = sku_planning["Recommended_Safety_Stock"].sum()
    total_rop = sku_planning["Reorder_Point_ROP"].sum()
    avg_safety_days = (total_safety_stock / max(1.0, sku_planning["Avg_Monthly_Demand"].sum())) * 30.0

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Portfolio Safety Stock</div>
                <div class="metric-value">{total_safety_stock:,}</div>
                <div class="metric-subtitle">Units Buffer Protection</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Portfolio Reorder Threshold</div>
                <div class="metric-value">{total_rop:,}</div>
                <div class="metric-subtitle">Cumulative ROP Units</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Average Buffer Coverage</div>
                <div class="metric-value">{avg_safety_days:.1f} Days</div>
                <div class="metric-subtitle">Days of Supply (DOS)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Planning Table
    st.markdown("### 📋 SKU Reorder Point & Safety Stock Schedule")
    st.markdown("*Sortable inventory parameters by SKU, Product Family, and Sales Region.*")

    display_df = sku_planning[[
        "SKU_ID", "Product_Family", "Region", "Avg_Monthly_Demand",
        "Lead_Time_Demand", "Recommended_Safety_Stock", "Reorder_Point_ROP", "Units_Sold_Forecast"
    ]].rename(columns={
        "Avg_Monthly_Demand": "Monthly Demand (P50)",
        "Lead_Time_Demand": f"Lead Time Demand ({lead_time_months}M)",
        "Recommended_Safety_Stock": "Safety Stock (SS)",
        "Reorder_Point_ROP": "Reorder Point (ROP)",
        "Units_Sold_Forecast": "19M Total Volume",
    }).sort_values(by="19M Total Volume", ascending=False)

    st.dataframe(display_df, use_container_width=True, hide_index=True)
