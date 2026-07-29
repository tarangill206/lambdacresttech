"""
days_of_cover.py — the simplest, most-used inventory number.

WHAT IT COMPUTES
  days_of_cover = available units / expected daily demand
"At today's sales rate, how long until the shelf is empty?"

WHY IT MATTERS
It's the early-warning gauge every ad decision consults: 45 days of cover
with a 75-day supplier lead time = trouble EVEN IF nothing changes — and a
SCALE recommendation makes demand rise, shrinking cover further. That
comparison (cover vs lead time) is the heart of "profitable but HOLD".

DEFINITIONS (kept strict so channels don't double-count)
  available = physically usable stock - already-reserved units.
  FBA + MCF share ONE pool: Amazon orders and Shopify orders drain the
  same units, so demand here is TOTAL demand across channels.

WHY THE MATH IS CORRECT
It's a definition (units / units-per-day). Zero demand -> None ("cover is
undefined/infinite while nothing sells"), matching metrics.py's rule:
no data isn't a zero. Negative inputs are corrupt data -> error.
"""

from decimal import Decimal

from commerce_math.core.errors import InvalidInputError
from commerce_math.core.money import ratio


def days_of_cover(available_units: int, expected_daily_demand: Decimal) -> Decimal | None:
    """Days until stockout at constant demand. None while demand is zero."""
    if available_units < 0:
        raise InvalidInputError(f"available_units must be >= 0, got {available_units}")
    if expected_daily_demand < 0:
        raise InvalidInputError("expected_daily_demand must be >= 0")
    if expected_daily_demand == 0:
        return None
    return (Decimal(available_units) / expected_daily_demand).quantize(Decimal("0.01"))