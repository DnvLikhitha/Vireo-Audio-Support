"""
Pipeline Step 05: Rule-Based Root-Cause Text Classifier (WP5).
Classifies tickets into root-cause themes, evaluates bot disagreements,
analyzes theme trends over time and across manufacturing lots, and generates
the 150-ticket stratified validation sample (preserving labels if already present).
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pandas as pd
import numpy as np
from classify import (
    identify_junk_ivr_mask,
    classify_tickets_dataframe,
    generate_validation_sample
)
from lots import link_tickets_to_orders


def main():
    print("=" * 80)
    print("Vireo Audio Support - Step 05: Rule-Based Root-Cause Text Classifier")
    print("=" * 80)

    # 1. Load Tickets and Orders
    print("\n1. Loading Tickets and Order Data...")
    raw_tickets = pd.read_csv('data/tickets.csv')
    orders = pd.read_csv('data/orders.csv')

    # 2. Filter Junk IVR Transcripts
    print("\n2. Identifying and Excluding Corrupted Voice IVR Transcripts...")
    junk_mask = identify_junk_ivr_mask(raw_tickets)
    junk_count = int(junk_mask.sum())
    clean_count = len(raw_tickets) - junk_count
    print(f"   Total tickets: {len(raw_tickets):,}")
    print(f"   Corrupted IVR / punctuation-only noise tickets excluded from text analysis: {junk_count} (matches brief: ~40)")
    print(f"   Tickets retained for NLP root-cause classification: {clean_count:,}")

    # 3. Classify Tickets into Themes
    print("\n3. Classifying Clean Tickets into Root-Cause Themes...")
    classified_tickets = classify_tickets_dataframe(raw_tickets)

    theme_counts = classified_tickets[~classified_tickets['is_junk_ivr']]['predicted_theme'].value_counts()
    theme_pcts = theme_counts / clean_count * 100.0
    theme_summary = pd.DataFrame({
        'Tickets': theme_counts,
        'Share (%)': theme_pcts
    })
    print("\n" + "=" * 80)
    print("TABLE 1: ROOT-CAUSE THEME DISTRIBUTION (COMPANY-WIDE)")
    print("=" * 80)
    print(theme_summary.to_string(formatters={'Tickets': '{:,}'.format, 'Share (%)': '{:.2f}%'.format}))

    # 4. Compare with Intake Bot Category
    print("\n" + "=" * 80)
    print("TABLE 2: INTAKE BOT CATEGORY vs CLASSIFIER THEME DISAGREEMENT MATRIX")
    print("=" * 80)
    clean_df = classified_tickets[~classified_tickets['is_junk_ivr']]
    ct = pd.crosstab(
        clean_df['category'],
        clean_df['predicted_theme'],
        margins=True,
        margins_name='Total'
    )
    print(ct.to_string())

    # 5. Theme Mix Over Time
    print("\n" + "=" * 80)
    print("TABLE 3: THEME MIX OVER TIME (QUARTERLY EVOLUTION)")
    print("=" * 80)
    clean_df = clean_df.copy()
    clean_df['quarter'] = pd.to_datetime(clean_df['created_at']).dt.to_period('Q').astype(str)
    q_theme = pd.crosstab(
        clean_df['quarter'],
        clean_df['predicted_theme'],
        normalize='index'
    ) * 100.0
    print(q_theme.round(1).to_string())

    # 6. Theme Mix by Lot for Pulse 2 (VA-EB-PL2)
    print("\n" + "=" * 80)
    print("TABLE 4: THEME MIX BY MANUFACTURING BATCH FOR PULSE 2 (VA-EB-PL2)")
    print("=" * 80)
    linked_tickets, _ = link_tickets_to_orders(clean_df, orders)
    pl2_linked = linked_tickets[linked_tickets['product_sku'] == 'VA-EB-PL2'].copy()
    pl2_linked['lot_month'] = pl2_linked['lot_code'].fillna('UNKNOWN').str.extract(r'^(PL2-\d{4})')[0].fillna('UNKNOWN')

    lot_theme = pd.crosstab(
        pl2_linked['lot_month'],
        pl2_linked['predicted_theme'],
        normalize='index'
    ) * 100.0
    print(lot_theme.round(1).to_string())

    # 7. Stratified Sample Preservation
    print("\n" + "=" * 80)
    print("7. Checking 150-Ticket Stratified Validation Sample...")
    print("=" * 80)
    os.makedirs('validation', exist_ok=True)
    sample_path = 'validation/labelled_sample.csv'
    if not os.path.exists(sample_path):
        sample_df = generate_validation_sample(raw_tickets, n_samples=150, random_state=42)
        sample_df.to_csv(sample_path, index=False)
        print(f"   Generated {len(sample_df)} tickets stratified proportionally by intake category.")
    else:
        print(f"   Preserving existing validation sample with hand-labels at {sample_path}.")

    # 8. Save Outputs
    print("\n8. Saving Step 05 Artifacts...")
    os.makedirs('outputs', exist_ok=True)
    ct.to_csv('outputs/bot_category_vs_theme.csv')
    q_theme.to_csv('outputs/theme_mix_quarterly.csv')
    lot_theme.to_csv('outputs/theme_mix_pl2_lots.csv')
    classified_tickets.to_csv('outputs/tickets_classified_wp5.csv', index=False)
    print("   Saved classifier outputs to outputs/")
    print("=" * 80)


if __name__ == '__main__':
    main()
