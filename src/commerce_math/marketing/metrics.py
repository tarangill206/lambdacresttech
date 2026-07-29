"""
metrics.py — the deterministic scoreboard for any ad unit.

WHAT IT COMPUTES
The observed performance rates every ad platform reports, computed by US
from canonical counts so all platforms are scored identically:

  CTR  = clicks / impressions        (does the creative stop the scroll?)
  CVR  = orders / clicks             (does the click become an order?)
  CPC  = spend / clicks              (price of one click)
  CPA  = spend / orders              (price of one order)
  ROAS = revenue / spend             (platform's favorite headline)
  ACOS = spend / revenue             (Amazon's inverse of ROAS)

WHY IT MATTERS
These are FACTS about the past, judged against break_even.py thresholds:
observed CPA $28 vs break-even $24 = losing $4/order. They deliberately
carry NO uncertainty — 2 orders from 20 clicks yields the same CVR number
as 200 from 2000. Honest treatment of that difference is the job of
probability/beta_binomial.py; keeping fact and inference in separate
modules is what keeps both trustworthy.

WHY THE MATH IS CORRECT
Definitions, exact Decimal division. Zero denominators return None
("undefined"), not 0 and not an error: no clicks yet doesn't mean CVR is
0%, it means CVR doesn't exist yet — and unlike break_even (where zero
contribution poisons decisions), "no data yet" is a normal early state
callers must display as such. Impossible counts (clicks > impressions)
raise: that's corrupt data, not a metric.
"""

from decimal import Decimal

from commerce_math.core.errors import InvalidInputError
from commerce_math.core.money import ratio


def _require_non_negative(**counts: int) -> None:
    for name, value in counts.items():
        if value < 0:
            raise InvalidInputError(f"{name} must be >= 0, got {value}")


def ctr(clicks: int, impressions: int) -> Decimal | None:
    """Click-through rate. None until impressions exist."""
    _require_non_negative(clicks=clicks, impressions=impressions)
    if clicks > impressions:
        raise InvalidInputError(f"clicks ({clicks}) > impressions ({impressions})")
    return ratio(clicks, impressions) if impressions else None


def cvr(orders: int, clicks: int) -> Decimal | None:
    """Conversion rate: confirmed orders per click. None until clicks exist.
    orders may legitimately exceed clicks in weird edge windows (delayed
    attribution), so we don't hard-reject — diagnostics flags it instead."""
    _require_non_negative(orders=orders, clicks=clicks)
    return ratio(orders, clicks) if clicks else None


def cpc_minor(spend_minor: int, clicks: int) -> Decimal | None:
    """Cost per click in minor units. None until clicks exist."""
    _require_non_negative(spend_minor=spend_minor, clicks=clicks)
    return ratio(spend_minor, clicks) if clicks else None


def cpa_minor(spend_minor: int, orders: int) -> Decimal | None:
    """Cost per confirmed order in minor units. None until orders exist."""
    _require_non_negative(spend_minor=spend_minor, orders=orders)
    return ratio(spend_minor, orders) if orders else None


def roas(revenue_minor: int, spend_minor: int) -> Decimal | None:
    """Revenue per spend unit. None until spend exists.
    NOTE: honest ROAS uses confirmed revenue; platform-attributed revenue
    yields an ATTRIBUTION_CLAIM roas — same formula, label the source."""
    _require_non_negative(revenue_minor=revenue_minor, spend_minor=spend_minor)
    return ratio(revenue_minor, spend_minor) if spend_minor else None


def acos(spend_minor: int, revenue_minor: int) -> Decimal | None:
    """Amazon's convention: spend / revenue. None until revenue exists."""
    _require_non_negative(spend_minor=spend_minor, revenue_minor=revenue_minor)
    return ratio(spend_minor, revenue_minor) if revenue_minor else None