"""
contribution.py — the foundation number of the entire business.

WHAT IT COMPUTES
Contribution = what one order (or a batch of orders) actually adds to the
company after every direct cost of serving it. Two flavors:

  contribution BEFORE ads = net revenue - product cost - inbound freight
                            - fulfillment - payment/marketplace fees
                            - refund cost
  contribution AFTER ads  = contribution before ads - ad spend

WHY IT MATTERS
Every ad decision reduces to: "does the next dollar of spend buy more than
a dollar of contribution?" Platforms report ROAS against gross revenue and
ignore our fees, refunds, and product cost — so a "3x ROAS" campaign can
lose money. Break-even CPA, marginal ad profit, budget allocation, cash
projections: ALL of them consume contribution as their value unit. If this
number is wrong, everything above it is wrong. That's why it's built first
and kept brutally simple.

WHY THE MATH IS CORRECT
Pure subtraction of integer minor units (cents) — exact, no floats, no
rounding. Order of subtraction doesn't matter. Costs are passed EXPLICITLY
(no hidden defaults): a missing cost must be an obvious 0 in the caller's
code, never silently assumed by us.

WHAT IT DOESN'T DO
No platform names, no attribution, no currency conversion (inputs must
already share one currency — the contract layer enforces that), no policy.
Negative results are VALID and important: they mean "this loses money."
"""

from dataclasses import dataclass

from commerce_math.core.errors import InvalidInputError


@dataclass(frozen=True)
class ContributionResult:
    """Both contribution levels plus the total cost, for transparency.
    frozen=True: results are facts; nobody may edit them after creation."""
    net_revenue_minor: int
    total_costs_minor: int              # everything except ad spend
    contribution_before_ads_minor: int
    ad_spend_minor: int
    contribution_after_ads_minor: int


def calculate_contribution(
    net_revenue_minor: int,
    product_cost_minor: int,
    inbound_freight_minor: int,
    fulfillment_cost_minor: int,
    payment_fees_minor: int,
    marketplace_fees_minor: int,
    refund_cost_minor: int,
    ad_spend_minor: int = 0,
) -> ContributionResult:
    """Compute contribution before and after advertising.

    All amounts are integer minor units (cents) in ONE currency.
    net_revenue_minor = product revenue actually kept (after discounts,
    excluding collected tax — Java's builder resolves that definition).

    Example: $100.00 revenue, $30 product, $5 freight, $10 fulfillment,
    $3 payment fees, $7 marketplace fees, $2 refunds, $25 ads:
        before ads = 100_00 - 57_00 = 43_00  ($43.00)
        after ads  = 43_00 - 25_00 = 18_00   ($18.00)
    """
    costs = {
        "product_cost_minor": product_cost_minor,
        "inbound_freight_minor": inbound_freight_minor,
        "fulfillment_cost_minor": fulfillment_cost_minor,
        "payment_fees_minor": payment_fees_minor,
        "marketplace_fees_minor": marketplace_fees_minor,
        "refund_cost_minor": refund_cost_minor,
        "ad_spend_minor": ad_spend_minor,
    }
    # Costs are magnitudes; a negative cost is a data error upstream
    # (credits/rebates arrive as separate records, not negative costs).
    for name, value in costs.items():
        if value < 0:
            raise InvalidInputError(f"{name} is negative ({value}); costs must be >= 0")

    total_costs = (
        product_cost_minor
        + inbound_freight_minor
        + fulfillment_cost_minor
        + payment_fees_minor
        + marketplace_fees_minor
        + refund_cost_minor
    )
    before_ads = net_revenue_minor - total_costs

    return ContributionResult(
        net_revenue_minor=net_revenue_minor,
        total_costs_minor=total_costs,
        contribution_before_ads_minor=before_ads,
        ad_spend_minor=ad_spend_minor,
        contribution_after_ads_minor=before_ads - ad_spend_minor,
    )