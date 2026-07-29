"""Tests for ad_actions.py — thresholds -> recommendations."""

from decimal import Decimal
from commerce_math.core.enums import AdAction, QualityStatus
from commerce_math.marketing.marginal_profit import MarginalProfitResult
from commerce_math.policy.ad_actions import decide_ad_action


def fake_marginal(p: str, expected: int = 100_00) -> MarginalProfitResult:
    """Hand-built result so policy tests don't depend on simulation."""
    return MarginalProfitResult(
        proposed_spend_minor=500_00, expected_orders=Decimal("14"),
        expected_profit_minor=expected, probability_profitable=Decimal(p),
        profit_p10_minor=-200_00, profit_p90_minor=400_00, seed=0,
    )

MATURE = dict(clicks_observed=900, orders_observed=34)


def test_blocked_data_always_holds():
    d = decide_ad_action(fake_marginal("0.95"), QualityStatus.BLOCKED, **MATURE)
    assert d.action == AdAction.HOLD

def test_immature_evidence_is_learning():
    d = decide_ad_action(fake_marginal("0.80"), QualityStatus.PASS,
                         clicks_observed=50, orders_observed=2)
    assert d.action == AdAction.LEARNING

def test_confident_winner_scales_capped():
    d = decide_ad_action(fake_marginal("0.80"), QualityStatus.PASS, **MATURE)
    assert d.action == AdAction.SCALE
    assert d.max_budget_change == Decimal("0.15")

def test_doubtful_reduces():
    d = decide_ad_action(fake_marginal("0.30", expected=-50_00),
                         QualityStatus.PASS, **MATURE)
    assert d.action == AdAction.REDUCE

def test_near_certain_loser_is_killed_even_while_learning():
    d = decide_ad_action(fake_marginal("0.05", expected=-300_00),
                         QualityStatus.PASS, clicks_observed=50, orders_observed=1)
    assert d.action == AdAction.KILL   # emergency guardrail beats LEARNING

def test_constraint_overrides_profitable_scale():
    d = decide_ad_action(fake_marginal("0.85"), QualityStatus.PASS,
                         constraint_binding=True, **MATURE)
    assert d.action == AdAction.HOLD
    assert "constraint" in d.reasons[0]

def test_middle_ground_holds():
    d = decide_ad_action(fake_marginal("0.55"), QualityStatus.PASS, **MATURE)
    assert d.action == AdAction.HOLD

def test_every_decision_has_reasons():
    d = decide_ad_action(fake_marginal("0.80"), QualityStatus.PASS, **MATURE)
    assert len(d.reasons) > 0