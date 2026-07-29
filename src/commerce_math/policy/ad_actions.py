"""
ad_actions.py — where estimates become recommendations.

THE SEPARATION
Models ESTIMATE ("73% chance the next $500 is profitable"). Policy DECIDES
("SCALE by at most 15%"). They live in different modules because business
rules change independently of statistics: you can tighten thresholds
without touching a single model, and vice versa. This is also why every
threshold lives in PolicyConfig — versioned configuration, never magic
numbers buried in code.

HOW A DECISION IS MADE (in order, first rule that fires wins)
  1. Data quality BLOCKED           -> HOLD (never act on unsafe data)
  2. Not enough evidence yet        -> LEARNING (test budget only)
  3. Losing badly, high confidence  -> KILL
  4. Losing, or profit doubtful     -> REDUCE
  5. Constraint binding (inventory/
     cash flag from caller)         -> HOLD despite good numbers
  6. Confidently profitable         -> SCALE (capped step size)
  7. Otherwise                      -> HOLD (default is inaction)

WHY THE ASYMMETRY BETWEEN SCALE AND KILL
Scaling needs HIGH confidence (wrong scale = burn money fast). Killing
needs high confidence too (wrong kill = destroy a winner while it's still
noisy) — but REDUCE exists precisely so we can de-risk without executing:
lowering spend on a doubtful ad is cheap insurance either way.

The maximum step size (~15%) is the policy-level answer to the constant-
efficiency assumption in marginal_profit.py AND to platform learning
phases: small edits keep the model honest and avoid learning resets.

Emergency rule from the blueprint: LEARNING raises the evidence bar for
SCALE but never disables loss protection — a hemorrhaging campaign in its
learning phase can still be KILLED.
"""

from dataclasses import dataclass
from decimal import Decimal

from commerce_math.core.enums import AdAction, QualityStatus
from commerce_math.marketing.marginal_profit import MarginalProfitResult


@dataclass(frozen=True)
class PolicyConfig:
    """All decision thresholds. Versioned config — tune WITHOUT code changes."""
    min_clicks_for_verdict: int = 300          # below this: LEARNING...
    min_orders_for_verdict: int = 10           # ...unless losses trigger KILL
    scale_min_probability: Decimal = Decimal("0.70")   # confidence to add money
    reduce_below_probability: Decimal = Decimal("0.40")  # doubt -> pull back
    kill_below_probability: Decimal = Decimal("0.10")    # near-certain loser
    max_budget_step: Decimal = Decimal("0.15")           # +/-15% per change


@dataclass(frozen=True)
class AdDecision:
    action: AdAction
    max_budget_change: Decimal      # signed cap: +0.15 scale, -0.15 reduce, 0 hold
    reasons: tuple[str, ...]        # every decision explains itself


def decide_ad_action(
    marginal: MarginalProfitResult,
    quality: QualityStatus,
    clicks_observed: int,
    orders_observed: int,
    constraint_binding: bool = False,   # inventory/cash says "not now"
    config: PolicyConfig = PolicyConfig(),
) -> AdDecision:
    """Turn a marginal-profit estimate + context into one recommendation.

    constraint_binding: the caller (later: an orchestrating layer checking
    stockout probability and cash ceiling) sets this True when a real-world
    constraint should override a profitable-looking scale.
    """
    p = marginal.probability_profitable
    zero = Decimal("0")

    # 1. Unsafe data -> refuse to act. (Matches InputQualityBlockedError
    #    philosophy, but policy HOLDs rather than raises: a recommendation
    #    row must exist to display, with the reason attached.)
    if quality == QualityStatus.BLOCKED:
        return AdDecision(AdAction.HOLD, zero, ("data quality BLOCKED",))

    immature = (clicks_observed < config.min_clicks_for_verdict
                or orders_observed < config.min_orders_for_verdict)

    # 2/3. Emergency loss protection fires even during LEARNING.
    if p < config.kill_below_probability and marginal.expected_profit_minor < 0:
        return AdDecision(AdAction.KILL, Decimal("-1"),
                          (f"P(profitable)={p} below kill threshold", "expected loss"))

    if immature:
        return AdDecision(AdAction.LEARNING, zero,
                          (f"evidence immature: {clicks_observed} clicks, "
                           f"{orders_observed} orders",))

    # 4. Doubtful -> de-risk.
    if p < config.reduce_below_probability:
        return AdDecision(AdAction.REDUCE, -config.max_budget_step,
                          (f"P(profitable)={p} below reduce threshold",))

    # 5. Real-world constraint overrides opportunity.
    if constraint_binding:
        return AdDecision(AdAction.HOLD, zero,
                          ("profitable but constraint binding (inventory/cash)",))

    # 6. Confident winner -> scale, capped.
    if p >= config.scale_min_probability:
        return AdDecision(AdAction.SCALE, config.max_budget_step,
                          (f"P(profitable)={p} meets scale threshold",))

    # 7. Middle ground -> keep collecting evidence at current spend.
    return AdDecision(AdAction.HOLD, zero,
                      (f"P(profitable)={p} between reduce and scale thresholds",))