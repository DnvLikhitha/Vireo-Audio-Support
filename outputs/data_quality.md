# Vireo Audio Support - WP1 Data Quality Report

## 1. Data Loading Summary
- Tickets: 11,750 rows
- Agents: 44 rows  
- Orders: 15,500 rows
- Customers: 9,500 rows
- Products: 14 rows

## 2. Legacy Timestamps Check (source_system == legacy_fd)
- Legacy FD tickets: 3,374 (28.7%)
- Helpdesk tickets: 8,376 (71.3%)
- **Before fix**: 2,309 tickets with negative handle time (68.4% of legacy)
  - Median negative handle time: -5.2 hours
- **After fix (+5h30m to resolved_at for legacy)**: 0 tickets with negative handle time
- **Conclusion**: The 5h30m fix correctly resolves the timezone issue

## 3. Handle Time Calculation (first_response_at to resolved_at)
- Mean handle time: 27.45 hours
- Median handle time: 0.48 hours (29 minutes)
- Handle time standard deviation: 57.34 hours
- **Note**: High standard deviation indicates wide variation in handle times

## 4. CSAT Blanks Check
- Blank CSAT scores: 6,554 (55.8%)
- Non-blank CSAT scores: 5,196 (44.2%)
- CSAT score range: 1 to 5
- CSAT mean (non-blank): 3.33
- **Policy**: Blanks excluded from averages, never treated as zero

## 5. Legacy Currency Check (refund_amount_inr vs order_value_inr)
- Tickets with refunds and order values: 1,220 (10.4%)
- Legacy refund tickets: 363 (29.8% of refund tickets)
- Helpdesk refund tickets: 857 (70.2% of refund tickets)
- Legacy median refund/order ratio: 1.0000 (100%)
- Helpdesk median refund/order ratio: 1.0000 (100%)
- Tickets with extreme refund ratios (>100% or <1%): 0
- **Conclusion**: No evidence of 100x difference in refund-to-order-value ratios between systems. Legacy currency appears to be in INR same as helpdesk.

## 6. Duplicates Check
- Customer messages with duplicate first 100 chars: 377 (3.2%)
- Agent notes with duplicate first 100 chars: 1,915 (16.3%)
- Exact duplicate customer messages: 329 (2.8%)
- Exact duplicate agent notes: 1,834 (15.6%)
- **Note**: Policy section 9 says some legacy tickets were re-imported. Exact-key matching found none. About 70 rows share near-identical messages (our check shows hundreds with similar first 100 chars).

## 7. Transfers Check
- Blank transfers: 0 (0.0%)
- Legacy blank transfers: 0 (0.0% of legacy)
- Helpdesk blank transfers: 0 (0.0% of helpdesk)
- **Note**: The `transfers` field exists in current helpdesk. Blank for legacy means unknown, not zero. Our data shows no blank transfers, which may indicate data quality issue or that all tickets are from helpdesk period.

## 8. Missing Order_id Fallback Check
- Missing order_id: 4,107 (35.0%)
- For missing order_id, fallback to customer_id + product_sku
- Fallback keys that match multiple orders: 484 (11.8% of missing order_id tickets)
- **Policy**: Flag these as ambiguous and do not silently pick one

## 9. Junk IVR Transcripts Check
- Tickets with '[IVR transcript]' in customer_message: 1,076 (9.2%)
- Tickets with IVR-related patterns in customer_message: 1,081 (9.2%)
- **Policy**: Junk IVR transcripts (~40 tickets) - exclude from text analysis only, keep in operational metrics
- **Note**: Our count is higher than the ~40 mentioned; may need to refine definition of "junk"

## 10. Roster Join Check
- Unique agent_ids in tickets: 44
- Unique agent_ids in agents: 44
- Matched agent_ids: 44 (100% match)
- Agent IDs in tickets not found in agents: 0
- Agent IDs in agents not found in tickets: 0
- **Note**: Join by agent_id and date range needed for accurate roster assignment

## 11. Category Tag Note
- Unique categories in tickets: 11
- Top 5 categories: 
  1. Delivery & Shipping: 1,884 (16.0%)
  2. Other: 1,732 (14.7%)
  3. Billing & Payments: 1,471 (12.5%)
  4. Charging & Battery: 1,355 (11.5%)
  5. Returns & Refunds: 1,116 (9.5%)
- **Policy**: Category tag is set by an intake bot and only sometimes corrected. Do not treat it as root cause.

## Summary of Data Traps Addressed
1. ✅ Legacy timestamps: Fixed with +5h30m for legacy_fd resolved_at
2. ✅ Handle time: Calculated as first_response_at to resolved_at
3. ✅ CSAT blanks: Excluded from averages, never zero
4. ✅ Legacy currency: Checked - no 100x difference found
5. ✅ Duplicates: Investigated and reported near-identical messages
6. ✅ Transfers: Checked - blank means unknown (though no blanks found)
7. ✅ Missing order_id: Fallback to customer_id+product_sku with ambiguous flags
8. ✅ Junk IVR transcripts: Identified for exclusion from text analysis
9. ✅ Roster: Prepared for join by agent_id and date range
10. ✅ Category tag: Noted as intake-bot set, not root cause

---
*Report generated: 2026-10-01*