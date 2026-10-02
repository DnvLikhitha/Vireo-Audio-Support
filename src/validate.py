"""
Validation module for Vireo Audio Support Analytics (WP6).
Evaluates rule-based text classifier against human hand-labelled sample,
computes precision, recall, confusion matrix, failure mode analyses,
and compiles non-text data quality verification checks.
"""

import pandas as pd
import numpy as np
import os
import sys
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
try:
    from classify import classify_single_ticket, identify_junk_ivr_mask
    from lots import calculate_lot_metrics, link_tickets_to_orders
except ImportError:
    from .classify import classify_single_ticket, identify_junk_ivr_mask
    from .lots import calculate_lot_metrics, link_tickets_to_orders


def run_non_text_checks(tickets_df, orders_df, agents_df):
    """
    Execute and return all non-text verification checks:
    - Timezone fix (+5h30m legacy resolved_at)
    - Join coverage (agent joins and order joins with fallback)
    - Blank CSAT handling
    - Lot-rate stability across manufacturing cohorts
    """
    # 1. Timezone fix
    legacy = tickets_df[tickets_df['source_system'] == 'legacy_fd'].copy()
    fr_dt = pd.to_datetime(legacy['first_response_at'])
    res_dt = pd.to_datetime(legacy['resolved_at'])
    ht_raw = (res_dt - fr_dt).dt.total_seconds() / 3600.0
    neg_before = int((ht_raw < 0).sum())
    neg_pct_before = neg_before / len(legacy) * 100.0

    from datetime import timedelta
    res_fixed = res_dt + timedelta(hours=5, minutes=30)
    ht_fixed = (res_fixed - fr_dt).dt.total_seconds() / 3600.0
    neg_after = int((ht_fixed < 0).sum())

    tz_checks = {
        'legacy_count': len(legacy),
        'neg_before': neg_before,
        'neg_pct_before': neg_pct_before,
        'neg_after': neg_after
    }

    # 2. Join coverage
    agent_matches = int(tickets_df['agent_id'].isin(agents_df['agent_id']).sum())
    direct_orders = int(tickets_df['order_id'].notna().sum())

    orders_clean = orders_df.copy()
    orders_clean['order_date_dt'] = pd.to_datetime(orders_clean['order_date'])
    tickets_copy = tickets_df.copy()
    tickets_copy['created_at_dt'] = pd.to_datetime(tickets_copy['created_at'])

    missing_t = tickets_copy[tickets_copy['order_id'].isna()]
    fallback_candidates = missing_t.merge(
        orders_clean[['order_id', 'customer_id', 'sku', 'order_date_dt']],
        left_on=['customer_id', 'product_sku'],
        right_on=['customer_id', 'sku'],
        how='left'
    )
    valid_candidates = fallback_candidates[
        fallback_candidates['order_date_dt'] <= fallback_candidates['created_at_dt']
    ]
    counts_per_t = valid_candidates.groupby('ticket_id')['order_id_y'].count()
    single_fb = int((counts_per_t == 1).sum())
    ambig_fb = int((counts_per_t > 1).sum())
    zero_fb = int(len(missing_t) - len(counts_per_t))
    total_usable = direct_orders + single_fb

    join_checks = {
        'total_tickets': len(tickets_df),
        'agent_matches': agent_matches,
        'agent_pct': agent_matches / len(tickets_df) * 100.0,
        'direct_orders': direct_orders,
        'direct_pct': direct_orders / len(tickets_df) * 100.0,
        'single_fb': single_fb,
        'single_fb_pct': single_fb / len(tickets_df) * 100.0,
        'ambig_fb': ambig_fb,
        'ambig_fb_pct': ambig_fb / len(tickets_df) * 100.0,
        'zero_fb': zero_fb,
        'zero_fb_pct': zero_fb / len(tickets_df) * 100.0,
        'total_usable': total_usable,
        'total_usable_pct': total_usable / len(tickets_df) * 100.0
    }

    # 3. Blank CSAT handling
    blank_csat = int(tickets_df['csat_score'].isna().sum())
    rated_csat = int(tickets_df['csat_score'].notna().sum())
    mean_csat_rated = float(tickets_df['csat_score'].mean())
    distorted_mean = float(tickets_df['csat_score'].fillna(0).mean())

    csat_checks = {
        'blank_count': blank_csat,
        'blank_pct': blank_csat / len(tickets_df) * 100.0,
        'rated_count': rated_csat,
        'rated_pct': rated_csat / len(tickets_df) * 100.0,
        'mean_rated': mean_csat_rated,
        'distorted_mean': distorted_mean
    }

    # 4. Lot-rate stability
    linked_t, _ = link_tickets_to_orders(tickets_df, orders_df)
    _, _, monthly_batches = calculate_lot_metrics(orders_df, linked_t)
    pl2_batches = monthly_batches[monthly_batches['sku'] == 'VA-EB-PL2'].copy()

    pre_defect = pl2_batches[pl2_batches['lot_month'].isin(['PL2-2505', 'PL2-2506', 'PL2-2507', 'PL2-2508', 'PL2-2509'])]
    defect = pl2_batches[pl2_batches['lot_month'].isin(['PL2-2510', 'PL2-2511', 'PL2-2512'])]
    post_defect = pl2_batches[pl2_batches['lot_month'].isin(['PL2-2601', 'PL2-2602', 'PL2-2603', 'PL2-2604', 'PL2-2605'])]

    pre_rate = float(pre_defect['orders_with_replacement'].sum() / pre_defect['orders_count'].sum() * 100.0)
    defect_rate = float(defect['orders_with_replacement'].sum() / defect['orders_count'].sum() * 100.0)
    post_rate = float(post_defect['orders_with_replacement'].sum() / post_defect['orders_count'].sum() * 100.0)

    lot_checks = {
        'pre_rate': pre_rate,
        'pre_orders': int(pre_defect['orders_count'].sum()),
        'pre_replacements': int(pre_defect['orders_with_replacement'].sum()),
        'defect_rate': defect_rate,
        'defect_orders': int(defect['orders_count'].sum()),
        'defect_replacements': int(defect['orders_with_replacement'].sum()),
        'post_rate': post_rate,
        'post_orders': int(post_defect['orders_count'].sum()),
        'post_replacements': int(post_defect['orders_with_replacement'].sum())
    }

    return {
        'timezone': tz_checks,
        'joins': join_checks,
        'csat': csat_checks,
        'lots': lot_checks
    }


def evaluate_sample(sample_path='validation/labelled_sample.csv'):
    """
    Evaluate classifier predictions against hand labels in sample_path.
    Returns:
        dict: evaluation metrics or status indicating whether labels exist.
    """
    df = pd.read_csv(sample_path)
    labeled_mask = df['hand_label'].notna() & (df['hand_label'].astype(str).str.strip() != '')

    labeled_count = int(labeled_mask.sum())
    total_count = len(df)

    if labeled_count == 0:
        return {
            'has_labels': False,
            'total_samples': total_count,
            'labeled_samples': 0
        }

    valid_df = df[labeled_mask].copy()

    # Generate model predictions for the sample
    valid_df['pred_theme'] = valid_df.apply(
        lambda r: classify_single_ticket(r['customer_message'], r['agent_notes'], r['product_sku']),
        axis=1
    )
    valid_df['hand_label_clean'] = valid_df['hand_label'].astype(str).str.strip().str.lower()

    y_true = valid_df['hand_label_clean']
    y_pred = valid_df['pred_theme']

    accuracy = float(accuracy_score(y_true, y_pred))

    # Confusion matrix & classification report
    labels = sorted(list(set(y_true).union(set(y_pred))))
    cm = pd.DataFrame(
        confusion_matrix(y_true, y_pred, labels=labels),
        index=[f'True: {l}' for l in labels],
        columns=[f'Pred: {l}' for l in labels]
    )

    report_dict = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    report_df = pd.DataFrame(report_dict).T

    # Map intake bot category to theme taxonomy for comparison
    bot_category_map = {
        'Delivery & Shipping': 'delivery_tracking',
        'Billing & Payments': 'refund_payment_delay',
        'Returns & Refunds': 'refund_payment_delay',
        'Charging & Battery': 'one_earbud_dead_or_not_charging',
        'Connectivity': 'pairing_connection_drop',
        'Audio Quality': 'audio_quality',
        'App & Firmware': 'app_firmware_account',
        'Account & Login': 'app_firmware_account',
        'Warranty & Repair': 'warranty_rma',
        'Product Enquiry': 'other',
        'Other': 'other'
    }
    valid_df['bot_theme'] = valid_df['category'].map(bot_category_map).fillna('other')
    bot_accuracy = float(accuracy_score(y_true, valid_df['bot_theme']))

    # Identify misclassifications
    misclass = valid_df[y_true != y_pred].copy()

    return {
        'has_labels': True,
        'total_samples': total_count,
        'labeled_samples': labeled_count,
        'accuracy': accuracy,
        'bot_accuracy': bot_accuracy,
        'confusion_matrix': cm,
        'classification_report': report_df,
        'misclassifications': misclass,
        'evaluated_df': valid_df
    }
