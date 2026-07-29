"""Tests for contribution.py — the numbers everything else stands on."""

import pytest
from commerce_math.core.errors import InvalidInputError
from commerce_math.economics.contribution import calculate_contribution


def test_docstring_example():
    r = calculate_contribution(
        net_revenue_minor=100_00,
        product_cost_minor=30_00,
        inbound_freight_minor=5_00,
        fulfillment_cost_minor=10_00,
        payment_fees_minor=3_00,
        marketplace_fees_minor=7_00,
        refund_cost_minor=2_00,
        ad_spend_minor=25_00,
    )
    assert r.contribution_before_ads_minor == 43_00
    assert r.contribution_after_ads_minor == 18_00
    assert r.total_costs_minor == 57_00

def test_negative_contribution_is_valid():
    # Losing money is a real answer, not an error.
    r = calculate_contribution(20_00, 30_00, 0, 0, 0, 0, 0)
    assert r.contribution_before_ads_minor == -10_00

def test_ad_spend_defaults_to_zero():
    r = calculate_contribution(50_00, 10_00, 0, 0, 0, 0, 0)
    assert r.contribution_before_ads_minor == r.contribution_after_ads_minor

def test_negative_cost_is_rejected():
    with pytest.raises(InvalidInputError):
        calculate_contribution(50_00, -10_00, 0, 0, 0, 0, 0)

def test_result_is_immutable():
    r = calculate_contribution(50_00, 10_00, 0, 0, 0, 0, 0)
    with pytest.raises(Exception):
        r.contribution_before_ads_minor = 999