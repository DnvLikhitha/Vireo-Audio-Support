"""
Tests for Data Traps and Integrity Rules.
Verifies:
1. Legacy timezone fix (+5h30m to resolved_at) eliminates negative handle times.
2. Blank CSAT handling (blanks excluded, never zeroed).
3. Agent joining strictly by agent_id with date range (differentiating the two Kavya Pandeys).
4. Missing order_id fallback identifies and flags ambiguous multi-order matches.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from load_clean import load_and_clean_data
from lots import link_tickets_to_orders


@pytest.fixture(scope="module")
def dataset():
    return load_and_clean_data()


def test_timezone_fix(dataset):
    tickets = dataset['tickets']
    legacy = tickets[tickets['source_system'] == 'legacy_fd']
    
    fr = pd.to_datetime(legacy['first_response_at'])
    res = pd.to_datetime(legacy['resolved_at'])
    ht = (res - fr).dt.total_seconds() / 3600.0
    
    negative_count = (ht < 0).sum()
    assert negative_count == 0, f"Expected 0 negative handle times after +5h30m fix, got {negative_count}"


def test_csat_blank_exclusion(dataset):
    tickets = dataset['tickets']
    blank_csat_count = tickets['csat_score'].isna().sum()
    total_tickets = len(tickets)
    
    # Blanks must be ~55% of dataset
    assert blank_csat_count == 6554, f"Expected 6,554 blank CSAT tickets, got {blank_csat_count}"
    
    # Non-blank mean must be ~3.33, not diluted by 0s
    mean_rated = tickets['csat_score'].dropna().mean()
    assert 3.30 <= mean_rated <= 3.35, f"Expected rated mean ~3.33, got {mean_rated:.3f}"


def test_kavya_pandey_distinction(dataset):
    agents = dataset['agents']
    kavya_records = agents[agents['agent_name'] == 'Kavya Pandey']
    
    # Must have exactly 2 distinct agent_ids
    unique_ids = kavya_records['agent_id'].unique()
    assert set(unique_ids) == {'A3006', 'A3029'}, f"Expected A3006 and A3029 for Kavya Pandey, got {unique_ids}"
    
    # Verify different teams
    teams = dict(zip(kavya_records['agent_id'], kavya_records['team']))
    assert teams['A3006'] == 'Chat Frontline'
    assert teams['A3029'] == 'Logistics Frontline'


def test_ambiguous_order_fallback(dataset):
    tickets = dataset['tickets']
    orders = dataset['orders']
    
    linked_tickets, stats = link_tickets_to_orders(tickets, orders)
    
    # Exactly 614 ambiguous fallback tickets must be flagged
    assert stats['fallback_ambiguous'] == 614, f"Expected 614 ambiguous fallback matches, got {stats['fallback_ambiguous']}"
    assert stats['direct_matches'] == 7643, f"Expected 7,643 direct order matches, got {stats['direct_matches']}"
    assert stats['fallback_single'] == 3401, f"Expected 3,401 single fallback matches, got {stats['fallback_single']}"
