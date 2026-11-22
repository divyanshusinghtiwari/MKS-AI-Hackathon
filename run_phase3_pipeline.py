#!/usr/bin/env python
"""One-command runner for Hackathon Phase 3: Feature Engineering & Macroeconomic Drivers."""

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline_phase3 import run_workstream_3_pipeline


def main():
    print("=" * 75)
    print("  MKS AI/ML Hackathon Phase 2 - Demand Forecasting")
    print("  WORKSTREAM 3: FEATURE ENGINEERING & MACROECONOMIC DRIVERS")
    print("=" * 75)

    start_time = time.time()
    try:
        report = run_workstream_3_pipeline()
        elapsed = time.time() - start_time
        print("\n" + "=" * 75)
        print(f"  PHASE 3 PIPELINE EXECUTED SUCCESSFULLY in {elapsed:.2f} seconds!")
        print(f"  - Feature Store:        data/cleaned/features_engineered.parquet")
        print(f"  - Total Columns:        {report['feature_store_summary']['total_features']} features")
        print(f"  - Feature Dictionary:   reports/feature_dictionary.md")
        print(f"  - Macro Analysis:       reports/macro_correlation_analysis.md")
        print(f"  - Quality Audit JSON:   reports/feature_quality_report.json")
        print("=" * 75)
        return 0
    except Exception as e:
        print(f"\n[ERROR] Phase 3 Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
