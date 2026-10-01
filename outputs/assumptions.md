# Assumptions Log: Vireo Audio Support Analytics

This log documents every key judgement call, the rationale behind it, and the evidence that would change that decision.

---

## 1. Legacy Resolved Timestamp (+5h30m Shift)
- **Decision:** For tickets where `source_system == 'legacy_fd'`, add 5 hours and 30 minutes to `resolved_at`.
- **Why:** Before the shift, 2,309 of 3,374 legacy tickets (68.44%) had negative handle times (`resolved_at < first_response_at`), with a median negative duration of -5.2 hours. After adding +5h30m (converting UTC event log reconstruction to IST), exactly 0 tickets have negative handle time.
- **What would change my mind:** If system logs demonstrated that specific legacy ticket categories or agent shifts were already recorded in IST, or if resolution events had microsecond timestamps pointing to a different offset.

---

## 2. Agent Identity and Joining on `agent_id` Only
- **Decision:** Join ticket records to the roster strictly using `agent_id`, never agent name.
- **Why:** There are two distinct agents named "Kavya Pandey":
  - `A3006`: Chat Frontline, Morning shift, Tier 1
  - `A3029`: Logistics, Morning shift, Tier 1
  Joining on name would falsely cross-attribute ticket volume, CSAT, and handle times between Chat Frontline and Logistics.
- **What would change my mind:** Nothing in the data pipeline; joining on unique ID is standard best practice.

---

## 3. Handling Missing `order_id` & Ambiguous Order Matching
- **Decision:** Fall back to matching on `customer_id` + `product_sku` where `order_date <= created_at`. When more than one prior order matches, flag the ticket as ambiguous and do not silently assign a single `order_id`.
- **Why:** 4,107 of 11,750 tickets (34.95%) lack an `order_id`. Restricting candidates to orders placed before ticket creation yields 3,401 single-order matches, 92 zero matches, and exactly 614 ambiguous matches (orders placed multiple times by the same customer for the same SKU). Silently picking an arbitrary order would corrupt lot tracking and warranty validation.
- **What would change my mind:** If customer communication transcripts explicitly referenced an order date or unique shipment ID resolving the ambiguity.

---

## 4. Exclusion of CSAT Blanks (Never Treating as Zero)
- **Decision:** Exclude blank `csat_score` rows entirely from agent and queue averages. Report the response count alongside every mean.
- **Why:** 6,554 tickets (55.78%) have no CSAT response. Treating non-responses as 0 would distort average CSAT from 3.33 down to 1.47 and penalize agents with lower response rates rather than lower satisfaction.
- **What would change my mind:** If company policy explicitly mandated non-responses to be counted as dissatisfaction (contrary to Support Operating Policy §8).

---

## 5. Separation of Tier 1 and Tier 2 Metrics
- **Decision:** Never rank Tier 2 handle time or CSAT against Tier 1 agents. Evaluate Tier 2 in days and Tier 1 in hours.
- **Why:** Tier 2 (Escalations & Warranty) handles complex hardware RMAs and warranty replacements requiring physical shipping and inspection. Tier 2 median handle time is 120.87 hours (5.04 days) vs 0.42 hours (25 minutes) for Tier 1. Comparing them on the same axis violates Operating Policy §6 and misrepresents agent performance.
- **What would change my mind:** If Tier 2 was assigned frontline ticket volume or Tier 1 was authorized to execute warranty hardware replacements.

---

## 6. Legacy Currency (Native Unit vs INR)
- **Decision:** Treat legacy refund amounts as standard INR without applying an arbitrary 100x conversion factor.
- **Why:** In tickets with refunds and matched orders, the median refund-to-order-value ratio is 1.0000 (100%) in both legacy Freshdesk (363 tickets) and the current helpdesk (857 tickets). There are 0 tickets with extreme ratios (>100% or <1%).
- **What would change my mind:** If financial invoices or payment gateway ledgers from before September 2025 showed refunds logged in paise or foreign currency.

---

## 7. Roster Date-Range Joining
- **Decision:** Join tickets to agent roster assignments using both `agent_id` and the assignment date range (`from_date` to `to_date`).
- **Why:** Agents can transfer teams, shifts, or tiers over time (Support Operating Policy §7). While each of the 44 agents in the current roster currently has a single assignment row starting in 2023, the data pipeline must strictly enforce date-range filtering to support historical audits without multiplying rows.
- **What would change my mind:** If IT confirmed roster rows represent permanent all-time snapshots rather than temporal assignments.

---

## 8. Case-Mix CSAT Regression Model Covariates
- **Decision:** Use an Ordinary Least Squares (OLS) linear model with `category`, `channel`, `priority`, `is_PL2` (Pulse 2 earbuds binary flag), and `period` (YYYY-MM) as exogenous covariates predicting `csat_score`.
- **Why:** This controls directly for exogenous ticket difficulty (e.g. charging and warranty issues have coefficients of -0.95 and -0.89, and Pulse 2 earbuds carry a -0.21 penalty). Linear regression runs in milliseconds at Rs 0 cost without external dependencies, fully adhering to Tech Stack and Finance constraints.
- **What would change my mind:** If non-linear interactions between channel and product materially altered agent-level residuals, or if additional ticket metadata (e.g. customer tenure) became available.

---

## 9. Identification of "Kavya's Four" and the Hardware Triage Rota
- **Decision:** Identify "Kavya's four" as the four Chat Frontline agents with high Pulse 2 exposure (A3004 Siddharth Kapoor [53.1%], A3005 Zaid Khanna [50.2%], A3006 Kavya Pandey [47.0%], and A3007 Siddharth Trivedi [51.1%]). The Hardware Triage Rota is defined as Kavya's four plus the 6 Escalations & Warranty agents (A3039 to A3044).
- **Why:** Neha's email explicitly notes that "the hardware triage rota (Kavya's four plus the warranty team) get the angriest customers by design." In the data, these exact 4 Chat Frontline agents handled 47% to 53% Pulse 2 defect tickets (vs. 24%–37% for other chat frontline agents).
- **What would change my mind:** If official shift-routing tables or CRM routing rules defined a different list of agents on the hardware triage rota.

---

## 10. Boundaries of Case-Mix Adjustment (Cannot Separate Team from Person)
- **Decision:** Explicitly document that case-mix adjustment controls for ticket-level queue difficulty but cannot separate team-level effects from individual agent competence.
- **Why:** Ticket types are segregated by team: only Escalations & Warranty handles Tier 2 RMA tickets, and rota agents handle the severe hardware complaints. Because team assignment is collinear with queue difficulty, unmeasured ticket friction remains in the agent residual. Furthermore, agent confidence intervals overlap substantially (mean standard error ±0.10, margin of error ±0.20), making individual rank differences statistically indistinguishable.
- **What would change my mind:** If tickets were randomized across all agents regardless of tier or team, creating an unconfounded natural experiment.

---

## 11. Replacement Costing Standard (Rs 1,820 vs. Arjun's Rs 2,500)
- **Decision:** Compute replacement costs strictly using the formula defined in Support Operating Policy §5: Product Unit Cost + Rs 340 reverse pickup and forward shipping. For Pulse 2 (unit cost Rs 1,480), this equals Rs 1,820 per replacement. Do not use Arjun Mehta's anecdotal Rs 2,500 figure.
- **Why:** Policy §5 explicitly states: *"Replacement cost for planning: the product's unit cost (see products.csv) plus Rs 340 for reverse pickup and forward shipping. Refurbishment recovery is not to be assumed in business cases."* Priya's email explicitly notes that Arjun's Rs 2,500 figure is incorrect arithmetic. Using Rs 2,500 overstates replacement financial impact by Rs 4.94 lakh.
- **What would change my mind:** If Finance presented audited accounting ledgers showing additional direct vendor RMA handling charges exceeding the Rs 340 logistics line.

---

## 12. Baseline Replacement Rate Assumption (7.0%)
- **Decision:** Use the normal Pulse 2 replacement rate of 7.00% (batches outside October–December 2025) as the baseline for calculating excess replacements.
- **Why:** Unaffected Pulse 2 batches average a 7.00% replacement rate (and non-PL2 products average 4.0% to 6.4%). Across the 1,979 orders shipped in lots PL2-2510, PL2-2511, and PL2-2512, expected replacements at 7.0% are 138.6, resulting in exactly 726.4 (~726) excess replacements and Rs 13.22 lakh in excess policy costs, matching the PRD's ~730 excess replacements and ~Rs 13 lakh.
- **What would change my mind:** If historical warranty records from prior product launches proved that standard earbud failure rates differ significantly from 7.0%.

---

## 13. Classification of the 131 Double-Remedy Orders
- **Decision:** Deconstruct the 131 orders receiving both a refund and a replacement into: (a) Legitimate operational cases (88 orders), (b) Genuine policy violations (22 orders), and (c) Ambiguous cancellations (21 orders).
- **Why:** Policy §5 states: *"In no case is a customer to receive both a refund and a replacement for the same order."* However, analyzing refund reason codes reveals that 55 orders involved goods returned and passing QC (`RETURN-QC-OK`), 35 orders were billing double charges (`DUP-PAYMENT`), and 4 were price matches (`PRICE-ADJ`). The true financial leakage from genuine double remedies (DOA-REPL, LOST-TRANSIT, WTY-BUYBACK) is isolated to 22 orders totaling Rs 62,551.
- **What would change my mind:** If internal audit logs revealed that customer service agents were systematically using `RETURN-QC-OK` to bypass system blocks against duplicate compensation.

---

## 14. First-Response SLA Breach Calculation
- **Decision:** Calculate SLA breaches based strictly on first response time against channel targets from Policy §3 (Chat: 15 min; Voice: 2 hrs; Social: 4 hrs; Email: 8 hrs), costed at Rs 350 store credit per breach.
- **Why:** Across 11,750 tickets, exactly 1,064 breached (9.06%, matching the exploratory ~9.1%), totaling Rs 372,400 (~Rs 3.7 lakh). Monthly breach rates varied narrowly between 6.4% and 11.3% throughout the 18 months, demonstrating complete operational stability and proving that support speed was not the driver of the CSAT drop.
- **What would change my mind:** If IT logs proved that automatic customer store credits were not actually disbursed on resolution.


