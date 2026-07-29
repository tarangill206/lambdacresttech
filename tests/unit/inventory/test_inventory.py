"""Tests for days_of_cover.py and stockout.py."""

from decimal import Decimal
import pytest
from commerce_math.core.errors import InvalidInputError
from commerce_math.inventory.days_of_cover import days_of_cover
from commerce_math.inventory.stockout import stockout_probability

BASE = dict(expected_daily_demand=20.0, daily_demand_std=6.0,
            lead_time_days_min=60, lead_time_days_max=90)


def test_days_of_cover_basic():
    assert days_of_cover(420, Decimal("20")) == Decimal("21.00")

def test_zero_demand_is_undefined_not_infinite_crash():
    assert days_of_cover(420, Decimal("0")) is None

def test_plenty_of_stock_means_low_risk():
    # ~75 days * 20/day = ~1500 expected; 3000 on hand is comfortable.
    r = stockout_probability(available_units=3000, inbound_units=0, **BASE)
    assert r.probability_stockout < Decimal("0.05")

def test_thin_stock_means_high_risk():
    # 900 units vs ~1500 expected demand: near-certain stockout.
    r = stockout_probability(available_units=900, inbound_units=0, **BASE)
    assert r.probability_stockout > Decimal("0.9")

def test_inbound_units_reduce_risk():
    without = stockout_probability(available_units=1400, inbound_units=0, **BASE)
    with_po = stockout_probability(available_units=1400, inbound_units=600, **BASE)
    assert with_po.probability_stockout < without.probability_stockout

def test_scaling_ads_raises_risk():
    # THE ads<->inventory connection: same stock, higher demand, more risk.
    calm = stockout_probability(1600, 0, expected_daily_demand=20.0,
                                daily_demand_std=6.0, lead_time_days_min=60,
                                lead_time_days_max=90)
    scaled = stockout_probability(1600, 0, expected_daily_demand=32.0,
                                  daily_demand_std=8.0, lead_time_days_min=60,
                                  lead_time_days_max=90)
    assert scaled.probability_stockout > calm.probability_stockout

def test_reproducible():
    a = stockout_probability(1500, 0, seed=7, **BASE)
    assert a == stockout_probability(1500, 0, seed=7, **BASE)

def test_invalid_inputs():
    with pytest.raises(InvalidInputError):
        stockout_probability(-1, 0, **BASE)
    with pytest.raises(InvalidInputError):
        stockout_probability(1500, 0, expected_daily_demand=20, daily_demand_std=6,
                             lead_time_days_min=90, lead_time_days_max=60)