"""
Metrics calculation module for Vireo Audio Support Analytics
Handles calculation of agent-level metrics: CSAT, handle time, ticket counts, etc.
"""

import pandas as pd
import numpy as np
from scipy import stats
import math

def calculate_agent_metrics(tickets_with_agent_df):
    """
    Calculate per-agent metrics from ticket data.

    Args:
        tickets_with_agent_df: DataFrame containing tickets joined with agent information

    Returns:
        DataFrame: Agent-level metrics including CSAT, handle time, ticket counts, etc.
    """
    # Filter to resolved tickets with CSAT scores for CSAT calculations
    resolved_tickets = tickets_with_agent_df[
        tickets_with_agent_df['csat_score'].notna() &
        (tickets_with_agent_df['status'].isin(['resolved', 'closed']))
    ].copy()

    # Calculate CSAT metrics per agent
    csat_metrics = resolved_tickets.groupby('agent_id').agg(
        csat_mean=('csat_score', 'mean'),
        csat_count=('csat_score', 'count'),
        csat_std=('csat_score', 'std')
    ).reset_index()

    # Calculate 95% confidence interval for CSAT mean
    # Using t-distribution: CI = mean ± (t * std / sqrt(n))
    # For large n, t ≈ 1.96 for 95% CI
    csat_metrics['csat_ci_lower'] = csat_metrics['csat_mean'] - 1.96 * csat_metrics['csat_std'] / np.sqrt(csat_metrics['csat_count'])
    csat_metrics['csat_ci_upper'] = csat_metrics['csat_mean'] + 1.96 * csat_metrics['csat_std'] / np.sqrt(csat_metrics['csat_count'])

    # Handle cases where std is NaN (only one response) or count is 0
    csat_metrics['csat_ci_lower'] = csat_metrics['csat_ci_lower'].fillna(csat_metrics['csat_mean'])
    csat_metrics['csat_ci_upper'] = csat_metrics['csat_ci_upper'].fillna(csat_metrics['csat_mean'])

    # Calculate handle time metrics per agent (using all resolved tickets)
    resolved_for_handle = tickets_with_agent_df[
        tickets_with_agent_df['status'].isin(['resolved', 'closed'])
    ].copy()

    handle_metrics = resolved_for_handle.groupby('agent_id').agg(
        median_handle_time_hours=('handle_time_hours', 'median'),
        mean_handle_time_hours=('handle_time_hours', 'mean'),
        handle_time_count=('handle_time_hours', 'count')
    ).reset_index()

    # Calculate ticket volume per agent (all tickets)
    ticket_volume = tickets_with_agent_df.groupby('agent_id').size().reset_index(name='ticket_count')

    # Get agent info (team, tier, shift, etc.) - take the most recent assignment or first one
    agent_info = tickets_with_agent_df.groupby('agent_id').agg(
        team=('team', 'first'),
        tier=('tier', 'first'),
        shift=('shift', 'first'),
        site=('site', 'first'),
        agent_name=('name', 'first')
    ).reset_index()

    # Merge all metrics
    agent_metrics = agent_info.merge(csat_metrics, on='agent_id', how='left')\
        .merge(handle_metrics, on='agent_id', how='left')\
                             .merge(ticket_volume, on='agent_id', how='left')

    # Fill NaN values for count/volume metrics (keep CSAT mean NaN if unrated)
    agent_metrics['csat_count'] = agent_metrics['csat_count'].fillna(0).astype(int)
    agent_metrics['median_handle_time_hours'] = agent_metrics['median_handle_time_hours'].fillna(0)
    agent_metrics['mean_handle_time_hours'] = agent_metrics['mean_handle_time_hours'].fillna(0)
    agent_metrics['handle_time_count'] = agent_metrics['handle_time_count'].fillna(0).astype(int)
    agent_metrics['ticket_count'] = agent_metrics['ticket_count'].fillna(0).astype(int)

    return agent_metrics

def flag_bottom_ten_by_csat(agent_metrics_df, min_responses=5):
    """
    Flag the bottom ten agents by raw CSAT score, separately for Tier 1, Tier 2, and overall.

    Args:
        agent_metrics_df: DataFrame with agent metrics
        min_responses: Minimum number of CSAT responses required to be eligible for ranking

    Returns:
        DataFrame: Agent metrics with bottom-ten flags added
    """
    # Filter agents with sufficient CSAT responses for ranking
    eligible_agents = agent_metrics_df[agent_metrics_df['csat_count'] >= min_responses].copy()

    # Initialize flag columns
    agent_metrics_df['bottom_ten_raw_csat'] = False
    agent_metrics_df['bottom_ten_raw_csat_tier1'] = False
    agent_metrics_df['bottom_ten_raw_csat_tier2'] = False

    # Process Tier 1 and Tier 2 separately
    for tier in [1, 2]:
        tier_agents = eligible_agents[eligible_agents['tier'] == tier].copy()
        n_flag = min(10, len(tier_agents))
        if n_flag > 0:
            bottom_tier = tier_agents.nsmallest(n_flag, 'csat_mean')['agent_id'].tolist()
            if tier == 1:
                agent_metrics_df.loc[agent_metrics_df['agent_id'].isin(bottom_tier), 'bottom_ten_raw_csat_tier1'] = True
            else:
                agent_metrics_df.loc[agent_metrics_df['agent_id'].isin(bottom_tier), 'bottom_ten_raw_csat_tier2'] = True

    # Overall bottom ten across all eligible agents
    if len(eligible_agents) > 0:
        overall_bottom_ten = eligible_agents.nsmallest(min(10, len(eligible_agents)), 'csat_mean')['agent_id'].tolist()
        agent_metrics_df.loc[agent_metrics_df['agent_id'].isin(overall_bottom_ten), 'bottom_ten_raw_csat'] = True

    return agent_metrics_df

def calculate_csat_confidence_interval(csat_mean, csat_std, csat_count, confidence=0.95):
    """
    Calculate confidence interval for CSAT score.

    Args:
        csat_mean: Mean CSAT score
        csat_std: Standard deviation of CSAT scores
        csat_count: Number of CSAT responses
        confidence: Confidence level (default 0.95)

    Returns:
        tuple: (lower_bound, upper_bound)
    """
    if csat_count <= 1 or pd.isna(csat_std) or csat_std == 0:
        return (csat_mean, csat_mean)

    # For t-distribution, with large sample size approx normal
    # Using 1.96 for 95% CI (z-score)
    z_score = 1.96  # for 95% confidence
    margin_of_error = z_score * csat_std / math.sqrt(csat_count)

    lower_bound = max(1, csat_mean - margin_of_error)  # CSAT can't be below 1
    upper_bound = min(5, csat_mean + margin_of_error)  # CSAT can't be above 5

    return (lower_bound, upper_bound)

if __name__ == "__main__":
    # Test the metrics calculation
    from load_clean import load_and_clean_data, join_tickets_with_agents

    print("Loading and cleaning data...")
    data = load_and_clean_data()

    print("Joining tickets with agents...")
    tickets_with_agent = join_tickets_with_agents(data['tickets'], data['agents'])

    print("Calculating agent metrics...")
    agent_metrics = calculate_agent_metrics(tickets_with_agent)

    print(f"Calculated metrics for {len(agent_metrics)} agents")
    print("\nSample agent metrics:")
    display_cols = ['agent_id', 'agent_name', 'team', 'tier', 'shift',
                   'csat_mean', 'csat_count', 'median_handle_time_hours', 'ticket_count']
    print(agent_metrics[display_cols].head(10))

    print("\nFlagging bottom ten by CSAT...")
    agent_metrics_flagged = flag_bottom_ten_by_csat(agent_metrics, min_responses=5)

    bottom_ten_count = agent_metrics_flagged['bottom_ten_raw_csat'].sum()
    bottom_ten_tier1 = agent_metrics_flagged['bottom_ten_raw_csat_tier1'].sum()
    bottom_ten_tier2 = agent_metrics_flagged['bottom_ten_raw_csat_tier2'].sum()

    print(f"Bottom ten agents flagged: {bottom_ten_count}")
    print(f"  Tier 1: {bottom_ten_tier1}")
    print(f"  Tier 2: {bottom_ten_tier2}")

    if bottom_ten_count > 0:
        print("\nBottom ten agents (raw CSAT):")
        bottom_ten_agents = agent_metrics_flagged[agent_metrics_flagged['bottom_ten_raw_csat']][
            ['agent_id', 'agent_name', 'team', 'tier', 'csat_mean', 'csat_count']
        ].sort_values('csat_mean')
        print(bottom_ten_agents.to_string(index=False))