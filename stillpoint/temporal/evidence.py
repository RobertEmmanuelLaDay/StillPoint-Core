"""Continuing evidence ingress.

Later evidence can enter after an earlier claim or decision.
A previous successful model must not close the evidence channel.
New evidence may support, weaken, contradict, supersede, or trigger review
while preserving historical records. Saturday does not become a lie because Sunday arrives.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvidenceKind(str, Enum):
    OBSERVATION = "observation"
    DOCUMENT = "document"
    MODEL_OUTPUT = "model_output"
    HUMAN_STATEMENT = "human_statement"
    SYSTEM_EVENT = "system_event"
    PREDICTION = "prediction"
    CORRECTION = "correction"
    OTHER = "other"


@dataclass
class EvidenceEvent:
    """Append-only evidence record. Never mutates prior evidence."""
    evidence_id: str
    kind: EvidenceKind
    subject: str
    content: Any
    source: str
    observed_at: str = ""
    recorded_at: str = field(default_factory=_utcnow)
    related_claim_ids: list[str] = field(default_factory=list)
    related_warrant_ids: list[str] = field(default_factory=list)
    sha256: str = ""
    confidence: float | None = None
    tags: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_id:
            object.__setattr__(self, "evidence_id", str(uuid4()))
        if not self.observed_at:
            object.__setattr__(self, "observed_at", self.recorded_at)
        if isinstance(self.kind, str):
            object.__setattr__(
                self,
                "kind",
                EvidenceKind(self.kind) if self.kind in EvidenceKind._value2member_map_ else EvidenceKind.OTHER,
            )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value if isinstance(self.kind, EvidenceKind) else self.kind
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "EvidenceEvent":
        kind = raw.get("kind", "other")
        if isinstance(kind, str):
            kind = EvidenceKind(kind) if kind in EvidenceKind._value2member_map_ else EvidenceKind.OTHER
        return cls(
            evidence_id=raw["evidence_id"],
            kind=kind,
            subject=raw["subject"],
            content=raw.get("content"),
            source=raw.get("source", ""),
            observed_at=raw.get("observed_at", ""),
            recorded_at=raw.get("recorded_at") or _utcnow(),
            related_claim_ids=list(raw.get("related_claim_ids") or []),
            related_warrant_ids=list(raw.get("related_warrant_ids") or []),
            sha256=raw.get("sha256", ""),
            confidence=raw.get("confidence"),
            tags=list(raw.get("tags") or []),
            provenance=dict(raw.get("provenance") or {}),
        )
