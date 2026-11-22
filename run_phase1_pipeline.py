#!/usr/bin/env python
"""One-command runner for Hackathon Phase 1: Data Cleaning & Quality Pipeline."""

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_data_cleaning_pipeline


def main():
    print("=" * 70)
    print("  MKS AI/ML Hackathon Phase 2 - Demand Forecasting")
    print("  PHASE 1: WORKSTREAM 1 DATA CLEANING & QUALITY AUDIT PIPELINE")
    print("=" * 70)

    start_time = time.time()
    try:
        report = run_data_cleaning_pipeline()
        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print(f"  PIPELINE EXECUTED SUCCESSFULLY in {elapsed:.2f} seconds!")
        print(f"  - Cleaned Datasets: data/cleaned/")
        print(f"  - Quality Reports:  reports/data_quality_report.json & .md")
        print(f"  - Audit Trail:      reports/audit_records.parquet & audit_summary.json")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
