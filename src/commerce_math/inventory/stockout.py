"""
stockout.py — probability we run out before replenishment arrives.

THE QUESTION
"If we reorder today, what's the chance demand eats all our stock before
the new units land?" One average number can't answer this: demand
fluctuates daily AND the supplier lead time itself is uncertain. Averages
hide exactly the tail risk that kills supplement brands (a stockout also
tanks Amazon organic rank — the cost is bigger than missed sales).

THE MODEL (Monte Carlo)
For each of many simulated futures:
  1. draw a lead time L (uniform between min and max supplier days)
  2. draw daily demand for L days (normal around the mean, floored at 0)
  3. total demand > (available + inbound arriving in time)?  -> stockout
P(stockout) = fraction of futures that ran out. Percentiles of demand
show best/worst cases. Fixed seed = reproducible (provenance rule).

WHY NORMAL DEMAND, AND ITS LIMITS
v1 uses Normal(mean, std) truncated at 0 — the standard starting point
when all you have is a mean and a spread (pre-launch: assumptions;
post-launch: forecasting's error). Low-volume days are really Poisson-ish;
if calibration later shows mismatch, the distribution swaps out behind
the same interface — model version bump, contract unchanged.

CONNECTION TO ADS
expected_daily_demand is the lever: policy asks this module twice —
once at current demand, once at post-SCALE demand — and the difference
in P(stockout) is the real cost of scaling.
"""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from commerce_math.core.errors import InvalidInputError

_PLACES = Decimal("0.000001")


@dataclass(frozen=True)
class StockoutResult:
    probability_stockout: Decimal      # the headline risk number
    expected_demand_units: Decimal     # mean total demand during lead time
    demand_p90_units: int              # bad-case demand (90th percentile)
    seed: int


def stockout_probability(
    available_units: int,
    inbound_units: int,                 # already ordered, arrives within lead time
    expected_daily_demand: float,
    daily_demand_std: float,
    lead_time_days_min: int,
    lead_time_days_max: int,
    n_samples: int = 100_000,
    seed: int = 0,
) -> StockoutResult:
    """P(demand during replenishment lead time exceeds what we can supply)."""
    if available_units < 0 or inbound_units < 0:
        raise InvalidInputError("units must be >= 0")
    if expected_daily_demand < 0 or daily_demand_std < 0:
        raise InvalidInputError("demand parameters must be >= 0")
    if not 0 < lead_time_days_min <= lead_time_days_max:
        raise InvalidInputError("need 0 < lead_time_days_min <= lead_time_days_max")

    rng = np.random.default_rng(seed)
    # Draw one lead time per simulated future (inclusive of max).
    lead_times = rng.integers(lead_time_days_min, lead_time_days_max + 1, size=n_samples)
    # Total demand over L days: sum of L daily normals = Normal(L*mu, sqrt(L)*sigma).
    # (Same math as simulating each day, but one draw per future = fast.)
    totals = rng.normal(lead_times * expected_daily_demand,
                        np.sqrt(lead_times) * daily_demand_std)
    totals = np.maximum(totals, 0)                       # demand can't be negative

    supply = available_units + inbound_units
    return StockoutResult(
        probability_stockout=Decimal(str(float(np.mean(totals > supply)))).quantize(_PLACES),
        expected_demand_units=Decimal(str(round(float(np.mean(totals)), 2))),
        demand_p90_units=int(round(float(np.percentile(totals, 90)))),
        seed=seed,
    )