"""
Rule-Based Text Classifier for Root-Cause Analysis (WP5).
Implements:
- Filtering of junk IVR transcripts (~37 tickets) from text analysis
- Keyword and regular-expression pattern matching on customer_message and agent_notes
- Themes:
  1. one_earbud_dead_or_not_charging
  2. charging_case_fault
  3. battery_drain
  4. pairing_connection_drop
  5. audio_quality (added: distinct sound defect vs hardware power loss)
  6. delivery_tracking
  7. refund_payment_delay
  8. warranty_rma
  9. app_firmware_account (added: software/login failure modes)
  10. other (pre-sales, cancellations, general)
- Comparison against intake-bot categories
- Theme mix analysis over time and by PL2 lot
- Stratified sampling of 150 tickets for hand-label validation
"""

import pandas as pd
import numpy as np
import re


def identify_junk_ivr_mask(tickets_df):
    """
    Identify junk IVR transcripts and uninformative messages to exclude from text classification.
    Catches bracketed audio dropouts ([inaudible], [crosstalk], [line dropped]),
    punctuation-only noise ('.', '-', '??', '...'), or blank voice calls.
    """
    msg = tickets_df['customer_message'].fillna('').astype(str).str.strip()
    channel = tickets_df['channel'].fillna('').astype(str)

    bracket_pattern = r'\[inaudible\]|\[crosstalk\]|\[line dropped\]'
    has_bracket_artifact = msg.str.contains(bracket_pattern, regex=True, case=False)
    is_punctuation_noise = msg.isin(['.', '-', '??', '...', 'test', 'call me', 'urgent'])
    is_empty_voice = (channel == 'voice') & (msg.str.len() <= 15)

    junk_mask = has_bracket_artifact | is_punctuation_noise | is_empty_voice
    return junk_mask


def classify_single_ticket(customer_message, agent_notes, product_sku=''):
    """
    Classify a single ticket using keyword and regex rules on customer_message and agent_notes.
    Priority order is structured from highly specific hardware defects to broad operational themes.
    """
    cust = str(customer_message).lower() if pd.notna(customer_message) else ''
    notes = str(agent_notes).lower() if pd.notna(agent_notes) else ''
    combined = cust + ' ' + notes

    # 1. One earbud dead or not charging
    # Look for asymmetric earbud failure patterns (left/right/single bud)
    if re.search(r'\b(left|right|one)\s+(earbud|bud|side)\b|single\s+side|one\s+side\s+(silent|dead|not\s+working)|paperweight|decorat|balance\s+setting', combined):
        if re.search(r'not\s+charging|won\'t\s+charge|no\s+charge|dead|silent|no\s+audio|0%|zero\s+percent|not\s+taking\s+charge|doesn\'t\s+charge', combined):
            return 'one_earbud_dead_or_not_charging'
        if re.search(r'silent|dead|no\s+audio|paperweight|decorat|left\s+sie\s+has\s+no\s+audio', combined):
            return 'one_earbud_dead_or_not_charging'

    # Direct mention of earbud not charging when earbud context is present
    if re.search(r'(bud|earbud)\s+(not\s+taking\s+charge|not\s+charging|won\'t\s+charge|shows\s+0%|dead)', combined):
        return 'one_earbud_dead_or_not_charging'

    # 2. Charging case fault
    # Specific fault in the charging case itself (case LED dead, case not charging, no power from case)
    if re.search(r'\bcase\b', combined):
        if re.search(r'case\s+(is\s+)?(dead|not\s+charging|no\s+led|won\'t\s+charge)|charging\s+case|case\s+fault|spare\s+case|case\s+led\s+dead|case\s+no\s+led', combined):
            return 'charging_case_fault'

    # 3. Battery drain / rapid discharge
    # General battery deterioration (affects both buds, smartwatch, speaker, or headphones)
    if re.search(r'battery\s+(drain|life|backup|draining|drops|dropped)|poor\s+battery|draining\s+(fast|even)|backup\s+issue|discharg|promised\s+\d+\s+hours\s+is\s+nowhere', combined):
        return 'battery_drain'

    # General charging pin / charging issue on earbuds
    if re.search(r'charging\s+pins|not\s+taking\s+charge|won\'t\s+charge|not\s+charging', combined) and ('bud' in combined or 'earbud' in combined or 'pulse' in combined or 'airlite' in combined):
        return 'one_earbud_dead_or_not_charging'

    # 4. Audio quality / distortion / microphone
    # Audio flaws like static, buzzing, crackling, mic failure, single-side sound imbalance
    if re.search(r'static\s+(noise|nosie)|crackling|distortion|buzzing|mic\s+(not\s+working|issue|permissions)|audio\s+distortion|eq\s+reset|sound\s+quality|only\s+one\s+direction', combined):
        return 'audio_quality'

    # 5. Pairing / connection drop
    # Bluetooth handshake, discoverability, cutting out, dropped connection
    if re.search(r'pair(ing)?\b|bluetooth|bt\s+(drop|dropout|dropouts)|disconnect|cutting\s+out|not\s+discoverable|forget\s+\+\s+re-pair|unable\s+to\s+pair|re-pair\s+successful', combined):
        return 'pairing_connection_drop'

    # 6. Delivery & tracking
    # Logistics, shipping delays, address corrections, damaged in transit, courier AWB
    if re.search(r'track(ing)?|deliver(y|ed)?|courier|awb|shipment|dispatch|pincode|address\s+update|lost\s+in\s+transit|rto|wrong\s+(product|item|variant)|transit\s+damage|damaged\s+in\s+transit|haven\'t\s+received\s+my\s+order|nothing\s+in\s+hand', combined):
        return 'delivery_tracking'

    # 7. Refund / payment delay
    # Financial delays, double payments, payment gateway deductions, price matching
    if re.search(r'refund|double\s+payment|debited|money\s+deducted|payment\s+failed|utr|arn|charge(d)?\s+two\s+times|price\s+adj|coupon|promo\s+code|refund\s+pending|refund\s+delay', combined):
        return 'refund_payment_delay'

    # 8. Warranty / RMA / Repair status
    # Formal RMA processing, repair escalation, warranty inspection
    if re.search(r'warranty|rma|repair|inspection|wty|repair\s+status|claim\s+pending|service\s+center', combined):
        return 'warranty_rma'

    # 9. App, Firmware, and Account/Login
    # Software crashes, firmware upgrade freezes, OTP authentication failures
    if re.search(r'otp|login|account\s+unlock|password|app\s+crash|app\s+not\s+opening|firmware\s+update|stuck\s+at\s+\d+%', combined):
        return 'app_firmware_account'

    return 'other'


def classify_tickets_dataframe(tickets_df):
    """
    Apply rule-based classification to a DataFrame of tickets, excluding junk IVR tickets.
    Returns:
        DataFrame: tickets with 'predicted_theme' and 'is_junk_ivr'
    """
    df = tickets_df.copy()
    junk_mask = identify_junk_ivr_mask(df)
    df['is_junk_ivr'] = junk_mask

    # Predict themes for non-junk tickets
    clean_indices = df[~junk_mask].index
    themes = [
        classify_single_ticket(df.loc[idx, 'customer_message'], df.loc[idx, 'agent_notes'], df.loc[idx, 'product_sku'])
        for idx in clean_indices
    ]

    df['predicted_theme'] = 'junk_ivr'
    df.loc[clean_indices, 'predicted_theme'] = themes
    return df


def generate_validation_sample(tickets_df, n_samples=150, random_state=42):
    """
    Generate a stratified random sample of tickets for human hand-labeling.
    Stratified solely on intake category without looking at model predictions.
    Leaves hand_label and user_notes completely blank for the user.
    """
    cat_counts = tickets_df['category'].value_counts()
    proportions = cat_counts / len(tickets_df)
    sample_sizes = (proportions * n_samples).round().astype(int)
    # Ensure minimum 6 samples per category for balanced representation
    sample_sizes = sample_sizes.clip(lower=6)
    diff = n_samples - sample_sizes.sum()
    if diff != 0:
        for cat in sample_sizes.nlargest(abs(diff)).index:
            sample_sizes[cat] += int(np.sign(diff))

    sampled_batches = []
    for cat, size in sample_sizes.items():
        cat_df = tickets_df[tickets_df['category'] == cat]
        batch = cat_df.sample(n=size, random_state=random_state)
        sampled_batches.append(batch)

    sample = pd.concat(sampled_batches).sample(frac=1, random_state=random_state).reset_index(drop=True)

    output_cols = [
        'ticket_id', 'created_at', 'channel', 'product_sku', 'category',
        'customer_message', 'agent_notes', 'hand_label', 'user_notes'
    ]
    sample['hand_label'] = ''
    sample['user_notes'] = ''
    return sample[output_cols]
