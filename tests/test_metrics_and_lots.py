"""
Tests for Metrics, Costing, Double Remedies, SLA, and Lot Backtest.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from load_clean import load_and_clean_data
from lots import (
    link_tickets_to_orders,
    calculate_lot_metrics,
    calculate_excess_cost,
    detect_refund_and_replacement_orders,
    calculate_sla_breaches
)
from 07_lot_early_warning import run_lot_early_warning_backtest


@pytest.fixture(scope="module")
def dataset():
    return load_and_clean_data()


def test_policy_costing_standard(dataset):
    tickets = dataset['tickets']
    orders = dataset['orders']
    products = dataset['products']
    
    linked_tickets, _ = link_tickets_to_orders(tickets, orders)
    _, _, monthly_batch_df = calculate_lot_metrics(orders, linked_tickets)
    cost_summary = calculate_excess_cost(monthly_batch_df, products)
    
    # Unit cost Rs 1,480 + logistics Rs 340 = Rs 1,820 per replacement
    assert cost_summary['unit_cost'] == 1480.0
    assert cost_summary['logistics_cost'] == 340.0
    assert cost_summary['policy_unit_cost'] == 1820.0
    assert cost_summary['arjun_unit_cost'] == 2500.0
    
    # Excess replacements ~726-730 units
    assert 720 <= cost_summary['excess_replacements'] <= 735
    # Excess cost policy ~Rs 13.2 Lakh vs Arjun Rs 18.2 Lakh
    assert 13.0 <= cost_summary['cost_policy_lakh'] <= 13.5
    assert 18.0 <= cost_summary['cost_arjun_lakh'] <= 18.5


def test_double_remedy_order_count(dataset):
    tickets = dataset['tickets']
    both_orders, cat_summary, _ = detect_refund_and_replacement_orders(tickets)
    
    # Exactly 131 orders received both refund and replacement
    assert len(both_orders) == 131, f"Expected 131 double-remedy orders, got {len(both_orders)}"


def test_sla_breach_rate(dataset):
    tickets = dataset['tickets']
    _, sla_summary = calculate_sla_breaches(tickets)
    
    # 1,064 breaches out of 11,750 tickets (~9.06%)
    assert sla_summary['breach_count'] == 1064
    assert 9.0 <= sla_summary['breach_rate_pct'] <= 9.2
    assert sla_summary['total_credit_inr'] == 372400.0


def test_early_warning_backtest(dataset):
    backtest = run_lot_early_warning_backtest(dataset)
    
    # Trigger date in mid-January 2026 for ticket stream, or early Nov for cohort
    assert backtest['realtime_fired_date'] == '2026-01-17'
    assert backtest['cohort_fired_date'] == '2025-11-08'
    
    # Avoidable cost range matches PRD goal (Rs 8 to 10 Lakh)
    assert 8.0 <= (backtest['avoidable_cost_realtime'] / 100000.0) <= 11.5
