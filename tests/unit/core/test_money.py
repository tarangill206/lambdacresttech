"""Tests for money.py — each test states the rule it protects."""

from decimal import Decimal
import pytest
from commerce_math.core.money import minor_to_decimal, decimal_to_minor, ratio


def test_minor_to_decimal_is_exact():
    assert minor_to_decimal(4999) == Decimal("49.99")

def test_decimal_to_minor_rounds_half_up():
    assert decimal_to_minor(Decimal("49.995")) == 5000  # half cent rounds UP

def test_round_trip_preserves_value():
    assert decimal_to_minor(minor_to_decimal(123456)) == 123456

def test_ratio_is_exact_not_float():
    # 1/3 as a float lies; as Decimal it's controlled to our precision.
    assert ratio(1, 3) == Decimal("0.333333")

def test_ratio_rejects_zero_denominator():
    with pytest.raises(ZeroDivisionError):
        ratio(500, 0)