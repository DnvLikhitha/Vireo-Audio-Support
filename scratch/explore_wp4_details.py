import pandas as pd
import numpy as np
from datetime import timedelta

tickets = pd.read_csv('data/tickets.csv')
orders = pd.read_csv('data/orders.csv')
products = pd.read_csv('data/products.csv')

# Timezone fix on tickets
tickets['first_response_at_dt'] = pd.to_datetime(tickets['first_response_at'])
tickets['resolved_at_dt'] = pd.to_datetime(tickets['resolved_at'])
legacy_mask = tickets['source_system'] == 'legacy_fd'
tickets.loc[legacy_mask, 'resolved_at_dt'] = tickets.loc[legacy_mask, 'resolved_at_dt'] + timedelta(hours=5, minutes=30)
tickets['created_at_dt'] = pd.to_datetime(tickets['created_at'])

# First, link tickets to orders:
# 1. Direct order_id
# 2. Unambiguous fallback on customer_id + product_sku where order_date <= created_at
tickets_with_order = tickets[tickets['order_id'].notna()].copy()
tickets_with_order['matched_order_id'] = tickets_with_order['order_id']

tickets_missing_order = tickets[tickets['order_id'].isna()].copy()
orders['order_date_dt'] = pd.to_datetime(orders['order_date'])

fallback_candidates = tickets_missing_order.merge(
    orders[['order_id', 'customer_id', 'sku', 'lot_code', 'order_date_dt']],
    left_on=['customer_id', 'product_sku'],
    right_on=['customer_id', 'sku'],
    how='left'
)
valid_candidates = fallback_candidates[fallback_candidates['order_date_dt'] <= fallback_candidates['created_at_dt']]
order_counts_per_ticket = valid_candidates.groupby('ticket_id')['order_id_y'].count()
single_match_tickets = order_counts_per_ticket[order_counts_per_ticket == 1].index
single_matches = valid_candidates[valid_candidates['ticket_id'].isin(single_match_tickets)].copy()
single_matches['matched_order_id'] = single_matches['order_id_y']

linked_tickets = pd.concat([
    tickets_with_order[['ticket_id', 'matched_order_id', 'product_sku', 'channel', 'status',
                        'replacement_issued', 'refund_amount_inr', 'refund_reason_code',
                        'created_at_dt', 'first_response_at_dt', 'resolved_at_dt']],
    single_matches[['ticket_id', 'matched_order_id', 'product_sku', 'channel', 'status',
                     'replacement_issued', 'refund_amount_inr', 'refund_reason_code',
                     'created_at_dt', 'first_response_at_dt', 'resolved_at_dt']]
])

print('=== 1. CHECK ORDERS WITH BOTH REFUND AND REPLACEMENT (FINDING 131) ===')
# Let's aggregate refund and replacement at the order level
# An order might have multiple tickets
order_events_linked = linked_tickets.groupby('matched_order_id').agg(
    has_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
    has_refund=('refund_amount_inr', lambda x: (x.notna() & (x > 0)).any()),
    total_refund=('refund_amount_inr', 'sum'),
    reason_codes=('refund_reason_code', lambda x: list(x.dropna().unique())),
    ticket_count=('ticket_id', 'count')
).reset_index()

both_linked = order_events_linked[order_events_linked['has_replacement'] & order_events_linked['has_refund']]
print(f'Linked orders (direct + single fallback) with both refund and replacement: {len(both_linked)}')

# What about direct order_id only?
order_events_direct = tickets_with_order.groupby('matched_order_id').agg(
    has_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
    has_refund=('refund_amount_inr', lambda x: (x.notna() & (x > 0)).any()),
    total_refund=('refund_amount_inr', 'sum'),
    reason_codes=('refund_reason_code', lambda x: list(x.dropna().unique())),
    ticket_count=('ticket_id', 'count')
).reset_index()
both_direct = order_events_direct[order_events_direct['has_replacement'] & order_events_direct['has_refund']]
print(f'Direct order_id only orders with both refund and replacement: {len(both_direct)}')

# What about across all tickets where refund_amount_inr > 0 and replacement_issued == 'Y' on same ticket?
same_ticket_both = tickets[(tickets['replacement_issued'] == 'Y') & (tickets['refund_amount_inr'].notna()) & (tickets['refund_amount_inr'] > 0)]
print(f'Tickets with both refund and replacement on the SAME ticket: {len(same_ticket_both)}')

print('\nReason codes in orders with both refund and replacement:')
print(both_linked['reason_codes'].explode().value_counts())

print('\n=== 2. SLA BREACHES AND CREDITS (Target ~9.1%, ~Rs 3.7 lakh) ===')
# Targets from Policy §3:
# chat 15 minutes = 0.25 hours
# voice callback 2 hours
# social 4 hours
# email 8 hours
tickets['fr_hours'] = (tickets['first_response_at_dt'] - tickets['created_at_dt']).dt.total_seconds() / 3600

def get_target(channel):
    if channel == 'chat':
        return 15.0 / 60.0 # 0.25h
    elif channel == 'voice':
        return 2.0
    elif channel == 'social':
        return 4.0
    elif channel == 'email':
        return 8.0
    return np.nan

tickets['sla_target_hours'] = tickets['channel'].apply(get_target)
tickets['is_breach'] = tickets['fr_hours'] > tickets['sla_target_hours']
total_tickets = len(tickets)
breach_count = tickets['is_breach'].sum()
breach_rate = breach_count / total_tickets * 100
total_credit_inr = breach_count * 350
print(f'Total tickets: {total_tickets}')
print(f'SLA breach count: {breach_count} ({breach_rate:.2f}%)')
print(f'Total breach credits at Rs 350 each: Rs {total_credit_inr:,.0f} ({total_credit_inr/100000:.2f} lakh)')

# Check monthly stability of breach rate
tickets['created_month'] = tickets['created_at_dt'].dt.to_period('M').astype(str)
monthly_sla = tickets.groupby('created_month').agg(
    tickets=('ticket_id', 'count'),
    breaches=('is_breach', 'sum')
).reset_index()
monthly_sla['breach_rate_pct'] = monthly_sla['breaches'] / monthly_sla['tickets'] * 100
monthly_sla['credits_inr'] = monthly_sla['breaches'] * 350
print('\nMonthly SLA breach trend:')
print(monthly_sla.to_string(index=False))

print('\n=== 3. LOT REPLACEMENT AND TICKET RATES ===')
# Merge orders with linked tickets
# For each order in orders.csv, did it have any tickets? Any replacements?
order_ticket_stats = linked_tickets.groupby('matched_order_id').agg(
    ticket_count=('ticket_id', 'count'),
    replacement_count=('replacement_issued', lambda x: (x == 'Y').sum()),
    has_replacement=('replacement_issued', lambda x: (x == 'Y').any())
).reset_index()

orders_with_tickets = orders.merge(order_ticket_stats, left_on='order_id', right_on='matched_order_id', how='left')
orders_with_tickets['ticket_count'] = orders_with_tickets['ticket_count'].fillna(0).astype(int)
orders_with_tickets['replacement_count'] = orders_with_tickets['replacement_count'].fillna(0).astype(int)
orders_with_tickets['has_replacement'] = orders_with_tickets['has_replacement'].fillna(False)

# Let's group by lot_code for Pulse 2 (VA-EB-PL2)
pl2_orders = orders_with_tickets[orders_with_tickets['sku'] == 'VA-EB-PL2'].copy()
pl2_orders['lot_month'] = pl2_orders['lot_code'].apply(lambda x: '-'.join(x.split('-')[:2]) if isinstance(x, str) else 'unknown')

monthly_lots = pl2_orders.groupby('lot_month').agg(
    orders=('order_id', 'count'),
    tickets=('ticket_count', 'sum'),
    orders_with_replacement=('has_replacement', 'sum'),
    total_replacements=('replacement_count', 'sum')
).reset_index()
monthly_lots['ticket_rate_pct'] = monthly_lots['tickets'] / monthly_lots['orders'] * 100
monthly_lots['replacement_rate_pct'] = monthly_lots['orders_with_replacement'] / monthly_lots['orders'] * 100
print('\nPulse 2 Monthly Lot Batches:')
print(monthly_lots.to_string(index=False))

print('\nPulse 2 Sub-lot Level (2510, 2511, 2512):')
sub_lots = pl2_orders[pl2_orders['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])].groupby('lot_code').agg(
    orders=('order_id', 'count'),
    tickets=('ticket_count', 'sum'),
    orders_with_replacement=('has_replacement', 'sum')
).reset_index()
sub_lots['replacement_rate_pct'] = sub_lots['orders_with_replacement'] / sub_lots['orders'] * 100
print(sub_lots.to_string(index=False))

print('\nOverall Baseline Replacement Rate (All other products / unaffected PL2 lots):')
baseline_orders = orders_with_tickets[~orders_with_tickets['lot_code'].str.contains('PL2-2510|PL2-2511|PL2-2512', na=False)]
base_repl = baseline_orders['has_replacement'].sum() / len(baseline_orders) * 100
print(f'Non-affected orders replacement rate: {base_repl:.2f}% ({baseline_orders["has_replacement"].sum()} of {len(baseline_orders)})')

pl2_baseline = pl2_orders[~pl2_orders['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])]
pl2_base_repl = pl2_baseline['has_replacement'].sum() / len(pl2_baseline) * 100
print(f'Pulse 2 baseline replacement rate (outside 2510-2512): {pl2_base_repl:.2f}% ({pl2_baseline["has_replacement"].sum()} of {len(pl2_baseline)})')
