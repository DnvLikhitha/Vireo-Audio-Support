import pandas as pd
import numpy as np

tickets = pd.read_csv('data/tickets.csv')
orders = pd.read_csv('data/orders.csv')

# Direct order_id tickets
direct_tickets = tickets[tickets['order_id'].notna()].copy()

# Group by order_id to find orders that had BOTH a refund and a replacement
order_analysis = direct_tickets.groupby('order_id').agg(
    ticket_ids=('ticket_id', list),
    ticket_count=('ticket_id', 'count'),
    has_replacement=('replacement_issued', lambda x: (x == 'Y').any()),
    has_refund=('refund_amount_inr', lambda x: (x.notna() & (x > 0)).any()),
    refund_reasons=('refund_reason_code', lambda x: list(x.dropna())),
    refund_amounts=('refund_amount_inr', lambda x: list(x.dropna())),
    replacements_list=('replacement_issued', list),
    skus=('product_sku', list),
    channels=('channel', list),
    agent_ids=('agent_id', list)
).reset_index()

both_131 = order_analysis[order_analysis['has_replacement'] & order_analysis['has_refund']].copy()
print(f'Total direct orders with both refund and replacement: {len(both_131)}')

# Inspect refund reasons
all_reasons = []
for r_list in both_131['refund_reasons']:
    all_reasons.extend(r_list)

reason_counts = pd.Series(all_reasons).value_counts()
print('\nBreakdown of refund reasons for the 131 orders:')
print(reason_counts)

# Let's inspect each reason code:
# Policy §5 definitions:
# - RETURN-QC-OK: "Return received and passed QC" -> Customer returned defective item, replacement was sent earlier, or customer returned replacement and got refund, or return passed QC and refund was issued after replacement failed. This is legitimate!
# - DUP-PAYMENT: "Duplicate or failed payment" -> Customer paid twice for one order, so the second payment was refunded, and the product itself was replaced. Legitimate billing refund!
# - CANCEL: "Cancellation before dispatch" -> Order was cancelled or partly cancelled, but replacement was issued. Could be error or multiple items.
# - PRICE-ADJ: "Price or coupon adjustment" -> Customer bought before sale / price match refund, and item later had hardware issue replaced. Legitimate price adjustment!
# - DOA-REPL: "Dead on arrival, refund chosen" -> BUT policy says customer chooses refund OR replacement, not both! This is a clear policy breach / genuine error!
# - LOST-TRANSIT: "Lost or undelivered" -> Reshipment or refund. If both reshipped/replaced and refunded, violation!
# - WTY-BUYBACK: "Warranty buy-back" -> Buyback refund AND replacement? Error!
# - GW-OTHER: "Goodwill / Other" -> Goodwill credit (capped at Rs 500) or error.

print('\nCheck ticket count per order for the 131 orders:')
print(both_131['ticket_count'].value_counts())

# Single ticket vs multi-ticket
# Did refund and replacement happen on the same ticket or different tickets?
same_ticket_both = direct_tickets[(direct_tickets['replacement_issued'] == 'Y') & (direct_tickets['refund_amount_inr'] > 0)]
print(f'\nOrders where refund and replacement occurred on the SAME ticket: {len(same_ticket_both)}')
print(same_ticket_both[['ticket_id', 'order_id', 'refund_reason_code', 'refund_amount_inr', 'replacement_issued']])

# Classify legitimate vs potential policy violation / genuine errors:
# Legitimate:
# 1. RETURN-QC-OK: return passed QC (standard return process, 50 orders)
# 2. DUP-PAYMENT: refund of accidental double charge (35 orders)
# 3. PRICE-ADJ: refund of price difference (8 orders)
# Genuine errors / policy violations (customer received product replacement AND refund of product price):
# 4. DOA-REPL: policy explicitly says "Dead on arrival: customer chooses full refund OR replacement" (10 orders)
# 5. LOST-TRANSIT: "reshipment or refund" (10 orders)
# 6. WTY-BUYBACK: buyback refund plus replacement (4 orders)
# 7. CANCEL / GW-OTHER / etc.

def classify_order(reasons):
    # Check if any legitimate business reason
    legit_reasons = {'RETURN-QC-OK', 'DUP-PAYMENT', 'PRICE-ADJ'}
    error_reasons = {'DOA-REPL', 'LOST-TRANSIT', 'WTY-BUYBACK'}

    r_set = set(reasons)
    if r_set.issubset(legit_reasons):
        return 'Legitimate (QC Return / Dup Payment / Price Adj)'
    elif any(r in error_reasons for r in r_set):
        return 'Genuine Policy Violation (Refund + Replacement for same fault)'
    else:
        return 'Ambiguous / Potential Error (Cancel/Other)'

both_131['category'] = both_131['refund_reasons'].apply(classify_order)
print('\nClassification of the 131 double-remedy orders:')
print(both_131['category'].value_counts())

# Financial exposure of genuine errors:
both_131['total_refund_amount'] = both_131['refund_amounts'].apply(sum)
for cat, grp in both_131.groupby('category'):
    print(f'\n{cat}:')
    print(f'  Orders: {len(grp)}')
    print(f'  Total refund issued: Rs {grp["total_refund_amount"].sum():,.0f}')
    print(f'  Avg refund per order: Rs {grp["total_refund_amount"].mean():,.0f}')
