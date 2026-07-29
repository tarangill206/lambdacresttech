"""Tests for metrics.py — the deterministic scoreboard."""

from decimal import Decimal
import pytest
from commerce_math.core.errors import InvalidInputError
from commerce_math.marketing.metrics import ctr, cvr, cpc_minor, cpa_minor, roas, acos


def test_ctr_basic():
    assert ctr(900, 50_000) == Decimal("0.018")

def test_cvr_basic():
    assert cvr(34, 900) == Decimal("0.037778")

def test_cpc_and_cpa():
    # $1200 spend, 900 clicks -> ~$1.33/click; 34 orders -> ~$35.29/order
    assert cpc_minor(1200_00, 900) == Decimal("133.333333")
    assert cpa_minor(1200_00, 34) == Decimal("3529.411765")

def test_roas_and_acos_are_reciprocal_conventions():
    assert roas(1630_00, 1200_00) == Decimal("1.358333")
    assert acos(1200_00, 1630_00) == Decimal("0.736196")

def test_zero_denominator_means_undefined_not_zero():
    assert ctr(0, 0) is None
    assert cvr(0, 0) is None
    assert cpa_minor(500_00, 0) is None   # spent money, no orders yet: CPA undefined
    assert roas(0, 0) is None

def test_impossible_counts_rejected():
    with pytest.raises(InvalidInputError):
        ctr(1200, 1000)                    # clicks > impressions = corrupt data
    with pytest.raises(InvalidInputError):
        cpa_minor(-100, 5)