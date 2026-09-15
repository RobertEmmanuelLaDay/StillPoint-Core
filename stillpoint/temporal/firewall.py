"""Claim-to-warrant and prediction firewalls.

No claim, classification, prediction, confidence score, model output,
historical record, category membership, or risk score may silently
create ActionRequest authority.

Moving from KNOW to ACT requires an explicit warrant.
PREDICTION DOES NOT SELF-AUTHORIZE.
A higher probability does not automatically produce greater jurisdiction.
Scope(action) ≤ Scope(warrant).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .claims import Claim, ClaimStatus, ClaimDomain
from .warrants import Warrant, WarrantStatus


class TemporalAuthorityError(Exception):
    """Raised when a temporal authority invariant is violated."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"[{code}] {message}")


@dataclass
class ClaimToWarrantFirewall:
    """Structural separation of knowledge and authority."""

    def assert_claim_is_not_warrant(self, claim: Claim) -> None:
        if hasattr(claim, "action_class") or hasattr(claim, "issuer"):
            raise TemporalAuthorityError(
                "CLAIM_AS_WARRANT",
                "Claim objects must not carry action authorization fields",
            )

    def require_warrant_for_action(
        self,
        *,
        action_type: str,
        domain: str,
        subject: str,
        warrants: list[Warrant],
        now_iso: str | None = None,
    ) -> Warrant:
        for w in warrants:
            if w.permits(action_type, domain, subject, now_iso=now_iso):
                return w
        raise TemporalAuthorityError(
            "NO_ACTIVE_WARRANT",
            f"No active warrant authorizes action_type={action_type!r} domain={domain!r} subject={subject!r}",
        )

    def claim_cannot_create_action_authority(self, claim: Claim) -> None:
        if claim.status not in (
            ClaimStatus.ACTIVE, ClaimStatus.HISTORICAL, ClaimStatus.SUPERSEDED,
            ClaimStatus.EXPIRED, ClaimStatus.WITHDRAWN, ClaimStatus.REVIEW_REQUIRED,
        ):
            raise TemporalAuthorityError("UNKNOWN_CLAIM_STATUS", f"Unrecognized claim status {claim.status}")
        raise TemporalAuthorityError(
            "CLAIM_NOT_AUTHORITY",
            f"Claim {claim.claim_id} (domain={claim.domain.value}) is information only; "
            "it does not authorize any action. An explicit warrant is required.",
        )


@dataclass
class PredictionFirewall:
    """PREDICTION DOES NOT SELF-AUTHORIZE."""

    def assert_prediction_is_evidence_not_authority(
        self,
        *,
        prediction: Any,
        confidence: float | None,
        action_type: str | None = None,
    ) -> None:
        if confidence is not None and confidence >= 0.99:
            pass
        raise TemporalAuthorityError(
            "PREDICTION_NOT_AUTHORITY",
            f"Prediction (confidence={confidence}) is evidence only. "
            f"It cannot authorize action_type={action_type!r}. Explicit warrant required.",
        )

    def prediction_may_become_evidence(self, prediction: Any, confidence: float | None = None) -> dict[str, Any]:
        return {
            "kind": "prediction",
            "content": prediction,
            "confidence": confidence,
            "is_authority": False,
        }


@dataclass
class DomainContainment:
    """A true claim in domain A must not automatically migrate into unrelated domains."""

    SENSITIVE = {
        ClaimDomain.MEDICAL.value,
        ClaimDomain.CRIMINAL.value,
        ClaimDomain.FINANCIAL.value,
        ClaimDomain.RELIGIOUS.value,
        ClaimDomain.IDENTITY.value,
        ClaimDomain.RISK.value,
    }

    def assert_domain_compatible(
        self,
        claim_domain: str | ClaimDomain,
        warrant_domain: str,
        action_domain: str,
    ) -> None:
        cd = claim_domain.value if isinstance(claim_domain, ClaimDomain) else claim_domain
        if cd == action_domain or cd == "general" or warrant_domain == "general":
            return
        if cd in self.SENSITIVE and action_domain != cd:
            raise TemporalAuthorityError(
                "CROSS_DOMAIN_PROMOTION",
                f"Claim domain {cd!r} cannot authorize action in domain {action_domain!r} "
                f"without an explicit warrant covering that promotion (warrant_domain={warrant_domain!r}).",
            )

    def scope_action_leq_warrant(
        self,
        action_type: str,
        action_domain: str,
        warrant: Warrant,
    ) -> bool:
        return warrant.permits(action_type, action_domain, warrant.subject)
