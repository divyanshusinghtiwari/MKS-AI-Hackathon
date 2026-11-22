"""Calendar, seasonality, cyclical, holiday, and business event feature engineering."""

import numpy as np
import pandas as pd


def create_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer calendar, seasonality, cyclical, and event indicators.
    
    Task 1:
    - Month, quarter, year
    - Cyclical sine/cosine encoding of month and quarter
    - Factory holiday and shutdown indicators (European August vacation, Golden Week, CNY)
    - Macro event indicators (COVID-19 lockdown, Semiconductor shortage window, Pre-price hike)
    """
    out = df.copy()

    # Temporal components
    out["Year"] = out["Date"].str[:4].astype(int)
    out["Month"] = out["Date"].str[5:7].astype(int)
    out["Quarter"] = ((out["Month"] - 1) // 3) + 1

    # Cyclical Sine/Cosine Encodings (smooth circular representations)
    out["month_sin"] = np.sin(2.0 * np.pi * out["Month"] / 12.0).round(4)
    out["month_cos"] = np.cos(2.0 * np.pi * out["Month"] / 12.0).round(4)
    out["quarter_sin"] = np.sin(2.0 * np.pi * out["Quarter"] / 4.0).round(4)
    out["quarter_cos"] = np.cos(2.0 * np.pi * out["Quarter"] / 4.0).round(4)

    # Factory Holiday & Shutdown Indicators
    # 1. European Summer Vacation Shutdown (August)
    out["is_europe_summer_shutdown"] = (
        (out["Month"] == 8) & (out["Region"] == "Europe")
    ).astype(int)

    # 2. Golden Week in Asia Pacific (May and October)
    out["is_golden_week_month"] = (
        out["Month"].isin([5, 10]) & (out["Region"] == "Asia Pacific")
    ).astype(int)

    # 3. Lunar New Year / Spring Festival in APAC (January and February)
    out["is_cny_month"] = (
        out["Month"].isin([1, 2]) & (out["Region"] == "Asia Pacific")
    ).astype(int)

    # 4. Global Year-End Holiday Slowdown (December)
    out["is_year_end_holiday"] = (out["Month"] == 12).astype(int)

    # Commercial & Event Indicators
    # 5. Pre-Price Hike Pull-Forward Window (November & December ahead of Jan 1 price updates)
    out["is_pre_price_hike_month"] = out["Month"].isin([11, 12]).astype(int)

    # 6. Post-Price Hike Payback Month (January following price adjustment)
    out["is_post_price_hike_month"] = (out["Month"] == 1).astype(int)

    # 7. COVID-19 Global Factory Lockdown Shock Window (March - May 2020)
    out["is_covid_lockdown_period"] = (
        out["Date"].isin(["2020-03", "2020-04", "2020-05"])
    ).astype(int)

    # 8. Global Semiconductor Shortage Window (March 2021 - December 2022)
    out["is_chip_shortage_period"] = (
        (out["Date"] >= "2021-03") & (out["Date"] <= "2022-12")
    ).astype(int)

    return out
