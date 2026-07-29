"""
beta_binomial.py — honest rate estimation from small samples.

THE PROBLEM
Ads produce yes/no trials: click or not, order or not, refund or not.
Raw rates lie when samples are small: 2 orders / 20 clicks "beats"
180 / 2000 (10% vs 9%) — but the first could easily be luck. Scaling
budget on raw rates systematically rewards lucky noise.

THE MODEL
A conversion process with true unknown rate p, observed successes k in
n trials. We describe our belief about p as a Beta distribution:

  prior:      p ~ Beta(alpha, beta)          (belief BEFORE the data)
  data:       k successes, n - k failures
  posterior:  p ~ Beta(alpha + k, beta + n - k)   (belief AFTER)

That update rule is the whole model — the Beta is "conjugate" to yes/no
data, meaning the posterior is just the prior with successes added to
alpha and failures added to beta. Intuition: alpha and beta act as
IMAGINARY prior trials. Prior Beta(2, 98) = "as if we'd already seen
2 orders in 100 clicks" (~2%, weakly held). Real data then outweighs
the prior as n grows: with 20 clicks the prior dominates (shrinking a
lucky 10% toward 2%); with 2000 clicks the data dominates.

WHY THIS IS CORRECT
It's Bayes' rule applied exactly (not approximated) for Bernoulli trials.
The posterior mean (alpha+k)/(alpha+beta+n) automatically blends prior
and evidence by their relative weights. Credible intervals come straight
from the posterior's quantiles: "95% probability the true rate lies in
[a, b] given prior + data" — the honest statement small samples deserve.

WHERE PRIORS COME FROM
Pre-launch: versioned assumption sets. Post-launch: account-level base
rates. Priors are CONFIG passed in by callers — never hard-coded here.
"""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from scipy import stats

from commerce_math.core.errors import InvalidInputError

# Quantization for reported probabilities/rates (6 places, like money.ratio).
_PLACES = Decimal("0.000001")


def _dec(x: float) -> Decimal:
    """float -> quantized Decimal for stable, comparable reporting."""
    return Decimal(str(x)).quantize(_PLACES)


@dataclass(frozen=True)
class BetaPosterior:
    """Belief about a rate after seeing data. alpha-1 ~ successes seen,
    beta-1 ~ failures seen (including the prior's imaginary ones)."""
    alpha: float
    beta: float

    @property
    def mean(self) -> Decimal:
        """Expected value of the rate: alpha / (alpha + beta)."""
        return _dec(self.alpha / (self.alpha + self.beta))

    def credible_interval(self, level: float = 0.95) -> tuple[Decimal, Decimal]:
        """Central interval containing the true rate with `level` probability.
        Wide interval = we know little; narrow = evidence has accumulated."""
        lo, hi = stats.beta.interval(level, self.alpha, self.beta)
        return _dec(lo), _dec(hi)

    def probability_above(self, threshold: Decimal) -> Decimal:
        """P(true rate > threshold). E.g. threshold = break-even CVR:
        this IS 'probability the creative is profitable per click'."""
        p = stats.beta.sf(float(threshold), self.alpha, self.beta)  # sf = 1 - CDF
        return _dec(p)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Draw n plausible rates from the posterior (for simulations)."""
        return rng.beta(self.alpha, self.beta, size=n)


def posterior(prior_alpha: float, prior_beta: float, successes: int, trials: int) -> BetaPosterior:
    """The conjugate update: add successes to alpha, failures to beta."""
    if prior_alpha <= 0 or prior_beta <= 0:
        raise InvalidInputError("prior alpha and beta must be > 0")
    if trials < 0 or successes < 0 or successes > trials:
        raise InvalidInputError(f"need 0 <= successes <= trials, got {successes}/{trials}")
    return BetaPosterior(prior_alpha + successes, prior_beta + (trials - successes))


def probability_a_beats_b(a: BetaPosterior, b: BetaPosterior,
                          n_samples: int = 100_000, seed: int = 0) -> Decimal:
    """P(rate A > rate B) — 'is creative A truly better than B?'

    Method: draw many plausible (a, b) rate pairs from both posteriors and
    count how often A wins. Fixed seed => reproducible. With overlapping
    posteriors this lands near 0.5 ('too close to call'), which is exactly
    the honesty that stops premature winner-picking."""
    rng = np.random.default_rng(seed)
    wins = np.mean(a.sample(n_samples, rng) > b.sample(n_samples, rng))
    return _dec(float(wins))