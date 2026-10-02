import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=" * 60)
print("Vireo Audio Support - WP1 Data Quality Checks")
print("=" * 60)

# Load data
print("\n1. Loading data...")
tickets = pd.read_csv('data/tickets.csv')
agents = pd.read_csv('data/agents.csv')
orders = pd.read_csv('data/orders.csv')
customers = pd.read_csv('data/customers.csv')
products = pd.read_csv('data/products.csv')

print(f"   Tickets: {len(tickets)} rows")
print(f"   Agents: {len(agents)} rows")
print(f"   Orders: {len(orders)} rows")
print(f"   Customers: {len(customers)} rows")
print(f"   Products: {len(products)} rows")

# 2. Legacy timestamps check
print("\n2. Legacy timestamps check (source_system == legacy_fd):")
legacy_tickets = tickets[tickets['source_system'] == 'legacy_fd']
current_tickets = tickets[tickets['source_system'] == 'helpdesk']
print(f"   Legacy FD tickets: {len(legacy_tickets)}")
print(f"   Helpdesk tickets: {len(current_tickets)}")

if len(legacy_tickets) > 0:
    # Convert to datetime for comparison
    legacy_tickets = legacy_tickets.copy()
    legacy_tickets['first_response_at_dt'] = pd.to_datetime(legacy_tickets['first_response_at'])
    legacy_tickets['resolved_at_dt'] = pd.to_datetime(legacy_tickets['resolved_at'])

    # Calculate handle time as-is (should be negative for many)
    legacy_tickets['handle_time_hours_raw'] = (legacy_tickets['resolved_at_dt'] - legacy_tickets['first_response_at_dt']).dt.total_seconds() / 3600

    negative_count = (legacy_tickets['handle_time_hours_raw'] < 0).sum()
    median_negative = legacy_tickets[legacy_tickets['handle_time_hours_raw'] < 0]['handle_time_hours_raw'].median()

    print(f"   Tickets with negative handle time (before fix): {negative_count} ({negative_count/len(legacy_tickets)*100:.1f}%)")
    print(f"   Median negative handle time: {median_negative:.1f} hours")

    # Apply fix: add 5h30m to resolved_at for legacy
    legacy_tickets['resolved_at_fixed'] = legacy_tickets['resolved_at_dt'] + timedelta(hours=5, minutes=30)
    legacy_tickets['handle_time_hours_fixed'] = (legacy_tickets['resolved_at_fixed'] - legacy_tickets['first_response_at_dt']).dt.total_seconds() / 3600

    negative_after_fix = (legacy_tickets['handle_time_hours_fixed'] < 0).sum()
    print(f"   Tickets with negative handle time (after fix): {negative_after_fix}")
    if negative_after_fix > 0:
        median_after = legacy_tickets[legacy_tickets['handle_time_hours_fixed'] < 0]['handle_time_hours_fixed'].median()
        print(f"   Median negative handle time after fix: {median_after:.1f} hours")

# 3. Handle time calculation
print("\n3. Handle time calculation (first_response_at to resolved_at):")
# For all tickets after applying legacy fix
tickets_processed = tickets.copy()
tickets_processed['first_response_at_dt'] = pd.to_datetime(tickets_processed['first_response_at'])
tickets_processed['resolved_at_dt'] = pd.to_datetime(tickets_processed['resolved_at'])

# Apply legacy fix
legacy_mask = tickets_processed['source_system'] == 'legacy_fd'
tickets_processed.loc[legacy_mask, 'resolved_at_dt'] = tickets_processed.loc[legacy_mask, 'resolved_at_dt'] + timedelta(hours=5, minutes=30)

tickets_processed['handle_time_hours'] = (tickets_processed['resolved_at_dt'] - tickets_processed['first_response_at_dt']).dt.total_seconds() / 3600

print(f"   Mean handle time: {tickets_processed['handle_time_hours'].mean():.2f} hours")
print(f"   Median handle time: {tickets_processed['handle_time_hours'].median():.2f} hours")
print(f"   Handle time std dev: {tickets_processed['handle_time_hours'].std():.2f} hours")

# Check Tier 1 vs Tier 2 handle time (need to join with agents)
# We'll do this later after joining

# 4. CSAT blanks
print("\n4. CSAT blanks check:")
csat_blank = tickets['csat_score'].isna().sum()
csat_total = len(tickets)
print(f"   Blank CSAT scores: {csat_blank} ({csat_blank/csat_total*100:.1f}%)")
print(f"   Non-blank CSAT scores: {csat_total - csat_blank} ({(csat_total - csat_blank)/csat_total*100:.1f}%)")

if csat_total - csat_blank > 0:
    csat_nonblank = tickets['csat_score'].dropna()
    print(f"   CSAT score range: {csat_nonblank.min():.0f} to {csat_nonblank.max():.0f}")
    print(f"   CSAT mean (non-blank): {csat_nonblank.mean():.2f}")

# 5. Legacy currency check
print("\n5. Legacy currency check (refund_amount_inr vs order_value_inr):")
# Join tickets with orders to get order_value_inr
tickets_with_order = tickets.merge(orders[['order_id', 'order_value_inr']], on='order_id', how='left')
# Only look at tickets with refunds and orders
refund_tickets = tickets_with_order[tickets_with_order['refund_amount_inr'].notna() & tickets_with_order['order_value_inr'].notna()]
print(f"   Tickets with refunds and order values: {len(refund_tickets)}")

if len(refund_tickets) > 0:
    # Calculate refund/order ratio
    refund_tickets['refund_ratio'] = refund_tickets['refund_amount_inr'] / refund_tickets['order_value_inr']

    # Check for legacy vs helpdesk
    legacy_refund = refund_tickets[refund_tickets['source_system'] == 'legacy_fd']
    current_refund = refund_tickets[refund_tickets['source_system'] == 'helpdesk']

    print(f"   Legacy refund tickets: {len(legacy_refund)}")
    print(f"   Helpdesk refund tickets: {len(current_refund)}")

    if len(legacy_refund) > 0:
        legacy_median_ratio = legacy_refund['refund_ratio'].median()
        print(f"   Legacy median refund/order ratio: {legacy_median_ratio:.4f}")

    if len(current_refund) > 0:
        current_median_ratio = current_refund['refund_ratio'].median()
        print(f"   Helpdesk median refund/order ratio: {current_median_ratio:.4f}")

    # Check if any ratio > 1.0 (100%) or < 0.01 (1%) to spot potential unit issues
    extreme_ratios = refund_tickets[(refund_tickets['refund_ratio'] > 1.0) | (refund_tickets['refund_ratio'] < 0.01)]
    print(f"   Tickets with extreme refund ratios (>100% or <1%): {len(extreme_ratios)}")

# 6. Duplicates check
print("\n6. Duplicates check (near-identical messages):")
# Check customer_message and agent_notes for near duplicates
# We'll do a simple check: look for messages that are very similar (first 100 chars)
print("   Checking for near-duplicate customer messages (first 100 chars)...")
tickets['customer_message_first100'] = tickets['customer_message'].fillna('').str[:100]
tickets['agent_notes_first100'] = tickets['agent_notes'].fillna('').str[:100]

# Count duplicates based on first 100 chars
msg_duplicates = tickets['customer_message_first100'].duplicated().sum()
notes_duplicates = tickets['agent_notes_first100'].duplicated().sum()

print(f"   Customer messages with duplicate first 100 chars: {msg_duplicates}")
print(f"   Agent notes with duplicate first 100 chars: {notes_duplicates}")

# Also check exact duplicates (though policy says exact-key matching found none)
exact_msg_duplicates = tickets['customer_message'].duplicated().sum()
exact_notes_duplicates = tickets['agent_notes'].duplicated().sum()
print(f"   Exact duplicate customer messages: {exact_msg_duplicates}")
print(f"   Exact duplicate agent notes: {exact_notes_duplicates}")

# 7. Transfers check
print("\n7. Transfers check:")
transfers_blank = tickets['transfers'].isna().sum()
print(f"   Blank transfers: {transfers_blank} ({transfers_blank/len(tickets)*100:.1f}%)")

# Check if blank transfers are mostly legacy
legacy_transfers_blank = legacy_tickets['transfers'].isna().sum() if len(legacy_tickets) > 0 else 0
current_transfers_blank = current_tickets['transfers'].isna().sum() if len(current_tickets) > 0 else 0
print(f"   Legacy blank transfers: {legacy_transfers_blank} ({legacy_transfers_blank/len(legacy_tickets)*100:.1f}% of legacy)")
print(f"   Helpdesk blank transfers: {current_transfers_blank} ({current_transfers_blank/len(current_tickets)*100:.1f}% of helpdesk)")

# 8. Missing order_id fallback
print("\n8. Missing order_id check:")
missing_order_id = tickets['order_id'].isna().sum()
print(f"   Missing order_id: {missing_order_id} ({missing_order_id/len(tickets)*100:.1f}%)")

if missing_order_id > 0:
    # For missing order_id, we'll use customer_id + product_sku fallback
    missing_tickets = tickets[tickets['order_id'].isna()].copy()
    missing_tickets['fallback_key'] = missing_tickets['customer_id'].astype(str) + '_' + missing_tickets['product_sku']

    # Check how many fallback keys match multiple orders
    # First get customer_id + sku from orders
    orders['customer_sku_key'] = orders['customer_id'].astype(str) + '_' + orders['sku']
    order_counts = orders['customer_sku_key'].value_counts()

    # Check how many fallback keys in missing tickets appear multiple times in orders
    missing_fallback_keys = missing_tickets['fallback_key']
    ambiguous_count = 0
    for key in missing_fallback_keys.unique():
        if key in order_counts.index and order_counts[key] > 1:
            ambiguous_count += 1

    print(f"   Fallback keys that match multiple orders: {ambiguous_count}")
    print(f"   (These should be flagged as ambiguous and not silently picked)")

# 9. Junk IVR transcripts
print("\n9. Junk IVR transcripts check:")
# Based on email-thread.txt: "About forty tickets have junk in the customer message (IVR transcripts that failed)"
# Let's look for patterns that indicate IVR transcripts
ivr_pattern_tickets = tickets[tickets['customer_message'].str.contains('\[IVR transcript\]', na=False)]
print(f"   Tickets with '[IVR transcript]' in customer_message: {len(ivr_pattern_tickets)}")

# Also check for other IVR patterns
ivr_like = tickets[tickets['customer_message'].str.contains('IVR|Interactive Voice', case=False, na=False)]
print(f"   Tickets with IVR-related patterns in customer_message: {len(ivr_like)}")

# 10. Roster join check
print("\n10. Roster join check:")
# Agents.csv has from_date and to_date for assignments
# We need to join tickets to agents based on agent_id and date range
# First, extract date from ticket (using created_at or resolved_at?)
# According to policy, we should use the ticket date for joining
tickets['ticket_date'] = pd.to_datetime(tickets['created_at']).dt.date

# Convert agent dates
agents['from_date_dt'] = pd.to_datetime(agents['from_date'])
agents['to_date_dt'] = pd.to_datetime(agents['to_date'], errors='coerce')  # Some might be empty

# For now, let's just check if we can join on agent_id alone (ignoring date range for simplicity)
unique_agent_ids_in_tickets = tickets['agent_id'].dropna().unique()
unique_agent_ids_in_agents = agents['agent_id'].unique()

matched_agents = set(unique_agent_ids_in_tickets) & set(unique_agent_ids_in_agents)
unmatched_in_tickets = set(unique_agent_ids_in_tickets) - set(unique_agent_ids_in_agents)
unmatched_in_agents = set(unique_agent_ids_in_agents) - set(unique_agent_ids_in_tickets)

print(f"   Unique agent_ids in tickets: {len(unique_agent_ids_in_tickets)}")
print(f"   Unique agent_ids in agents: {len(unique_agent_ids_in_agents)}")
print(f"   Matched agent_ids: {len(matched_agents)}")
print(f"   Agent IDs in tickets not found in agents: {len(unmatched_in_tickets)}")
if len(unmatched_in_tickets) > 0:
    print(f"   Example unmatched IDs: {list(unmatched_in_tickets)[:5]}")
print(f"   Agent IDs in agents not found in tickets: {len(unmatched_in_agents)}")

# 11. Category tag note
print("\n11. Category tag note:")
print(f"   Unique categories in tickets: {tickets['category'].nunique()}")
print(f"   Top 5 categories: {tickets['category'].value_counts().head().to_dict()}")
print("   Note: Category tag is set by intake bot and only sometimes corrected. Do not treat as root cause.")

print("\n" + "=" * 60)
print("Data quality checks completed.")
print("=" * 60)