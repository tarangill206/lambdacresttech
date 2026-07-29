"""
errors.py — the package's named failure modes.

WHY: "refuse loudly rather than guess" is a design rule. When input is
unsafe we raise a SPECIFIC error naming the problem, so Java (and you,
debugging) knows exactly what was wrong. A generic ValueError tells you
nothing; CurrencyMismatchError tells you everything.
All inherit CommerceMathError so callers can catch our errors as a family.
"""


class CommerceMathError(Exception):
    """Base class for every error this package raises."""


class CurrencyMismatchError(CommerceMathError):
    """Amounts in one calculation used different currencies."""


class InputQualityBlockedError(CommerceMathError):
    """Java stamped the input BLOCKED; we refuse to compute on bad data."""


class InsufficientDataError(CommerceMathError):
    """Not enough observations for the model to say anything honest."""


class InvalidInputError(CommerceMathError):
    """Input is structurally impossible (e.g. clicks > impressions)."""


class UnsupportedContractVersionError(CommerceMathError):
    """Request used a contract version this code doesn't speak."""