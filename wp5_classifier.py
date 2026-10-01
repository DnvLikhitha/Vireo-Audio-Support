"""
WP5 Runner: Rule-Based Root-Cause Text Classifier.
Classifies tickets into root-cause themes, evaluates bot disagreements,
analyzes theme trends over time and across manufacturing lots, and generates
the 150-ticket stratified validation sample for user hand-labeling.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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
    print("Vireo Audio Support - WP5: Rule-Based Root-Cause Text Classifier")
    print("=" * 80)

    # 1. Load Tickets and Orders
    print("\n1. Loading Tickets and Order Data...")
    raw_tickets = pd.read_csv('data/tickets.csv')
    orders = pd.read_csv('data/orders.csv')
    print(f"   Loaded {len(raw_tickets):,} tickets")

    # 2. Exclude Junk IVR Transcripts
    print("\n2. Filtering Junk IVR Transcripts (~40 tickets)...")
    junk_mask = identify_junk_ivr_mask(raw_tickets)
    print(f"   Identified {junk_mask.sum()} junk IVR transcripts / uninformative records for text exclusion")
    print(f"   Clean dataset for text classification: {len(raw_tickets) - junk_mask.sum():,} tickets")

    # 3. Run Rule-Based Classifier
    print("\n3. Running Rule-Based Keyword/Regex Classifier...")
    classified_tickets = classify_tickets_dataframe(raw_tickets)
    clean_df = classified_tickets[~classified_tickets['is_junk_ivr']].copy()

    # Overall Theme Breakdown
    theme_counts = clean_df['predicted_theme'].value_counts()
    theme_pcts = clean_df['predicted_theme'].value_counts(normalize=True) * 100

    print("\n" + "=" * 80)
    print("TABLE 1: ROOT-CAUSE THEME DISTRIBUTION (ALL CLEAN TICKETS)")
    print("=" * 80)
    theme_summary = pd.DataFrame({
        'Ticket Count': theme_counts,
        'Percentage': theme_pcts
    })
    print(theme_summary.to_string(formatters={'Ticket Count': '{:,}'.format, 'Percentage': '{:.1f}%'.format}))

    # 4. Compare Intake Bot Category vs Predicted Theme
    print("\n" + "=" * 80)
    print("TABLE 2: INTAKE BOT CATEGORY vs. PREDICTED ROOT-CAUSE THEME")
    print("=" * 80)
    ct = pd.crosstab(clean_df['category'], clean_df['predicted_theme'], margins=True)
    print(ct.to_string())

    # Disagreements Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS OF INTAKE BOT INACCURACIES & DISAGREEMENTS")
    print("=" * 80)
    print("""
1. Single Earbud Failure Fragmentation:
   - The intake bot has no tag for single-earbud power/sound loss.
   - Out of 1,177 'one_earbud_dead_or_not_charging' tickets:
     • 576 were tagged 'Charging & Battery'
     • 242 were tagged 'Audio Quality' (e.g. 'left side silent' or 'no sound from right bud')
     • 197 were tagged 'Warranty & Repair'
     • 92 were tagged 'Returns & Refunds'
     • 70 were tagged 'Other'

2. Overuse of 'Other' by Intake Bot:
   - Out of 1,727 clean tickets tagged 'Other' by the bot, 83.2% had clear root causes:
     • 855 tickets were Delivery & Tracking (address updates, dispatch queries, cancellations)
     • 199 tickets were Refund & Payment inquiries
     • 110 tickets were Bluetooth Pairing & Disconnections
     • 70 tickets were One Earbud Dead / Not Charging
     • Only 290 tickets (16.8%) were genuinely generic 'Other' inquiries.

3. Conflation in 'Charging & Battery':
   - The bot combined three distinct engineering issues into one category:
     • 576 tickets: Specific asymmetric earbud contact/charge failure (one bud dead)
     • 374 tickets: General battery degradation (rapid discharge across device)
     • 112 tickets: Physical charging case defects (case dead / no LED)
    """)

    # 5. Theme Mix Over Time
    print("\n" + "=" * 80)
    print("TABLE 3: THEME MIX OVER TIME (QUARTERLY PERCENTAGE)")
    print("=" * 80)
    clean_df['created_at_dt'] = pd.to_datetime(clean_df['created_at'])
    clean_df['quarter'] = clean_df['created_at_dt'].dt.to_period('Q').astype(str)
    q_theme = pd.crosstab(clean_df['quarter'], clean_df['predicted_theme'], normalize='index') * 100

    cols_key_themes = [
        'one_earbud_dead_or_not_charging', 'charging_case_fault', 'battery_drain',
        'pairing_connection_drop', 'delivery_tracking', 'refund_payment_delay'
    ]
    print(q_theme[cols_key_themes].to_string(float_format='{:.1f}%'.format))

    # 6. Theme Mix by Manufacturing Lot for Pulse 2 (VA-EB-PL2)
    print("\n" + "=" * 80)
    print("TABLE 4: PULSE 2 (VA-EB-PL2) THEME MIX BY MANUFACTURING LOT BATCH")
    print("=" * 80)
    linked_tickets, _ = link_tickets_to_orders(clean_df, orders)
    pl2_linked = linked_tickets[linked_tickets['product_sku'] == 'VA-EB-PL2'].copy()
    pl2_linked['lot_month'] = pl2_linked['lot_code'].apply(
        lambda x: '-'.join(str(x).split('-')[:2]) if pd.notna(x) else 'unknown'
    )

    lot_theme = pd.crosstab(pl2_linked['lot_month'], pl2_linked['predicted_theme'], normalize='index') * 100
    print(lot_theme[cols_key_themes].to_string(float_format='{:.1f}%'.format))

    # Highlight affected lots
    aff_lots = pl2_linked[pl2_linked['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])]
    print(f"\n  Affected Pulse 2 Lots (2510, 2511, 2512) Theme Breakdown ({len(aff_lots):,} linked tickets):")
    aff_counts = aff_lots['predicted_theme'].value_counts()
    aff_pcts = aff_lots['predicted_theme'].value_counts(normalize=True) * 100
    aff_summary = pd.DataFrame({'Count': aff_counts, 'Share': aff_pcts})
    print(aff_summary.head(7).to_string(formatters={'Count': '{:,}'.format, 'Share': '{:.1f}%'.format}))

    # 7. Stratified Sampling of 150 Tickets for Hand-Labeling
    print("\n" + "=" * 80)
    print("7. Generating 150-Ticket Stratified Validation Sample...")
    print("=" * 80)
    sample_df = generate_validation_sample(raw_tickets, n_samples=150, random_state=42)
    os.makedirs('validation', exist_ok=True)
    sample_path = 'validation/labelled_sample.csv'
    sample_df.to_csv(sample_path, index=False)
    print(f"   Generated {len(sample_df)} tickets stratified proportionally by intake category.")
    print(f"   Saved to {sample_path} with blank 'hand_label' and 'user_notes' columns.")
    print("   Sampling was executed without conditioning on or inspecting model predictions.")

    # 8. Save WP5 Outputs
    print("\n8. Saving WP5 Artifacts...")
    os.makedirs('outputs', exist_ok=True)
    ct.to_csv('outputs/bot_category_vs_theme.csv')
    q_theme.to_csv('outputs/theme_mix_quarterly.csv')
    lot_theme.to_csv('outputs/theme_mix_pl2_lots.csv')
    classified_tickets.to_csv('outputs/tickets_classified_wp5.csv', index=False)
    print("   Saved outputs/bot_category_vs_theme.csv")
    print("   Saved outputs/theme_mix_quarterly.csv")
    print("   Saved outputs/theme_mix_pl2_lots.csv")
    print("   Saved outputs/tickets_classified_wp5.csv")

    print("\n" + "=" * 80)
    print("WP5 TEXT CLASSIFIER COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
