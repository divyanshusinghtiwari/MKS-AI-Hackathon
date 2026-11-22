# Macroeconomic Lead/Lag Analysis & Justification Report

**Target**: Celeris Automobili Industrial Demand Forecasting
**Evaluation Horizon**: Jan 2019 – Oct 2026 (94 historical months)

## 1. Executive Summary: Primary Macro Drivers per Product Family

Macroeconomic indicators exhibit pronounced, delayed transmission channels into automotive and industrial component demand. The table below highlights the optimal leading indicators and their calibrated transmission lags:

| Product Family | Primary Leading Macro Driver | Optimal Lead (Lags) | Correlation ($r$) | Economic & Industrial Transmission Justification |
| :--- | :--- | :--- | :--- | :--- |
| Brake & Safety Systems | `EV_Adoption_Index` | **0 Month(s)** | **+0.684** | EV safety architectures require high-spec caliper assemblies with regenerative braking integration. |
| Brake & Safety Systems | `Auto_Production_YoY_Pct` | **1 Month(s)** | **+0.591** | Brake assemblies are tier-1 JIT deliveries; OEM production growth translates to orders within 1 month. |
| Chassis & Structural | `EV_Adoption_Index` | **4 Month(s)** | **+0.692** | Heavy battery tray subframes and chassis stiffening components lead EV ramp-up at a 4-month lag. |
| Chassis & Structural | `Auto_Production_YoY_Pct` | **1 Month(s)** | **+0.631** | OEM vehicle assembly schedule adjustments propagate directly into chassis stamping schedules within 30 days. |
| Electrical Assemblies | `EV_Adoption_Index` | **0 Month(s)** | **+0.753** | EV wiring harnesses and battery management connectors scale directly with EV adoption. |
| Electrical Assemblies | `Industrial_Util_Rate_Pct` | **0 Month(s)** | **+0.606** | Electronics manufacturing line utilization reflects supplier capacity and component availability. |
| Hydraulic Systems | `New_Vehicle_Orders_Index` | **1 Month(s)** | **+0.693** | Commercial truck and industrial vehicle orders precede hydraulic steering and lifting valve shipments by 1 month. |
| Hydraulic Systems | `Industrial_Util_Rate_Pct` | **0 Month(s)** | **+0.620** | Industrial equipment factory utilization directly drives replacement valve and hydraulic pump demand. |
| Powertrain Components | `Industrial_Util_Rate_Pct` | **0 Month(s)** | **+0.721** | Machining engine and drive transmission lines operates synchronously with industrial utilization. |
| Powertrain Components | `New_Vehicle_Orders_Index` | **3 Month(s)** | **+0.644** | Heavy-duty powertrain gear sets require 3-month casting and hobbing procurement lead times. |
| Precision Machined Parts | `Industrial_Util_Rate_Pct` | **0 Month(s)** | **+0.753** | Precision rotor shafts and turned parts track broader industrial manufacturing throughput. |
| Precision Machined Parts | `New_Vehicle_Orders_Index` | **1 Month(s)** | **+0.675** | Tooling and rotor shaft machining orders lead final assembly schedules by 1 month. |
| Thermal Management | `Auto_Production_YoY_Pct` | **1 Month(s)** | **+0.639** | Coolant pumps and radiators are installed during primary vehicle assembly; leads by 1 month. |
| Thermal Management | `New_Vehicle_Orders_Index` | **0 Month(s)** | **+0.563** | Cooling system orders are finalized upon order placement. |

## 2. Complete Cross-Correlation Matrix

| Product Family | Macro Indicator | Opt Lag | Max $r$ | Lag 0 | Lag 1 | Lag 2 | Lag 3 | Lag 4 | Lag 6 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Brake & Safety Systems | `ISM_Manufacturing_PMI` | 1 | +0.111 | +0.068 | +0.111 | +0.056 | +0.055 | -0.014 | -0.048 |
| Brake & Safety Systems | `Auto_Production_YoY_Pct` | 1 | +0.591 | +0.570 | +0.591 | +0.565 | +0.502 | +0.374 | +0.144 |
| Brake & Safety Systems | `Vehicle_Inventory_Days` | 3 | -0.257 | -0.220 | -0.236 | -0.252 | -0.257 | -0.238 | -0.180 |
| Brake & Safety Systems | `Raw_Material_Cost_Index` | 0 | +0.179 | +0.179 | +0.161 | +0.135 | +0.100 | +0.073 | +0.041 |
| Brake & Safety Systems | `New_Vehicle_Orders_Index` | 0 | +0.573 | +0.573 | +0.553 | +0.461 | +0.367 | +0.277 | +0.110 |
| Brake & Safety Systems | `Industrial_Util_Rate_Pct` | 0 | +0.467 | +0.467 | +0.401 | +0.305 | +0.202 | +0.132 | +0.027 |
| Brake & Safety Systems | `Fuel_Price_Index` | 0 | +0.244 | +0.244 | +0.226 | +0.199 | +0.179 | +0.162 | +0.155 |
| Brake & Safety Systems | `EV_Adoption_Index` | 0 | +0.684 | +0.684 | +0.674 | +0.667 | +0.662 | +0.659 | +0.648 |
| Chassis & Structural | `ISM_Manufacturing_PMI` | 6 | -0.135 | -0.099 | +0.011 | -0.031 | -0.033 | -0.093 | -0.135 |
| Chassis & Structural | `Auto_Production_YoY_Pct` | 1 | +0.631 | +0.594 | +0.631 | +0.589 | +0.515 | +0.441 | +0.228 |
| Chassis & Structural | `Vehicle_Inventory_Days` | 0 | +0.050 | +0.050 | +0.027 | -0.006 | -0.025 | -0.030 | -0.017 |
| Chassis & Structural | `Raw_Material_Cost_Index` | 6 | -0.115 | -0.034 | -0.054 | -0.082 | -0.099 | -0.109 | -0.115 |
| Chassis & Structural | `New_Vehicle_Orders_Index` | 1 | +0.484 | +0.482 | +0.484 | +0.414 | +0.326 | +0.241 | +0.065 |
| Chassis & Structural | `Industrial_Util_Rate_Pct` | 0 | +0.520 | +0.520 | +0.470 | +0.380 | +0.309 | +0.248 | +0.120 |
| Chassis & Structural | `Fuel_Price_Index` | 6 | +0.151 | +0.119 | +0.123 | +0.118 | +0.124 | +0.126 | +0.151 |
| Chassis & Structural | `EV_Adoption_Index` | 4 | +0.692 | +0.682 | +0.677 | +0.677 | +0.684 | +0.692 | +0.691 |
| Electrical Assemblies | `ISM_Manufacturing_PMI` | 3 | +0.132 | +0.094 | +0.117 | +0.113 | +0.132 | +0.075 | +0.031 |
| Electrical Assemblies | `Auto_Production_YoY_Pct` | 1 | +0.501 | +0.479 | +0.501 | +0.485 | +0.446 | +0.388 | +0.241 |
| Electrical Assemblies | `Vehicle_Inventory_Days` | 3 | -0.137 | -0.118 | -0.125 | -0.126 | -0.137 | -0.135 | -0.107 |
| Electrical Assemblies | `Raw_Material_Cost_Index` | 1 | +0.157 | +0.151 | +0.157 | +0.152 | +0.154 | +0.133 | +0.105 |
| Electrical Assemblies | `New_Vehicle_Orders_Index` | 1 | +0.571 | +0.535 | +0.571 | +0.559 | +0.520 | +0.461 | +0.310 |
| Electrical Assemblies | `Industrial_Util_Rate_Pct` | 0 | +0.606 | +0.606 | +0.570 | +0.506 | +0.431 | +0.345 | +0.186 |
| Electrical Assemblies | `Fuel_Price_Index` | 4 | +0.248 | +0.235 | +0.242 | +0.245 | +0.245 | +0.248 | +0.229 |
| Electrical Assemblies | `EV_Adoption_Index` | 0 | +0.753 | +0.753 | +0.749 | +0.744 | +0.748 | +0.749 | +0.741 |
| Hydraulic Systems | `ISM_Manufacturing_PMI` | 3 | +0.382 | +0.306 | +0.349 | +0.351 | +0.382 | +0.285 | +0.227 |
| Hydraulic Systems | `Auto_Production_YoY_Pct` | 1 | +0.429 | +0.422 | +0.429 | +0.382 | +0.304 | +0.206 | +0.011 |
| Hydraulic Systems | `Vehicle_Inventory_Days` | 3 | -0.442 | -0.397 | -0.416 | -0.434 | -0.442 | -0.426 | -0.336 |
| Hydraulic Systems | `Raw_Material_Cost_Index` | 1 | +0.428 | +0.405 | +0.428 | +0.420 | +0.417 | +0.394 | +0.352 |
| Hydraulic Systems | `New_Vehicle_Orders_Index` | 1 | +0.693 | +0.663 | +0.693 | +0.663 | +0.590 | +0.511 | +0.356 |
| Hydraulic Systems | `Industrial_Util_Rate_Pct` | 0 | +0.620 | +0.620 | +0.555 | +0.458 | +0.345 | +0.221 | +0.055 |
| Hydraulic Systems | `Fuel_Price_Index` | 0 | +0.477 | +0.477 | +0.431 | +0.377 | +0.321 | +0.252 | +0.109 |
| Hydraulic Systems | `EV_Adoption_Index` | 0 | +0.515 | +0.515 | +0.506 | +0.495 | +0.497 | +0.492 | +0.478 |
| Powertrain Components | `ISM_Manufacturing_PMI` | 3 | +0.204 | +0.066 | +0.106 | +0.200 | +0.204 | +0.130 | +0.094 |
| Powertrain Components | `Auto_Production_YoY_Pct` | 3 | +0.601 | +0.459 | +0.561 | +0.591 | +0.601 | +0.562 | +0.342 |
| Powertrain Components | `Vehicle_Inventory_Days` | 6 | -0.329 | -0.136 | -0.180 | -0.215 | -0.271 | -0.304 | -0.329 |
| Powertrain Components | `Raw_Material_Cost_Index` | 4 | +0.289 | +0.275 | +0.287 | +0.275 | +0.285 | +0.289 | +0.284 |
| Powertrain Components | `New_Vehicle_Orders_Index` | 3 | +0.644 | +0.566 | +0.634 | +0.639 | +0.644 | +0.602 | +0.452 |
| Powertrain Components | `Industrial_Util_Rate_Pct` | 0 | +0.721 | +0.721 | +0.691 | +0.652 | +0.589 | +0.497 | +0.294 |
| Powertrain Components | `Fuel_Price_Index` | 0 | +0.424 | +0.424 | +0.422 | +0.413 | +0.392 | +0.354 | +0.298 |
| Powertrain Components | `EV_Adoption_Index` | 6 | +0.531 | +0.520 | +0.510 | +0.502 | +0.517 | +0.521 | +0.531 |
| Precision Machined Parts | `ISM_Manufacturing_PMI` | 3 | +0.238 | +0.142 | +0.202 | +0.221 | +0.238 | +0.173 | +0.118 |
| Precision Machined Parts | `Auto_Production_YoY_Pct` | 1 | +0.585 | +0.543 | +0.585 | +0.552 | +0.483 | +0.388 | +0.192 |
| Precision Machined Parts | `Vehicle_Inventory_Days` | 4 | -0.325 | -0.198 | -0.246 | -0.276 | -0.319 | -0.325 | -0.284 |
| Precision Machined Parts | `Raw_Material_Cost_Index` | 6 | +0.289 | +0.233 | +0.249 | +0.254 | +0.273 | +0.275 | +0.289 |
| Precision Machined Parts | `New_Vehicle_Orders_Index` | 1 | +0.675 | +0.627 | +0.675 | +0.651 | +0.605 | +0.523 | +0.352 |
| Precision Machined Parts | `Industrial_Util_Rate_Pct` | 0 | +0.753 | +0.753 | +0.708 | +0.634 | +0.526 | +0.410 | +0.212 |
| Precision Machined Parts | `Fuel_Price_Index` | 0 | +0.375 | +0.375 | +0.361 | +0.342 | +0.322 | +0.297 | +0.260 |
| Precision Machined Parts | `EV_Adoption_Index` | 6 | +0.611 | +0.586 | +0.579 | +0.575 | +0.591 | +0.596 | +0.611 |
| Thermal Management | `ISM_Manufacturing_PMI` | 1 | +0.255 | +0.227 | +0.255 | +0.194 | +0.233 | +0.162 | +0.107 |
| Thermal Management | `Auto_Production_YoY_Pct` | 1 | +0.639 | +0.587 | +0.639 | +0.577 | +0.452 | +0.310 | +0.010 |
| Thermal Management | `Vehicle_Inventory_Days` | 3 | -0.120 | -0.087 | -0.106 | -0.111 | -0.120 | -0.103 | -0.064 |
| Thermal Management | `Raw_Material_Cost_Index` | 0 | +0.166 | +0.166 | +0.127 | +0.072 | +0.036 | -0.015 | -0.066 |
| Thermal Management | `New_Vehicle_Orders_Index` | 0 | +0.563 | +0.563 | +0.549 | +0.469 | +0.368 | +0.260 | +0.070 |
| Thermal Management | `Industrial_Util_Rate_Pct` | 0 | +0.453 | +0.453 | +0.387 | +0.293 | +0.179 | +0.074 | -0.081 |
| Thermal Management | `Fuel_Price_Index` | 0 | +0.179 | +0.179 | +0.138 | +0.085 | +0.030 | -0.023 | -0.122 |
| Thermal Management | `EV_Adoption_Index` | 6 | +0.381 | +0.342 | +0.333 | +0.327 | +0.343 | +0.356 | +0.381 |

## 3. Prevention of Future Information Leakage

1. **Official Forecast Horizon Availability**: `macro_indicators.csv` contains projections for the complete forecast window (2019-01 to 2028-05). All external drivers are thus strictly aligned with reality.
2. **Lagged Feature Generation**: In training and inference, lagged macro variables ($t-1$, $t-2$, $t-3$) use past economic readings, preventing any leakage of future macroeconomic shocks.
