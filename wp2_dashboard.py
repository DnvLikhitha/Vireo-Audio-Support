"""
WP2: Agent dashboard as asked.
Per agent: CSAT (mean, n responses, 95% interval), median handle time, ticket count, team, tier, shift.
Flag the bottom ten by raw CSAT, shown separately for Tier 1 and Tier 2.
Never put Tier 2 and Tier 1 on the same handle-time ranking.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from load_clean import load_and_clean_data, join_tickets_with_agents
from metrics import calculate_agent_metrics, flag_bottom_ten_by_csat
import pandas as pd
import numpy as np

def main():
    print("=" * 80)
    print("Vireo Audio Support - WP2: Agent Dashboard")
    print("=" * 80)

    # Load and clean data
    print("\n1. Loading and cleaning data...")
    data = load_and_clean_data()
    print(f"   Loaded {len(data['tickets'])} tickets, {len(data['agents'])} agents")

    # Join tickets with agents
    print("\n2. Joining tickets with agents (by agent_id)...")
    tickets_with_agent = join_tickets_with_agents(data['tickets'], data['agents'])
    print(f"   Joined dataset: {len(tickets_with_agent)} ticket-agent assignments")

    # Calculate agent metrics
    print("\n3. Calculating agent-level metrics...")
    agent_metrics = calculate_agent_metrics(tickets_with_agent)
    print(f"   Calculated metrics for {len(agent_metrics)} agents")

    # Flag bottom ten by CSAT (separately for Tier 1 and Tier 2)
    print("\n4. Flagging bottom ten agents by raw CSAT score (separately by tier)...")
    agent_metrics_flagged = flag_bottom_ten_by_csat(agent_metrics, min_responses=5)

    # Display results
    print("\n" + "=" * 80)
    print("AGENT DASHBOARD RESULTS")
    print("=" * 80)

    # Summary statistics
    print(f"\nSUMMARY:")
    print(f"  Total agents: {len(agent_metrics_flagged)}")
    print(f"  Agents with CSAT data: {(agent_metrics_flagged['csat_count'] > 0).sum()}")
    print(f"  Agents with sufficient CSAT responses (>=5): {(agent_metrics_flagged['csat_count'] >= 5).sum()}")

    # Overall CSAT statistics
    agents_with_csat = agent_metrics_flagged[agent_metrics_flagged['csat_count'] > 0]
    if len(agents_with_csat) > 0:
        print(f"  Overall CSAT mean (weighted by responses): {np.average(agents_with_csat['csat_mean'], weights=agents_with_csat['csat_count']):.2f}")
        print(f"  Overall CSAT mean (simple average of agents): {agents_with_csat['csat_mean'].mean():.2f}")

    # Handle time statistics (note: we won't rank Tier 1 and Tier 2 together)
    print(f"\nHANDLE TIME STATISTICS (ALL TIERS COMBINED FOR REFERENCE ONLY):")
    print(f"  Median handle time: {agent_metrics_flagged['median_handle_time_hours'].median():.2f} hours")
    print(f"  Mean handle time: {agent_metrics_flagged['median_handle_time_hours'].mean():.2f} hours")

    # Separate handle time by tier (as required - never rank Tier 2 against Tier 1)
    print(f"\nHANDLE TIME BY TIER (AS REQUIRED - NEVER RANK TIER 2 AGAINST TIER 1):")
    for tier in [1, 2]:
        tier_agents = agent_metrics_flagged[agent_metrics_flagged['tier'] == tier]
        if len(tier_agents) > 0:
            print(f"  Tier {tier} agents: {len(tier_agents)}")
            print(f"    Median handle time: {tier_agents['median_handle_time_hours'].median():.2f} hours")
            print(f"    Mean handle time: {tier_agents['median_handle_time_hours'].mean():.2f} hours")

    # Bottom ten agents by raw CSAT (separate for each tier)
    print(f"\nBOTTOM TEN AGENTS BY RAW CSAT SCORE:")
    print(f"  (Flagged separately for Tier 1 and Tier 2, minimum 5 CSAT responses required)")

    # Tier 1 bottom ten
    tier1_eligible = agent_metrics_flagged[
        (agent_metrics_flagged['tier'] == 1) &
        (agent_metrics_flagged['csat_count'] >= 5)
    ].copy()

    print(f"\n  TIER 1 BOTTOM TEN ({len(tier1_eligible)} eligible agents):")
    if len(tier1_eligible) >= 10:
        tier1_bottom_ten = tier1_eligible.nsmallest(10, 'csat_mean')[
            ['agent_id', 'agent_name', 'team', 'shift', 'csat_mean', 'csat_count', 'median_handle_time_hours']
        ]
        print(tier1_bottom_ten.to_string(index=False, float_format='%.2f'))
    else:
        print(f"    Only {len(tier1_eligible)} Tier 1 agents eligible for ranking (need ≥5 CSAT responses)")
        if len(tier1_eligible) > 0:
            print(tier1_eligible[
                ['agent_id', 'agent_name', 'team', 'shift', 'csat_mean', 'csat_count', 'median_handle_time_hours']
            ].sort_values('csat_mean').to_string(index=False, float_format='%.2f'))

    # Tier 2 bottom ten
    tier2_eligible = agent_metrics_flagged[
        (agent_metrics_flagged['tier'] == 2) &
        (agent_metrics_flagged['csat_count'] >= 5)
    ].copy()

    print(f"\n  TIER 2 BOTTOM TEN ({len(tier2_eligible)} eligible agents):")
    if len(tier2_eligible) >= 10:
        tier2_bottom_ten = tier2_eligible.nsmallest(10, 'csat_mean')[
            ['agent_id', 'agent_name', 'team', 'shift', 'csat_mean', 'csat_count', 'median_handle_time_hours']
        ]
        print(tier2_bottom_ten.to_string(index=False, float_format='%.2f'))
    else:
        print(f"    Only {len(tier2_eligible)} Tier 2 agents eligible for ranking (need >=5 CSAT responses)")
        if len(tier2_eligible) > 0:
            print(tier2_eligible[
                ['agent_id', 'agent_name', 'team', 'shift', 'csat_mean', 'csat_count', 'median_handle_time_hours']
            ].sort_values('csat_mean').to_string(index=False, float_format='%.2f'))

    # Show agents with overlapping confidence intervals (warning about reliability)
    print(f"\nCONFIDENCE INTERVAL OVERLAP WARNING:")
    print(f"  Agents with overlapping 95% CSAT confidence intervals may not have reliably different performance")
    agents_with_csat = agent_metrics_flagged[agent_metrics_flagged['csat_count'] >= 5].copy()
    if len(agents_with_csat) > 1:
        # Sort by CSAT mean
        agents_sorted = agents_with_csat.sort_values('csat_mean')
        overlapping_pairs = 0
        for i in range(len(agents_sorted) - 1):
            current_upper = agents_sorted.iloc[i]['csat_ci_upper']
            next_lower = agents_sorted.iloc[i + 1]['csat_ci_lower']
            if current_upper >= next_lower:
                overlapping_pairs += 1
                if overlapping_pairs <= 5:  # Show first 5 examples
                    print(f"    {agents_sorted.iloc[i]['agent_name']} (CI: {agents_sorted.iloc[i]['csat_ci_lower']:.2f}-{agents_sorted.iloc[i]['csat_ci_upper']:.2f}) overlaps with "
                          f"{agents_sorted.iloc[i + 1]['agent_name']} (CI: {agents_sorted.iloc[i + 1]['csat_ci_lower']:.2f}-{agents_sorted.iloc[i + 1]['csat_ci_upper']:.2f})")
        if overlapping_pairs > 5:
            print(f"    ... and {overlapping_pairs - 5} more overlapping pairs")
        print(f"  Total overlapping adjacent pairs: {overlapping_pairs} out of {len(agents_sorted) - 1} comparisons")

    # Save results to outputs directory for potential use in later WPs
    print(f"\n5. Saving results...")
    os.makedirs('outputs', exist_ok=True)
    agent_metrics_flagged.to_csv('outputs/agent_metrics_wp2.csv', index=False)
    print(f"   Agent metrics saved to outputs/agent_metrics_wp2.csv")

    print("\n" + "=" * 80)
    print("WP2 AGENT DASHBOARD COMPLETE")
    print("=" * 80)

    return agent_metrics_flagged

if __name__ == "__main__":
    agent_metrics_results = main()