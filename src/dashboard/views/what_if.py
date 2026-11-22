"""What-If Scenario Simulator View: Interactive Macro Shocks and Demand Sensitivity."""

from typing import Dict, Any
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.dashboard.filters import filter_dataframe


def render_what_if_view(
    fc_df: pd.DataFrame,
    filters: Dict[str, Any],
):
    """Render the optional What-If Scenario Simulator dashboard view."""
    st.markdown("## 🔮 What-If Scenario & Macro Stress Simulator")
    st.markdown(
        "*Stress test the 19-month demand forecast against macroeconomic supply chain disruptions, "
        "interest rate shocks, and industrial manufacturing downturns.*"
    )

    st.markdown(
        """
        <div class="callout-simulation">
            <b>⚠️ Simulation Integrity Notice:</b> This tool applies linear empirical macro elasticity coefficients 
            to simulate demand deltas. It <b>does not</b> retrain the production machine learning model, and all modifications 
            are strictly sandboxed within this view—official production forecasts and <code>submission.csv</code> are <b>never modified or overwritten</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtered_fc = filter_dataframe(fc_df, filters)
    if filtered_fc.empty:
        st.warning("No forecast data matching current filters.")
        return

    # Base Forecast Volume
    base_volume = filtered_fc["Units_Sold_Forecast"].sum()

    st.markdown("### 🎛️ Scenario Shock Controls")
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)

    with ctrl_col1:
        pmi_shock = st.slider(
            "ISM Manufacturing PMI Shock (Points):",
            min_value=-10.0, max_value=10.0, value=-3.0, step=0.5,
            help="E.g. PMI drops from 50 to 47 indicating industrial contraction.",
        )
    with ctrl_col2:
        auto_prod_shock = st.slider(
            "Auto Production YoY% Shock (%):",
            min_value=-20.0, max_value=20.0, value=-5.0, step=1.0,
            help="E.g. OEM vehicle assembly drops by 5%.",
        )
    with ctrl_col3:
        ev_adoption_shock = st.slider(
            "EV Adoption Index Shock (%):",
            min_value=-25.0, max_value=25.0, value=10.0, step=2.5,
            help="E.g. Accelerated fleet transition to electric vehicles.",
        )
    with ctrl_col4:
        general_demand_shock = st.slider(
            "General Demand Adjustment (%):",
            min_value=-30.0, max_value=30.0, value=0.0, step=2.0,
            help="Discretionary planner volume shift.",
        )

    # Elasticity-based simulation formula:
    # - PMI: +1 pt PMI -> +1.2% demand for industrial families
    # - Auto Production: +1% Auto prod -> +0.8% demand for chassis & powertrain
    # - EV Adoption: +1% EV adoption -> +0.9% for Electrical Assemblies, -0.4% for ICE Powertrain
    # - General Demand: direct percentage shift

    sim_fc = filtered_fc.copy()
    elasticity_multipliers = np.ones(len(sim_fc))

    # Family-specific adjustments
    for i, fam in enumerate(sim_fc["Product_Family"]):
        fam_str = str(fam)
        mult = 1.0 + (general_demand_shock / 100.0)

        # PMI impact
        mult += (pmi_shock * 0.012)

        # Auto production impact
        if fam_str in ["Chassis & Structural", "Powertrain Components", "Hydraulic Systems"]:
            mult += (auto_prod_shock * 0.008)
        else:
            mult += (auto_prod_shock * 0.004)

        # EV impact
        if fam_str == "Electrical Assemblies":
            mult += (ev_adoption_shock * 0.009)
        elif fam_str == "Powertrain Components":
            mult -= (ev_adoption_shock * 0.004)

        elasticity_multipliers[i] = max(0.0, mult)

    sim_fc["Simulated_Forecast"] = np.round(sim_fc["Units_Sold_Forecast"] * elasticity_multipliers).astype(int)
    sim_volume = sim_fc["Simulated_Forecast"].sum()
    volume_delta = sim_volume - base_volume
    pct_delta = (volume_delta / max(1, base_volume)) * 100.0

    # Impact Summary Cards
    st.markdown("### 📊 Simulated Impact Analysis")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Baseline Forecast</div>
                <div class="metric-value">{base_volume:,.0f}</div>
                <div class="metric-subtitle">Official LightGBM P50</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Simulated Demand</div>
                <div class="metric-value" style="color:#7e22ce;">{sim_volume:,.0f}</div>
                <div class="metric-subtitle">Under selected macro shocks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        delta_class = "metric-delta-pos" if volume_delta >= 0 else "metric-delta-neg"
        delta_sign = "+" if volume_delta >= 0 else ""
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Volume Delta</div>
                <div class="metric-value {delta_class}">{delta_sign}{volume_delta:,.0f}</div>
                <div class="metric-subtitle">Units Impact</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Percentage Shift</div>
                <div class="metric-value {delta_class}">{delta_sign}{pct_delta:.2f}%</div>
                <div class="metric-subtitle">Net Portfolio Change</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Comparison Timeline Chart: Base vs Simulated
    st.markdown("### 📈 Monthly Trajectory: Baseline vs. Simulated Shock")
    monthly_sim = (
        sim_fc.groupby("Date")
        .agg({
            "Units_Sold_Forecast": "sum",
            "Simulated_Forecast": "sum",
        })
        .reset_index()
    )

    fig_sim = go.Figure()
    fig_sim.add_trace(
        go.Scatter(
            x=monthly_sim["Date"],
            y=monthly_sim["Units_Sold_Forecast"],
            mode="lines+markers",
            name="Official Baseline Forecast (P50)",
            line=dict(color="#16a34a", width=2.5),
        )
    )
    fig_sim.add_trace(
        go.Scatter(
            x=monthly_sim["Date"],
            y=monthly_sim["Simulated_Forecast"],
            mode="lines+markers",
            name=f"Simulated Scenario (PMI {pmi_shock:+} | Auto {auto_prod_shock:+}% | EV {ev_adoption_shock:+}%)",
            line=dict(color="#a855f7", width=3, dash="dash"),
        )
    )
    fig_sim.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=20, b=30),
        xaxis_title="Date",
        yaxis_title="Monthly Units",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_sim, use_container_width=True)
