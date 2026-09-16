"""Blast Radius check (AA-001).

Answers the CISO question: "if this agent is compromised or misbehaves, how
much can it break?" It does NOT judge whether the agent is good — it measures
the potential impact surface, transparently, from the manifest alone.

Maps to OWASP Agentic Top 10 ASI08 (Cascading failures) and ASI03 (Identity &
privilege abuse). Adapted from OWASP APTS SC-020 (external action allowlist),
whose intent — bounding what an autonomous system can reach — transfers cleanly.
"""

from __future__ import annotations

from typing import ClassVar

from .. import risk
from ..manifest import Manifest
from .base import Check, CheckResult, StandardRef, Status

# Bands that warrant a gate. LOW/MEDIUM pass; HIGH -> review; CRITICAL -> fail.
REVIEW_BANDS = {"HIGH"}
FAIL_BANDS = {"CRITICAL"}


class BlastRadiusCheck(Check):
    check_id = "AA-001"
    title = "Blast Radius"
    standards: ClassVar[list[StandardRef]] = [
        StandardRef("OWASP-ASI", "ASI08", "maps"),
        StandardRef("OWASP-ASI", "ASI03", "maps"),
        StandardRef("OWASP-APTS", "APTS-SC-020", "adapted"),
    ]

    def run(self, manifest: Manifest) -> CheckResult:
        p = risk.assess(manifest)

        if p.band in FAIL_BANDS:
            status = Status.FAIL
        elif p.band in REVIEW_BANDS:
            status = Status.REVIEW
        else:
            status = Status.PASS

        details: list[str] = []
        if p.systems:
            details.append("Systems affected: " + ", ".join(sorted(p.systems)))
        if p.data_classes:
            details.append("Sensitive data: " + ", ".join(sorted(p.data_classes)))
        if p.write_capabilities:
            details.append("Write capabilities: " + ", ".join(p.write_capabilities))
        if p.external_side_effects:
            details.append(
                "External side effects: " + ", ".join(p.external_side_effects)
            )
        if p.irreversible_actions:
            details.append(
                "Irreversible actions: " + ", ".join(p.irreversible_actions)
            )
        details.append(f"Autonomy: L{manifest.autonomy}")
        details.append(f"Risk score: {p.score} ({p.band})")

        summary = f"Blast radius {p.band} (score {p.score})"

        return CheckResult(
            check_id=self.check_id,
            title=self.title,
            status=status,
            summary=summary,
            details=details,
            standards=self.standards,
            data={
                "score": p.score,
                "band": p.band,
                "systems": sorted(p.systems),
                "data_classes": sorted(p.data_classes),
                "write_capabilities": p.write_capabilities,
                "external_side_effects": p.external_side_effects,
                "irreversible_actions": p.irreversible_actions,
                "factors": [
                    {"points": f.points, "reason": f.reason} for f in p.factors
                ],
            },
        )
