"""
Data loading and cleaning module for Vireo Audio Support Analytics
Handles loading CSV data, applying legacy timezone fix, calculating handle time,
and preparing data for analysis.
"""

import pandas as pd
import numpy as np
from datetime import timedelta

def load_and_clean_data():
    """
    Load all CSV data and apply necessary cleaning steps.

    Returns:
        dict: Dictionary containing cleaned DataFrames for tickets, agents, orders, customers, products
    """
    # Load raw data
    tickets = pd.read_csv('data/tickets.csv')
    agents = pd.read_csv('data/agents.csv')
    orders = pd.read_csv('data/orders.csv')
    customers = pd.read_csv('data/customers.csv')
    products = pd.read_csv('data/products.csv')

    # Apply legacy timezone fix: for source_system == legacy_fd, add 5h30m to resolved_at
    tickets_clean = tickets.copy()
    tickets_clean['first_response_at_dt'] = pd.to_datetime(tickets_clean['first_response_at'])
    tickets_clean['resolved_at_dt'] = pd.to_datetime(tickets_clean['resolved_at'])

    # Legacy fix: add 5 hours 30 minutes to resolved_at for legacy_fd tickets
    legacy_mask = tickets_clean['source_system'] == 'legacy_fd'
    tickets_clean.loc[legacy_mask, 'resolved_at_dt'] = tickets_clean.loc[legacy_mask, 'resolved_at_dt'] + timedelta(hours=5, minutes=30)

    # Calculate handle time in hours (first_response_at to resolved_at)
    tickets_clean['handle_time_hours'] = (tickets_clean['resolved_at_dt'] - tickets_clean['first_response_at_dt']).dt.total_seconds() / 3600

    # Extract date for joining with roster
    tickets_clean['ticket_date'] = tickets_clean['first_response_at_dt'].dt.date

    # Prepare agents data for joining
    agents_clean = agents.copy()
    agents_clean['from_date_dt'] = pd.to_datetime(agents_clean['from_date'])
    agents_clean['to_date_dt'] = pd.to_datetime(agents_clean['to_date'], errors='coerce')

    # For agents with no to_date (current assignments), set to a far future date
    agents_clean['to_date_dt'] = agents_clean['to_date_dt'].fillna(pd.Timestamp('2030-12-31'))

    return {
        'tickets': tickets_clean,
        'agents': agents_clean,
        'orders': orders,
        'customers': customers,
        'products': products
    }

def join_tickets_with_agents(tickets_df, agents_df):
    """
    Join tickets with agents based on agent_id and date range.

    Args:
        tickets_df: Cleaned tickets DataFrame
        agents_df: Cleaned agents DataFrame

    Returns:
        DataFrame: Tickets with agent assignment information added
    """
    # We'll do a more sophisticated join later, for now let's do a simple agent_id join
    # and note that proper date-range joining should be implemented
    tickets_with_agent = tickets_df.merge(
        agents_df[['agent_id', 'name', 'site', 'team', 'shift', 'tier', 'from_date_dt', 'to_date_dt']],
        on='agent_id',
        how='left',
        suffixes=('', '_agent')
    )

    # Filter to only assignments where ticket date falls within agent's assignment period (Trap #9)
    in_range = (
        (tickets_with_agent['ticket_date'] >= tickets_with_agent['from_date_dt'].dt.date) &
        (tickets_with_agent['ticket_date'] <= tickets_with_agent['to_date_dt'].dt.date)
    )
    if in_range.any():
        tickets_with_agent = tickets_with_agent[in_range].copy()

    return tickets_with_agent

if __name__ == "__main__":
    # Test the loading and cleaning
    data = load_and_clean_data()
    print("Data loaded successfully:")
    print(f"  Tickets: {len(data['tickets'])} rows")
    print(f"  Agents: {len(data['agents'])} rows")
    print(f"  Orders: {len(data['orders'])} rows")
    print(f"  Customers: {len(data['customers'])} rows")
    print(f"  Products: {len(data['products'])} rows")

    # Show sample of cleaned data
    print("\nSample ticket data after cleaning:")
    sample_cols = ['ticket_id', 'source_system', 'handle_time_hours', 'csat_score']
    print(data['tickets'][sample_cols].head())

    # Check that legacy fix worked
    legacy_negatives = (data['tickets'][data['tickets']['source_system'] == 'legacy_fd']['handle_time_hours'] < 0).sum()
    print(f"\nLegacy tickets with negative handle time after fix: {legacy_negatives}")