"""
Streamlit Dashboard: Vireo Audio Support Intelligence System.
Delivers:
- Executive Overview & Key Findings
- Agent Performance & Fairness (Raw vs Mix-Adjusted CSAT, Tier 1 vs Tier 2)
- Manufacturing Lot Defect Analysis & Policy Costing
- Root-Cause Text Classification & Validation Benchmark
- Lot Early-Warning Rule & Financial Savings Simulator
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# Ensure src modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

st.set_page_config(
    page_title="Vireo Audio Support Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #64748B; margin-bottom: 1.5rem; }
    .metric-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
    .metric-val { font-size: 1.8rem; font-weight: 700; color: #0F172A; }
    .metric-lbl { font-size: 0.85rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; }
    .highlight-red { color: #DC2626; font-weight: 600; }
    .highlight-green { color: #16A34A; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all_artifacts():
    data = {}
    if os.path.exists('outputs/agent_metrics.csv'):
        data['agent_metrics'] = pd.read_csv('outputs/agent_metrics.csv')
    if os.path.exists('outputs/agent_metrics_wp3.csv'):
        data['agent_metrics_wp3'] = pd.read_csv('outputs/agent_metrics_wp3.csv')
    if os.path.exists('outputs/lot_metrics_wp4.csv'):
        data['lot_metrics'] = pd.read_csv('outputs/lot_metrics_wp4.csv')
    if os.path.exists('outputs/double_remedy_orders_wp4.csv'):
        data['double_remedies'] = pd.read_csv('outputs/double_remedy_orders_wp4.csv')
    if os.path.exists('outputs/sla_monthly_trend_wp4.csv'):
        data['sla_trend'] = pd.read_csv('outputs/sla_monthly_trend_wp4.csv')
    if os.path.exists('outputs/bot_category_vs_theme.csv'):
        data['bot_cross'] = pd.read_csv('outputs/bot_category_vs_theme.csv', index_col=0)
    if os.path.exists('outputs/theme_mix_quarterly.csv'):
        data['theme_quarterly'] = pd.read_csv('outputs/theme_mix_quarterly.csv', index_col=0)
    if os.path.exists('outputs/theme_mix_pl2_lots.csv'):
        data['theme_lots'] = pd.read_csv('outputs/theme_mix_pl2_lots.csv', index_col=0)
    if os.path.exists('outputs/lot_early_warning_backtest.csv'):
        data['early_warning_sim'] = pd.read_csv('outputs/lot_early_warning_backtest.csv')
    if os.path.exists('validation/labelled_sample.csv'):
        data['val_sample'] = pd.read_csv('validation/labelled_sample.csv')
    return data

artifacts = load_all_artifacts()

# Sidebar Navigation
st.sidebar.title("🎧 Vireo Audio CX")
st.sidebar.markdown("**Decision Support System**")
st.sidebar.markdown("*Audit & Root-Cause Toolkit*")

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "Executive Summary",
        "Agent CSAT & Fairness (WP2/3)",
        "Lot Analysis & Costing (WP4)",
        "Text Classifier & Validation (WP5/6)",
        "Early-Warning Backtest (WP7)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Client: Priya Raman (Head of CX)\nRuntime Cost: Rs 0\nVersion: 1.0.0")

# 1. Executive Summary
if nav_choice == "Executive Summary":
    st.markdown('<div class="main-header">Executive Summary & Operational Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Addressing the Festive Season CSAT Slide & Bonus Allocation</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""<div class="metric-card"><div class="metric-lbl">True CSAT Driver</div><div class="metric-val" style="color: #DC2626;">Pulse 2 Lots</div>Lot 2510-2512 Defect</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="metric-card"><div class="metric-lbl">Excess Replacements</div><div class="metric-val">~726 units</div>Rs 13.22 Lakh excess</div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="metric-card"><div class="metric-lbl">Avoidable Cost</div><div class="metric-val" style="color: #16A34A;">Rs 8.3 - 11 Lakh</div>Saved via Early Warning</div>""", unsafe_allow_html=True)
    with col4:
        st.markdown("""<div class="metric-card"><div class="metric-lbl">Bottom-10 Agents</div><div class="metric-val">100% Rota</div>Hardware Triage Queue</div>""", unsafe_allow_html=True)

    st.markdown("### Key Audit Conclusions")
    st.info("""
    1. **CSAT Decline is a Product Fault, Not an Agent Deficit:** Customer satisfaction dropped because Pulse 2 earbuds suffered an asymmetric dead-earbud failure (lots 2510, 2511, 2512 reached 41% replacement rate vs 7% baseline).
    2. **Priya's Bottom 10 is Unfair:** All 10 lowest agents on the raw dashboard were assigned to the hardware triage rota (handling 47–53% defective Pulse 2 inquiries). Ranking Tier 2 (measured in days) against Tier 1 violates policy.
    3. **Finance Overstatement:** Finance Controller Arjun Mehta estimated Rs 2,500/replacement (Rs 18.16L). Operating Policy §5 standard is Rs 1,480 + Rs 340 = Rs 1,820/replacement (Rs 13.22L), an overstatement of Rs 4.94L.
    4. **Early-Warning Solution:** Implementing a 3x baseline replacement alert rule detects bad lots early, preventing Rs 8.3 to 11.0 Lakh in replacement waste.
    """)

# 2. Agent CSAT & Fairness
elif nav_choice == "Agent CSAT & Fairness (WP2/3)":
    st.markdown('<div class="main-header">Agent Performance & Fairness Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating CSAT, Handle Time, and Case-Mix Adjustments (WP2 & WP3)</div>', unsafe_allow_html=True)

    tier_tab = st.radio("Select View:", ["Tier 1 (Frontline Front Desk)", "Tier 2 (Escalations & Warranty)", "Case-Mix Adjustment Proof"], horizontal=True)

    if 'agent_metrics_wp3' in artifacts:
        df_agents = artifacts['agent_metrics_wp3']

        if tier_tab == "Tier 1 (Frontline Front Desk)":
            st.markdown("#### Tier 1 Agents: CSAT vs Handle Time")
            t1 = df_agents[df_agents['tier'] == 1].sort_values('csat_mean_actual')
            st.dataframe(
                t1[['agent_id', 'agent_name', 'team', 'shift', 'csat_mean_actual', 'csat_mean_adjusted', 'csat_count_actual', 'median_handle_time_hours', 'pl2_ticket_pct', 'is_hardware_triage_rota']],
                column_config={
                    "csat_mean_actual": st.column_config.NumberColumn("Raw CSAT", format="%.2f"),
                    "csat_mean_adjusted": st.column_config.NumberColumn("Mix-Adjusted", format="%+.2f"),
                    "median_handle_time_hours": st.column_config.NumberColumn("Median HT (hrs)", format="%.2f"),
                    "pl2_ticket_pct": st.column_config.NumberColumn("Pulse 2 Share", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )
            st.warning("⚠️ **Notice on Kavya's Four (A3004, A3005, A3006, A3007):** All 4 agents have overlapping 95% confidence intervals (std err ~0.11). Distinguishing performance among them is statistically invalid.")

        elif tier_tab == "Tier 2 (Escalations & Warranty)":
            st.markdown("#### Tier 2 Agents: Escalations & Warranty Rota (Never Ranked Against Tier 1)")
            t2 = df_agents[df_agents['tier'] == 2].sort_values('csat_mean_actual')
            st.dataframe(
                t2[['agent_id', 'agent_name', 'team', 'csat_mean_actual', 'csat_mean_expected', 'csat_mean_adjusted', 'csat_count_actual', 'median_handle_time_days', 'pl2_ticket_pct']],
                column_config={
                    "csat_mean_actual": st.column_config.NumberColumn("Raw CSAT", format="%.2f"),
                    "csat_mean_expected": st.column_config.NumberColumn("Expected CSAT", format="%.2f"),
                    "csat_mean_adjusted": st.column_config.NumberColumn("Mix-Adjusted", format="%+.2f"),
                    "median_handle_time_days": st.column_config.NumberColumn("Median HT (Days)", format="%.1f"),
                    "pl2_ticket_pct": st.column_config.NumberColumn("Pulse 2 Share", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )
            st.info("Policy §6 mandates that Tier 2 handle time is measured in days and must never be evaluated against Tier 1 hourly benchmarks.")

        else:
            st.markdown("#### Case-Mix CSAT Regression Finding")
            st.markdown("""
            - **Expected CSAT Formula:** Evaluates ticket category, channel, priority, Pulse 2 product flag, and timeframe.
            - **Finding:** The adjusted bottom 10 overall contains the **exact same 10 agents** as the raw bottom 10.
            - **Root Cause:** All 10 agents belong to the Hardware Triage Rota. Case-mix adjustment lowers expectations for difficult queues (expected CSAT ~2.85 for Tier 2 vs ~3.55 for frontline), but cannot separate team effects from individual skill due to queue collinearity.
            """)

# 3. Lot Analysis & Costing
elif nav_choice == "Lot Analysis & Costing (WP4)":
    st.markdown('<div class="main-header">Manufacturing Lot Defect & Financial Impact</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Pulse 2 Cohort Surge, Replacement Costing, and SLA Audits (WP4)</div>', unsafe_allow_html=True)

    if 'lot_metrics' in artifacts:
        lots = artifacts['lot_metrics']
        pl2_lots = lots[lots['sku'] == 'VA-EB-PL2'].sort_values('lot_month')

        st.markdown("#### Pulse 2 Replacement Rate by Manufacturing Cohort")
        st.bar_chart(data=pl2_lots.set_index('lot_month')['replacement_rate_pct'])

        st.markdown("#### Defective Cohort Costing Comparison")
        c1, c2, c3 = st.columns(3)
        c1.metric("Policy §5 Cost (Rs 1,820/unit)", "Rs 13.22 Lakh", "726 Excess Units")
        c2.metric("Finance Estimate (Rs 2,500/unit)", "Rs 18.16 Lakh", "+Rs 4.94L Overstatement", delta_color="inverse")
        c3.metric("Normal Baseline Replacement Rate", "7.00%", "Defective Lots: 41.03%")

        st.markdown("#### Double-Remedy Audit (131 Orders)")
        st.markdown("- **88 Legitimate Operations (Rs 2.21 Lakh):** Returns passed QC (`RETURN-QC-OK`: 55) or billing duplicate payments resolved (`DUP-PAYMENT`: 35).\n- **22 Policy Violations (Rs 62,551):** Customer received both refund and replacement on Dead-on-Arrival or lost transit claims.\n- **21 Cancellations / Goodwill (Rs 71,912).**")

# 4. Text Classifier & Validation
elif nav_choice == "Text Classifier & Validation (WP5/6)":
    st.markdown('<div class="main-header">Root-Cause NLP Classification & Validation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Keyword Regex Engine vs. Intake Bot & Ground-Truth Hand Labels (WP5 & WP6)</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Classifier Accuracy", "86.67%", "+32.67% over Bot", delta_color="normal")
    c2.metric("Intake Bot Accuracy", "54.00%", "Low Granularity")
    c3.metric("Execution Cost", "Rs 0", "Zero LLM API calls")

    if 'bot_cross' in artifacts:
        st.markdown("#### Intake Bot Category vs. Classifier Root-Cause Disagreements")
        st.dataframe(artifacts['bot_cross'], use_container_width=True)

    st.markdown("#### Validation Core Finding")
    st.info('*"The classifier is wrong about 13.3% of the time, mainly on `one_earbud_dead_or_not_charging` being classified as `other` due to colloquial phrasing (e.g. left pod stays flat, never gets green light)."*')

# 5. Early-Warning Backtest
elif nav_choice == "Early-Warning Backtest (WP7)":
    st.markdown('<div class="main-header">Manufacturing Lot Early-Warning System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automated Production Alert Backtest & Avoidable Replacement Cost (WP7)</div>', unsafe_allow_html=True)

    st.markdown("### Early-Warning Rule Parameterization")
    col1, col2, col3 = st.columns(3)
    col1.metric("Alert Condition", ">= 21.0% Rate", "3x SKU Baseline (7.0%)")
    col2.metric("Volume Gate", ">= 50 Orders", "Prevents Small-Sample Noise")
    col3.metric("Policy Costing Standard", "Rs 1,820", "Unit Rs 1,480 + Logistics Rs 340")

    st.markdown("### Backtest Results on Defective Lot PL2-2510")
    st.success("""
    - **Launch Date:** October 23, 2025
    - **Cohort Signal Date:** November 08, 2025 (51 orders shipped, 49.0% defect incidence — triggered within **16 days** of launch)
    - **Operational Support Alert Date:** January 17, 2026 (Ticket return stream crossed 21.04% vs 20.89% threshold)
    - **Avoidable Excess Replacements:** **458 units**
    - **Avoidable Excess Cost Saved:** **Rs 8.33 Lakh to Rs 11.02 Lakh**
    """)

    if 'early_warning_sim' in artifacts:
        sim = artifacts['early_warning_sim']
        st.markdown("#### Daily Cumulative Replacement Rate Progression (PL2-2510)")
        st.line_chart(data=sim.set_index('date')['cumulative_rate'])
