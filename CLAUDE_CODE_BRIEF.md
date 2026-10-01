# Claude Code Brief: Vireo Audio Support Analytics (Set B)

Paste this file (or point Claude Code at it) at the start of the session. Read `PRD.md` and `TECHSTACK.md` too.

## Mission

Build a small, runnable tool that (1) delivers the dashboard Priya asked for (CSAT and handle time per agent, bottom ten flagged) and (2) makes it fair and honest, then (3) surfaces the real driver of the CSAT slide: a product-lot fault in the Pulse 2 earbuds (VA-EB-PL2). Budget: about 5 hours of total human effort. Prefer a small thing that runs over a large thing that doesn't.

## Hard constraints

- **No per-ticket LLM calls at runtime.** Finance (Arjun) objected to about Rs 5 per ticket across ~12,000 tickets. Runtime must be rules + classic ML only, Rs 0 per run.
- An LLM may be used **offline, on a small sample only** (a few hundred tickets) to help design categories and draft labels. Log what it cost.
- Must start from the README on a clean machine: one install command, one run command.
- Do not write code until you have printed the data-quality checks below and I have seen the output.
- Join agents on `agent_id` only, never on name. Two agents are called Kavya Pandey (A3006 Chat, A3029 Logistics).

## Data traps to handle (in this order)

1. **Legacy timestamps.** For `source_system == legacy_fd`, `resolved_at` was rebuilt from a UTC log while other fields are IST. Add 5h30m to legacy `resolved_at`. Evidence from exploration: about 72% of legacy handle times were negative (median about -5.1h) before the fix and 0 negative after.
2. **Handle time** = `first_response_at` to `resolved_at` (policy section 10), not creation to resolution. Tier 2 handle time is in days and must never be ranked against Tier 1.
3. **CSAT blanks** = no response. Exclude from averages. Never treat as zero. Report response count per agent.
4. **Legacy currency.** Policy section 9 says legacy money uses a native unit. Exploration found no 100x difference in refund-to-order-value ratios between systems. Re-check on legacy refunds before Sep 2025 and document the result either way. Do not invent a conversion.
5. **Duplicates.** Policy section 9 says some legacy tickets were re-imported. Exact-key matching found none. About 70 rows share near-identical messages. Investigate and report, without claiming there are none.
6. **`transfers`** exists only in the current helpdesk. Blank for legacy means unknown, not zero.
7. **Missing `order_id` (~35% of tickets).** Fall back to `customer_id` + `product_sku`. About 614 of ~4,100 fallbacks match multiple orders. Flag these as ambiguous and do not silently pick one.
8. **Junk IVR transcripts (~40 tickets).** Exclude from text analysis only. Keep them in operational metrics.
9. **Roster** has one row per assignment with from/to dates. Join by agent_id and date range.
10. **Category tag** is set by an intake bot and only sometimes corrected. Do not treat it as root cause.

## Work packages (do in order, stop and show me the output of each)

**WP1: Load, clean, data-quality report (target 45 min).**
Print a data-quality report: row counts, timezone fix before/after, blanks, duplicates, join coverage. Save as `outputs/data_quality.md`.

**WP2: Agent dashboard as asked (target 45 min).**
Per agent: CSAT (mean, n responses, 95% interval), median handle time, ticket count, team, tier, shift. Flag the bottom ten by raw CSAT, shown separately for Tier 1 and Tier 2. Never put Tier 2 and Tier 1 on the same handle-time ranking.

**WP3: Make it fair (target 45 min).**
Add a mix-adjusted view: expected CSAT given category, channel, priority, product (PL2 or not) and period, then actual minus expected. Show raw and adjusted bottom ten side by side, and mark agents on the hardware triage rota and the warranty team. In exploration, the adjusted bottom ten was the same ten agents, so state plainly what the adjustment can and cannot tell us. It cannot separate team from person. Do not oversell it.

**WP4: Find the cause (target 60 min).**
- Replacement and ticket rate per manufacturing lot (`orders.lot_code`) against orders shipped per lot. Show PL2 lots 2510, 2511, 2512 against baseline.
- Excess replacements and cost, using policy formula: unit cost + Rs 340 per replacement. Do not use Rs 2,500.
- Count orders where a refund and a replacement were both issued (policy section 5 forbids both). Exploration found 131 orders. Separate genuine errors from legitimate cases such as returns passed QC, and say so.
- SLA breach count and credits at Rs 350 each (exploration: ~9.1% breach rate, about Rs 3.7 lakh over 18 months). Show it is stable and not the cause of the slide.

**WP5: Text classifier, cheap (target 45 min).**
Rule-based keyword classifier on `customer_message` and `agent_notes` for root-cause themes (for example: one earbud dead, not charging, pairing drop, delivery, refund delay). Compare against the intake-bot category. Report where the bot tag is wrong.

**WP6: Validation (target 30 min).**
Hand-label a stratified sample of about 120 tickets (my labels, not the model's). Report accuracy and the main failure modes of the classifier. Also report checks on the timezone fix, join coverage and lot-rate stability. Say how often the tool is wrong.

**WP7: Lot early-warning (target 30 min).**
A simple rule: flag a lot when its replacement rate reaches about 3 times the SKU baseline once it has at least 50 orders. Backtest it: on what date would it have fired for PL2-2510, and what excess cost could have been avoided if the lot had been stopped then? This is the business-goal number.

## Cut list (do not build)

Authentication, databases, polished UI design, deep-learning or LLM classification at runtime, forecasting, mobile layout. If time is short, drop WP5 before WP4.

## Assumptions log (keep a running file `outputs/assumptions.md`)

For every judgement call: what I decided, why, what would change my mind. Examples: the 5h30 shift, the Kavya identification, the minimum responses per agent for ranking, how ambiguous order joins are treated.

## Definition of done

- `README.md` that works on a clean machine.
- Dashboard runs locally.
- `outputs/` contains the data-quality report, lot analysis, validation results and assumptions log.
- Every number in the memo traces to a table in the tool.
