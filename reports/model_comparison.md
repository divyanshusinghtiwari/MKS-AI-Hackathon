# Model Comparison & 19-Month Rolling-Origin Backtesting Report

**Evaluation Protocol**: Strictly out-of-sample 19-month time-based rolling-origin backtest (2025-04 to 2026-10).
**Target**: `Units_Unconstrained` (Unconstrained Demand)

## 1. Overall Portfolio Performance Comparison

| Model Architecture | WAPE (%) | Forecast Bias (%) | MAE (Units) | RMSE (Units) | Model Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Global LightGBM (P50 L1 Regressor)** | **32.27%** | **-7.00%** | **15.60** | **97.69** | 🥇 **Rank 1 (Best)** |
| Seasonal Naive Benchmark | 43.04% | +3.60% | 20.80 | 116.56 | 🥈 Rank 2 |
| Croston / SBA Benchmark | 54.93% | -9.54% | 26.55 | 103.14 | 🥉 Rank 3 |
| Composite Routing Baseline | 59.03% | -0.11% | 28.53 | 115.45 | Rank 4 |

## 2. Performance Breakdown by Product Family

| Product Family | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) | WAPE Gain |
| :--- | :--- | :--- | :--- | :--- |
| Brake & Safety Systems | **31.44%** | -11.94% | 42.47% | **+11.03%** |
| Chassis & Structural | **30.86%** | -7.02% | 38.27% | **+7.41%** |
| Electrical Assemblies | **34.58%** | -6.59% | 51.45% | **+16.87%** |
| Hydraulic Systems | **32.99%** | -3.92% | 47.48% | **+14.49%** |
| Powertrain Components | **32.74%** | -6.15% | 43.15% | **+10.41%** |
| Precision Machined Parts | **33.08%** | -4.67% | 40.56% | **+7.48%** |
| Thermal Management | **31.38%** | -6.57% | 41.89% | **+10.51%** |

## 3. Performance Breakdown by Intermittency Classification

| Intermittency Class | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) | WAPE Gain |
| :--- | :--- | :--- | :--- | :--- |
| `Smooth` | **26.87%** | -2.50% | 37.57% | **+10.70%** |
| `Intermittent` | **36.18%** | -7.01% | 35.47% | **-0.71%** |
| `Erratic` | **47.80%** | -26.34% | 77.14% | **+29.34%** |
| `Lumpy` | **54.38%** | -23.93% | 79.95% | **+25.57%** |

## 4. Performance Breakdown by Global Region

| Region | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) | WAPE Gain |
| :--- | :--- | :--- | :--- | :--- |
| Asia Pacific | **31.22%** | -7.20% | 42.06% | **+10.84%** |
| Europe | **29.95%** | -7.24% | 38.40% | **+8.45%** |
| India | **33.40%** | -7.18% | 42.43% | **+9.03%** |
| Latin America | **37.43%** | -10.43% | 49.59% | **+12.16%** |
| Middle East & Africa | **35.06%** | -4.55% | 57.58% | **+22.52%** |
| North America | **28.42%** | -4.34% | 36.19% | **+7.77%** |

## 5. Performance by Forecast Horizon (1 to 19 Months Ahead)

| Horizon Month | Date | LightGBM WAPE (%) | LightGBM Bias (%) | Benchmark WAPE (%) |
| :---: | :---: | :---: | :---: | :---: |
| 1 | 2025-04 | **33.47%** | -16.21% | 41.71% |
| 2 | 2025-05 | **34.04%** | -16.68% | 43.05% |
| 3 | 2025-06 | **29.84%** | -6.23% | 39.22% |
| 4 | 2025-07 | **31.50%** | -4.45% | 44.58% |
| 5 | 2025-08 | **31.43%** | -1.24% | 45.05% |
| 6 | 2025-09 | **32.69%** | -9.68% | 45.10% |
| 7 | 2025-10 | **34.46%** | -7.60% | 47.34% |
| 8 | 2025-11 | **35.37%** | -8.34% | 46.58% |
| 9 | 2025-12 | **33.30%** | +4.53% | 47.39% |
| 10 | 2026-01 | **34.59%** | -2.89% | 45.80% |
| 11 | 2026-02 | **33.78%** | +9.25% | 45.51% |
| 12 | 2026-03 | **32.78%** | -3.20% | 43.75% |
| 13 | 2026-04 | **31.87%** | -7.05% | 43.02% |
| 14 | 2026-05 | **31.28%** | -9.95% | 41.94% |
| 15 | 2026-06 | **29.72%** | -6.07% | 37.76% |
| 16 | 2026-07 | **32.01%** | -5.74% | 43.85% |
| 17 | 2026-08 | **31.16%** | -6.16% | 42.06% |
| 18 | 2026-09 | **29.76%** | -11.70% | 38.25% |
| 19 | 2026-10 | **30.41%** | -13.25% | 38.26% |
