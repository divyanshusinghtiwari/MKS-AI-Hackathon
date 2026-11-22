"""Orchestrator for Workstream 1: Data Cleaning & Quality Pipeline."""

import logging
import sys
from pathlib import Path
import pandas as pd

from src.config import CLEANED_DATA_DIR, REPORTS_DIR
from src.data.loader import load_all_raw_datasets
from src.data.audit import AuditTrail
from src.data.cleaner import (
    clean_train_data,
    clean_sku_master,
    clean_macro_indicators,
    clean_inventory_stockouts,
    clean_events_calendar,
    validate_test_data,
)
from src.data.aggregator import aggregate_to_date_sku_region, build_regularized_panel_grid
from src.data.quality_report import generate_quality_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_data_cleaning_pipeline(
    cleaned_dir: Path = CLEANED_DATA_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> dict:
    """Execute the end-to-end Workstream 1 data cleaning and quality pipeline."""
    logger.info("=== STARTING WORKSTREAM 1 DATA CLEANING PIPELINE ===")
    audit = AuditTrail()

    # 1. Load raw datasets safely (read-only)
    logger.info("Step 1: Loading all 7 raw datasets...")
    raw_data = load_all_raw_datasets()

    # 2. Clean SKU Master first (needed for lookups)
    logger.info("Step 2: Cleaning SKU Master...")
    cleaned_sku_master = clean_sku_master(raw_data["sku_master"], audit)

    # 3. Clean Train Transactions
    logger.info("Step 3: Cleaning raw transactions (train.csv)...")
    cleaned_train = clean_train_data(raw_data["train"], cleaned_sku_master, audit)

    # 4. Aggregate to One Clean Row per Date-SKU-Region (Workstream 1 Core)
    logger.info("Step 4: Aggregating to Date-SKU-Region...")
    cleaned_monthly = aggregate_to_date_sku_region(cleaned_train, cleaned_sku_master)

    # 5. Build regularized panel grid (Workstream 1 Advanced: missing rows vs zeros)
    logger.info("Step 5: Building regularized panel grid...")
    cleaned_grid = build_regularized_panel_grid(cleaned_monthly, cleaned_sku_master)

    # 6. Clean Auxiliary Datasets
    logger.info("Step 6: Cleaning macro indicators, stockouts, events, and validating test...")
    cleaned_macro = clean_macro_indicators(raw_data["macro_indicators"], audit)
    cleaned_stockouts = clean_inventory_stockouts(raw_data["inventory_stockouts"], audit)
    cleaned_events = clean_events_calendar(raw_data["events_calendar"], audit)
    cleaned_test = validate_test_data(raw_data["test"], audit)

    # 7. Save Cleaned Datasets
    logger.info(f"Step 7: Saving cleaned outputs to {cleaned_dir}...")
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    # Save train datasets (both parquet for high performance and csv for inspection)
    cleaned_train.to_parquet(cleaned_dir / "train_cleaned.parquet", index=False)
    cleaned_train.head(5000).to_csv(cleaned_dir / "train_cleaned_sample.csv", index=False)
    
    cleaned_monthly.to_parquet(cleaned_dir / "train_monthly_cleaned.parquet", index=False)
    cleaned_monthly.to_csv(cleaned_dir / "train_monthly_cleaned.csv", index=False)
    
    cleaned_grid.to_parquet(cleaned_dir / "train_panel_grid.parquet", index=False)

    cleaned_macro.to_csv(cleaned_dir / "macro_indicators_cleaned.csv", index=False)
    cleaned_sku_master.to_csv(cleaned_dir / "sku_master_cleaned.csv", index=False)
    cleaned_stockouts.to_csv(cleaned_dir / "inventory_stockouts_cleaned.csv", index=False)
    cleaned_events.to_csv(cleaned_dir / "events_calendar_cleaned.csv", index=False)
    cleaned_test.to_csv(cleaned_dir / "test_cleaned.csv", index=False)

    # 8. Export Audit Trail
    logger.info(f"Step 8: Exporting audit trail to {reports_dir}...")
    audit.export(reports_dir)

    # 9. Generate Quality Report (JSON and Markdown)
    logger.info("Step 9: Generating Data Quality Report...")
    report = generate_quality_report(
        raw_datasets=raw_data,
        cleaned_train=cleaned_train,
        cleaned_monthly=cleaned_monthly,
        cleaned_grid=cleaned_grid,
        audit=audit,
        output_dir=reports_dir,
    )

    logger.info("=== WORKSTREAM 1 DATA CLEANING PIPELINE COMPLETED SUCCESSFULLY ===")
    return report


if __name__ == "__main__":
    run_data_cleaning_pipeline()
