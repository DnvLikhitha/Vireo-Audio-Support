"""
Manufacturing Lot Analysis and Replacement Costing Module for Vireo Audio (WP4).
Implements:
- Linking tickets to orders (direct and unambiguous fallback)
- Lot-level replacement and ticket rates (highlighting Pulse 2 defective lots: 2510, 2511, 2512)
- Excess replacements and costing using policy formula (unit cost + Rs 340 vs Rs 2,500)
- Refund-plus-replacement detector (identifying 131 orders and separating genuine errors from legitimate cases)
- SLA first-response breach detector and credit calculator (Rs 350 per breach)
"""

import pandas as pd
import numpy as np


def link_tickets_to_orders(tickets_df, orders_df):
    """
    Link tickets to orders using direct order_id, with unambiguous fallback
    to customer_id + product_sku where order_date <= created_at.

    Returns:
        DataFrame: linked_tickets with matched_order_id, match_type, lot_code, order_date
        dict: linking statistics (direct, fallback_single, fallback_ambiguous, fallback_zero)
    """
    tickets = tickets_df.copy()
    orders = orders_df.copy()

    tickets['created_at_dt'] = pd.to_datetime(tickets['created_at'])
    orders['order_date_dt'] = pd.to_datetime(orders['order_date'])

    # 1. Direct matches
    direct_mask = tickets['order_id'].notna()
    direct_tickets = tickets[direct_mask].copy()
    direct_tickets = direct_tickets.merge(
        orders[['order_id', 'lot_code', 'order_date_dt']],
        on='order_id',
        how='left'
    )
    direct_tickets['matched_order_id'] = direct_tickets['order_id']
    direct_tickets['match_type'] = 'direct'

    # 2. Missing order_id fallback
    missing_tickets = tickets[~direct_mask].copy()
    fallback_candidates = missing_tickets.merge(
        orders[['order_id', 'customer_id', 'sku', 'lot_code', 'order_date_dt']],
        left_on=['customer_id', 'product_sku'],
        right_on=['customer_id', 'sku'],
        how='left'
    )

    # Valid candidates must be purchased before or on ticket creation
    valid_candidates = fallback_candidates[
        fallback_candidates['order_date_dt'] <= fallback_candidates['created_at_dt']
    ]

    candidate_counts = valid_candidates.groupby('ticket_id')['order_id_y'].count()
    single_match_ids = candidate_counts[candidate_counts == 1].index
    ambiguous_ids = candidate_counts[candidate_counts > 1].index
    zero_match_ids = set(missing_tickets['ticket_id']) - set(candidate_counts.index)

    single_fallback = valid_candidates[valid_candidates['ticket_id'].isin(single_match_ids)].copy()
    single_fallback['matched_order_id'] = single_fallback['order_id_y']
    single_fallback['match_type'] = 'fallback_single'
    # Drop helper join columns
    drop_cols = [c for c in ['order_id_x', 'order_id_y', 'sku'] if c in single_fallback.columns]
    single_fallback = single_fallback.drop(columns=drop_cols)

    # Combine direct and unambiguous single matches
    linked = pd.concat([direct_tickets, single_fallback], ignore_index=True)

    stats = {
        'total_tickets': len(tickets),
        'direct_matches': len(direct_tickets),
        'fallback_single': len(single_fallback),
        'fallback_ambiguous': len(ambiguous_ids),
        'fallback_zero': len(zero_match_ids),
        'total_linked': len(linked)
    }

    return linked, stats


def calculate_lot_metrics(orders_df, linked_tickets_df):
    """
    Aggregate orders, tickets, and replacements per lot code and per monthly batch.
    """
    # Order-level ticket aggregations
    order_summary = linked_tickets_df.groupby('matched_order_id').agg(
        tickets_count=('ticket_id', 'count'),
        replacements_count=('replacement_issued', lambda x: (x == 'Y').sum()),
        has_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
        has_refund=('refund_amount_inr', lambda x: (x.notna() & (x > 0)).any()),
        refund_amount=('refund_amount_inr', 'sum')
    ).reset_index()

    orders_merged = orders_df.merge(
        order_summary,
        left_on='order_id',
        right_on='matched_order_id',
        how='left'
    )
    orders_merged['tickets_count'] = orders_merged['tickets_count'].fillna(0).astype(int)
    orders_merged['replacements_count'] = orders_merged['replacements_count'].fillna(0).astype(int)
    orders_merged['has_replacement'] = orders_merged['has_replacement'].fillna(False)
    orders_merged['has_refund'] = orders_merged['has_refund'].fillna(False)
    orders_merged['refund_amount'] = orders_merged['refund_amount'].fillna(0.0)

    # Sub-lot level metrics
    lot_metrics = orders_merged.groupby(['sku', 'lot_code']).agg(
        orders_count=('order_id', 'count'),
        tickets_count=('tickets_count', 'sum'),
        replacements_count=('replacements_count', 'sum'),
        orders_with_replacement=('has_replacement', 'sum'),
        first_order_date=('order_date', 'min'),
        last_order_date=('order_date', 'max')
    ).reset_index()

    lot_metrics['replacement_rate_pct'] = (
        lot_metrics['orders_with_replacement'] / lot_metrics['orders_count'] * 100.0
    )
    lot_metrics['ticket_rate_pct'] = (
        lot_metrics['tickets_count'] / lot_metrics['orders_count'] * 100.0
    )

    # Monthly batch level (e.g. PL2-2510)
    orders_merged['lot_month'] = orders_merged['lot_code'].apply(
        lambda x: '-'.join(x.split('-')[:2]) if isinstance(x, str) else 'unknown'
    )

    monthly_batch_metrics = orders_merged.groupby(['sku', 'lot_month']).agg(
        orders_count=('order_id', 'count'),
        tickets_count=('tickets_count', 'sum'),
        replacements_count=('replacements_count', 'sum'),
        orders_with_replacement=('has_replacement', 'sum'),
        first_order_date=('order_date', 'min'),
        last_order_date=('order_date', 'max')
    ).reset_index()

    monthly_batch_metrics['replacement_rate_pct'] = (
        monthly_batch_metrics['orders_with_replacement'] / monthly_batch_metrics['orders_count'] * 100.0
    )
    monthly_batch_metrics['ticket_rate_pct'] = (
        monthly_batch_metrics['tickets_count'] / monthly_batch_metrics['orders_count'] * 100.0
    )

    return orders_merged, lot_metrics, monthly_batch_metrics


def calculate_excess_cost(monthly_batch_df, products_df, affected_months=('PL2-2510', 'PL2-2511', 'PL2-2512')):
    """
    Calculate excess replacements and cost comparison:
    Policy formula: unit_cost_inr + Rs 340 logistics
    vs Finance (Arjun): Rs 2,500
    """
    pl2_row = products_df[products_df['sku'] == 'VA-EB-PL2'].iloc[0]
    unit_cost = float(pl2_row['unit_cost_inr'])  # 1480
    logistics_cost = 340.0
    policy_unit_cost = unit_cost + logistics_cost  # 1820
    arjun_unit_cost = 2500.0

    pl2_batches = monthly_batch_df[monthly_batch_df['sku'] == 'VA-EB-PL2'].copy()

    # Affected vs baseline batches
    affected = pl2_batches[pl2_batches['lot_month'].isin(affected_months)]
    baseline = pl2_batches[~pl2_batches['lot_month'].isin(affected_months)]

    total_affected_orders = int(affected['orders_count'].sum())  # 1979
    total_affected_replacements = int(affected['replacements_count'].sum())  # 865
    total_affected_repl_orders = int(affected['orders_with_replacement'].sum())  # 812

    baseline_repl_rate = float(baseline['orders_with_replacement'].sum() / baseline['orders_count'].sum())  # ~0.0700 (7.0%)

    expected_replacements = total_affected_orders * baseline_repl_rate
    excess_replacements = total_affected_replacements - expected_replacements

    cost_policy = excess_replacements * policy_unit_cost
    cost_arjun = excess_replacements * arjun_unit_cost
    arjun_overstatement = cost_arjun - cost_policy

    cost_summary = {
        'affected_orders': total_affected_orders,
        'actual_replacements': total_affected_replacements,
        'actual_repl_orders': total_affected_repl_orders,
        'baseline_rate_pct': baseline_repl_rate * 100.0,
        'expected_replacements': expected_replacements,
        'excess_replacements': excess_replacements,
        'unit_cost': unit_cost,
        'logistics_cost': logistics_cost,
        'policy_unit_cost': policy_unit_cost,
        'arjun_unit_cost': arjun_unit_cost,
        'cost_policy_inr': cost_policy,
        'cost_policy_lakh': cost_policy / 100000.0,
        'cost_arjun_inr': cost_arjun,
        'cost_arjun_lakh': cost_arjun / 100000.0,
        'overstatement_inr': arjun_overstatement,
        'overstatement_lakh': arjun_overstatement / 100000.0
    }

    return cost_summary


def detect_refund_and_replacement_orders(tickets_df):
    """
    Detect orders where both a refund and a replacement were issued (violating Policy §5).
    Evaluated on tickets with direct order_id (yielding the 131 orders from exploration).
    Separates genuine errors from legitimate business operations.
    """
    direct_tickets = tickets_df[tickets_df['order_id'].notna()].copy()

    order_grp = direct_tickets.groupby('order_id').agg(
        ticket_ids=('ticket_id', list),
        ticket_count=('ticket_id', 'count'),
        has_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
        has_refund=('refund_amount_inr', lambda x: (x.notna() & (x > 0)).any()),
        refund_reasons=('refund_reason_code', lambda x: list(x.dropna())),
        refund_amounts=('refund_amount_inr', lambda x: list(x.dropna())),
        customer_ids=('customer_id', 'first'),
        skus=('product_sku', list)
    ).reset_index()

    both_orders = order_grp[order_grp['has_replacement'] & order_grp['has_refund']].copy()

    def classify_double_remedy(reasons):
        legit_set = {'RETURN-QC-OK', 'DUP-PAYMENT', 'PRICE-ADJ'}
        error_set = {'DOA-REPL', 'LOST-TRANSIT', 'WTY-BUYBACK'}
        r_set = set(reasons)

        if r_set.issubset(legit_set):
            return 'Legitimate (QC Return / Dup Payment / Price Adj)'
        elif any(r in error_set for r in r_set):
            return 'Genuine Policy Violation (Double Remedy for Fault)'
        else:
            return 'Ambiguous / Cancelled Order'

    both_orders['category'] = both_orders['refund_reasons'].apply(classify_double_remedy)
    both_orders['total_refund_amount'] = both_orders['refund_amounts'].apply(sum)

    category_summary = both_orders.groupby('category').agg(
        order_count=('order_id', 'count'),
        total_refund=('total_refund_amount', 'sum'),
        avg_refund=('total_refund_amount', 'mean')
    ).reset_index()

    reason_distribution = {}
    for r_list in both_orders['refund_reasons']:
        for r in r_list:
            reason_distribution[r] = reason_distribution.get(r, 0) + 1

    return both_orders, category_summary, reason_distribution


def calculate_sla_breaches(tickets_df):
    """
    Calculate first-response SLA breaches and credits:
    Targets (Policy §3):
    - chat: 15 minutes (0.25h)
    - voice callback: 2 hours
    - social: 4 hours
    - email: 8 hours
    Credit: Rs 350 per breach
    """
    df = tickets_df.copy()
    df['first_response_at_dt'] = pd.to_datetime(df['first_response_at'])
    df['created_at_dt'] = pd.to_datetime(df['created_at'])

    df['first_response_hours'] = (df['first_response_at_dt'] - df['created_at_dt']).dt.total_seconds() / 3600.0

    target_map = {
        'chat': 15.0 / 60.0,  # 0.25h
        'voice': 2.0,
        'social': 4.0,
        'email': 8.0
    }
    df['sla_target_hours'] = df['channel'].map(target_map)
    df['is_sla_breach'] = df['first_response_hours'] > df['sla_target_hours']
    df['sla_credit_inr'] = np.where(df['is_sla_breach'], 350.0, 0.0)

    total_tickets = len(df)
    breach_count = int(df['is_sla_breach'].sum())
    breach_rate = breach_count / total_tickets * 100.0
    total_credit = breach_count * 350.0

    # Monthly stability trend
    df['created_month'] = df['created_at_dt'].dt.to_period('M').astype(str)
    monthly_trend = df.groupby('created_month').agg(
        total_tickets=('ticket_id', 'count'),
        breach_count=('is_sla_breach', 'sum'),
        total_credit_inr=('sla_credit_inr', 'sum')
    ).reset_index()
    monthly_trend['breach_rate_pct'] = (
        monthly_trend['breach_count'] / monthly_trend['total_tickets'] * 100.0
    )

    sla_summary = {
        'total_tickets': total_tickets,
        'breach_count': breach_count,
        'breach_rate_pct': breach_rate,
        'total_credit_inr': total_credit,
        'total_credit_lakh': total_credit / 100000.0,
        'monthly_trend': monthly_trend
    }

    return df, sla_summary
