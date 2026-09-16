"""Agent Assurance manifest models.

The manifest (`agent-assurance.yaml`, apiVersion `agent-assurance/v1`) is the
common representation every check consumes. It is the strategic asset: define it
once, and blast-radius / drift / evidence / action-trust all read the same shape.
"""

from __future__ import annotations

from enum import Enum

import yaml
from pydantic import BaseModel, Field, ValidationError

API_VERSION = "agent-assurance/v1"


class ToolAccess(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    EXTERNAL_SEND = "external_send"
    FINANCIAL = "financial"


class DataClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PII = "pii"
    FINANCIAL = "financial"
    CREDENTIAL = "credential"
    HEALTH = "health"


class Tool(BaseModel):
    name: str
    type: ToolAccess = ToolAccess.READ
    # Free-form target system this tool touches (e.g. "crm", "aws", "postgres").
    system: str | None = None
    # Marks the tool as acting on a production system (raises risk).
    production: bool = False
    # Marks the action as irreversible (raises risk, cannot be rolled back).
    irreversible: bool = False


class DataSource(BaseModel):
    type: DataClass = DataClass.INTERNAL
    systems: list[str] = Field(default_factory=list)


class ModelSpec(BaseModel):
    provider: str | None = None
    name: str | None = None


class FrameworkSpec(BaseModel):
    name: str | None = None
    version: str | None = None


class Delegation(BaseModel):
    enabled: bool = False
    # Optional: sub-agents this agent can delegate authority to.
    subagents: list[str] = Field(default_factory=list)


class AgentInfo(BaseModel):
    name: str
    version: str = "0.0.0"


class Manifest(BaseModel):
    """The agent-assurance/v1 manifest."""

    apiVersion: str = API_VERSION
    agent: AgentInfo
    framework: FrameworkSpec = Field(default_factory=FrameworkSpec)
    model: ModelSpec = Field(default_factory=ModelSpec)
    tools: list[Tool] = Field(default_factory=list)
    data: list[DataSource] = Field(default_factory=list)
    autonomy: int = Field(default=1, ge=0, le=5)
    delegation: Delegation = Field(default_factory=Delegation)
    policies: list[str] = Field(default_factory=list)

    @classmethod
    def from_file(cls, path: str) -> Manifest:
        with open(path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        return cls.load(raw, source=path)

    @classmethod
    def load(cls, raw: dict, source: str = "<memory>") -> Manifest:
        if not isinstance(raw, dict):
            raise ManifestError(f"{source}: manifest root must be a mapping")
        api = raw.get("apiVersion")
        if api != API_VERSION:
            raise ManifestError(
                f"{source}: unsupported apiVersion {api!r} (expected {API_VERSION!r})"
            )
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:  # normalize to our error type
            raise ManifestError(f"{source}: invalid manifest\n{exc}") from exc


class ManifestError(ValueError):
    """Raised when a manifest is missing, malformed, or the wrong apiVersion."""
