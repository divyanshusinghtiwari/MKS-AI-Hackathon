"""Global multi-quantile LightGBM forecasting engine with P10/P50/P90 prediction intervals."""

import logging
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import lightgbm as lgb

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    # Calendar & Cyclical
    "Month",
    "Quarter",
    "month_sin",
    "month_cos",
    "quarter_sin",
    "quarter_cos",
    "is_europe_summer_shutdown",
    "is_golden_week_month",
    "is_cny_month",
    "is_year_end_holiday",
    "is_pre_price_hike_month",
    "is_post_price_hike_month",
    # Macroeconomic Drivers (contemporaneous + lags)
    "ISM_Manufacturing_PMI",
    "Auto_Production_YoY_Pct",
    "Vehicle_Inventory_Days",
    "Raw_Material_Cost_Index",
    "New_Vehicle_Orders_Index",
    "Industrial_Util_Rate_Pct",
    "Fuel_Price_Index",
    "EV_Adoption_Index",
    "ISM_Manufacturing_PMI_lag1",
    "Auto_Production_YoY_Pct_lag1",
    "New_Vehicle_Orders_Index_lag1",
    "New_Vehicle_Orders_Index_lag3",
    "Industrial_Util_Rate_Pct_lag1",
    # Intermittency & Baselines
    "adi",
    "cv2",
    "croston_baseline_rate",
    "sba_baseline_rate",
    "historical_stockout_rate",
    "historical_active_customers",
    # Lifecycle & Constraints
    "months_since_launch",
    "months_until_eol",
    "is_pre_launch",
    "is_post_eol",
    "has_replacement_sku",
    # Seasonal Anchor
    "lag_12",
    "rolling_mean_12",
]

CATEGORICAL_COLUMNS = [
    "Product_Family",
    "Region",
    "Business_Unit",
    "intermittency_class",
    "Powertrain_Application",
]


class GlobalLightGBMForecaster:
    """Trains global multi-quantile LightGBM models for probabilistic demand forecasting."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, lgb.Booster] = {}
        self.feature_importance_df: pd.DataFrame = None
        self.categorical_levels: Dict[str, List[str]] = {}

    def prepare_features(self, df: pd.DataFrame, is_train: bool = False) -> Tuple[pd.DataFrame, List[str]]:
        """Ensure consistent feature types and categories."""
        X = pd.DataFrame(index=df.index)
        used_cols = []
        for col in FEATURE_COLUMNS:
            if col in df.columns:
                X[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            else:
                X[col] = 0.0
            used_cols.append(col)

        for col in CATEGORICAL_COLUMNS:
            if is_train:
                if col in df.columns:
                    cats = sorted([str(v) for v in df[col].dropna().unique().tolist()])
                else:
                    cats = []
                self.categorical_levels[col] = cats

            cats = self.categorical_levels.get(col, None)
            if col in df.columns and cats:
                X[col] = pd.Categorical(df[col].astype(str), categories=cats)
            elif col in df.columns:
                X[col] = df[col].astype("category")
            else:
                X[col] = pd.Categorical(["Unknown"] * len(df))
            used_cols.append(col)

        return X[used_cols], used_cols

    def train(
        self,
        train_df: pd.DataFrame,
        target_col: str = "Units_Unconstrained",
        val_df: pd.DataFrame = None,
        num_boost_round: int = 150,
    ):
        """Train P10, P50, and P90 quantile regressors."""
        logger.info(f"Training Global LightGBM on {len(train_df):,} records...")
        X_train, feature_names = self.prepare_features(train_df, is_train=True)
        y_train = train_df[target_col].clip(lower=0.0).values

        train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False)

        val_data = None
        if val_df is not None:
            X_val, _ = self.prepare_features(val_df, is_train=False)
            y_val = val_df[target_col].clip(lower=0.0).values
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data, free_raw_data=False)

        # 1. Primary Model: P50 Median / L1 Regression (WAPE-aligned)
        logger.info("Training P50 (Median) Regressor...")
        params_p50 = {
            "objective": "regression_l1",
            "metric": "mae",
            "learning_rate": 0.08,
            "num_leaves": 45,
            "min_child_samples": 20,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "random_state": self.random_state,
            "verbose": -1,
        }
        self.models["p50"] = lgb.train(
            params_p50,
            train_data,
            num_boost_round=num_boost_round,
            valid_sets=[val_data] if val_data else None,
        )

        # 2. Lower Bound: P10 Quantile Regressor (alpha = 0.10)
        logger.info("Training P10 (10th percentile) Quantile Regressor...")
        params_p10 = {
            "objective": "quantile",
            "alpha": 0.10,
            "metric": "quantile",
            "learning_rate": 0.08,
            "num_leaves": 31,
            "min_child_samples": 20,
            "random_state": self.random_state,
            "verbose": -1,
        }
        self.models["p10"] = lgb.train(
            params_p10,
            train_data,
            num_boost_round=num_boost_round,
        )

        # 3. Upper Bound: P90 Quantile Regressor (alpha = 0.90)
        logger.info("Training P90 (90th percentile) Quantile Regressor...")
        params_p90 = {
            "objective": "quantile",
            "alpha": 0.90,
            "metric": "quantile",
            "learning_rate": 0.08,
            "num_leaves": 45,
            "min_child_samples": 20,
            "random_state": self.random_state,
            "verbose": -1,
        }
        self.models["p90"] = lgb.train(
            params_p90,
            train_data,
            num_boost_round=num_boost_round,
        )

        # Extract Feature Importance from P50 model
        importances_gain = self.models["p50"].feature_importance(importance_type="gain")
        importances_split = self.models["p50"].feature_importance(importance_type="split")
        self.feature_importance_df = pd.DataFrame({
            "Feature": feature_names,
            "Importance_Gain": importances_gain,
            "Importance_Split": importances_split,
        }).sort_values(by="Importance_Gain", ascending=False).reset_index(drop=True)

        logger.info(f"Top 5 LightGBM Features by Gain: {self.feature_importance_df['Feature'].head(5).tolist()}")

    def predict_quantiles(self, test_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict calibrated P10, P50, and P90 intervals with enforced monotonicity."""
        X_test, _ = self.prepare_features(test_df, is_train=False)
        
        raw_p10 = self.models["p10"].predict(X_test)
        raw_p50 = self.models["p50"].predict(X_test)
        raw_p90 = self.models["p90"].predict(X_test)

        # Enforce statistical monotonicity: 0 <= P10 <= P50 <= P90
        p10 = np.clip(raw_p10, a_min=0.0, a_max=None)
        p50 = np.maximum(p10, raw_p50)
        p90 = np.maximum(p50, raw_p90)

        return p10, p50, p90

    def save(self, output_dir: Path):
        """Save model artifacts and feature importance."""
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, model in self.models.items():
            model.save_model(str(output_dir / f"lightgbm_{name}.txt"))
        if self.feature_importance_df is not None:
            self.feature_importance_df.to_csv(output_dir / "feature_importance.csv", index=False)
        logger.info(f"LightGBM artifacts saved to {output_dir}")
