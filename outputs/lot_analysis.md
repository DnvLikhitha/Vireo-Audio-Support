# Manufacturing Lot Analysis & Financial Impact Report (WP4)

## 1. Executive Summary
- **Root Cause Identified:** The company-wide CSAT slide was driven by defective Pulse 2 earbuds (SKU `VA-EB-PL2`) from manufacturing lots **PL2-2510, PL2-2511, and PL2-2512** (October–December 2025).
- **Replacement Rate Spike:** Replacement rates surged to **37.4% – 42.9%** across these three lots, compared to a baseline of **7.0%** for normal Pulse 2 lots and **4.0%** for non-PL2 products.
- **Excess Replacements:** **726 excess replacements** were issued across 1,979 shipped units.
- **Policy Cost Impact:** Total excess cost is **Rs 13.22 lakh** (using Policy §5: unit cost Rs 1,480 + Rs 340 logistics = Rs 1,820).
- **Correction to Finance:** Finance Controller Arjun Mehta's estimate of Rs 2,500 overstated excess costs by **Rs 4.94 lakh** (Rs 18.16 lakh estimated vs. Rs 13.22 lakh actual).

## 2. Pulse 2 Monthly Batch Performance

| Batch Month | Orders Shipped | Tickets | Replacements Issued | Orders w/ Replacement | Replacement Rate | Ticket Rate |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| PL2-2504 | 36 | 38 | 4 | 4 | 11.1% | 105.6% |
| PL2-2505 | 135 | 113 | 11 | 11 | 8.1% | 83.7% |
| PL2-2506 | 184 | 137 | 16 | 15 | 8.2% | 74.5% |
| PL2-2507 | 276 | 200 | 22 | 20 | 7.2% | 72.5% |
| PL2-2508 | 438 | 313 | 31 | 31 | 7.1% | 71.5% |
| PL2-2509 | 573 | 395 | 43 | 42 | 7.3% | 68.9% |
| PL2-2510 | 781 | 913 | 352 | 327 | 41.9% | 116.9% |
| PL2-2511 | 679 | 809 | 310 | 291 | 42.9% | 119.1% |
| PL2-2512 | 519 | 582 | 203 | 194 | 37.4% | 112.1% |
| PL2-2601 | 340 | 210 | 27 | 27 | 7.9% | 61.8% |
| PL2-2602 | 171 | 109 | 11 | 11 | 6.4% | 63.7% |
| PL2-2603 | 184 | 89 | 12 | 12 | 6.5% | 48.4% |
| PL2-2604 | 128 | 42 | 1 | 1 | 0.8% | 32.8% |
| PL2-2605 | 70 | 15 | 4 | 4 | 5.7% | 21.4% |
| PL2-2606 | 7 | 1 | 0 | 0 | 0.0% | 14.3% |

## 3. Double-Remedy Audit (Policy §5: Refund + Replacement)
- **Total Detected Orders:** 131 orders received both a refund and a replacement.
- **Legitimate Operations (88 orders, Rs 220,971):**
  - 55 orders: `RETURN-QC-OK` (legitimate return received and passed QC after replacement or cancellation).
  - 35 orders: `DUP-PAYMENT` (customer was accidentally double-charged; refund fixed the billing error while replacement resolved the hardware issue).
  - 4 orders: `PRICE-ADJ` (post-purchase price match or coupon adjustment).
- **Genuine Policy Violations (22 orders, Rs 62,551):**
  - 11 orders: `DOA-REPL` (Dead on Arrival; Policy §5 mandates customer chooses refund OR replacement, not both).
  - 8 orders: `LOST-TRANSIT` (Lost in transit; received both reshipment and refund).
  - 3 orders: `WTY-BUYBACK` (Warranty buy-back refund plus replacement).
- **Ambiguous / Cancellations (21 orders, Rs 71,912):**
  - 20 orders: `CANCEL` (cancellation before dispatch with cross-ticket replacement).
  - 2 orders: `GW-OTHER` (goodwill refunds).

## 4. First-Response SLA Breach Audit
- **Overall Breach Rate:** **9.06%** (1,064 breaches out of 11,750 tickets).
- **Total Credits Issued:** **Rs 372,400** (3.72 lakh) at Rs 350 per breach.
- **Stability:** The monthly breach rate remained remarkably stable across all 18 months (varying narrowly between 6.4% and 11.3%, averaging 9.1%). SLA adherence was not the cause of the customer satisfaction slide.
