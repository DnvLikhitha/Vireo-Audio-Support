"""
Pipeline Step 02: Agent Metrics & Dashboard Calculations (WP2).
Calculates per-agent CSAT (mean, count, 95% confidence interval), median handle time,
ticket volume, and flags the bottom-10 raw CSAT performers separated by Tier 1 and Tier 2.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pandas as pd
import numpy as np
from load_clean import load_and_clean_data
from metrics import calculate_agent_metrics, flag_bottom_ten


def main():
    print("=" * 80)
    print("Vireo Audio Support - Step 02: Per-Agent Metrics & Performance Audit")
    print("=" * 80)

    # 1. Load Cleaned Data
    data = load_and_clean_data()
    tickets_with_agents = data['tickets_with_agents']

    # 2. Calculate Agent Metrics
    print("\nCalculating per-agent CSAT, handle time, and volume metrics...")
    agent_metrics = calculate_agent_metrics(tickets_with_agents)
    flagged_metrics = flag_bottom_ten(agent_metrics)

    # 3. Print Tier 1 vs Tier 2 Summaries
    print("\n" + "-" * 80)
    print("TIER 1 (FRONTLINE) - RAW BOTTOM 10 CSAT RANKING")
    print("-" * 80)
    t1 = flagged_metrics[flagged_metrics['tier'] == 'Tier 1'].sort_values('csat_mean')
    print(t1[['agent_id', 'agent_name', 'team', 'shift', 'csat_mean', 'csat_count', 'median_handle_time_hours', 'bottom_ten_raw']].head(10).to_string(index=False))

    print("\n" + "-" * 80)
    print("TIER 2 (ESCALATIONS & WARRANTY) - SEPARATE CSAT & HANDLE TIME RANKING")
    print("-" * 80)
    t2 = flagged_metrics[flagged_metrics['tier'] == 'Tier 2'].sort_values('csat_mean')
    print(t2[['agent_id', 'agent_name', 'team', 'shift', 'csat_mean', 'csat_count', 'median_handle_time_hours', 'bottom_ten_raw']].to_string(index=False))

    # 4. Save Output
    os.makedirs('outputs', exist_ok=True)
    out_path = 'outputs/agent_metrics.csv'
    flagged_metrics.to_csv(out_path, index=False)
    print(f"\nSaved agent metrics to {out_path}")
    print("=" * 80)


if __name__ == '__main__':
    main()
