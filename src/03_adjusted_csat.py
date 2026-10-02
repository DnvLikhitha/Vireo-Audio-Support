"""
Pipeline Step 03: Make it Fair (Mix-Adjusted CSAT Analysis - WP3).
Calculates expected CSAT given category, channel, priority, product (PL2 or not) and period,
then actual minus expected. Shows raw and adjusted bottom ten side by side, and marks agents
on the hardware triage rota and the warranty team.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from adjust import (
    load_cleaned_data,
    calculate_expected_csat,
    calculate_agent_adjusted_metrics,
    identify_special_teams
)
import pandas as pd
import numpy as np


def main():
    print("=" * 80)
    print("Vireo Audio Support - Step 03: Make it Fair (Mix-Adjusted CSAT Analysis)")
    print("=" * 80)

    # 1. Load data
    print("\n1. Loading and cleaning data...")
    data, tickets_with_agent = load_cleaned_data()
    print(f"   Loaded {len(data['tickets'])} tickets, {len(data['agents'])} agents")

    # 2. Fit Mix-Adjustment Model
    print("\n2. Fitting Case-Mix CSAT Regression Model...")
    print("   Factors: category, channel, priority, product (PL2 or not), and period (YYYY-MM)")
    tickets_adjusted, meta = calculate_expected_csat(tickets_with_agent)
    print(f"   Model fitted on {meta['n_samples']} rated tickets (R² = {meta['r2']:.4f})")
    print(f"   Intercept: {meta['intercept']:.3f} (Mean CSAT: {meta['mean_csat']:.3f})")
    print(f"   Pulse 2 earbud coefficient (is_PL2): {meta['coefficients'].get('is_PL2', 0):.4f}")

    # Top impact drivers
    sorted_coefs = sorted(meta['coefficients'].items(), key=lambda x: x[1])
    print("\n   Strongest negative drivers of CSAT:")
    for feat, coef in sorted_coefs[:5]:
        print(f"     • {feat:30s}: {coef:+.3f} CSAT points")

    # 3. Calculate Agent-Level Metrics
    print("\n3. Computing Agent Metrics (Raw vs Adjusted, Handle Times, Special Teams)...")
    agent_metrics = calculate_agent_adjusted_metrics(tickets_adjusted, data['agents'], min_responses=5)
    print(f"   Computed metrics for {len(agent_metrics)} agents")

    # 4. Display Overall Bottom 10 Side-by-Side
    print("\n" + "=" * 80)
    print("TABLE 1: OVERALL COMPANY BOTTOM 10 (RAW vs ADJUSTED CSAT)")
    print("=" * 80)
    raw_b10_overall = agent_metrics.sort_values('csat_mean_actual').head(10)
    adj_b10_overall = agent_metrics.sort_values('csat_mean_adjusted').head(10)

    print("\n[RAW CSAT BOTTOM 10 OVERALL]")
    display_cols_raw = [
        'agent_id', 'agent_name', 'team', 'tier', 'csat_mean_actual',
        'csat_count_actual', 'csat_se_actual', 'csat_ci_lower', 'csat_ci_upper',
        'is_hardware_triage_rota'
    ]
    print(raw_b10_overall[display_cols_raw].to_string(
        index=False,
        formatters={
            'csat_mean_actual': '{:.2f}'.format,
            'csat_se_actual': '{:.2f}'.format,
            'csat_ci_lower': '{:.2f}'.format,
            'csat_ci_upper': '{:.2f}'.format
        }
    ))

    print("\n[ADJUSTED CSAT BOTTOM 10 OVERALL]")
    display_cols_adj = [
        'agent_id', 'agent_name', 'team', 'tier', 'csat_mean_adjusted',
        'csat_mean_actual', 'csat_mean_expected', 'csat_count_actual',
        'csat_se_adjusted', 'is_hardware_triage_rota'
    ]
    print(adj_b10_overall[display_cols_adj].to_string(
        index=False,
        formatters={
            'csat_mean_adjusted': '{:+.2f}'.format,
            'csat_mean_actual': '{:.2f}'.format,
            'csat_mean_expected': '{:.2f}'.format,
            'csat_se_adjusted': '{:.2f}'.format
        }
    ))

    raw_ids = set(raw_b10_overall['agent_id'])
    adj_ids = set(adj_b10_overall['agent_id'])
    overlap_overall = raw_ids.intersection(adj_ids)
    print(f"\n>> Overlap in Overall Bottom 10: {len(overlap_overall)} of 10 agents")
    print(f">> All 10 agents in the bottom ten belong to the Hardware Triage Rota: {all(raw_b10_overall['is_hardware_triage_rota'])}")

    # 5. Display Tier 1 Bottom 10 Side-by-Side
    print("\n" + "=" * 80)
    print("TABLE 2: TIER 1 FRONTLINE BOTTOM 10 (RAW vs ADJUSTED CSAT)")
    print("=" * 80)
    t1_agents = agent_metrics[agent_metrics['tier'] == 1].copy()
    t1_raw_b10 = t1_agents.sort_values('csat_mean_actual').head(10)
    t1_adj_b10 = t1_agents.sort_values('csat_mean_adjusted').head(10)

    print("\n[TIER 1 RAW CSAT BOTTOM 10]")
    t1_cols_raw = [
        'agent_id', 'agent_name', 'team', 'shift', 'csat_mean_actual',
        'csat_count_actual', 'csat_se_actual', 'csat_ci_lower', 'csat_ci_upper',
        'median_handle_time_hours', 'pl2_ticket_pct', 'is_hardware_triage_rota'
    ]
    print(t1_raw_b10[t1_cols_raw].to_string(
        index=False,
        formatters={
            'csat_mean_actual': '{:.2f}'.format,
            'csat_se_actual': '{:.2f}'.format,
            'csat_ci_lower': '{:.2f}'.format,
            'csat_ci_upper': '{:.2f}'.format,
            'median_handle_time_hours': '{:.2f}h'.format,
            'pl2_ticket_pct': '{:.1f}%'.format
        }
    ))

    # 6. Save outputs
    print("\n5. Saving Step 03 Artifacts...")
    os.makedirs('outputs', exist_ok=True)
    out_csv = 'outputs/agent_metrics_wp3.csv'
    agent_metrics.to_csv(out_csv, index=False)
    print(f"   Saved agent metrics to {out_csv}")

    ticket_out = 'outputs/tickets_with_adjustment_wp3.csv'
    tickets_adjusted.to_csv(ticket_out, index=False)
    print(f"   Saved ticket-level adjustments to {ticket_out}")
    print("=" * 80)
    return agent_metrics


if __name__ == '__main__':
    main()
