import pandas as pd
import numpy as np

# Load test predictions
import sys
sys.path.append('scratch')
from test_classifier import clean_tickets

tickets = clean_tickets.copy()
tickets['created_at_dt'] = pd.to_datetime(tickets['created_at'])
tickets['quarter'] = tickets['created_at_dt'].dt.to_period('Q').astype(str)
tickets['month'] = tickets['created_at_dt'].dt.to_period('M').astype(str)

print('=== THEME MIX OVER TIME (QUARTERLY) ===')
q_theme = pd.crosstab(tickets['quarter'], tickets['predicted_theme'], normalize='index') * 100
print(q_theme[['one_earbud_dead_or_not_charging', 'charging_case_fault', 'battery_drain', 'pairing_connection_drop', 'delivery_tracking', 'refund_payment_delay']].to_string())

print('\n=== THEME MIX FOR PULSE 2 (VA-EB-PL2) OVER TIME ===')
pl2 = tickets[tickets['product_sku'] == 'VA-EB-PL2'].copy()
pl2_q_theme = pd.crosstab(pl2['quarter'], pl2['predicted_theme'], normalize='index') * 100
print(pl2_q_theme[['one_earbud_dead_or_not_charging', 'charging_case_fault', 'battery_drain', 'pairing_connection_drop', 'delivery_tracking', 'refund_payment_delay']].to_string())

print('\n=== THEME MIX FOR PULSE 2 (VA-EB-PL2) BY MANUFACTURING LOT BATCH ===')
# To get lot for tickets, we join with orders
orders = pd.read_csv('data/orders.csv')
orders['order_date_dt'] = pd.to_datetime(orders['order_date'])

# Direct and fallback matching
direct_t = pl2[pl2['order_id'].notna()].copy()
direct_t = direct_t.merge(orders[['order_id', 'lot_code']], on='order_id', how='left')

missing_t = pl2[pl2['order_id'].isna()].copy()
fallback_c = missing_t.merge(
    orders[['order_id', 'customer_id', 'sku', 'lot_code', 'order_date_dt']],
    left_on=['customer_id', 'product_sku'],
    right_on=['customer_id', 'sku'],
    how='left'
)
valid_c = fallback_c[fallback_c['order_date_dt'] <= fallback_c['created_at_dt']]
single_match_ids = valid_c.groupby('ticket_id')['order_id_y'].count()
single_match_ids = single_match_ids[single_match_ids == 1].index
single_f = valid_c[valid_c['ticket_id'].isin(single_match_ids)].copy()
single_f['order_id'] = single_f['order_id_y']

linked_pl2 = pd.concat([direct_t, single_f])
linked_pl2['lot_month'] = linked_pl2['lot_code'].apply(lambda x: '-'.join(str(x).split('-')[:2]) if pd.notna(x) else 'unknown')

lot_theme = pd.crosstab(linked_pl2['lot_month'], linked_pl2['predicted_theme'], normalize='index') * 100
print(lot_theme[['one_earbud_dead_or_not_charging', 'charging_case_fault', 'battery_drain', 'pairing_connection_drop', 'delivery_tracking', 'refund_payment_delay']].to_string())

print('\nCounts of themes in affected lots (2510, 2511, 2512):')
aff_lots = linked_pl2[linked_pl2['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])]
print(aff_lots['predicted_theme'].value_counts())
print('\nPercentage of themes in affected lots (2510, 2511, 2512):')
print(aff_lots['predicted_theme'].value_counts(normalize=True) * 100)
