#!/usr/bin/env python
"""One-command runner for Hackathon Phase 2: Anomaly Detection & Unconstrained Demand Reconstruction."""

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline_phase2 import run_workstream_2_pipeline


def main():
    print("=" * 75)
    print("  MKS AI/ML Hackathon Phase 2 - Demand Forecasting")
    print("  WORKSTREAM 2: ANOMALY DETECTION & UNCONSTRAINED DEMAND RECONSTRUCTION")
    print("=" * 75)

    start_time = time.time()
    try:
        summary = run_workstream_2_pipeline()
        elapsed = time.time() - start_time
        print("\n" + "=" * 75)
        print(f"  PHASE 2 PIPELINE EXECUTED SUCCESSFULLY in {elapsed:.2f} seconds!")
        print(f"  - Reconstructed Demand: data/cleaned/demand_reconstructed.parquet")
        print(f"  - Anomaly Register:     reports/anomaly_register.csv & artifacts/")
        print(f"  - Summary Metrics:      reports/anomaly_summary.json")
        print(f"  - Business Report:      reports/anomaly_analysis.md")
        print(f"  - High-Res Charts:      reports/charts/")
        print("=" * 75)
        return 0
    except Exception as e:
        print(f"\n[ERROR] Phase 2 Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
