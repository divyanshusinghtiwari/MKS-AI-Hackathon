"""CLI Runner for Workstream 4: Forecasting Engine, Rolling-Origin Backtesting, and Submission Generation."""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.pipeline_phase4 import run_forecasting_pipeline

def main():
    print("================================================================================")
    print("MKS AI/ML HACKATHON PHASE 2: WORKSTREAM 4 FORECASTING ENGINE")
    print("================================================================================")
    t0 = time.time()
    try:
        metrics = run_forecasting_pipeline()
        t1 = time.time()
        print("\n" + "=" * 80)
        print("PHASE 4 FORECASTING PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"Elapsed Time: {t1 - t0:.2f} seconds")
        print(f"Submission File: submission.csv ({metrics['submission_rows']:,} rows)")
        print(f"Total 19-Month Forecast Volume: {metrics['total_forecast_volume']:,} units")
        print(f"19-Month Backtest WAPE: {metrics['backtest_wape']:.2f}%")
        print(f"19-Month Backtest Bias: {metrics['backtest_bias']:+.2f}%")
        print("=" * 80)
    except Exception as e:
        print(f"\n[FATAL ERROR] Phase 4 pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
