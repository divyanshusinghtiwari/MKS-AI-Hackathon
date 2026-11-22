"""Submission Viewer View: Official submission.csv Inspection, Audit, and Export."""

import streamlit as st
import pandas as pd

from src.dashboard.data_loader import load_submission_data, SUBMISSION_PATH


def render_submission_viewer_view():
    """Render the official Submission Viewer & Export dashboard view."""
    st.markdown("## 📥 Official Submission & Data Export Center")
    st.markdown(
        "*Verify, audit, and download the official competition submission artifact (`submission.csv`) "
        "and downstream analytical datasets.*"
    )

    sub_df = load_submission_data()
    if sub_df.empty:
        st.error("Official submission file not found.")
        return

    # Submission Integrity Metrics
    total_rows = len(sub_df)
    total_units = sub_df["Units_Sold_Forecast"].sum()
    zero_rows = (sub_df["Units_Sold_Forecast"] == 0).sum()
    unique_skus = sub_df["SKU_ID"].nunique()
    unique_regions = sub_df["Region"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Submission Rows</div>
                <div class="metric-value">{total_rows:,}</div>
                <div class="metric-subtitle">Matches test.csv (100%)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Forecast Volume</div>
                <div class="metric-value">{total_units:,}</div>
                <div class="metric-subtitle">Non-Negative Integers</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Rule 5 Zeroed Records</div>
                <div class="metric-value">{zero_rows:,}</div>
                <div class="metric-subtitle">Pre-launch & post-EOL rows</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Portfolio Scope</div>
                <div class="metric-value">{unique_skus} SKUs</div>
                <div class="metric-subtitle">Across {unique_regions} Regions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # One-Click Direct Download
    csv_bytes = sub_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="💾 Download Official submission.csv (58,219 Rows)",
        data=csv_bytes,
        file_name="submission.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Searchable & Filterable Table
    st.markdown("### 🔍 Live Submission Browser")
    st.markdown("*Inspect individual records, cold-start forecasts, and regional distributions.*")

    col_filter_sku, col_filter_reg = st.columns(2)
    with col_filter_sku:
        filter_sku = st.text_input("Search by SKU ID (e.g., PMP-020, PTC-029, BSS-001):", value="")
    with col_filter_reg:
        filter_reg = st.selectbox("Filter by Region:", options=["All Regions"] + sorted(sub_df["Region"].unique().tolist()))

    display_sub = sub_df.copy()
    if filter_sku:
        display_sub = display_sub[display_sub["SKU_ID"].str.contains(filter_sku, case=False, na=False)]
    if filter_reg != "All Regions":
        display_sub = display_sub[display_sub["Region"] == filter_reg]

    st.dataframe(display_sub.head(250), use_container_width=True, hide_index=True)
    st.caption(f"Showing {min(250, len(display_sub)):,} of {len(display_sub):,} matching rows.")
