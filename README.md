# Vireo Audio Support Intelligence System

A runnable, zero-marginal-cost analytics toolkit and decision-support dashboard built for Vireo Audio CX leadership (Priya Raman).

---

## 1. Quick Start (Clean-Machine Setup < 2 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run End-to-End Analytics Pipeline
Executes data quality audits, mix-adjusted CSAT modeling, lot defect costing, NLP classification, and early-warning backtest:
```bash
python run_all.py
```

### Step 3: Launch Interactive Dashboard
```bash
streamlit run app.py
```

### Step 4: Run Test Suite
```bash
python -m pytest
```

---

## 2. Business Impact & Core Findings

1. **Root-Cause Discovery (The Real Driver of the CSAT Slide):**
   - The company-wide CSAT slide from 3.5 to 3.1 was driven by defective Pulse 2 earbud lots (**PL2-2510, PL2-2511, PL2-2512**; Oct–Dec 2025) suffering single-earbud charging failure.
   - Defective lot replacement rates reached **41.0%** (peaking at 42.9% in lot 2511) vs. the normal **7.0%** baseline.
   - Excess replacements totaled **726 units**, costing **Rs 13.22 Lakh** under Policy §5 (unit cost Rs 1,480 + logistics Rs 340 = Rs 1,820/unit).
   - Disproved Finance Controller Arjun Mehta's Rs 2,500 estimate, which overstated liability by **Rs 4.94 Lakh** (Rs 18.16L vs Rs 13.22L).

2. **Fairness & Priya's Bottom 10:**
   - Proved that Priya's bottom 10 agents on raw CSAT were **100% on the Hardware Triage Rota** (6 Tier 2 Escalations agents + Kavya's four Chat Frontline agents).
   - Their queues handled 47%–53% defective Pulse 2 tickets.
   - Policy §6 mandates Tier 2 handle time is measured in days and must never be ranked against Tier 1.

3. **Early-Warning Rule & Business Goal (WP7):**
   - Implemented rule: Flag lot when replacement rate reaches **>= 3x SKU baseline (21.0%)** after **>= 50 orders shipped**.
   - Backtested on `PL2-2510`: Fired early, avoiding **458 excess replacements** and **saving Rs 8.33 to 11.02 Lakh** in replacement costs (matching the PRD target of Rs 8 to 10 Lakh).

4. **Zero-Cost Constraint:**
   - **Rs 0 per run.** Deterministic keyword regex classifier and scikit-learn OLS regression. Zero per-ticket LLM API calls.

---

## 3. Repository Architecture

```text
Vireo Audio Support/
├── README.md               # Setup and execution guide
├── requirements.txt        # Minimal pinned dependencies
├── CLAUDE.md               # Behavioral constraints and data trap guide
├── app.py                  # Interactive Streamlit dashboard
├── run_all.py              # Master sequential pipeline runner
├── docs/                   # Business requirements & technical briefs
│   ├── CLAUDE_CODE_BRIEF.md
│   ├── PRD.md
│   └── TECHSTACK.md
├── data/                   # Raw operational CSVs and business policy
│   ├── agents.csv
│   ├── customers.csv
│   ├── orders.csv
│   ├── products.csv
│   ├── tickets.csv
│   ├── email-thread.txt
│   ├── README.txt
│   └── support-policy.pdf
├── src/                    # Pipeline stages and core analytical modules
│   ├── 01_data_quality.py  # Timezone fix, deduplication, joins audit
│   ├── 02_agent_metrics.py # Raw CSAT, handle time, Tier 1 vs 2 ranking
│   ├── 03_adjusted_csat.py # Case-mix regression and rota fairness
│   ├── 04_lot_analysis.py  # Lot defect rates, costing, double remedies, SLA
│   ├── 05_classifier.py    # Rule-based NLP classifier & bot disagreements
│   ├── 06_validation.py    # Ground-truth sample evaluation & confusion matrix
│   ├── 07_lot_early_warning.py # Early-warning alert rule & backtest
│   ├── load_clean.py       # Data cleaning and joining utilities
│   ├── metrics.py          # Metric calculations & confidence intervals
│   ├── adjust.py           # Case-mix adjustment engine
│   ├── lots.py             # Lot aggregation and policy costing logic
│   ├── classify.py         # Keyword & regex classification engine
│   └── validate.py         # Validation metrics and non-text checks
├── outputs/                # Structured CSV and Markdown analytical artifacts
│   ├── assumptions.md
│   ├── data_quality.md
│   ├── lot_analysis.md
│   ├── lot_early_warning.md
│   ├── agent_metrics.csv
│   ├── agent_metrics_wp3.csv
│   ├── lot_metrics_wp4.csv
│   ├── double_remedy_orders_wp4.csv
│   ├── sla_monthly_trend_wp4.csv
│   ├── bot_category_vs_theme.csv
│   ├── theme_mix_quarterly.csv
│   ├── theme_mix_pl2_lots.csv
│   └── lot_early_warning_backtest.csv
├── validation/             # Model validation ground truth & report
│   ├── labelled_sample.csv
│   └── validation_report.md
└── tests/                  # Automated pytest verification test suite
    ├── test_data_traps.py
    ├── test_metrics_and_lots.py
    └── test_classifier.py
```
