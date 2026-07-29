"""
money.py — the single source of truth for how money is represented.

WHY THIS FILE EXISTS
Floats corrupt money: 0.1 + 0.2 == 0.30000000000000004. Over thousands of
orders those errors compound, and financial results must be EXACT and
reproducible. So the whole package follows three rules:

1. Amounts at boundaries (API, storage) are integers in MINOR UNITS.
   $49.99 = 4999 cents. Integer math is exact.
2. Ratios/divisions (margins, break-evens) use Decimal. Exact base-10 math.
3. Only simulation arrays (thousands of random draws) may use floats,
   because there speed matters and sampling noise dwarfs float error.

Every module imports these helpers instead of inventing its own handling.
"""

from decimal import Decimal, ROUND_HALF_UP

# Decimal places kept when computing ratios (enough precision for any
# margin/rate; quantized so results are reproducible byte-for-byte).
RATIO_PLACES = Decimal("0.000001")


def minor_to_decimal(amount_minor: int) -> Decimal:
    """4999 -> Decimal('49.99'). For display and ratio math."""
    return Decimal(amount_minor) / Decimal(100)


def decimal_to_minor(amount: Decimal) -> int:
    """Decimal('49.99') -> 4999. Half-up rounding: $0.005 rounds to 1 cent,
    the convention people expect on invoices."""
    cents = (amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def ratio(numerator: int, denominator: int) -> Decimal:
    """Exact division of two minor-unit amounts (e.g. margin = profit/revenue).
    Raises ZeroDivisionError deliberately — a zero denominator means the
    caller asked a meaningless question and must handle it, not get a 0."""
    return (Decimal(numerator) / Decimal(denominator)).quantize(RATIO_PLACES)