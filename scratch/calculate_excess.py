import pandas as pd
import numpy as np

tickets = pd.read_csv('data/tickets.csv')
orders = pd.read_csv('data/orders.csv')
products = pd.read_csv('data/products.csv')

# Link tickets to orders (direct order_id and direct + single fallback)
tickets_with_order = tickets[tickets['order_id'].notna()].copy()
tickets_with_order['matched_order_id'] = tickets_with_order['order_id']

# Replacement count per order (direct order_id)
direct_order_repl = tickets_with_order.groupby('matched_order_id').agg(
    replacement_count=('replacement_issued', lambda x: (x == 'Y').sum()),
    has_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
    ticket_count=('ticket_id', 'count')
).reset_index()

orders_direct = orders.merge(direct_order_repl, left_on='order_id', right_on='matched_order_id', how='left')
orders_direct['replacement_count'] = orders_direct['replacement_count'].fillna(0).astype(int)
orders_direct['has_replacement'] = orders_direct['has_replacement'].fillna(False)
orders_direct['ticket_count'] = orders_direct['ticket_count'].fillna(0).astype(int)

# Check Pulse 2 lots
pl2_orders = orders_direct[orders_direct['sku'] == 'VA-EB-PL2'].copy()
pl2_orders['lot_month'] = pl2_orders['lot_code'].apply(lambda x: '-'.join(x.split('-')[:2]))

# Let's inspect baseline replacement rates:
# 1. Non-PL2 products
non_pl2 = orders_direct[orders_direct['sku'] != 'VA-EB-PL2']
print(f'Non-PL2 products orders: {len(non_pl2)}, replacements: {non_pl2["replacement_count"].sum()} ({non_pl2["has_replacement"].sum()/len(non_pl2)*100:.2f}%)')

# 2. PL2 baseline (outside 2510, 2511, 2512)
pl2_normal = pl2_orders[~pl2_orders['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])]
print(f'PL2 baseline orders (outside 2510-2512): {len(pl2_normal)}, replacements: {pl2_normal["replacement_count"].sum()} ({pl2_normal["has_replacement"].sum()/len(pl2_normal)*100:.2f}%)')

# 3. Affected PL2 lots: 2510, 2511, 2512
pl2_affected = pl2_orders[pl2_orders['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])].copy()
print(f'PL2 affected orders (2510, 2511, 2512): {len(pl2_affected)}, replacements: {pl2_affected["replacement_count"].sum()} ({pl2_affected["has_replacement"].sum()/len(pl2_affected)*100:.2f}%)')

# Now check with single fallback included:
# Let's see how much difference fallback makes
tickets_missing_order = tickets[tickets['order_id'].isna()].copy()
orders['order_date_dt'] = pd.to_datetime(orders['order_date'])
tickets_missing_order['created_at_dt'] = pd.to_datetime(tickets_missing_order['created_at'])

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
    tickets_with_order[['ticket_id', 'matched_order_id', 'replacement_issued']],
    single_matches[['ticket_id', 'matched_order_id', 'replacement_issued']]
])

linked_order_repl = linked_tickets.groupby('matched_order_id').agg(
    replacement_count=('replacement_issued', lambda x: (x == 'Y').sum()),
    has_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
    ticket_count=('ticket_id', 'count')
).reset_index()

orders_linked = orders.merge(linked_order_repl, left_on='order_id', right_on='matched_order_id', how='left')
orders_linked['replacement_count'] = orders_linked['replacement_count'].fillna(0).astype(int)
orders_linked['has_replacement'] = orders_linked['has_replacement'].fillna(False)

pl2_linked = orders_linked[orders_linked['sku'] == 'VA-EB-PL2'].copy()
pl2_linked['lot_month'] = pl2_linked['lot_code'].apply(lambda x: '-'.join(x.split('-')[:2]))
pl2_aff_linked = pl2_linked[pl2_linked['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])]
pl2_norm_linked = pl2_linked[~pl2_linked['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])]

print('\n--- REPLACEMENT COUNTS AND RATES (DIRECT ONLY vs DIRECT + FALLBACK) ---')
print('DIRECT ONLY:')
print(f'  Affected lots orders: {len(pl2_affected)}')
print(f'  Affected replacements: {pl2_affected["replacement_count"].sum()}')
print(f'  Affected orders with replacement: {pl2_affected["has_replacement"].sum()} ({pl2_affected["has_replacement"].sum()/len(pl2_affected)*100:.2f}%)')
print(f'  Baseline rate (PL2 normal): {pl2_normal["has_replacement"].sum()/len(pl2_normal)*100:.2f}%')
print(f'  Baseline rate (All non-affected products): {orders_direct[~orders_direct["lot_code"].str.contains("PL2-2510|PL2-2511|PL2-2512", na=False)]["has_replacement"].sum() / len(orders_direct[~orders_direct["lot_code"].str.contains("PL2-2510|PL2-2511|PL2-2512", na=False)])*100:.2f}%')

print('DIRECT + FALLBACK:')
print(f'  Affected lots orders: {len(pl2_aff_linked)}')
print(f'  Affected replacements: {pl2_aff_linked["replacement_count"].sum()}')
print(f'  Affected orders with replacement: {pl2_aff_linked["has_replacement"].sum()} ({pl2_aff_linked["has_replacement"].sum()/len(pl2_aff_linked)*100:.2f}%)')
print(f'  Baseline rate (PL2 normal): {pl2_norm_linked["has_replacement"].sum()/len(pl2_norm_linked)*100:.2f}%')
print(f'  Baseline rate (All non-affected products): {orders_linked[~orders_linked["lot_code"].str.contains("PL2-2510|PL2-2511|PL2-2512", na=False)]["has_replacement"].sum() / len(orders_linked[~orders_linked["lot_code"].str.contains("PL2-2510|PL2-2511|PL2-2512", na=False)])*100:.2f}%')

# PRD says:
# "Estimated excess replacements across Q3 2025 to Q2 2026: about 730, roughly Rs 13 lakh at the policy cost (unit cost plus Rs 340)."
# "The Rs 13 lakh figure uses a 9.9% baseline replacement share, which is an assumption."
# Let's verify:
# If affected replacements is ~865 (or ~812), and baseline is ~5-10%:
# Expected replacements at baseline: 1979 orders * 0.05 = ~99; or * 0.07 = ~138; excess = ~727 to 730!
# Cost per unit = 1480 + 340 = 1820.
# 730 * 1820 = Rs 1,328,600 (Rs 13.29 lakh)!
# At Arjun's Rs 2500: 730 * 2500 = Rs 18.25 lakh!
print('\n--- EXCESS REPLACEMENTS & COST ---')
total_affected_orders = len(pl2_aff_linked)
total_actual_repl = pl2_aff_linked['replacement_count'].sum()
actual_repl_orders = pl2_aff_linked['has_replacement'].sum()
print(f'Total affected orders (lots 2510, 2511, 2512): {total_affected_orders}')
print(f'Actual replacements issued in affected lots: {total_actual_repl}')
print(f'Actual orders with replacement in affected lots: {actual_repl_orders}')

# Test baseline assumptions:
# 1. 5% baseline (approx non-PL2 products baseline or PRD mention)
# 2. 7.0% baseline (PL2 normal baseline)
# 3. 9.9% baseline (PRD Risk section 9 mention)
unit_cost_pl2 = 1480
logistics_cost = 340
policy_cost_per_repl = unit_cost_pl2 + logistics_cost # 1820
arjun_cost_per_repl = 2500

for base_pct in [0.05, 0.0638, 0.070, 0.099]:
    expected_repl = total_affected_orders * base_pct
    excess_repl = total_actual_repl - expected_repl
    cost_policy = excess_repl * policy_cost_per_repl
    cost_arjun = excess_repl * arjun_cost_per_repl
    print(f'\nBaseline {base_pct*100:.1f}%:')
    print(f'  Expected replacements: {expected_repl:.1f}')
    print(f'  Excess replacements: {excess_repl:.1f} (~{round(excess_repl)})')
    print(f'  Policy cost (Rs 1,820): Rs {cost_policy:,.0f} ({cost_policy/100000:.2f} lakh)')
    print(f'  Arjun cost (Rs 2,500): Rs {cost_arjun:,.0f} ({cost_arjun/100000:.2f} lakh)')
    print(f'  Difference / Overstatement by Arjun: Rs {cost_arjun - cost_policy:,.0f} ({(cost_arjun - cost_policy)/100000:.2f} lakh)')
