"""Celeris Automobili Industrial Demand Forecasting & Planning Control Tower.

Main Streamlit Application Entrypoint.
"""

import streamlit as st
from pathlib import Path

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Celeris Demand Control Tower",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import Dashboard Components
from src.dashboard.styles import apply_custom_styles
from src.dashboard.data_loader import (
    load_historical_demand,
    load_forecast_data,
    load_submission_data,
)
from src.dashboard.filters import render_sidebar_filters
from src.dashboard.views.executive import render_executive_view
from src.dashboard.views.data_health import render_data_health_view
from src.dashboard.views.demand_explorer import render_demand_explorer_view
from src.dashboard.views.anomaly_monitor import render_anomaly_monitor_view
from src.dashboard.views.forecast_accuracy import render_forecast_accuracy_view
from src.dashboard.views.macro_heatmap import render_macro_heatmap_view
from src.dashboard.views.what_if import render_what_if_view
from src.dashboard.views.procurement_planner import render_procurement_planner_view
from src.dashboard.views.submission_viewer import render_submission_viewer_view


def main():
    """Main application orchestrator."""
    apply_custom_styles()

    # Load Core Datasets
    hist_df = load_historical_demand()
    fc_df = load_forecast_data()

    if hist_df.empty:
        st.error("Failed to load historical demand dataset. Please ensure pipeline has completed.")
        return

    # Header Banner
    st.markdown(
        """
        <div class="control-tower-banner">
            <h1>🏭 CELERIS AUTOMOBILI INDUSTRIAL</h1>
            <p>Global Demand Forecasting & Supply Chain Planning Control Tower | MKS AI/ML Hackathon Phase 2</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar Navigation View Selector
    st.sidebar.markdown("## 🧭 Navigation Control")
    nav_view = st.sidebar.radio(
        "Select Control Tower View:",
        options=[
            "📊 Executive Overview",
            "🛡️ Data Health & Audit",
            "🔎 Demand Explorer",
            "🚨 Anomaly Monitor",
            "🎯 Forecast & Accuracy",
            "🌐 Macro Lead/Lag Heatmap",
            "🔮 What-If Simulator",
            "📦 Safety Stock & Procurement",
            "📥 Official Submission & Export",
        ],
        index=0,
    )
    st.sidebar.markdown("---")

    # Global Interactive Filters (applied across relevant views)
    filters = render_sidebar_filters(hist_df, fc_df)

    # View Router
    if nav_view == "📊 Executive Overview":
        render_executive_view(hist_df, fc_df, filters)
    elif nav_view == "🛡️ Data Health & Audit":
        render_data_health_view()
    elif nav_view == "🔎 Demand Explorer":
        render_demand_explorer_view(hist_df, filters)
    elif nav_view == "🚨 Anomaly Monitor":
        render_anomaly_monitor_view(hist_df, filters)
    elif nav_view == "🎯 Forecast & Accuracy":
        render_forecast_accuracy_view(hist_df, fc_df, filters)
    elif nav_view == "🌐 Macro Lead/Lag Heatmap":
        render_macro_heatmap_view()
    elif nav_view == "🔮 What-If Simulator":
        render_what_if_view(fc_df, filters)
    elif nav_view == "📦 Safety Stock & Procurement":
        render_procurement_planner_view(fc_df, filters)
    elif nav_view == "📥 Official Submission & Export":
        render_submission_viewer_view()


if __name__ == "__main__":
    main()
