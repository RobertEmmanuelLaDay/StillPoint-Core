"""Temporal warrants: explicit authority to act.

Warrant is not claim. Claim is not warrant.
Authority must be time-bound and domain-scoped.
Scope(action) ≤ Scope(warrant).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class WarrantStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPLETED = "completed"
    SUPERSEDED = "superseded"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True)
class WarrantScope:
    domain: str
    action_class: str
    subjects: tuple[str, ...] = ()
    max_actions: int | None = None


@dataclass
class Warrant:
    warrant_id: str
    domain: str
    action_class: str
    subject: str
    target: str = ""
    claim_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    issuer: str = ""
    policy_basis: str = ""
    issued_at: str = field(default_factory=_utcnow)
    valid_from: str = field(default_factory=_utcnow)
    valid_to: str | None = None
    status: WarrantStatus = WarrantStatus.ACTIVE
    scope: dict[str, Any] = field(default_factory=dict)
    completion_condition: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    superseded_by: str | None = None
    revoked_reason: str = ""
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.warrant_id:
            object.__setattr__(self, "warrant_id", str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, WarrantStatus) else self.status
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Warrant":
        status = raw.get("status", "active")
        if isinstance(status, str):
            status = WarrantStatus(status) if status in WarrantStatus._value2member_map_ else WarrantStatus.ACTIVE
        return cls(
            warrant_id=raw["warrant_id"],
            domain=raw["domain"],
            action_class=raw["action_class"],
            subject=raw["subject"],
            target=raw.get("target", ""),
            claim_ids=list(raw.get("claim_ids") or []),
            evidence_ids=list(raw.get("evidence_ids") or []),
            issuer=raw.get("issuer", ""),
            policy_basis=raw.get("policy_basis", ""),
            issued_at=raw.get("issued_at") or _utcnow(),
            valid_from=raw.get("valid_from") or _utcnow(),
            valid_to=raw.get("valid_to"),
            status=status,
            scope=dict(raw.get("scope") or {}),
            completion_condition=raw.get("completion_condition", ""),
            provenance=dict(raw.get("provenance") or {}),
            created_at=raw.get("created_at") or _utcnow(),
            updated_at=raw.get("updated_at") or _utcnow(),
            superseded_by=raw.get("superseded_by"),
            revoked_reason=raw.get("revoked_reason", ""),
            completed_at=raw.get("completed_at"),
        )

    def is_active(self, now_iso: str | None = None) -> bool:
        if self.status != WarrantStatus.ACTIVE:
            return False
        now = _parse(now_iso) if now_iso else datetime.now(timezone.utc)
        start = _parse(self.valid_from)
        if start and now < start:
            return False
        if self.valid_to:
            end = _parse(self.valid_to)
            if end and now >= end:
                return False
        return True

    def permits(self, action_type: str, domain: str, subject: str, now_iso: str | None = None) -> bool:
        if not self.is_active(now_iso):
            return False
        if self.domain != domain and self.domain != "general":
            return False
        if self.action_class != action_type and self.action_class != "*":
            return False
        if self.subject and self.subject != subject and self.subject != "*":
            return False
        return True

    def expire(self) -> None:
        if self.status == WarrantStatus.ACTIVE:
            self.status = WarrantStatus.EXPIRED
            self.updated_at = _utcnow()

    def revoke(self, reason: str = "") -> None:
        self.status = WarrantStatus.REVOKED
        self.revoked_reason = reason
        self.updated_at = _utcnow()

    def complete(self) -> None:
        self.status = WarrantStatus.COMPLETED
        self.completed_at = _utcnow()
        self.updated_at = _utcnow()

    def require_review(self, reason: str = "") -> None:
        self.status = WarrantStatus.REVIEW_REQUIRED
        self.updated_at = _utcnow()
        if reason:
            self.provenance["review_reason"] = reason

    def supersede(self, by_warrant_id: str) -> None:
        self.status = WarrantStatus.SUPERSEDED
        self.superseded_by = by_warrant_id
        self.updated_at = _utcnow()


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
