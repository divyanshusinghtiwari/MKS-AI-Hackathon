# Workstream 2: Anomaly Detection & Unconstrained Demand Reconstruction Report

**Target**: Celeris Automobili Industrial Demand Forecasting Control Tower
**Status**: ✅ `COMPLETED_SUCCESSFULLY`

## 1. Executive Summary & Demand Gap

In Workstream 2, supply-constrained sales history (`train.csv`) was reconciled with `inventory_stockouts.csv` to reconstruct true market demand. A multi-lens anomaly detection system was applied across macroeconomic shocks, commercial price elasticity pull-forward, plant shutdowns, and structural technology transitions.

### Key Reconstruction Metrics
- **Total Shipped Volume**: `12,037,763` units
- **Total True Unconstrained Market Demand**: `12,131,045` units
- **Recovered Unserved Demand Gap**: `+93,282` units
- **Total Lost Sales Recovered**: `81,827` units across `5,830` supply-constrained months
- **Balance Equation Verification**: `Requested_Units + Carried_In_Units == Shipped_Units + Backordered_Units + Lost_Units` verified with **100% exact equality (0 discrepancies)**.
- **Backorder Non-Double-Counting**: True new monthly demand is isolated via `Requested_Units`, preventing double-counting of previous-month carry-in orders.

## 2. Anomaly Classification Breakdown

### By Business Category

| Business Category | Count | Strategic Interpretation & Model Treatment |
| :--- | :--- | :--- |
| `SUPPLY_CONSTRAINT` | 5,830 | External supply bottlenecks (chip shortage, supplier quality). Replaced with unconstrained demand. |
| `GENUINE_BUSINESS_EVENT` | 6,632 | Macro/commercial shocks (COVID dip, pre-price hike buying, EV transition). Modeled with features. |
| `UNUSUAL_LEGITIMATE_DEMAND` | 769 | Authentic OEM batch purchases / tender spikes. Retained in training; regularized with robust loss. |

### By Anomaly Type

| Anomaly Type | Total Detected | Primary Root Cause & Modeling Action |
| :--- | :--- | :--- |
| `MACRO_CHIP_SHORTAGE` | 4,314 | Cataloged in `anomaly_register.csv` with recommended actions. |
| `MACRO_PANDEMIC_DISRUPTION` | 2,553 | Cataloged in `anomaly_register.csv` with recommended actions. |
| `STRUCTURAL_BREAK_EV` | 2,242 | Cataloged in `anomaly_register.csv` with recommended actions. |
| `SUPPLY_STOCKOUT` | 1,516 | Cataloged in `anomaly_register.csv` with recommended actions. |
| `HOLIDAY_SEASONAL_SHUTDOWN` | 1,124 | Cataloged in `anomaly_register.csv` with recommended actions. |
| `STATISTICAL_SPIKE` | 769 | Cataloged in `anomaly_register.csv` with recommended actions. |
| `PRICE_HIKE_PULL_FORWARD` | 713 | Cataloged in `anomaly_register.csv` with recommended actions. |

## 3. Deep-Dive Business Analysis

### A. The Global Semiconductor Allocation Crisis (2021–2022)
Over **4,300 stockout events** were driven by semiconductor allocations, heavily concentrated in `Electrical Assemblies` (`ELA-xxx`). Using unconstrained demand restores the true underlying trajectory rather than learning false demand depression.

### B. Pre-Price Hike Pull-Forward Buying (Q4 Elasticity)
Under Business Rule 4, catalog prices increase annually on January 1. Analysis reveals repeated spikes in November/December (e.g., Dec 2022 volume surged before the +5.0% price rise, followed by a 24.3% drop in Jan 2023). Model recommendation: Engineer pre-hike lead features to capture this cyclical demand pull-forward.

### C. Structural Break: Accelerating EV Adoption
EV product sales experienced exponential growth, climbing from 44 units in 2019 to over 160,000 units in 2024–2026, while conventional ICE component sales declined. The `EV_Adoption_Index` in `macro_indicators.csv` will serve as a primary dynamic driver.

### D. European Summer Plant Shutdowns (August)
European automotive manufacturing consistently experiences seasonal volume drops of 40–60% during August plant vacation shutdowns. Model recommendation: Standard calendar month-of-year seasonal decomposition.
