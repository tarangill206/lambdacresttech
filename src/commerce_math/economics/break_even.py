"""
break_even.py — the "most we can afford" numbers for advertising.

WHAT IT COMPUTES
Break-even thresholds: the exact point where an ad neither makes nor loses
money. Everything is derived from ONE input — contribution before ads —
by asking the same question four ways:

  break-even CPA  = contribution per order
      Spend this much to get one order and you made $0. Pay less = profit.
  break-even CPC  = contribution per order x conversion rate
      What one CLICK is worth, since only some clicks become orders.
  break-even ROAS = revenue / contribution   (per order)
      Platforms report ROAS vs gross revenue; this converts our margin
      into their language. Thin margins => you need HIGH ROAS to survive.
  break-even ACOS = contribution / revenue   (Amazon's inverse convention)
      ACOS = ad spend / ad revenue. Profitable only BELOW this number.

WHY IT MATTERS
These are the yardsticks every observed metric is judged against. "CPA is
$28" means nothing; "CPA is $28 and break-even is $24" is a decision.
The Bayesian layer later replaces the fixed conversion rate with a
posterior distribution — but the arithmetic here stays identical.

WHY THE MATH IS CORRECT
Definition, not estimation: profit(x) = contribution - x is zero exactly
at x = contribution. Ratios use Decimal (exact). Zero/negative
contribution raises InvalidInputError: "how much can we afford to spend?"
has no meaningful answer when each order already loses money — returning
0 or a negative "budget" would poison downstream comparisons silently.
"""

from decimal import Decimal

from commerce_math.core.errors import InvalidInputError
from commerce_math.core.money import ratio


def _require_positive(name: str, value) -> None:
    if value <= 0:
        raise InvalidInputError(f"{name} must be > 0, got {value}")


def break_even_cpa_minor(contribution_before_ads_minor: int) -> int:
    """Max spend per ORDER at zero profit = the contribution itself."""
    _require_positive("contribution_before_ads_minor", contribution_before_ads_minor)
    return contribution_before_ads_minor


def break_even_cpc(contribution_before_ads_minor: int, conversion_rate: Decimal) -> Decimal:
    """Max spend per CLICK, in minor units (Decimal for sub-cent precision).

    A click is worth (chance it becomes an order) x (what an order is worth).
    Example: $24.00 contribution, 2.5% conversion -> 2400 x 0.025 = 60.0
    minor units = $0.60 max CPC. conversion_rate in (0, 1]."""
    _require_positive("contribution_before_ads_minor", contribution_before_ads_minor)
    if not Decimal("0") < conversion_rate <= Decimal("1"):
        raise InvalidInputError(f"conversion_rate must be in (0, 1], got {conversion_rate}")
    return Decimal(contribution_before_ads_minor) * conversion_rate


def break_even_roas(net_revenue_minor: int, contribution_before_ads_minor: int) -> Decimal:
    """Min platform ROAS to break even = revenue / contribution (per order).

    Why: at break-even, spend = contribution. Platform ROAS = revenue/spend
    = revenue/contribution. Example: $100 revenue, $43 contribution ->
    2.325814 -> a "2x ROAS!" campaign is actually losing money."""
    _require_positive("net_revenue_minor", net_revenue_minor)
    _require_positive("contribution_before_ads_minor", contribution_before_ads_minor)
    return ratio(net_revenue_minor, contribution_before_ads_minor)


def break_even_acos(net_revenue_minor: int, contribution_before_ads_minor: int) -> Decimal:
    """Max Amazon ACOS to break even = contribution / revenue = 1 / roas.

    ACOS is spend/revenue, so profitability flips: LOWER is better.
    Example: $100 revenue, $43 contribution -> 0.43 -> profitable only
    while ACOS stays under 43%."""
    _require_positive("net_revenue_minor", net_revenue_minor)
    _require_positive("contribution_before_ads_minor", contribution_before_ads_minor)
    return ratio(contribution_before_ads_minor, net_revenue_minor)