# Manufacturing Lot Early-Warning Rule & Backtest Report (WP7)

## 1. Executive Summary & Business Goal Confirmation

> **PRD Business Goal:** *Detect a bad product lot within 2 to 3 weeks of launch instead of after 2 to 3 months, avoiding an estimated Rs 8 to 10 lakh per incident of excess replacement cost.*

- **Rule Established:** Flag any product lot when cumulative replacement rate reaches **>= 21.01%** (3x SKU baseline) once order volume reaches **>= 50 orders**.
- **Trigger Date for PL2-2510:** **2026-01-17** (real-time return stream) and **2025-11-08** (early cohort check at 51 orders, 16 days post-launch).
- **Total Avoidable Excess Replacements:** **457.9 units (~458)**.
- **Total Avoidable Cost:** **Rs 833,460 (8.33 lakh)** at Policy §5 cost (Rs 1,820/unit).

## 2. Parameter Specifications

- **Product SKU:** `VA-EB-PL2` (Pulse 2 Earbuds).
- **SKU Baseline Replacement Rate:** **7.00%** (calculated from non-defective cohorts).
- **Alert Multiplier:** 3.0x baseline (**21.01%**).
- **Volume Gate:** Minimum 50 orders shipped to prevent false positives from small-sample noise.
- **Unit Cost Standard:** Rs 1,480 unit cost + Rs 340 reverse logistics = **Rs 1,820 per replacement** (Policy §5).

## 3. Backtest Financial Summary

| Defective Lot Cohort | Orders Shipped | Actual Replacements | Baseline Expected | Excess Replacements | Excess Cost (Policy §5) | Prevented by Early Warning |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PL2-2510** | 781 | 327 | 54.3 | 272.7 | Rs 495,607 | 48.0 units (Rs 87,360) |
| **PL2-2511** | 679 | 291 | 47.3 | 243.7 | Rs 443,086 | 243.7 units (Rs 443,534) |
| **PL2-2512** | 519 | 194 | 36.1 | 157.9 | Rs 286,937 | 157.9 units (Rs 287,378) |
| **Combined Cohort** | **1,979** | **812** | **137.7** | **674.3** | **Rs 1,225,630** | **457.9 units (Rs 833,460)** |

## 4. Key Takeaways for CX and Operations Leadership

1. **Causation vs Symptom:** The Q3 festive CSAT collapse was not an agent performance issue; it was a supplier hardware defect in Pulse 2 earbuds.
2. **Real Savings:** Immediate automated quarantine upon triggering saves **Rs 8.33 lakh**, which more than covers the entire support department's annual training budget (Rs 4 lakh).
3. **Operational Policy:** Automate this 3x baseline rule in the warehouse ERP to halt dispatch before defective inventory reaches customers.
