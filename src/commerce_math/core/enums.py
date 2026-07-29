"""
enums.py — the controlled vocabulary of the whole package.

WHY: strings like "pass"/"PASS"/"ok" drifting across modules cause silent
bugs. Enums make every allowed value explicit and typo-proof: if code says
QualityStatus.PASSS it crashes immediately instead of misbehaving quietly.
These names also appear in the Java<->Python contracts, so this file is
part of the shared language, not an implementation detail.
"""

from enum import Enum


class QualityStatus(str, Enum):
    """Java's verdict on input data. BLOCKED means we refuse to calculate."""
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    BLOCKED = "BLOCKED"


class ValueSource(str, Enum):
    """Where a number came from — actual fact vs claim vs assumption.
    Keeping these separate is the core integrity rule of the system."""
    ACTUAL = "ACTUAL"                        # confirmed financial fact
    ATTRIBUTION_CLAIM = "ATTRIBUTION_CLAIM"  # platform-reported, not truth
    APPROVED_ASSUMPTION = "APPROVED_ASSUMPTION"
    SCENARIO_OVERRIDE = "SCENARIO_OVERRIDE"
    MODEL_DEFAULT = "MODEL_DEFAULT"


class AdAction(str, Enum):
    """The only recommendation states the policy layer may emit."""
    LEARNING = "LEARNING"   # collecting evidence; scaling not allowed yet
    SCALE = "SCALE"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    REFRESH = "REFRESH"     # creative fatigued; swap variant
    REWORK = "REWORK"       # concept salvageable, execution isn't
    KILL = "KILL"


class Platform(str, Enum):
    """Ad platforms we model. Math is shared; this tags rows so policy and
    diagnostics can apply platform-specific rules (priors, learning phases)."""
    META = "META"
    TIKTOK = "TIKTOK"
    GOOGLE = "GOOGLE"
    AMAZON = "AMAZON"