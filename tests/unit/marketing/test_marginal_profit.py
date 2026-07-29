"""Tests for marginal_profit.py — the core ROI-of-next-spend number."""

from decimal import Decimal
import pytest
from commerce_math.core.errors import InvalidInputError
from commerce_math.probability.beta_binomial import posterior
from commerce_math.marketing.marginal_profit import expected_marginal_profit

# A solid performer: 34 orders / 900 clicks on a weak 2% prior.
GOOD = posterior(2, 98, successes=34, trials=900)
ARGS = dict(recent_cpc_minor=Decimal("133.33"), contribution_per_order_minor=43_00)


def test_profitable_ad_shows_high_probability():
    r = expected_marginal_profit(500_00, cvr_posterior=GOOD, **ARGS)
    # ~375 clicks * ~3.6% * $43 ≈ $580 revenue-side vs $500 spend.
    assert r.probability_profitable > Decimal("0.5")
    assert r.profit_p10_minor < r.expected_profit_minor < r.profit_p90_minor

def test_expensive_clicks_flip_the_answer():
    r = expected_marginal_profit(
        500_00, recent_cpc_minor=Decimal("400"),  # $4 clicks kill it
        cvr_posterior=GOOD, contribution_per_order_minor=43_00,
    )
    assert r.probability_profitable < Decimal("0.1")
    assert r.expected_profit_minor < 0

def test_uncertain_ad_gives_uncertain_answer():
    # 2/20 clicks: the model must hedge, not promise.
    shaky = posterior(2, 98, successes=2, trials=20)
    r = expected_marginal_profit(500_00, cvr_posterior=shaky, **ARGS)
    assert Decimal("0.1") < r.probability_profitable < Decimal("0.9")

def test_reproducible_with_same_seed():
    a = expected_marginal_profit(500_00, cvr_posterior=GOOD, seed=7, **ARGS)
    b = expected_marginal_profit(500_00, cvr_posterior=GOOD, seed=7, **ARGS)
    assert a == b

def test_invalid_inputs_rejected():
    with pytest.raises(InvalidInputError):
        expected_marginal_profit(0, cvr_posterior=GOOD, **ARGS)
    with pytest.raises(InvalidInputError):
        expected_marginal_profit(500_00, recent_cpc_minor=Decimal("133"),
                                 cvr_posterior=GOOD, contribution_per_order_minor=0)