"""Transparent, rule-based risk model.

This is deliberately NOT an "AI-generated risk score". Every point is
attributable to an observable property of the manifest, and the breakdown is
always shown. A human (or an auditor) can reproduce the number by hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .manifest import DataClass, Manifest, ToolAccess

# Per-property weights. Kept in one place so the model is auditable and tunable.
TOOL_WEIGHTS: dict[ToolAccess, int] = {
    ToolAccess.READ: 1,
    ToolAccess.EXECUTE: 3,
    ToolAccess.WRITE: 3,
    ToolAccess.EXTERNAL_SEND: 3,
    ToolAccess.DELETE: 5,
    ToolAccess.FINANCIAL: 5,
    # Unknown scores like a write: we refuse to assume an unrecognised server
    # is harmless, but we do not inflate it to "delete" either. The report
    # always names what was unknown so a human can classify it.
    ToolAccess.UNKNOWN: 3,
}

DATA_WEIGHTS: dict[DataClass, int] = {
    DataClass.PUBLIC: 0,
    DataClass.INTERNAL: 1,
    DataClass.PII: 3,
    DataClass.HEALTH: 4,
    DataClass.FINANCIAL: 4,
    DataClass.CREDENTIAL: 5,
}

PRODUCTION_WEIGHT = 5
IRREVERSIBLE_WEIGHT = 5
# A non-read, unscoped tool the host will run without asking a human (e.g.
# Claude Code `allow: Bash(*)`). The capability was already scored; this is the
# cost of removing the person from the loop for it. A scoped grant
# (`Bash(npm test:*)`) is not penalised: a person chose that scope.
AUTO_APPROVAL_WEIGHT = 2
DELEGATION_WEIGHT = 3
# Autonomy adds risk above "act with approval" (L2).
AUTONOMY_WEIGHT_PER_LEVEL = 2

# Score thresholds -> band. Cumulative, transparent.
BANDS = [
    (0, "LOW"),
    (8, "MEDIUM"),
    (16, "HIGH"),
    (28, "CRITICAL"),
]


@dataclass
class RiskFactor:
    """One line of the risk breakdown: what added points and why."""

    points: int
    reason: str


@dataclass
class RiskProfile:
    score: int = 0
    factors: list[RiskFactor] = field(default_factory=list)
    systems: set[str] = field(default_factory=set)
    data_classes: set[str] = field(default_factory=set)
    write_capabilities: list[str] = field(default_factory=list)
    external_side_effects: list[str] = field(default_factory=list)
    irreversible_actions: list[str] = field(default_factory=list)
    unknown_capabilities: list[str] = field(default_factory=list)
    auto_approved: list[str] = field(default_factory=list)

    @property
    def band(self) -> str:
        band = "LOW"
        for threshold, name in BANDS:
            if self.score >= threshold:
                band = name
        return band

    def add(self, points: int, reason: str) -> None:
        if points:
            self.score += points
            self.factors.append(RiskFactor(points=points, reason=reason))


def assess(manifest: Manifest) -> RiskProfile:
    """Compute the transparent risk profile of an agent manifest."""
    p = RiskProfile()

    for tool in manifest.tools:
        weight = TOOL_WEIGHTS.get(tool.type, 1)
        p.add(weight, f"tool '{tool.name}' ({tool.type.value})")
        if tool.system:
            p.systems.add(tool.system)
        if tool.type in (ToolAccess.WRITE, ToolAccess.DELETE):
            p.write_capabilities.append(tool.name)
        if tool.type == ToolAccess.EXTERNAL_SEND:
            p.external_side_effects.append(tool.name)
        if tool.type == ToolAccess.UNKNOWN:
            p.unknown_capabilities.append(tool.name)
        if tool.production:
            p.add(PRODUCTION_WEIGHT, f"tool '{tool.name}' acts on production")
        if tool.irreversible:
            p.add(IRREVERSIBLE_WEIGHT, f"tool '{tool.name}' is irreversible")
            p.irreversible_actions.append(tool.name)
        if tool.approval == "auto" and tool.type is not ToolAccess.READ and not tool.scoped:
            p.add(AUTO_APPROVAL_WEIGHT, f"tool '{tool.name}' runs without human approval")
            p.auto_approved.append(tool.name)

    for source in manifest.data:
        weight = DATA_WEIGHTS.get(source.type, 1)
        p.add(weight, f"data access: {source.type.value}")
        p.data_classes.add(source.type.value)
        p.systems.update(source.systems)

    if manifest.delegation.enabled:
        p.add(DELEGATION_WEIGHT, "delegation enabled")

    if manifest.autonomy > 2:
        extra = (manifest.autonomy - 2) * AUTONOMY_WEIGHT_PER_LEVEL
        p.add(extra, f"autonomy level L{manifest.autonomy} (above L2 approval)")

    return p
