# ADR-002: Gate complete candidates and publish Gold atomically

Status: adopted for Step 0 implementation baseline; runtime work pending.

## Context

FR-020 promises last known-good serving, while ORCH-001 originally ended with
quality checks and metrics but no explicit publication boundary. NFR-009's 98%
check-pass target cannot override a failed critical check.

## Decision

Require 100% of critical checks, then publish all configured cities as a coherent
batch. Keep candidates invisible. Promote data and publication metadata in one
PostgreSQL transaction, serialize publishers, and reject stale live candidates.
Historical repair and daily rollups cannot reset hourly freshness. Persist
failure results even when promotion is skipped. Follow the publication and KPI
contracts in [DATA_CONTRACTS.md](../DATA_CONTRACTS.md).

## Alternatives and tradeoffs

- Updating live tables before tests is simpler but exposes invalid data; rejected.
- Per-city publication improves availability but requires separate versions and
  freshness semantics across every view; defer until evidence justifies it.
- A single aggregate quality percentage is concise but can hide critical defects;
  report severity-specific checks and keep the aggregate KPI separately.
- External deployment/feature-flag infrastructure is unnecessary here; PostgreSQL
  transactions and isolated candidates are sufficient for this scale.

## Consequences and validation

One bad city holds back all new serving data; prior valid Gold remains available.
Candidate storage, publication locking, and consistent dashboard reads are needed.
Test a missing city, critical failure despite 99% pass rate, interrupted promotion,
concurrent publishers, and first-run no-data behavior in Steps 5 and 8–11.
This extends ORCH-001 with `publish_gold` and clarifies FR-015, FR-020, and NFR-009.
