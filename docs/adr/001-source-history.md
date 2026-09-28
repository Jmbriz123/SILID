# ADR-001: Preserve raw artifacts and model retrieval history honestly

Status: adopted for Step 0 implementation baseline; runtime work pending.

## Context

The specification chooses MinIO Bronze, with an optional PostgreSQL mirror. The
prototype stores parsed JSONB only. FR-014 requires forecast issue time, but the
standard MVP API does not document one. Observation wording also obscures that
current conditions are model-derived. Forecast history and score history need
identities beyond the target weather hour.

## Decision

Follow [data contracts](../DATA_CONTRACTS.md): authoritative response bodies and
metadata in MinIO; disposable parsed PostgreSQL staging; separate collection,
attempt, artifact, forecast snapshot, and publication identities. Retain nullable
provider issue time with availability status. Never call fetch time issue time.
Keep the observation fact name with explicit model-derived semantics. Preserve
forecast/score history and expose a current score projection at the original grain.

## Alternatives and tradeoffs

- JSONB-only Bronze is simpler but loses original representation and malformed
  bodies; rejected as authoritative storage. Existing legacy rows remain intact.
- Treating retrieval as issuance avoids nulls but invents source information;
  rejected. The limitation means MVP cannot measure true provider issue-to-target lead time.
- Adding a station or single-model-run source now could supply different semantics,
  but expands scope; defer until after the batch MVP.
- Overwriting forecasts/scores is easy to query but destroys history; retain
  additional rows and use explicit current projections instead.

## Consequences and validation

Object/manifest reconciliation is required; no cross-system exactly-once claim.
Storage grows with collection history. Replays preserve source timestamps and
formula versions. Step 3 tests interrupted writes; Steps 5–7 test reruns, repeated
target hours, and formula changes. Updates affect FR-003, FR-011, FR-014, FR-018,
DQ-004, and DM-005 through DM-008 without changing their identifiers.

Source semantics checked against [Open-Meteo docs](https://open-meteo.com/en/docs).
