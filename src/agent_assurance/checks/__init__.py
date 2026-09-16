"""Check registry.

New checks register here. The engine and CLI iterate over ALL_CHECKS, so adding
a check (governance-diff, evidence-contract, action-trust...) is a one-line
change plus the check module itself.
"""

from __future__ import annotations

from .base import Check, CheckResult, StandardRef, Status
from .blast_radius import BlastRadiusCheck

ALL_CHECKS: dict[str, type[Check]] = {
    BlastRadiusCheck.check_id: BlastRadiusCheck,
}

# Friendly names -> check id, for `agent-assurance check blast-radius`.
CHECK_ALIASES: dict[str, str] = {
    "blast-radius": BlastRadiusCheck.check_id,
}

__all__ = [
    "ALL_CHECKS",
    "CHECK_ALIASES",
    "BlastRadiusCheck",
    "Check",
    "CheckResult",
    "StandardRef",
    "Status",
]
