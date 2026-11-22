"""Custom CSS styling and design system for Celeris Demand Control Tower Dashboard."""

import streamlit as st


def apply_custom_styles():
    """Apply modern executive control tower styling."""
    st.markdown(
        """
        <style>
        /* Main background and font styling */
        .main {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Metric cards */
        .metric-card {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .metric-title {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.2;
        }
        .metric-subtitle {
            font-size: 0.8rem;
            color: #475569;
            margin-top: 4px;
        }
        .metric-delta-pos {
            color: #16a34a;
            font-weight: 600;
        }
        .metric-delta-neg {
            color: #dc2626;
            font-weight: 600;
        }

        /* Status badges */
        .badge {
            display: inline-block;
            padding: 3px 8px;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 12px;
            margin-right: 6px;
        }
        .badge-success {
            background-color: #dcfce7;
            color: #15803d;
            border: 1px solid #bbf7d0;
        }
        .badge-warning {
            background-color: #fef9c3;
            color: #a16207;
            border: 1px solid #fef08a;
        }
        .badge-danger {
            background-color: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fecaca;
        }
        .badge-info {
            background-color: #e0f2fe;
            color: #0369a1;
            border: 1px solid #bae6fd;
        }
        .badge-purple {
            background-color: #f3e8ff;
            color: #7e22ce;
            border: 1px solid #e9d5ff;
        }

        /* Header banners */
        .control-tower-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 20px 24px;
            border-radius: 10px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        .control-tower-banner h1 {
            color: #ffffff !important;
            font-size: 1.75rem;
            margin: 0;
            font-weight: 700;
        }
        .control-tower-banner p {
            color: #94a3b8;
            font-size: 0.95rem;
            margin: 4px 0 0 0;
        }

        /* Callout containers */
        .callout-box {
            background-color: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 12px 16px;
            border-radius: 0 6px 6px 0;
            margin: 12px 0;
            font-size: 0.9rem;
            color: #14532d;
        }
        .callout-warning {
            background-color: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 12px 16px;
            border-radius: 0 6px 6px 0;
            margin: 12px 0;
            font-size: 0.9rem;
            color: #78350f;
        }
        .callout-simulation {
            background-color: #faf5ff;
            border-left: 4px solid #a855f7;
            padding: 12px 16px;
            border-radius: 0 6px 6px 0;
            margin: 12px 0;
            font-size: 0.9rem;
            color: #581c87;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
