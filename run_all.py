"""
Master Pipeline Runner: Vireo Audio Support Analytics Toolkit.
Executes the end-to-end analytics workflow in sequential order:
  Step 01: Data Quality Checks, Deduplication, and Legacy Timezone Fix
  Step 02: Agent CSAT & Handle Time Metrics (Tier 1 vs Tier 2, Bottom-10 Flag)
  Step 03: Mix-Adjusted CSAT & Hardware Triage Fairness Analysis
  Step 04: Manufacturing Lot Analysis, Costing, Double Remedies, & SLA Audits
  Step 05: Rule-Based Root-Cause Text Classifier & Disagreement Cross-Tabs
  Step 06: Ground-Truth Validation, Failure Mode Analysis, & Non-Text Audits
  Step 07: Lot Early-Warning Rule Backtest & Avoidable Cost Estimation
"""

import sys
import os
import subprocess
import time

STEPS = [
    ("Step 01: Data Quality & Cleaning", "src/01_data_quality.py"),
    ("Step 02: Per-Agent CSAT & Handle Time", "src/02_agent_metrics.py"),
    ("Step 03: Case-Mix Adjusted CSAT & Fairness", "src/03_adjusted_csat.py"),
    ("Step 04: Manufacturing Lot & Costing Analysis", "src/04_lot_analysis.py"),
    ("Step 05: Root-Cause Text Classifier", "src/05_classifier.py"),
    ("Step 06: Validation & Failure Mode Report", "src/06_validation.py"),
    ("Step 07: Lot Early-Warning Rule & Backtest", "src/07_lot_early_warning.py")
]

def main():
    print("=" * 80)
    print("      VIREO AUDIO SUPPORT ANALYTICS PIPELINE - FULL RUNNER")
    print("=" * 80)
    start_total = time.time()
    
    python_cmd = sys.executable

    for idx, (title, script_path) in enumerate(STEPS, 1):
        print(f"\n[{idx}/7] RUNNING: {title} ({script_path})")
        print("-" * 80)
        t0 = time.time()
        res = subprocess.run([python_cmd, script_path], capture_output=False)
        elapsed = time.time() - t0
        
        if res.returncode != 0:
            print(f"\n[ERROR] Pipeline failed at {title} with exit code {res.returncode}.")
            sys.exit(res.returncode)
        
        print(f"\n[OK] {title} completed in {elapsed:.1f}s.")

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {total_time:.1f}s!")
    print("All outputs generated in 'outputs/' and 'validation/'.")
    print("Launch dashboard: streamlit run app.py")
    print("=" * 80)


if __name__ == '__main__':
    main()
