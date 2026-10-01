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

print('=== 1. TICKET TO ORDER LINKING & LOT ANALYSIS ===')
# How are tickets linked to orders?
# Direct match on order_id when present
# When order_id is missing, fallback to customer_id + product_sku where order_date <= created_at, excluding ambiguous matches
tickets_with_order = tickets[tickets['order_id'].notna()].copy()
tickets_with_order['matched_order_id'] = tickets_with_order['order_id']
tickets_with_order['match_type'] = 'direct'

tickets_missing_order = tickets[tickets['order_id'].isna()].copy()
orders['order_date_dt'] = pd.to_datetime(orders['order_date'])

# Candidate orders for fallback
fallback_candidates = tickets_missing_order.merge(
    orders[['order_id', 'customer_id', 'sku', 'lot_code', 'order_date_dt']],
    left_on=['customer_id', 'product_sku'],
    right_on=['customer_id', 'sku'],
    how='left'
)
# Valid candidate orders must be before/on ticket creation
valid_candidates = fallback_candidates[fallback_candidates['order_date_dt'] <= fallback_candidates['created_at_dt']]
order_counts_per_ticket = valid_candidates.groupby('ticket_id')['order_id_y'].count()

single_match_tickets = order_counts_per_ticket[order_counts_per_ticket == 1].index
single_matches = valid_candidates[valid_candidates['ticket_id'].isin(single_match_tickets)].copy()
single_matches['matched_order_id'] = single_matches['order_id_y']
single_matches['match_type'] = 'fallback_single'

ambiguous_tickets = order_counts_per_ticket[order_counts_per_ticket > 1].index
zero_match_tickets = set(tickets_missing_order['ticket_id']) - set(order_counts_per_ticket.index)

print(f'Total tickets: {len(tickets)}')
print(f'Direct order_id tickets: {len(tickets_with_order)}')
print(f'Fallback single match tickets: {len(single_matches)}')
print(f'Fallback ambiguous tickets: {len(ambiguous_tickets)}')
print(f'Fallback zero match tickets: {len(zero_match_tickets)}')

# Let's inspect ticket linking: should we use direct only, or direct + unambiguous fallback?
# Let's check both ways!
print('\nLet us check orders linked by direct vs direct + fallback:')
all_linked = pd.concat([
    tickets_with_order[['ticket_id', 'matched_order_id', 'replacement_issued', 'refund_amount_inr', 'refund_reason_code', 'product_sku']],
    single_matches[['ticket_id', 'matched_order_id', 'replacement_issued', 'refund_amount_inr', 'refund_reason_code', 'product_sku']]
])
print(f'Total linked ticket records: {len(all_linked)}')

print('\n=== 2. LOT CODE ANALYSIS (DIRECT ORDERS VS FALLBACK) ===')
# Let us check how many replacements per lot in orders
# Note: tickets has replacement_issued ('Y' / 'N')
# How is replacement tracked on order?
# Let's check replacement_issued distribution in tickets
print('replacement_issued values in tickets:')
print(tickets['replacement_issued'].value_counts(dropna=False))

# Let's link tickets to orders to calculate replacements per order
# Notice an order might have multiple tickets
# Does orders.csv have lot_code for all orders?
print('\norders.csv lot_code overview:')
print(f'Total orders: {len(orders)}')
print(f'Orders missing lot_code: {orders["lot_code"].isna().sum()}')
print(f'Unique lot codes: {orders["lot_code"].nunique()}')

# Let's check lot codes per SKU
orders_sku_lot = orders.groupby(['sku', 'lot_code']).size().reset_index(name='order_count')
print('Sample orders by SKU and lot:')
print(orders_sku_lot.head(15))

print('\nPulse 2 (VA-EB-PL2) lots:')
pl2_lots = orders_sku_lot[orders_sku_lot['sku'] == 'VA-EB-PL2']
print(pl2_lots)
