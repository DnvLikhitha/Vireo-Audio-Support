"""
Mix-adjusted CSAT calculation module for Vireo Audio Support Analytics (WP3).
Calculates expected CSAT based on category, channel, priority, product (PL2 or not), and period,
then computes actual minus expected for fairer agent comparisons.
Uses scikit-learn LinearRegression (zero runtime cost, standard library / scikit-learn stack).
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def load_cleaned_data():
    """
    Load cleaned data and join tickets with agents.
    """
    from load_clean import load_and_clean_data, join_tickets_with_agents

    data = load_and_clean_data()
    tickets_with_agent = join_tickets_with_agents(data['tickets'], data['agents'])
    return data, tickets_with_agent


def calculate_expected_csat(tickets_df):
    """
    Fit an OLS regression model predicting CSAT from:
    - category (intake bot category)
    - channel (chat, email, voice, social)
    - priority (Low, Normal, High)
    - is_PL2 (1 if product_sku == 'VA-EB-PL2', 0 otherwise)
    - period (YYYY-MM string based on first_response_at)

    Returns:
        DataFrame: tickets_df with 'is_PL2', 'period', 'expected_csat', and 'adjusted_csat'
        dict: regression metadata (model, feature names, coefficients, r2, sample size)
    """
    df = tickets_df.copy()

    # Create features
    df['is_PL2'] = (df['product_sku'] == 'VA-EB-PL2').astype(int)
    # Period based on first_response_at_dt (or created_at if missing)
    if 'first_response_at_dt' in df.columns:
        df['period'] = df['first_response_at_dt'].dt.to_period('M').astype(str)
    else:
        df['period'] = pd.to_datetime(df['first_response_at']).dt.to_period('M').astype(str)

    # Filter to rated tickets
    rated_mask = df['csat_score'].notna()
    rated_df = df[rated_mask].copy()

    categorical_cols = ['category', 'channel', 'priority', 'period']
    # One-hot encode categoricals with drop_first=True for full rank
    X_cat = pd.get_dummies(rated_df[categorical_cols], drop_first=True, dtype=float)
    X = pd.concat([X_cat, rated_df[['is_PL2']]], axis=1)
    y = rated_df['csat_score'].values

    # Fit linear regression
    model = LinearRegression()
    model.fit(X, y)

    # Predict expected CSAT for rated tickets
    expected_csat_rated = model.predict(X)

    # Attach to full dataframe
    df['expected_csat'] = np.nan
    df['adjusted_csat'] = np.nan
    df.loc[rated_mask, 'expected_csat'] = expected_csat_rated
    df.loc[rated_mask, 'adjusted_csat'] = df.loc[rated_mask, 'csat_score'] - expected_csat_rated

    model_metadata = {
        'r2': float(model.score(X, y)),
        'intercept': float(model.intercept_),
        'features': list(X.columns),
        'coefficients': dict(zip(X.columns, model.coef_)),
        'n_samples': int(len(rated_df)),
        'mean_csat': float(rated_df['csat_score'].mean())
    }

    return df, model_metadata


def identify_special_teams(agents_df):
    """
    Identify special teams from the brief and email thread:
    - warranty_team: Escalations & Warranty (Tier 2, 6 agents)
    - kavya_four: The 4 Chat Frontline agents handling the bulk of PL2 tickets
      (A3004 Siddharth Kapoor, A3005 Zaid Khanna, A3006 Kavya Pandey, A3007 Siddharth Trivedi)
    - hardware_triage_rota: Warranty team + Kavya's four (total 10 agents)
    """
    warranty_team = set(agents_df[agents_df['team'] == 'Escalations & Warranty']['agent_id'].unique())

    # Kavya's four: Chat Frontline agents with high PL2 concentration (47% - 53%)
    kavya_four = {'A3004', 'A3005', 'A3006', 'A3007'}

    hardware_triage_rota = warranty_team.union(kavya_four)

    return {
        'warranty_team': warranty_team,
        'kavya_four': kavya_four,
        'hardware_triage_rota': hardware_triage_rota
    }


def calculate_agent_adjusted_metrics(tickets_with_adjustment_df, agents_df, min_responses=5):
    """
    Aggregate metrics at the agent level:
    - Raw CSAT: mean, count, std, SE, 95% CI
    - Expected CSAT: mean
    - Adjusted CSAT: mean, std, SE, 95% CI
    - Median handle time (hours and days)
    - Volume: total tickets, PL2 tickets, PL2 percentage
    - Team tags: is_warranty_team, is_hardware_triage_rota
    - Bottom ten flags: raw and adjusted (overall, Tier 1, Tier 2)
    """
    special_teams = identify_special_teams(agents_df)
    warranty_team = special_teams['warranty_team']
    rota_team = special_teams['hardware_triage_rota']

    # Rated tickets for CSAT calculations
    rated = tickets_with_adjustment_df[tickets_with_adjustment_df['csat_score'].notna()].copy()

    csat_agg = rated.groupby('agent_id').agg(
        csat_mean_actual=('csat_score', 'mean'),
        csat_count_actual=('csat_score', 'count'),
        csat_std_actual=('csat_score', 'std'),
        csat_mean_expected=('expected_csat', 'mean'),
        csat_mean_adjusted=('adjusted_csat', 'mean'),
        csat_std_adjusted=('adjusted_csat', 'std')
    ).reset_index()

    # Standard errors and 95% confidence intervals
    # Raw CSAT CI
    csat_agg['csat_se_actual'] = csat_agg['csat_std_actual'] / np.sqrt(csat_agg['csat_count_actual'])
    csat_agg['csat_ci_lower'] = csat_agg['csat_mean_actual'] - 1.96 * csat_agg['csat_se_actual']
    csat_agg['csat_ci_upper'] = csat_agg['csat_mean_actual'] + 1.96 * csat_agg['csat_se_actual']

    # Adjusted CSAT CI
    csat_agg['csat_se_adjusted'] = csat_agg['csat_std_adjusted'] / np.sqrt(csat_agg['csat_count_actual'])
    csat_agg['csat_adj_ci_lower'] = csat_agg['csat_mean_adjusted'] - 1.96 * csat_agg['csat_se_adjusted']
    csat_agg['csat_adj_ci_upper'] = csat_agg['csat_mean_adjusted'] + 1.96 * csat_agg['csat_se_adjusted']

    # Handle time metrics across all resolved/closed tickets
    resolved = tickets_with_adjustment_df[
        tickets_with_adjustment_df['status'].isin(['resolved', 'closed'])
    ].copy()

    ht_agg = resolved.groupby('agent_id').agg(
        median_handle_time_hours=('handle_time_hours', 'median'),
        mean_handle_time_hours=('handle_time_hours', 'mean')
    ).reset_index()
    ht_agg['median_handle_time_days'] = ht_agg['median_handle_time_hours'] / 24.0

    # Total ticket volume and PL2 tickets
    vol_agg = tickets_with_adjustment_df.groupby('agent_id').agg(
        ticket_count=('ticket_id', 'count'),
        pl2_ticket_count=('product_sku', lambda x: (x == 'VA-EB-PL2').sum())
    ).reset_index()
    vol_agg['pl2_ticket_pct'] = (vol_agg['pl2_ticket_count'] / vol_agg['ticket_count']) * 100.0

    # Agent metadata
    agent_info = agents_df.groupby('agent_id').agg(
        agent_name=('name', 'first'),
        team=('team', 'first'),
        shift=('shift', 'first'),
        tier=('tier', 'first'),
        site=('site', 'first')
    ).reset_index()

    # Merge everything
    agent_metrics = agent_info.merge(csat_agg, on='agent_id', how='left')\
                              .merge(ht_agg, on='agent_id', how='left')\
                              .merge(vol_agg, on='agent_id', how='left')

    # Add team membership indicators
    agent_metrics['is_warranty_team'] = agent_metrics['agent_id'].isin(warranty_team)
    agent_metrics['is_hardware_triage_rota'] = agent_metrics['agent_id'].isin(rota_team)

    # Initialize bottom flags
    agent_metrics['bottom_ten_raw_overall'] = False
    agent_metrics['bottom_ten_adj_overall'] = False
    agent_metrics['bottom_ten_raw_tier1'] = False
    agent_metrics['bottom_ten_adj_tier1'] = False
    agent_metrics['bottom_ten_raw_tier2'] = False
    agent_metrics['bottom_ten_adj_tier2'] = False

    # Eligible agents for ranking
    eligible = agent_metrics[agent_metrics['csat_count_actual'] >= min_responses].copy()

    # Overall bottom 10 (raw and adjusted)
    if len(eligible) >= 10:
        raw_b10_overall = eligible.nsmallest(10, 'csat_mean_actual')['agent_id'].tolist()
        adj_b10_overall = eligible.nsmallest(10, 'csat_mean_adjusted')['agent_id'].tolist()
        agent_metrics.loc[agent_metrics['agent_id'].isin(raw_b10_overall), 'bottom_ten_raw_overall'] = True
        agent_metrics.loc[agent_metrics['agent_id'].isin(adj_b10_overall), 'bottom_ten_adj_overall'] = True

    # Tier 1 bottom 10 (raw and adjusted)
    t1_eligible = eligible[eligible['tier'] == 1].copy()
    n_t1 = min(10, len(t1_eligible))
    if n_t1 > 0:
        raw_b10_t1 = t1_eligible.nsmallest(n_t1, 'csat_mean_actual')['agent_id'].tolist()
        adj_b10_t1 = t1_eligible.nsmallest(n_t1, 'csat_mean_adjusted')['agent_id'].tolist()
        agent_metrics.loc[agent_metrics['agent_id'].isin(raw_b10_t1), 'bottom_ten_raw_tier1'] = True
        agent_metrics.loc[agent_metrics['agent_id'].isin(adj_b10_t1), 'bottom_ten_adj_tier1'] = True

    # Tier 2 bottom (all eligible Tier 2 agents)
    t2_eligible = eligible[eligible['tier'] == 2].copy()
    n_t2 = min(10, len(t2_eligible))
    if n_t2 > 0:
        raw_b10_t2 = t2_eligible.nsmallest(n_t2, 'csat_mean_actual')['agent_id'].tolist()
        adj_b10_t2 = t2_eligible.nsmallest(n_t2, 'csat_mean_adjusted')['agent_id'].tolist()
        agent_metrics.loc[agent_metrics['agent_id'].isin(raw_b10_t2), 'bottom_ten_raw_tier2'] = True
        agent_metrics.loc[agent_metrics['agent_id'].isin(adj_b10_t2), 'bottom_ten_adj_tier2'] = True

    return agent_metrics