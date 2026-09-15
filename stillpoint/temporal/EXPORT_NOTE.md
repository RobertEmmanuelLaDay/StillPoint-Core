# StillPoint Core Engineering Export

**Repository:** https://github.com/RobertEmmanuelLaDay/StillPoint-Core

**Version:** 0.2.0a1  
**Milestone:** temporal-authority-layer  
**Schema:** 5  
**Tests:** 209 full suite / 37 temporal focused  

## What is in this repo

This is the StillPoint Core Engineering build of the temporal authority / continuing evidence layer.

Core package path: `stillpoint/temporal/`

- Claim / ClaimStatus / ClaimDomain
- Warrant / WarrantStatus
- EvidenceEvent / EvidenceKind
- ClaimToWarrantFirewall, PredictionFirewall, DomainContainment
- ReevaluationTrigger, ReleaseRecord
- Migration 005

## Full tree note

The complete StillPoint Core source (prior RC + temporal layer + all tests) was developed on branch `feature/temporal-authority-layer` against the upstream StillPoint- checkout.

To obtain the complete tree including all prior modules (runtime, authority, adapters, eval corpora, full test suite):

1. Clone upstream: `git clone https://github.com/RobertEmmanuelLaDay/StillPoint-.git`
2. Apply temporal layer from this repo's `stillpoint/temporal/`, `migrations/005_temporal_authority.sql`, and related db methods / tests.

Or contact StillPoint Core Engineering for the full local feature-branch archive.

## Authority

Robert Emmanuel LaDay — sole human CEO and final authority.
Authorship ≠ epistemic sovereignty.
