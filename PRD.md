# PRD: Vireo Support Insight Tool

**Client:** Vireo Audio (Priya Raman, Head of Customer Experience)
**Status:** Draft for a 5-hour build
**Numbers below come from my exploratory checks and must be reproduced by the tool before use in the memo.**

## 1. Problem

CSAT has been sliding since the festive season. Priya wants a per-agent dashboard of CSAT and handle time with the bottom ten flagged, to target a Rs 4 lakh Q3 training budget. The top five get a Diwali bonus, so the ranking has real consequences for people.

## 2. What the data suggests

- The slide is concentrated in one product. Pulse 2 earbuds (VA-EB-PL2) went from near 0% of tickets in early 2025 to about 65% in Q1 2026. PL2 tickets average CSAT 3.07 against 3.48 for others. Replacements are 26% of PL2 tickets against 10% for the rest.
- Three manufacturing lots (2025-10, 2025-11, 2025-12) show replacement rates of about 28 to 33% of orders against a baseline of about 5%. Lots from 2026-01 onward are back at baseline.
- Estimated excess replacements across Q3 2025 to Q2 2026: about 730, roughly Rs 13 lakh at the policy cost (unit cost plus Rs 340).
- The six lowest raw-CSAT agents are all Tier 2 (Escalations & Warranty). Tier 2 handle time is measured in days and policy section 6 says it must not be compared with Tier 1. The next four are Chat Frontline agents with 47 to 53% PL2 tickets.
- Replacement volume rose about 100% against festive volume of about 30%, so volume alone does not explain it.

## 3. Goals

**Business goal (to be confirmed by the tool):**
Detect a bad product lot within 2 weeks of its launch instead of after roughly 2 to 3 months, avoiding an estimated Rs 8 to 10 lakh per incident of excess replacement cost. The tool backtests this on the PL2 lots and states the exact figure.

**Product goals:**
1. Deliver the dashboard Priya asked for, without overstating what it shows.
2. Make the ranking fair, or clearly say where it cannot be.
3. Surface the lot-level cause with a cost number.
4. Run for Rs 0 per execution, with no per-ticket model calls.

## 4. Non-goals

Authentication, a database, a polished UI, runtime LLM classification, forecasting, any decision on an individual's pay, retraining or bonus.

## 5. Users

- **Priya (CX Head):** wants the dashboard and a decision on training spend.
- **Neha (Support Ops):** needs queue difficulty taken into account.
- **Arjun (Finance):** wants low run cost and correct replacement costing.
- **Sameer (IT):** needs a clean, reproducible run.

## 6. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| F1 | Load all CSVs, apply the legacy timezone fix, de-duplicate, and print a data-quality report | Must |
| F2 | Per-agent CSAT (mean, n, 95% interval) and median handle time, split by tier | Must |
| F3 | Bottom-ten flag, with sample size and a warning when intervals overlap | Must |
| F4 | Mix-adjusted CSAT view, shown beside raw, with the hardware rota and warranty team marked | Must |
| F5 | Lot analysis: replacement and ticket rate per lot against orders; PL2 lots highlighted | Must |
| F6 | Replacement costing with the policy formula, not the Rs 2,500 figure | Must |
| F7 | Refund-plus-replacement detector (policy section 5) | Should |
| F8 | SLA breach and credit summary at Rs 350 per breach | Should |
| F9 | Rule-based root-cause classifier on message and note text | Should |
| F10 | Lot early-warning rule with backtest | Must |
| F11 | Validation report from a hand-labelled sample | Must |

## 7. Data requirements and rules

- Join agents on `agent_id` only.
- Legacy `resolved_at` plus 5h30m (UTC to IST).
- Handle time is first response to resolution.
- Blank CSAT is excluded. Never zero.
- Blank `transfers` for legacy means unknown.
- Missing `order_id` uses a customer + SKU fallback and flags ambiguous matches.
- Junk IVR transcripts excluded from text analysis only.

## 8. Success metrics

| Metric | Target |
|---|---|
| Fresh-machine setup (README to dashboard) | Under 10 minutes |
| Per-run cost | Rs 0 |
| Text classifier accuracy on the hand-labelled sample | Reported honestly; aim for 80% or better on the main themes |
| Lot backtest | Flag date for PL2 lots stated, with the avoidable cost |
| Every figure in the memo | Traceable to a tool output |

## 9. Risks and limits

- Mix adjustment cannot separate team from person. Ranks of agents with overlapping intervals are not reliable (about 105 responses each, standard error about 0.11).
- The Kavya Pandey identification (A3006 vs A3029) is inferred from the email, not confirmed.
- Legacy currency units could not be verified from the exports and are an open question.
- The Rs 13 lakh figure uses a 9.9% baseline replacement share, which is an assumption.
- Refund-plus-replacement cases may include legitimate ones.

## 10. Open questions for Priya (not blocking)

1. Does the bonus ranking stay Tier 1 only?
2. Who owns manufacturing-lot escalation today?
3. Were PL2 units from lots 2025-10 to 2025-12 ever quarantined?
