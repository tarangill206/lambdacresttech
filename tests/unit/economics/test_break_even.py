"""Tests for break_even.py — the affordability yardsticks."""

from decimal import Decimal
import pytest
from commerce_math.core.errors import InvalidInputError
from commerce_math.economics.break_even import (
    break_even_cpa_minor, break_even_cpc, break_even_roas, break_even_acos,
)


def test_cpa_equals_contribution():
    assert break_even_cpa_minor(24_00) == 24_00

def test_cpc_scales_by_conversion_rate():
    # $24 contribution, 2.5% conversion -> $0.60 per click
    assert break_even_cpc(24_00, Decimal("0.025")) == Decimal("60.000")

def test_roas_example():
    assert break_even_roas(100_00, 43_00) == Decimal("2.325581")

def test_acos_is_inverse_convention():
    assert break_even_acos(100_00, 43_00) == Decimal("0.430000")

def test_roas_times_acos_is_one_ish():
    # Sanity: the two conventions are reciprocals (within quantization).
    r = break_even_roas(100_00, 43_00) * break_even_acos(100_00, 43_00)
    assert Decimal("0.999") < r < Decimal("1.001")

def test_unprofitable_product_is_rejected():
    # No meaningful ad budget exists when each order loses money.
    with pytest.raises(InvalidInputError):
        break_even_cpa_minor(0)
    with pytest.raises(InvalidInputError):
        break_even_cpa_minor(-5_00)

def test_bad_conversion_rate_rejected():
    with pytest.raises(InvalidInputError):
        break_even_cpc(24_00, Decimal("0"))
    with pytest.raises(InvalidInputError):
        break_even_cpc(24_00, Decimal("1.5"))