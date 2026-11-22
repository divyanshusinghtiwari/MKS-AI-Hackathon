"""Demand Explorer View: Drill-Down by Family, SKU, Region, Customer, Seasonality, and Lifecycle."""

from typing import Dict, Any
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.dashboard.data_loader import load_sku_master
from src.dashboard.filters import filter_dataframe


def render_demand_explorer_view(
    hist_df: pd.DataFrame,
    filters: Dict[str, Any],
):
    """Render the official Demand Explorer dashboard view."""
    st.markdown("## 🔎 Demand Explorer & Granular Series Diagnostics")
    st.markdown(
        "*Multi-level hierarchical drill-down across Product Family, SKU, Region, and Customer accounts. "
        "Inspect seasonal signatures, zero-order intermittency, and lifecycle status.*"
    )

    filtered_hist = filter_dataframe(hist_df, filters)
    sku_master = load_sku_master()

    # 1. Interactive Item Selector if not filtered from sidebar
    available_skus = sorted(filtered_hist["SKU_ID"].dropna().unique().tolist())
    if not available_skus:
        st.warning("No data matches current filter criteria.")
        return

    selected_sku = filters.get("sku")
    if not selected_sku:
        selected_sku = st.selectbox(
            "Select Target SKU for Detailed Diagnostics:",
            options=available_skus,
            index=0,
            help="Choose an individual SKU to inspect its monthly sales, seasonality curve, and account mix.",
        )

    sku_data = hist_df[hist_df["SKU_ID"] == selected_sku].copy()
    sku_info = sku_master[sku_master["SKU_ID"] == selected_sku] if not sku_master.empty else pd.DataFrame()

    # SKU Metadata Header Card
    family_name = sku_data["Product_Family"].iloc[0] if not sku_data.empty else "N/A"
    unit_name = sku_data["Business_Unit"].iloc[0] if ("Business_Unit" in sku_data.columns and not sku_data.empty) else "N/A"
    launch_d = sku_info["Launch_Date"].iloc[0] if (not sku_info.empty and pd.notnull(sku_info["Launch_Date"].iloc[0])) else "Pre-2019"
    eol_d = sku_info["EOL_Date"].iloc[0] if (not sku_info.empty and pd.notnull(sku_info["EOL_Date"].iloc[0])) else "Active (None)"
    replaces_sku = sku_info["Replaces_SKU"].iloc[0] if (not sku_info.empty and pd.notnull(sku_info["Replaces_SKU"].iloc[0])) else "None"

    # Headline Stats for the SKU
    total_unconstrained = sku_data["Units_Unconstrained"].sum()
    total_shipped = sku_data["Units_Shipped"].sum()
    stockout_gap = total_unconstrained - total_shipped
    zero_months = (sku_data.groupby("Date")["Units_Unconstrained"].sum() == 0).sum()
    active_months = sku_data["Date"].nunique()

    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
    with meta_col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Product Hierarchy</div>
                <div class="metric-value" style="font-size:1.3rem;">{selected_sku}</div>
                <div class="metric-subtitle">{family_name} ({unit_name})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with meta_col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Lifecycle Status</div>
                <div class="metric-value" style="font-size:1.3rem;">{'EOL Scheduled' if eol_d != 'Active (None)' else 'Active'}</div>
                <div class="metric-subtitle">Launch: {launch_d} | EOL: {eol_d}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with meta_col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Unconstrained Demand</div>
                <div class="metric-value">{total_unconstrained:,.0f}</div>
                <div class="metric-subtitle">Shipped: {total_shipped:,.0f} (Gap: {stockout_gap:,.0f})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with meta_col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Intermittency & Zero Months</div>
                <div class="metric-value">{zero_months} / {active_months}</div>
                <div class="metric-subtitle">Zero-Demand Months ({(zero_months/max(1, active_months))*100:.1f}%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 1. Historical Time Series for Selected SKU
    st.markdown(f"### 📈 Monthly Demand History: `{selected_sku}`")
    sku_monthly = (
        sku_data.groupby("Date")
        .agg({
            "Units_Shipped": "sum",
            "Units_Unconstrained": "sum",
        })
        .reset_index()
    )

    fig_sku = go.Figure()
    fig_sku.add_trace(
        go.Scatter(
            x=sku_monthly["Date"],
            y=sku_monthly["Units_Unconstrained"],
            mode="lines+markers",
            name="Unconstrained Market Demand",
            line=dict(color="#0284c7", width=2.5),
            marker=dict(size=4),
        )
    )
    fig_sku.add_trace(
        go.Scatter(
            x=sku_monthly["Date"],
            y=sku_monthly["Units_Shipped"],
            mode="lines",
            name="Actual Shipped Units",
            line=dict(color="#f59e0b", width=1.5, dash="dot"),
        )
    )
    fig_sku.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=20, b=30),
        xaxis_title="Date",
        yaxis_title="Units",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_sku, use_container_width=True)

    # 2. Seasonality and Regional Distribution
    col_season, col_region = st.columns(2)

    with col_season:
        st.markdown("### 🗓️ Annual Seasonality Profile (Month 1 – 12)")
        sku_data["Month_Num"] = pd.to_numeric(sku_data["Date"].str.slice(5, 7))
        monthly_seasonality = (
            sku_data.groupby("Month_Num")["Units_Unconstrained"]
            .mean()
            .reset_index()
        )
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_seasonality["Month_Label"] = [month_names[m - 1] for m in monthly_seasonality["Month_Num"]]

        fig_season = go.Figure(
            go.Bar(
                x=monthly_seasonality["Month_Label"],
                y=monthly_seasonality["Units_Unconstrained"],
                marker=dict(
                    color=monthly_seasonality["Units_Unconstrained"],
                    colorscale="Blues",
                ),
            )
        )
        fig_season.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=30),
            xaxis_title="Calendar Month",
            yaxis_title="Average Monthly Units",
            template="plotly_white",
        )
        st.plotly_chart(fig_season, use_container_width=True)

    with col_region:
        st.markdown("### 🌍 Regional Demand Distribution")
        reg_breakdown = (
            sku_data.groupby("Region")["Units_Unconstrained"]
            .sum()
            .reset_index()
            .sort_values(by="Units_Unconstrained", ascending=False)
        )
        fig_reg_bar = go.Figure(
            go.Bar(
                x=reg_breakdown["Region"],
                y=reg_breakdown["Units_Unconstrained"],
                marker=dict(color="#3b82f6"),
            )
        )
        fig_reg_bar.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=30),
            xaxis_title="Region",
            yaxis_title="Total Historical Units",
            template="plotly_white",
            xaxis_tickangle=-25,
        )
        st.plotly_chart(fig_reg_bar, use_container_width=True)

    # 3. Top Customer Account Mix
    if "Customer_Name" in sku_data.columns:
        st.markdown("### 🏢 Top Customer Accounts for this SKU")
        cust_summary = (
            sku_data.groupby("Customer_Name")
            .agg({
                "Units_Unconstrained": "sum",
                "Units_Shipped": "sum",
                "Transaction_Count": "sum" if "Transaction_Count" in sku_data.columns else "count",
            })
            .reset_index()
            .sort_values(by="Units_Unconstrained", ascending=False)
            .head(8)
        )
        st.dataframe(cust_summary, use_container_width=True, hide_index=True)
