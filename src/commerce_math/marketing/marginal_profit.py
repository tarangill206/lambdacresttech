"""
marginal_profit.py — what will the NEXT block of spend actually earn?

THE QUESTION
Past ROAS answers "how did money already spent perform?" Scaling needs a
different question: "if we add $500 tomorrow, what happens?" This module
answers with a distribution, not one number: expected profit AND the
probability that profit is positive.

THE MODEL (v1 — deliberately simple, honest about what it assumes)
For a proposed extra spend S on one ad unit:

  expected clicks  = S / recent CPC          (spend buys clicks at ~today's price)
  conversion rate  = DRAWN from the Beta posterior (uncertainty included)
  orders           = clicks x drawn rate
  profit           = orders x contribution_per_order - S

We simulate many draws of the rate, producing a profit distribution:
  expected_profit, P(profit > 0), and pessimistic/optimistic percentiles.

KEY ASSUMPTION — CONSTANT MARGINAL EFFICIENCY
v1 assumes the next clicks cost and convert like recent ones. Reality has
diminishing returns (bigger budgets reach worse audiences), which is why
policy CAPS budget steps (~15%): within a small step, the constant
assumption is roughly true; across a 3x jump it is not. Real response
curves need spend-variation data we won't have for months — encoding a
made-up curve now would be fake sophistication. The honest v1 is:
simple model + small steps + uncertainty carried all the way through.

WHY THE MATH IS CORRECT
Profit is a deterministic function of the rate; the rate's uncertainty is
the posterior (exact Bayes from beta_binomial). Pushing posterior samples
through the profit function IS the profit distribution — Monte Carlo, with
a fixed seed for reproducibility. Floats are fine here (rule 3 in
money.py): sampling noise dwarfs float error; results are reported
quantized.
"""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from commerce_math.core.errors import InvalidInputError
from commerce_math.probability.beta_binomial import BetaPosterior

_PLACES = Decimal("0.000001")


def _dec(x: float) -> Decimal:
    return Decimal(str(round(x, 6))).quantize(_PLACES)


@dataclass(frozen=True)
class MarginalProfitResult:
    """The decision-grade summary of the next-spend profit distribution."""
    proposed_spend_minor: int
    expected_orders: Decimal
    expected_profit_minor: int            # mean of the distribution
    probability_profitable: Decimal       # P(profit > 0) — the headline number
    profit_p10_minor: int                 # pessimistic case (10th percentile)
    profit_p90_minor: int                 # optimistic case (90th percentile)
    seed: int                             # provenance: rerun reproduces exactly


def expected_marginal_profit(
    proposed_spend_minor: int,
    recent_cpc_minor: Decimal,
    cvr_posterior: BetaPosterior,
    contribution_per_order_minor: int,
    n_samples: int = 100_000,
    seed: int = 0,
) -> MarginalProfitResult:
    """Simulate the profit of one additional spend block on one ad unit.

    recent_cpc_minor: observed CPC from a recent window (metrics.cpc_minor).
    cvr_posterior: click->confirmed-order posterior (beta_binomial).
    contribution_per_order_minor: BEFORE-ads contribution (contribution.py).

    Example: $500 more at $1.33/click ≈ 375 clicks; CVR posterior centered
    ~3.7%; $43 contribution/order -> expected ≈ 14 orders x 4300 - 50000
    ≈ +$10,200 minor... the distribution and P(profitable) tell the story.
    """
    if proposed_spend_minor <= 0:
        raise InvalidInputError("proposed_spend_minor must be > 0")
    if recent_cpc_minor <= 0:
        raise InvalidInputError("recent_cpc_minor must be > 0")
    if contribution_per_order_minor <= 0:
        # Same rule as break_even: ads are unaffordable at <= 0 contribution.
        raise InvalidInputError("contribution_per_order_minor must be > 0")

    expected_clicks = float(proposed_spend_minor) / float(recent_cpc_minor)

    rng = np.random.default_rng(seed)
    rates = cvr_posterior.sample(n_samples, rng)             # plausible CVRs
    orders = expected_clicks * rates                          # orders per draw
    profits = orders * contribution_per_order_minor - proposed_spend_minor

    return MarginalProfitResult(
        proposed_spend_minor=proposed_spend_minor,
        expected_orders=_dec(float(np.mean(orders))),
        expected_profit_minor=int(round(float(np.mean(profits)))),
        probability_profitable=_dec(float(np.mean(profits > 0))),
        profit_p10_minor=int(round(float(np.percentile(profits, 10)))),
        profit_p90_minor=int(round(float(np.percentile(profits, 90)))),
        seed=seed,
    )