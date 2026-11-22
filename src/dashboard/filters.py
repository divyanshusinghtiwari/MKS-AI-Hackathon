"""Sidebar filter component and filtering logic for the Control Tower Dashboard."""

from typing import Dict, Any, List
import pandas as pd
import streamlit as st


def render_sidebar_filters(
    hist_df: pd.DataFrame,
    fc_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Render unified sidebar filters and return user selections."""
    st.sidebar.markdown("### 🎛️ Control Tower Filters")

    # Combine unique values across historical and forecast data
    all_families = sorted(
        list(set(hist_df["Product_Family"].dropna().unique()).union(
            set(fc_df["Product_Family"].dropna().unique()) if not fc_df.empty else set()
        ))
    )
    all_regions = sorted(
        list(set(hist_df["Region"].dropna().unique()).union(
            set(fc_df["Region"].dropna().unique()) if not fc_df.empty else set()
        ))
    )

    # 1. Product Family Filter
    selected_families = st.sidebar.multiselect(
        "Product Family",
        options=all_families,
        default=all_families,
        help="Filter dashboard metrics by one or more product families.",
    )

    # 2. Region Filter
    selected_regions = st.sidebar.multiselect(
        "Sales Region",
        options=all_regions,
        default=all_regions,
        help="Filter metrics across global sales regions.",
    )

    # 3. Dynamic SKU Filter (filtered by selected families)
    available_skus = hist_df[hist_df["Product_Family"].isin(selected_families)]["SKU_ID"].dropna().unique()
    if not fc_df.empty:
        fc_skus = fc_df[fc_df["Product_Family"].isin(selected_families)]["SKU_ID"].dropna().unique()
        available_skus = sorted(list(set(available_skus).union(set(fc_skus))))
    else:
        available_skus = sorted(list(available_skus))

    sku_options = ["All SKUs"] + available_skus
    selected_sku = st.sidebar.selectbox(
        "Specific SKU Drill-Down",
        options=sku_options,
        index=0,
        help="Select a specific SKU to view single-item time series and lifecycle details.",
    )

    # 4. Date Range Filter
    all_dates = sorted(list(hist_df["Date"].unique()))
    if not fc_df.empty:
        all_dates = sorted(list(set(all_dates).union(set(fc_df["Date"].unique()))))

    date_range = st.sidebar.select_slider(
        "Timeline Horizon",
        options=all_dates,
        value=(all_dates[0], all_dates[-1]),
        help="Adjust timeline window spanning Jan 2019 through May 2028.",
    )

    # Quick reset button
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='font-size:0.75rem; color:#64748b; line-height:1.4;'>"
        "<b>Celeris Control Tower v2.4</b><br>"
        "Historical: 2019-01 → 2026-10<br>"
        "Forecast: 2026-11 → 2028-05 (19M)<br>"
        "Reconciliation: 100% Additive"
        "</div>",
        unsafe_allow_html=True,
    )

    return {
        "families": selected_families if selected_families else all_families,
        "regions": selected_regions if selected_regions else all_regions,
        "sku": None if selected_sku == "All SKUs" else selected_sku,
        "start_date": date_range[0],
        "end_date": date_range[1],
    }


def filter_dataframe(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply global filter selections to a dataframe."""
    if df.empty:
        return df

    filtered = df.copy()

    # Date filter
    if "Date" in filtered.columns:
        filtered = filtered[
            (filtered["Date"] >= filters["start_date"]) &
            (filtered["Date"] <= filters["end_date"])
        ]

    # Product Family filter
    if "Product_Family" in filtered.columns and filters.get("families"):
        filtered = filtered[filtered["Product_Family"].isin(filters["families"])]

    # Region filter
    if "Region" in filtered.columns and filters.get("regions"):
        filtered = filtered[filtered["Region"].isin(filters["regions"])]

    # Specific SKU filter
    if "SKU_ID" in filtered.columns and filters.get("sku"):
        filtered = filtered[filtered["SKU_ID"] == filters["sku"]]

    return filtered
