"""Durable temporal claim model.

A claim is information. It never carries implicit authorization to act.
Claims may be true at T1, superseded or not-current at T2, without rewriting history.
Unknown is not coerced to false (? ≠ 0).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ClaimStatus(str, Enum):
    """Small coherent vocabulary with runtime meaning."""
    ACTIVE = "active"
    HISTORICAL = "historical"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    REVIEW_REQUIRED = "review_required"


class ClaimDomain(str, Enum):
    """Domain containment. A true claim in one domain does not auto-migrate."""
    GENERAL = "general"
    MEDICAL = "medical"
    EMPLOYMENT = "employment"
    FINANCIAL = "financial"
    CRIMINAL = "criminal"
    RELIGIOUS = "religious"
    IDENTITY = "identity"
    OPERATIONAL = "operational"
    RISK = "risk"
    PREDICTION = "prediction"
    OTHER = "other"


@dataclass(frozen=True)
class EvidenceRef:
    """Reference to supporting or contradicting evidence. Provenance preserved."""
    evidence_id: str
    kind: str = "observation"
    note: str = ""
    sha256: str = ""
    observed_at: str = ""


@dataclass
class Claim:
    """Durable claim representation.

    claim_id is stable. History is append-only via supersession and status transitions.
    A claim object must never contain implicit ActionRequest authority.
    """
    claim_id: str
    subject: str
    predicate: str
    value: Any
    domain: ClaimDomain
    source: str
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    time_observed: str = ""
    time_asserted: str = ""
    effective_from: str | None = None
    effective_to: str | None = None
    confidence: float | None = None
    status: ClaimStatus = ClaimStatus.ACTIVE
    supersedes: str | None = None
    superseded_by: str | None = None
    review_conditions: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.claim_id:
            object.__setattr__(self, "claim_id", str(uuid4()))
        if not self.time_asserted:
            object.__setattr__(self, "time_asserted", self.created_at)
        if self.confidence is not None and not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError("confidence must be None or in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["domain"] = self.domain.value if isinstance(self.domain, ClaimDomain) else self.domain
        d["status"] = self.status.value if isinstance(self.status, ClaimStatus) else self.status
        d["evidence_refs"] = [asdict(e) if hasattr(e, "__dataclass_fields__") else e for e in self.evidence_refs]
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Claim":
        refs = [
            EvidenceRef(**r) if isinstance(r, dict) else r
            for r in (raw.get("evidence_refs") or [])
        ]
        domain = raw.get("domain", "general")
        if isinstance(domain, str):
            domain = ClaimDomain(domain) if domain in ClaimDomain._value2member_map_ else ClaimDomain.OTHER
        status = raw.get("status", "active")
        if isinstance(status, str):
            status = ClaimStatus(status) if status in ClaimStatus._value2member_map_ else ClaimStatus.ACTIVE
        return cls(
            claim_id=raw["claim_id"],
            subject=raw["subject"],
            predicate=raw["predicate"],
            value=raw.get("value"),
            domain=domain,
            source=raw.get("source", ""),
            evidence_refs=refs,
            time_observed=raw.get("time_observed", ""),
            time_asserted=raw.get("time_asserted", ""),
            effective_from=raw.get("effective_from"),
            effective_to=raw.get("effective_to"),
            confidence=raw.get("confidence"),
            status=status,
            supersedes=raw.get("supersedes"),
            superseded_by=raw.get("superseded_by"),
            review_conditions=list(raw.get("review_conditions") or []),
            provenance=dict(raw.get("provenance") or {}),
            created_at=raw.get("created_at") or _utcnow(),
            updated_at=raw.get("updated_at") or _utcnow(),
        )

    def is_current(self, now_iso: str | None = None) -> bool:
        if self.status != ClaimStatus.ACTIVE:
            return False
        now = _parse(now_iso) if now_iso else datetime.now(timezone.utc)
        if self.effective_from:
            start = _parse(self.effective_from)
            if start and now < start:
                return False
        if self.effective_to:
            end = _parse(self.effective_to)
            if end and now >= end:
                return False
        return True

    def mark_historical(self, reason: str = "") -> None:
        self.status = ClaimStatus.HISTORICAL
        self.updated_at = _utcnow()
        if reason:
            self.provenance["historical_reason"] = reason

    def mark_superseded(self, by_claim_id: str) -> None:
        self.status = ClaimStatus.SUPERSEDED
        self.superseded_by = by_claim_id
        self.updated_at = _utcnow()

    def mark_expired(self) -> None:
        self.status = ClaimStatus.EXPIRED
        self.updated_at = _utcnow()

    def mark_review_required(self, condition: str = "") -> None:
        self.status = ClaimStatus.REVIEW_REQUIRED
        self.updated_at = _utcnow()
        if condition and condition not in self.review_conditions:
            self.review_conditions.append(condition)


def _parse(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
