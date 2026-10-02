"""
Tests for Rule-Based Classifier and Text Processing.
"""

import pytest
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from classify import classify_single_ticket, identify_junk_ivr_mask


def test_classifier_rules():
    # Asymmetric dead earbud
    pred1 = classify_single_ticket(
        customer_message="right side works perfectly, left one just does not wake up",
        agent_notes="walked through reset, esc to hardware team",
        product_sku="VA-EB-PL2"
    )
    assert pred1 == 'one_earbud_dead_or_not_charging'

    # Charging case fault
    pred2 = classify_single_ticket(
        customer_message="the case is dead, no light comes on when plugged in",
        agent_notes="replacement case raised",
        product_sku="VA-EB-PL2"
    )
    assert pred2 == 'charging_case_fault'

    # Battery drain
    pred3 = classify_single_ticket(
        customer_message="dies by lunchtime with light use, battery drops from 100% to 0 in an hour",
        agent_notes="battery health check",
        product_sku="VA-EB-PL1"
    )
    assert pred3 == 'battery_drain'

    # Pairing connection drop
    pred4 = classify_single_ticket(
        customer_message="bluetooth keeps cutting out and disconnecting every 5 minutes",
        agent_notes="advised unpair and re-pair",
        product_sku="VA-EB-PL2"
    )
    assert pred4 == 'pairing_connection_drop'

    # Delivery tracking
    pred5 = classify_single_ticket(
        customer_message="courier tracking link is broken, haven't received my package for 10 days",
        agent_notes="checked awb with bluedart",
        product_sku="VA-EB-PL1"
    )
    assert pred5 == 'delivery_tracking'

    # Refund payment delay
    pred6 = classify_single_ticket(
        customer_message="money was debited twice from my account, refund still pending",
        agent_notes="checked payment gateway for duplicate txn",
        product_sku="VA-EB-PL2"
    )
    assert pred6 == 'refund_payment_delay'


def test_junk_ivr_filter():
    df = pd.DataFrame({
        'customer_message': [
            '[inaudible] [crosstalk] caller disconnected',
            '...',
            '??',
            'Hello my pulse buds left earbud is dead'
        ],
        'channel': ['voice', 'chat', 'chat', 'voice']
    })
    
    mask = identify_junk_ivr_mask(df)
    assert mask.tolist() == [True, True, True, False]
