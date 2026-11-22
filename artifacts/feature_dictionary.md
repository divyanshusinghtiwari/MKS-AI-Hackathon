# Feature Store Data Dictionary

**Total Records**: `247,106` rows | **Total Features**: `112` columns

| Column Name | Data Type | Feature Group | Description & Mathematical Definition |
| :--- | :--- | :--- | :--- |
| `Date` | `str` | Calendar & Events | Requested delivery month, canonical YYYY-MM. |
| `Year` | `int64` | Calendar & Events | Feature driver representing Year. |
| `Month` | `int64` | Metadata / Core | Feature driver representing Month. |
| `SKU_ID` | `str` | Metadata / Core | Canonical product identifier, [FamilyCode]-[NNN]. |
| `Region` | `str` | Metadata / Core | Canonical sales region (6 global regions). |
| `Product_Family` | `str` | Metadata / Core | Feature driver representing Product_Family. |
| `Business_Unit` | `str` | Metadata / Core | Feature driver representing Business_Unit. |
| `SKU_Description` | `str` | Metadata / Core | Feature driver representing SKU_Description. |
| `Units_Shipped` | `int64` | Metadata / Core | Actual constrained units shipped from ERP history. |
| `Units_Unconstrained` | `int64` | Target Variable | TARGET. Reconstructed unconstrained demand (includes stockout requests). |
| `Unit_Price_USD` | `float64` | Metadata / Core | Feature driver representing Unit_Price_USD. |
| `Revenue_Shipped` | `float64` | Metadata / Core | Feature driver representing Revenue_Shipped. |
| `Revenue_Unconstrained` | `float64` | Target Variable | Unconstrained dollar volume: Units_Unconstrained * Unit_Price_USD. |
| `is_stockout_month` | `bool` | Calendar & Events | Feature driver representing is_stockout_month. |
| `Stockout_Reason` | `str` | Metadata / Core | Feature driver representing Stockout_Reason. |
| `Fill_Rate_Pct` | `float64` | Macroeconomic | Feature driver representing Fill_Rate_Pct. |
| `Stockout_Days` | `int64` | Macroeconomic | Feature driver representing Stockout_Days. |
| `Carried_In_Units` | `int64` | Metadata / Core | Feature driver representing Carried_In_Units. |
| `Backordered_Units` | `int64` | Metadata / Core | Feature driver representing Backordered_Units. |
| `Lost_Units` | `int64` | Metadata / Core | Feature driver representing Lost_Units. |
| `Units_Sold` | `float64` | Metadata / Core | Feature driver representing Units_Sold. |
| `Revenue_USD` | `float64` | Metadata / Core | Feature driver representing Revenue_USD. |
| `Transaction_Count` | `float64` | Metadata / Core | Feature driver representing Transaction_Count. |
| `Return_Count` | `float64` | Metadata / Core | Feature driver representing Return_Count. |
| `Zero_Order_Count` | `float64` | Metadata / Core | Feature driver representing Zero_Order_Count. |
| `Units_Sold_Net` | `float64` | Metadata / Core | Feature driver representing Units_Sold_Net. |
| `Quarter` | `int64` | Metadata / Core | Feature driver representing Quarter. |
| `month_sin` | `float64` | Calendar & Events | Cyclical sine transformation: sin(2*pi*Month/12). |
| `month_cos` | `float64` | Calendar & Events | Cyclical cosine transformation: cos(2*pi*Month/12). |
| `quarter_sin` | `float64` | Calendar & Events | Cyclical sine transformation: sin(2*pi*Quarter/4). |
| `quarter_cos` | `float64` | Calendar & Events | Cyclical cosine transformation: cos(2*pi*Quarter/4). |
| `is_europe_summer_shutdown` | `int64` | Metadata / Core | Indicator for August European automotive plant vacation shutdown. |
| `is_golden_week_month` | `int64` | Calendar & Events | Indicator for May/October Asian manufacturing holiday periods. |
| `is_cny_month` | `int64` | Calendar & Events | Indicator for Lunar New Year / Spring Festival in Asia Pacific (Jan/Feb). |
| `is_year_end_holiday` | `int64` | Calendar & Events | Indicator for December global year-end holiday slowdown. |
| `is_pre_price_hike_month` | `int64` | Calendar & Events | Indicator for Nov/Dec commercial order pull-forward ahead of Jan 1 price adjustments. |
| `is_post_price_hike_month` | `int64` | Calendar & Events | Indicator for January demand payback following catalog price hikes. |
| `is_covid_lockdown_period` | `int64` | Calendar & Events | Indicator for COVID-19 acute plant shutdown disruption (March-May 2020). |
| `is_chip_shortage_period` | `int64` | Calendar & Events | Indicator for global semiconductor supply bottleneck window (2021-2022). |
| `lag_1` | `float64` | Time Series Lags | Unconstrained demand 1 month prior (t-1). |
| `lag_2` | `float64` | Time Series Lags | Unconstrained demand 2 months prior (t-2). |
| `lag_3` | `float64` | Time Series Lags | Unconstrained demand 3 months prior (t-3). |
| `lag_6` | `float64` | Time Series Lags | Unconstrained demand 6 months prior (t-6). |
| `lag_9` | `float64` | Time Series Lags | Unconstrained demand 9 months prior (t-9). |
| `lag_12` | `float64` | Time Series Lags | Unconstrained demand same month last year (t-12 seasonal anchor). |
| `lag_18` | `float64` | Time Series Lags | Unconstrained demand 18 months prior (t-18). |
| `lag_24` | `float64` | Time Series Lags | Unconstrained demand 2 years prior (t-24 long-term baseline). |
| `rolling_mean_3` | `float64` | Rolling & Momentum | 3-month rolling mean of past demand (shift 1). |
| `rolling_mean_6` | `float64` | Rolling & Momentum | 6-month rolling mean of past demand (shift 1). |
| `rolling_mean_12` | `float64` | Rolling & Momentum | 12-month rolling annual mean of past demand (shift 1). |
| `rolling_std_3` | `float64` | Rolling & Momentum | 3-month rolling standard deviation of past demand. |
| `rolling_std_6` | `float64` | Rolling & Momentum | 6-month rolling standard deviation of past demand. |
| `rolling_std_12` | `float64` | Rolling & Momentum | 12-month rolling standard deviation of past demand. |
| `rolling_min_6` | `float64` | Rolling & Momentum | 6-month rolling minimum demand floor. |
| `rolling_max_6` | `float64` | Rolling & Momentum | 6-month rolling maximum demand ceiling. |
| `rolling_min_12` | `float64` | Rolling & Momentum | 12-month rolling annual minimum demand floor. |
| `rolling_max_12` | `float64` | Rolling & Momentum | 12-month rolling annual maximum demand ceiling. |
| `ewma_span_3` | `float64` | Rolling & Momentum | Exponentially weighted moving average (span=3) for fast trend tracking. |
| `ewma_span_12` | `float64` | Rolling & Momentum | Exponentially weighted moving average (span=12) for smooth baseline tracking. |
| `mom_growth_rate` | `float64` | Rolling & Momentum | Month-over-month growth rate: (lag_1 - lag_2) / (lag_2 + 1). |
| `yoy_growth_rate` | `float64` | Rolling & Momentum | Year-over-year annual growth rate: (lag_1 - lag_12) / (lag_12 + 1). |
| `momentum_3m` | `float64` | Rolling & Momentum | 3-month demand acceleration momentum: (lag_1 - lag_3) / (lag_3 + 1). |
| `adi` | `float64` | Demand Intermittency | Average Demand Interval: average periods between non-zero order arrivals. |
| `cv2` | `float64` | Demand Intermittency | Squared Coefficient of Variation: variance of non-zero order batch sizes. |
| `intermittency_class` | `str` | Demand Intermittency | Syntetos-Boylan demand category: Smooth, Intermittent, Erratic, or Lumpy. |
| `croston_baseline_rate` | `float64` | Demand Intermittency | Croston smoothed demand arrival rate (size / interval). |
| `sba_baseline_rate` | `float64` | Demand Intermittency | Syntetos-Boylan Approximation de-biased demand rate. |
| `ISM_Manufacturing_PMI` | `float64` | Macroeconomic | Feature driver representing ISM_Manufacturing_PMI. |
| `Auto_Production_YoY_Pct` | `float64` | Macroeconomic | Feature driver representing Auto_Production_YoY_Pct. |
| `Vehicle_Inventory_Days` | `float64` | Macroeconomic | Feature driver representing Vehicle_Inventory_Days. |
| `Raw_Material_Cost_Index` | `float64` | Macroeconomic | Feature driver representing Raw_Material_Cost_Index. |
| `New_Vehicle_Orders_Index` | `float64` | Macroeconomic | Feature driver representing New_Vehicle_Orders_Index. |
| `Industrial_Util_Rate_Pct` | `float64` | Macroeconomic | Feature driver representing Industrial_Util_Rate_Pct. |
| `Fuel_Price_Index` | `float64` | Macroeconomic | Feature driver representing Fuel_Price_Index. |
| `EV_Adoption_Index` | `float64` | Macroeconomic | Feature driver representing EV_Adoption_Index. |
| `ISM_Manufacturing_PMI_lag1` | `float64` | Macroeconomic | Feature driver representing ISM_Manufacturing_PMI_lag1. |
| `ISM_Manufacturing_PMI_lag2` | `float64` | Macroeconomic | Feature driver representing ISM_Manufacturing_PMI_lag2. |
| `ISM_Manufacturing_PMI_lag3` | `float64` | Macroeconomic | Feature driver representing ISM_Manufacturing_PMI_lag3. |
| `Auto_Production_YoY_Pct_lag1` | `float64` | Macroeconomic | Feature driver representing Auto_Production_YoY_Pct_lag1. |
| `Auto_Production_YoY_Pct_lag2` | `float64` | Macroeconomic | Feature driver representing Auto_Production_YoY_Pct_lag2. |
| `Auto_Production_YoY_Pct_lag3` | `float64` | Macroeconomic | Feature driver representing Auto_Production_YoY_Pct_lag3. |
| `Vehicle_Inventory_Days_lag1` | `float64` | Macroeconomic | Feature driver representing Vehicle_Inventory_Days_lag1. |
| `Vehicle_Inventory_Days_lag2` | `float64` | Macroeconomic | Feature driver representing Vehicle_Inventory_Days_lag2. |
| `Vehicle_Inventory_Days_lag3` | `float64` | Macroeconomic | Feature driver representing Vehicle_Inventory_Days_lag3. |
| `Raw_Material_Cost_Index_lag1` | `float64` | Macroeconomic | Feature driver representing Raw_Material_Cost_Index_lag1. |
| `Raw_Material_Cost_Index_lag2` | `float64` | Macroeconomic | Feature driver representing Raw_Material_Cost_Index_lag2. |
| `Raw_Material_Cost_Index_lag3` | `float64` | Macroeconomic | Feature driver representing Raw_Material_Cost_Index_lag3. |
| `New_Vehicle_Orders_Index_lag1` | `float64` | Macroeconomic | Feature driver representing New_Vehicle_Orders_Index_lag1. |
| `New_Vehicle_Orders_Index_lag2` | `float64` | Macroeconomic | Feature driver representing New_Vehicle_Orders_Index_lag2. |
| `New_Vehicle_Orders_Index_lag3` | `float64` | Macroeconomic | Feature driver representing New_Vehicle_Orders_Index_lag3. |
| `Industrial_Util_Rate_Pct_lag1` | `float64` | Macroeconomic | Feature driver representing Industrial_Util_Rate_Pct_lag1. |
| `Industrial_Util_Rate_Pct_lag2` | `float64` | Macroeconomic | Feature driver representing Industrial_Util_Rate_Pct_lag2. |
| `Industrial_Util_Rate_Pct_lag3` | `float64` | Macroeconomic | Feature driver representing Industrial_Util_Rate_Pct_lag3. |
| `Fuel_Price_Index_lag1` | `float64` | Macroeconomic | Feature driver representing Fuel_Price_Index_lag1. |
| `Fuel_Price_Index_lag2` | `float64` | Macroeconomic | Feature driver representing Fuel_Price_Index_lag2. |
| `Fuel_Price_Index_lag3` | `float64` | Macroeconomic | Feature driver representing Fuel_Price_Index_lag3. |
| `EV_Adoption_Index_lag1` | `float64` | Macroeconomic | Feature driver representing EV_Adoption_Index_lag1. |
| `EV_Adoption_Index_lag2` | `float64` | Macroeconomic | Feature driver representing EV_Adoption_Index_lag2. |
| `EV_Adoption_Index_lag3` | `float64` | Macroeconomic | Feature driver representing EV_Adoption_Index_lag3. |
| `Size_Class` | `str` | Product Lifecycle | Feature driver representing Size_Class. |
| `Powertrain_Application` | `str` | Product Lifecycle | Feature driver representing Powertrain_Application. |
| `Launch_Date` | `str` | Metadata / Core | Feature driver representing Launch_Date. |
| `EOL_Date` | `str` | Metadata / Core | Feature driver representing EOL_Date. |
| `Replaces_SKU` | `str` | Metadata / Core | Feature driver representing Replaces_SKU. |
| `Lifecycle_Status` | `str` | Metadata / Core | Feature driver representing Lifecycle_Status. |
| `months_since_launch` | `int64` | Calendar & Events | Product tenure in months since Launch_Date. |
| `months_until_eol` | `int64` | Calendar & Events | Months remaining until scheduled End-Of-Life (999 if active). |
| `is_pre_launch` | `int64` | Product Lifecycle | Rule 5 constraint indicator: 1 if date is before Launch_Date (demands 0 forecast). |
| `is_post_eol` | `int64` | Product Lifecycle | Rule 5 constraint indicator: 1 if date is after EOL_Date (demands 0 forecast). |
| `has_replacement_sku` | `int64` | Product Lifecycle | Indicator that product is succeeded by or succeeds another SKU. |
| `historical_stockout_rate` | `float64` | Product Lifecycle | Historical proportion of months impacted by stockouts. |
| `historical_active_customers` | `int64` | Product Lifecycle | Number of distinct OEM customers historically ordering this SKU-Region. |
