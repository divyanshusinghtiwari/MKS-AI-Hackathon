"""Anomaly Monitor View: Categorization, Anomaly Register, Stockouts, and Business Events."""

from typing import Dict, Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.data_loader import load_anomaly_data
from src.dashboard.filters import filter_dataframe


def render_anomaly_monitor_view(
    hist_df: pd.DataFrame,
    filters: Dict[str, Any],
):
    """Render the official Anomaly Monitor dashboard view."""
    st.markdown("## 🚨 Anomaly Monitor & Root Cause Register")
    st.markdown(
        "*Detection and classification of 13,231 anomalous events separating genuine business events, "
        "supply chain stockouts, and unusual customer demand patterns.*"
    )

    reg_df, summary = load_anomaly_data()
    if reg_df.empty:
        st.warning("Anomaly register not found in reports directory.")
        return

    # Filter anomaly register based on global filters
    filtered_reg = filter_dataframe(reg_df, filters)
    filtered_hist = filter_dataframe(hist_df, filters)

    # Top KPI Row
    total_anomalies = len(filtered_reg)
    supply_anomalies = (filtered_reg["Anomaly_Category"] == "SUPPLY_CONSTRAINT").sum() if "Anomaly_Category" in filtered_reg.columns else 0
    business_events = (filtered_reg["Anomaly_Category"] == "GENUINE_BUSINESS_EVENT").sum() if "Anomaly_Category" in filtered_reg.columns else 0
    unusual_demand = (filtered_reg["Anomaly_Category"] == "UNUSUAL_LEGITIMATE_DEMAND").sum() if "Anomaly_Category" in filtered_reg.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Flagged Incidents</div>
                <div class="metric-value">{total_anomalies:,}</div>
                <div class="metric-subtitle">Across selected filter scope</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Supply Constraints</div>
                <div class="metric-value" style="color:#ef4444;">{supply_anomalies:,}</div>
                <div class="metric-subtitle">Stockouts & allocation shortfalls</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Genuine Business Events</div>
                <div class="metric-value" style="color:#0284c7;">{business_events:,}</div>
                <div class="metric-subtitle">Pre-price hikes & seasonal shutdowns</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Unusual Customer Surges</div>
                <div class="metric-value" style="color:#8b5cf6;">{unusual_demand:,}</div>
                <div class="metric-subtitle">Valid non-recurring bulk orders</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 1. Timeline of Portfolio Demand with Overlay Flagged Anomalies
    st.markdown("### 📈 Monthly Portfolio Demand with Anomaly Scatter Overlays")
    monthly_demand = (
        filtered_hist.groupby("Date")["Units_Unconstrained"]
        .sum()
        .reset_index()
    )

    fig_ano = go.Figure()
    # Baseline demand curve
    fig_ano.add_trace(
        go.Scatter(
            x=monthly_demand["Date"],
            y=monthly_demand["Units_Unconstrained"],
            mode="lines",
            name="Unconstrained Market Demand",
            line=dict(color="#0284c7", width=2),
        )
    )

    # Aggregate anomalies by month and category
    if not filtered_reg.empty and "Date" in filtered_reg.columns and "Anomaly_Category" in filtered_reg.columns:
        cat_colors = {
            "SUPPLY_CONSTRAINT": "#ef4444",
            "GENUINE_BUSINESS_EVENT": "#10b981",
            "UNUSUAL_LEGITIMATE_DEMAND": "#8b5cf6",
            "DATA_QUALITY_ERROR": "#f59e0b",
        }
        monthly_ano = (
            filtered_reg.groupby(["Date", "Anomaly_Category"])
            .agg({
                "Observed_Demand": "sum",
                "Anomaly_ID": "count",
            })
            .reset_index()
        )

        for cat, color in cat_colors.items():
            cat_subset = monthly_ano[monthly_ano["Anomaly_Category"] == cat]
            if not cat_subset.empty:
                fig_ano.add_trace(
                    go.Scatter(
                        x=cat_subset["Date"],
                        y=cat_subset["Observed_Demand"],
                        mode="markers",
                        name=f"Anomaly: {cat.replace('_', ' ').title()}",
                        marker=dict(
                            color=color,
                            size=cat_subset["Anomaly_ID"].clip(upper=20) + 4,
                            symbol="circle",
                            line=dict(width=1, color="#ffffff"),
                        ),
                        text=[f"{count} incidents" for count in cat_subset["Anomaly_ID"]],
                    )
                )

    fig_ano.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=20, b=30),
        xaxis_title="Date",
        yaxis_title="Total Units",
        template="plotly_white",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_ano, use_container_width=True)

    # 2. Stockout Root Cause Breakdown & Severity Distribution
    col_causes, col_sev = st.columns(2)

    with col_causes:
        st.markdown("### ⚙️ Stockout Incidents by Root Cause")
        stockouts = filtered_reg[filtered_reg["Anomaly_Category"] == "SUPPLY_CONSTRAINT"]
        if not stockouts.empty and "Detection_Method" in stockouts.columns:
            cause_data = (
                stockouts["Explanation"]
                .str.extract(r"reason: ([^;]+)")[0]
                .fillna("General Component Allocation")
                .value_counts()
                .reset_index()
            )
            cause_data.columns = ["Root_Cause", "Incident_Count"]

            fig_cause = go.Figure(
                go.Bar(
                    x=cause_data["Root_Cause"],
                    y=cause_data["Incident_Count"],
                    marker=dict(color="#ef4444"),
                )
            )
            fig_cause.update_layout(
                height=280,
                margin=dict(l=20, r=20, t=20, b=30),
                xaxis_title="Root Cause Description",
                yaxis_title="Incident Count",
                template="plotly_white",
                xaxis_tickangle=-25,
            )
            st.plotly_chart(fig_cause, use_container_width=True)
        else:
            st.info("No supply constraint records in current filter scope.")

    with col_sev:
        st.markdown("### 🎯 Anomaly Severity Distribution")
        if not filtered_reg.empty and "Severity" in filtered_reg.columns:
            sev_counts = filtered_reg["Severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]

            fig_sev = go.Figure(
                go.Pie(
                    labels=sev_counts["Severity"],
                    values=sev_counts["Count"],
                    hole=0.45,
                    marker=dict(colors=["#ef4444", "#f59e0b", "#3b82f6", "#10b981"]),
                )
            )
            fig_sev.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_sev, use_container_width=True)

    # 3. Filterable Anomaly Register Table
    st.markdown("### 📑 Detailed Anomaly Register & Recommended Actions")
    display_cols = [
        "Date", "SKU_ID", "Region", "Observed_Demand", "Anomaly_Type",
        "Severity", "Detection_Method", "Explanation", "Recommended_Action"
    ]
    avail_cols = [c for c in display_cols if c in filtered_reg.columns]
    st.dataframe(filtered_reg[avail_cols].head(150), use_container_width=True, hide_index=True)
