# Demand Forecasting & Planning Control Tower: Dashboard Validation Report
**MKS AI/ML Hackathon — Workstream 5: Control Tower Dashboard**  
*System: Celeris Automobili Demand Forecasting Control Tower*  
*Application Entrypoint: `app.py`*  
*Local Access URL: `http://localhost:8501`*  

---

## Executive Summary

The **Celeris Automobili Demand Forecasting & Planning Control Tower** has been built, tested, and validated as a modular, production-grade Streamlit application. The dashboard provides an interactive decision-support platform connecting the historical unconstrained market demand (Jan 2019 – Oct 2026) with the 19-month forward machine learning forecast (Nov 2026 – May 2028).

All **five official Core dashboard views** and **four advanced strategic views** specified in the official Problem Statement have been fully implemented, validated against Phase 1–4 outputs, and verified through an automated test suite.

---

## 1. Local Run Instructions

To launch the dashboard locally on any workstation:

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Launch the Streamlit application
streamlit run app.py --server.port 8501 --server.headless false
```

- **Local Web Address**: `http://localhost:8501`
- **Network Web Address**: `http://<host-ip>:8501`
- **Configuration**: Wide-screen responsive layout, sidebar navigation, cached data loaders (`@st.cache_data`), zero hardcoded absolute paths.

---

## 2. Core Dashboard Views (Official Requirements)

### View 1: 📊 Executive Overview
- **Scope**: Unified history (2019-01 → 2026-10) and forward forecast (2026-11 → 2028-05).
- **Core Visualizations**:
  - **Continuous Demand & Revenue Timeline**: Displays historical unconstrained demand, historical actual shipments (revealing stockout gaps), primary ML point forecast (P50), and P10/P90 uncertainty intervals on a single unbroken timeline.
  - **Forecast Boundary Cutoff**: A clear vertical demarcation line at `2026-10` isolates the forecast horizon.
  - **Commercial Value Trajectory**: Monthly gross revenue projection based on SKU-specific prices.
  - **Structural Mix Breakdowns**: Donut and bar charts showing demand distribution by Product Family, Sales Region, and Historical Channel.
- **Headline 19-Month KPIs**:
  - Total 19-Month Forecast Volume: **2,541,937 units**
  - Average Monthly Run-Rate: **133,786 units / month**
  - Projected Gross Commercial Revenue: **$2,154.4M ($2.15B USD)** (based on authoritative SKU-level ERP unit prices averaging $731–$944/unit, rather than an arbitrary $50 placeholder)
  - Portfolio Uncertainty Range: **P10 (1,364,670 units) to P90 (3,947,895 units)** (82.27% verified out-of-sample empirical coverage from global LightGBM quantile regression models, rather than an uncalibrated ±15% heuristic)
  - Active SKUs: **601 items across 6 global sales regions**

---

### View 2: 🛡️ Data Health & Audit
- **Scope**: Comprehensive audit trail and defect resolution metrics from Phase 1.
- **Core Visualizations**:
  - **Issues by Type & File**: Detailed audit table detailing defect categories, affected files, raw defect counts, cleaned status, and resolution logic.
  - **Resolution Waterfall**: Visual breakdown of remediated records:
    - Rule 2 Deduplications: **3,682 duplicates removed** via latest `Load_Timestamp`
    - Missing Units Recovery: **3,208 records recovered** via `Revenue / Price` zero-remainder check
    - SKU Taxonomy Normalization: **1,840 records standardized** (`CHS` $\rightarrow$ `CSS`, zero padding)
    - Pricing Multiplier Corrections: **1,506 rows fixed** for 100x clerical error
    - Missing Region Imputation: **942 rows resolved** via customer master profile
    - Rule 1 Date Authority: **246 year/month conflicts corrected**
  - **Reference Data Audit**: Completeness checklists for `sku_master.csv`, `macro_indicators.csv`, and `inventory_stockouts.csv`.
  - **Data Completeness**: **100% verified** with 0 remaining nulls or unmapped keys.

---

### View 3: 🔎 Demand Explorer
- **Scope**: Granular drill-down across the product and customer hierarchy.
- **Core Visualizations**:
  - **Hierarchical Drill-Down**: Interactive selector for Product Family $\rightarrow$ SKU $\rightarrow$ Sales Region $\rightarrow$ Customer account.
  - **SKU Metadata & Lifecycle Header**: Displays SKU ID, Family, Business Unit, Lifecycle Status (Active vs. EOL Scheduled), Launch Date, EOL Date, and Predecessor/Replacement mappings.
  - **Individual Monthly Time Series**: Interactive Plotly line chart comparing unconstrained demand against shipped units.
  - **Annual Seasonality Profile**: Monthly demand distribution (Months 1 to 12) illustrating seasonal peaks and dips.
  - **Zero-Demand Intermittency**: Explicit tracking of zero-order months and transaction frequency.
  - **Top Customer Account Mix**: Summary table of primary customer volume for the selected SKU.

---

### View 4: 🚨 Anomaly Monitor
- **Scope**: 13,231 detected anomalies from Phase 2 classified into distinct business categories.
- **Core Visualizations**:
  - **Time Series with Overlay Markers**: Monthly portfolio demand timeline with color-coded scatter markers sized by anomaly incident volume:
    - 🔴 **Supply Constraints**: 5,830 stockout incidents, fill rate drops, and allocation shortfalls.
    - 🟢 **Genuine Business Events**: Pre-price hike purchasing surges, European summer shutdowns, Golden Week, and CNY.
    - 🟣 **Unusual Legitimate Demand**: Valid non-recurring large customer bulk orders.
    - 🟡 **Data Quality Errors**: Clerical and load errors remediated in Phase 1.
  - **Stockout Root Cause Breakdown**: Bar chart categorizing stockouts by reported driver (e.g. Semiconductor allocation, Logistics delays).
  - **Severity Breakdown**: Distribution across Critical, High, Medium, and Low severity tiers.
  - **Interactive Anomaly Register Table**: Filterable table showing Date, SKU_ID, Region, Observed Demand, Anomaly Type, Severity, Detection Method, Explanation, and Recommended Planner Action.

---

### View 5: 🎯 Forecast & Accuracy
- **Scope**: Out-of-sample rolling-origin backtesting scorecard and probabilistic interval diagnostics.
- **Core Visualizations**:
  - **Probabilistic Fan Chart**: History plus P10 (conservative capacity), P50 (primary WAPE-optimal median), and P90 (procurement safety stock) intervals.
  - **Benchmark Scorecard**: Direct comparison of Global LightGBM against Seasonal Naive, Croston/SBA, and Composite Baselines:
    - Global LightGBM: **WAPE = 32.27%**, Bias = -7.00%, MAE = 15.60, RMSE = 97.69 (🥇 Rank 1)
    - Seasonal Naive: **WAPE = 43.04%**, Bias = +3.60%, MAE = 20.80, RMSE = 116.56 (🥈 Rank 2)
    - Croston / SBA: **WAPE = 54.93%**, Bias = -9.54%, MAE = 26.55, RMSE = 103.14 (🥉 Rank 3)
    - Composite Baseline: **WAPE = 59.03%**, Bias = -0.11%, MAE = 28.53, RMSE = 115.45
  - **Horizon Accuracy (1 to 19 Months)**: Line chart demonstrating accuracy stability across all 19 forecast months.
  - **Product Family WAPE Gains**: Bar chart illustrating +7.41% to +16.87% WAPE improvements across all 7 families.
  - **Top Feature Drivers**: Horizontal bar chart of the top 10 LightGBM features by gain (`lag_12`, `croston_baseline_rate`, `adi`, `EV_Adoption_Index`, `rolling_mean_12`).
  - **Transparent Performance Disclosures**:
    - Clear display and explanation of the **-7.00% portfolio bias**.
    - Disclosure of LightGBM's comparable performance on pure intermittent series.
    - Advisory note that predictions are statistical estimates, not guaranteed demand.

---

## 3. Advanced Strategic Views

### View 6: 🌐 Macro Lead/Lag Heatmap
- **Capability**: Interactive cross-correlation matrix between 8 macroeconomic indicators and all 7 product families.
- **Interactivity**: Slider allowing planners to vary the lead/lag horizon from 0 to 6 months.
- **Key Empirical Dynamics**: Visualizes EV adoption leading Electrical Assemblies ($r = +0.75$) and New Vehicle Orders leading Hydraulics at Lag 1 ($r = +0.69$).

### View 7: 🔮 What-If Scenario Simulator
- **Capability**: Real-time stress testing of the 19-month forecast under macroeconomic shocks:
  - ISM Manufacturing PMI shock ($\pm 10$ points)
  - Auto Production YoY% shock ($\pm 20\%$)
  - EV Adoption Index acceleration ($\pm 25\%$)
  - General discretionary demand shift ($\pm 30\%$)
- **Simulation Isolation**: Employs empirical elasticity models; prominently displays notice that calculations are simulated and **do not overwrite official production forecasts or `submission.csv`**.

### View 8: 📦 Safety Stock & Procurement Planner
- **Capability**: Translates probabilistic P90 upper demand bounds into actionable supply chain inventory parameters.
- **Configurable Parameters**: Configurable supplier lead time (1 to 6 months) and target cycle service levels (95% P90 vs. P95 extended).
- **Outputs**: Computes Average Monthly Demand, Lead Time Demand ($LTD = D \times L$), Recommended Safety Stock ($SS = (P90 - P50) \times \sqrt{L}$), and Reorder Point ($ROP = LTD + SS$).
- **Compliance**: Clearly labeled as *calculated planning guidance* rather than confirmed purchase orders.

### View 9: 📥 Official Submission & Data Export
- **Capability**: Live inspection of the official competition submission artifact.
- **Validation Metrics**: Exactly 58,219 rows, zero nulls, non-negative integers, verified 100% key alignment with `test.csv`.
- **One-Click Download**: Direct download button for `submission.csv`.
- **Searchable Browser**: Instant filtering and lookup by SKU ID or Region.

---

## 4. Data Lineage and Source Matrix

| Dashboard View | Primary Data Sources Used |
| :--- | :--- |
| **Executive Overview** | `data/cleaned/demand_reconstructed.parquet`<br>`artifacts/forecasts_with_intervals.parquet`<br>`submission.csv` |
| **Data Health & Audit** | `reports/data_quality_report.json`<br>`reports/data_quality_report.md` |
| **Demand Explorer** | `data/cleaned/demand_reconstructed.parquet`<br>`data/cleaned/sku_master_cleaned.csv` |
| **Anomaly Monitor** | `reports/anomaly_register.csv`<br>`reports/anomaly_summary.json`<br>`data/cleaned/demand_reconstructed.parquet` |
| **Forecast & Accuracy** | `reports/backtest_results.csv`<br>`reports/backtest_summary.json`<br>`reports/model_comparison.md`<br>`reports/feature_importance.csv`<br>`artifacts/forecasts_with_intervals.parquet` |
| **Macro Heatmap** | `data/cleaned/macro_indicators_cleaned.csv`<br>`data/cleaned/demand_reconstructed.parquet` |
| **What-If Simulator** | `artifacts/forecasts_with_intervals.parquet` |
| **Procurement Planner** | `artifacts/forecasts_with_intervals.parquet` |
| **Submission Viewer** | `submission.csv` |

---

## 5. Automated Test Suite Validation

The dashboard test suite was verified via pytest (`pytest tests/test_dashboard.py -v`):
- `test_dashboard_data_artifacts_exist`: PASSED (all required data artifacts exist and load)
- `test_continuous_timeline_transformation`: PASSED (seamless history-to-forecast merging)
- `test_filter_dataframe_logic`: PASSED (multi-dimension filter responsiveness)
- `test_what_if_simulation_isolation`: PASSED (source data immutability during simulation)
- `test_procurement_safety_stock_formulas`: PASSED (valid inventory planning formulas)

**Overall Test Suite**: **30 passed in 2.90s** (100% pass rate across Phases 1 through 5).

---
*Generated for MKS AI/ML Hackathon Phase 2 Evaluation.*
