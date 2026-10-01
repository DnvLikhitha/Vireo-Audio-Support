import pandas as pd
import numpy as np
import re

tickets = pd.read_csv('data/tickets.csv')

# Exclude junk IVR transcripts (~40 tickets) from text analysis
# Junk IVR criteria:
# Voice tickets with audio bracket artifacts or uninformative/blank messages:
junk_mask = (
    tickets['customer_message'].str.contains(r'\[inaudible\]|\[crosstalk\]|\[line dropped\]', regex=True, case=False) |
    (tickets['customer_message'].str.strip().isin(['.', '-', '??', '...', 'test', 'call me', 'urgent'])) |
    ((tickets['channel'] == 'voice') & (tickets['customer_message'].str.strip().str.len() <= 15))
)
print(f'Junk IVR / uninformative tickets to exclude: {junk_mask.sum()}')

clean_tickets = tickets[~junk_mask].copy()
print(f'Clean tickets for text classification: {len(clean_tickets)}')

# Let's inspect themes and keywords on combined text (customer_message + ' ' + agent_notes)
clean_tickets['combined_text'] = (
    clean_tickets['customer_message'].fillna('') + ' ' + clean_tickets['agent_notes'].fillna('')
).str.lower()

# Define keywords for each theme
# Notice priority order: more specific hardware issues first!

def classify_ticket(text, sku=''):
    # 1. One earbud dead or not charging
    # Keywords: left earbud, right earbud, left bud, right bud, one bud, one earbud, single side, one side silent, one side dead, paperweight
    if re.search(r'\b(left|right|one)\s+(earbud|bud|side)\b|single\s+side|one\s+side\s+(silent|dead|not\s+working)|paperweight|balance\s+setting', text):
        if re.search(r'not\s+charging|won\'t\s+charge|no\s+charge|dead|silent|no\s+audio|0%|zero\s+percent|not\s+taking\s+charge', text):
            return 'one_earbud_dead_or_not_charging'
        # If it specifically mentions one side silent/dead/no audio
        if re.search(r'silent|dead|no\s+audio|paperweight|decorat', text):
            return 'one_earbud_dead_or_not_charging'

    # 2. Charging case fault
    # Keywords: charging case, case dead, case led, case not charging, case no led
    if re.search(r'\bcase\b', text) and re.search(r'case\s+(is\s+)?(dead|not\s+charging|no\s+led|won\'t\s+charge)|charging\s+case|case\s+fault|spare\s+case', text):
        return 'charging_case_fault'

    # 3. Battery drain / poor battery life
    # Keywords: battery drain, battery life, poor backup, discharging fast, draining, battery backup
    if re.search(r'battery\s+(drain|life|backup|draining|drops|dropped)|poor\s+battery|draining\s+(fast|even)|backup\s+issue|discharg', text):
        return 'battery_drain'

    # General charging if not caught above
    if re.search(r'not\s+charging|won\'t\s+charge|charging\s+pin|not\s+taking\s+charge|charging\s+issue', text) and ('bud' in text or 'earbud' in text or 'pulse' in text):
        return 'one_earbud_dead_or_not_charging'

    # 4. Pairing / connection drop
    # Keywords: pairing, pair, bluetooth, bt drop, connection drop, disconnect, cutting out, discoverable
    if re.search(r'pair(ing)?\b|bluetooth|bt\s+(drop|dropout)|disconnect|cutting\s+out|not\s+discoverable|forget\s+\+\s+re-pair|unable\s+to\s+pair', text):
        return 'pairing_connection_drop'

    # 5. Audio quality / distortion / mic (should this be a distinct theme or other?)
    # Keywords: static noise, crackling, distortion, buzzing, mic not working, audio quality
    if re.search(r'static\s+noise|crackling|distortion|buzzing|mic\s+(not\s+working|issue)|audio\s+distortion|eq\s+reset|sound\s+quality', text):
        return 'audio_quality'

    # 6. Delivery & tracking
    # Keywords: tracking, delivery, delivered, courier, awb, dispatch, shipment, wrong product, damaged, pincode, address update, transit
    if re.search(r'track(ing)?|deliver(y|ed)?|courier|awb|shipment|dispatch|pincode|address\s+update|lost\s+in\s+transit|rto|wrong\s+(product|item|variant)|transit\s+damage|damaged\s+in\s+transit', text):
        return 'delivery_tracking'

    # 7. Refund / payment delay
    # Keywords: refund, double payment, amount debited, money deducted, payment, gateway, utr, arn, reverse pickup qc, refund delay
    if re.search(r'refund|double\s+payment|debited|money\s+deducted|payment\s+failed|utr|arn|charge(d)?\s+two\s+times|price\s+adj|coupon|promo\s+code', text):
        return 'refund_payment_delay'

    # 8. Warranty / RMA / Repair
    # Keywords: warranty, rma, repair, inspection, claim, replacement pending, repair status
    if re.search(r'warranty|rma|repair|inspection|wty|repair\s+status|claim\s+pending', text):
        return 'warranty_rma'

    # 9. App & Firmware / Account / Other
    if re.search(r'otp|login|account\s+unlock|password|app\s+crash|firmware\s+update|stuck\s+at', text):
        return 'app_firmware_account'

    return 'other'

clean_tickets['predicted_theme'] = clean_tickets.apply(lambda r: classify_ticket(r['combined_text'], r['product_sku']), axis=1)

print('\nPredicted theme distribution:')
print(clean_tickets['predicted_theme'].value_counts())
print('\nPercentage distribution:')
print(clean_tickets['predicted_theme'].value_counts(normalize=True) * 100)
