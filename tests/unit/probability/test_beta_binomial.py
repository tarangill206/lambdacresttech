"""Tests for beta_binomial.py — small samples must not fool us."""

from decimal import Decimal
import numpy as np
import pytest
from commerce_math.core.errors import InvalidInputError
from commerce_math.probability.beta_binomial import posterior, probability_a_beats_b


# Weak ~2% prior: as if we'd seen 2 orders in 100 clicks before this ad.
PRIOR = dict(prior_alpha=2, prior_beta=98)


def test_posterior_update_is_exact():
    p = posterior(2, 98, successes=34, trials=900)
    assert p.alpha == 36 and p.beta == 964   # 2+34, 98+(900-34)

def test_small_sample_gets_shrunk_toward_prior():
    lucky = posterior(**PRIOR, successes=2, trials=20)     # raw 10%
    # Posterior mean = 4/120 ≈ 3.3%: pulled hard toward the 2% prior.
    assert lucky.mean < Decimal("0.05")

def test_large_sample_overrides_prior():
    solid = posterior(**PRIOR, successes=180, trials=2000)  # raw 9%
    assert Decimal("0.08") < solid.mean < Decimal("0.10")

def test_interval_narrows_with_evidence():
    small = posterior(**PRIOR, successes=2, trials=20)
    large = posterior(**PRIOR, successes=200, trials=2000)
    width = lambda p: p.credible_interval()[1] - p.credible_interval()[0]
    assert width(large) < width(small)

def test_probability_above_threshold():
    p = posterior(**PRIOR, successes=180, trials=2000)
    assert p.probability_above(Decimal("0.05")) > Decimal("0.99")  # clearly above 5%
    assert p.probability_above(Decimal("0.20")) < Decimal("0.01")  # clearly below 20%

def test_lucky_small_sample_does_not_beat_solid_large_sample():
    # THE test this module exists for: raw 10% vs raw 9%,
    # but the model must say 'too close to call', not 'A wins'.
    lucky = posterior(**PRIOR, successes=2, trials=20)
    solid = posterior(**PRIOR, successes=180, trials=2000)
    p_win = probability_a_beats_b(lucky, solid)
    assert p_win < Decimal("0.65")   # nowhere near confident

def test_comparison_is_reproducible():
    a = posterior(**PRIOR, successes=30, trials=500)
    b = posterior(**PRIOR, successes=25, trials=500)
    assert probability_a_beats_b(a, b, seed=42) == probability_a_beats_b(a, b, seed=42)

def test_invalid_inputs_rejected():
    with pytest.raises(InvalidInputError):
        posterior(0, 98, 1, 10)          # prior must be positive
    with pytest.raises(InvalidInputError):
        posterior(2, 98, 11, 10)         # successes > trials