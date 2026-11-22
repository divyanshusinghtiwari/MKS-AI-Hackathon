"""Orchestrator for Workstream 3: Feature Engineering & Macroeconomic Drivers."""

import json
import logging
import sys
from pathlib import Path
import pandas as pd

from src.config import CLEANED_DATA_DIR, REPORTS_DIR, ARTIFACTS_DIR
from src.features.store import build_feature_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_workstream_3_pipeline(
    cleaned_dir: Path = CLEANED_DATA_DIR,
    reports_dir: Path = REPORTS_DIR,
    artifacts_dir: Path = ARTIFACTS_DIR,
) -> dict:
    """Execute end-to-end Workstream 3 feature engineering pipeline."""
    logger.info("=== STARTING WORKSTREAM 3: FEATURE ENGINEERING & MACRO DRIVERS ===")

    # 1. Load Cleaned Datasets
    logger.info("Step 1: Loading reconstructed demand, macro indicators, and master data...")
    demand_df = pd.read_parquet(cleaned_dir / "demand_reconstructed.parquet")
    macro_df = pd.read_csv(cleaned_dir / "macro_indicators_cleaned.csv")
    sku_master_df = pd.read_csv(cleaned_dir / "sku_master_cleaned.csv")
    raw_train_cleaned_df = pd.read_parquet(cleaned_dir / "train_cleaned.parquet")

    # 2. Assemble Feature Store
    logger.info("Step 2: Engineering features across calendar, time-series, intermittency, macro, and lifecycle blocks...")
    features_df, macro_corr_df, macro_analysis_md, quality_report = build_feature_store(
        demand_df=demand_df,
        macro_df=macro_df,
        sku_master_df=sku_master_df,
        raw_train_cleaned_df=raw_train_cleaned_df,
        output_dir=cleaned_dir,
    )

    # 3. Export Engineered Parquet
    logger.info(f"Step 3: Saving features_engineered.parquet ({len(features_df):,} rows, {len(features_df.columns)} cols)...")
    feat_parquet_path = cleaned_dir / "features_engineered.parquet"
    features_df.to_parquet(feat_parquet_path, index=False)
    features_df.to_parquet(artifacts_dir / "features_engineered.parquet", index=False)

    # 4. Export Documentation & Reports
    logger.info("Step 4: Exporting feature dictionary and macro correlation reports...")
    with open(reports_dir / "feature_dictionary.md", "w", encoding="utf-8") as f:
        f.write(generate_feature_dictionary_content(features_df))
    with open(artifacts_dir / "feature_dictionary.md", "w", encoding="utf-8") as f:
        f.write(generate_feature_dictionary_content(features_df))

    with open(reports_dir / "macro_correlation_analysis.md", "w", encoding="utf-8") as f:
        f.write(macro_analysis_md)
    with open(artifacts_dir / "macro_correlation_analysis.md", "w", encoding="utf-8") as f:
        f.write(macro_analysis_md)

    with open(reports_dir / "feature_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)
    with open(artifacts_dir / "feature_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)

    logger.info("=== WORKSTREAM 3 PIPELINE COMPLETED SUCCESSFULLY ===")
    return quality_report


def generate_feature_dictionary_content(df: pd.DataFrame) -> str:
    """Helper to return feature dictionary string."""
    from src.features.store import generate_feature_dictionary
    return generate_feature_dictionary(df)


if __name__ == "__main__":
    run_workstream_3_pipeline()
