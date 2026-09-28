# ADR-003: Use dependency and learning gates with native retry policy

Status: adopted for Step 0 implementation baseline; runtime work pending.

## Context

The original plan groups work into four weeks and introduces incremental behavior,
observability, and testing late. Its retry illustration promises 1/5/15-minute
waits while calling them exponential. These are avoidable sources of rework.

## Decision

Execute [delivery sequence](../REQUIREMENT_TRACEABILITY.md) Steps 0–12 in order,
one explicitly requested step at a time. Add component tests, run records, and
idempotency with the component. Use three extraction retries with native bounded
exponential backoff (one-minute base, fifteen-minute cap); exact delays are not a
contract. Verify scheduler behavior against the chosen runtime before Step 4.
Keep one transformation retry. Do not layer another HTTP retry loop.

## Alternatives and tradeoffs

- A four-week deadline provides predictability but conflicts with deliberate
  learning; retain milestone themes without promised dates.
- Deferring tests and identities gives quicker demos but risks schema rework;
  build them early and keep the final integration/soak phase.
- Custom exact 1/5/15 scheduling adds machinery without a product need; prefer
  native behavior and accept different actual delays.

## Consequences and validation

Completion requires evidence plus explanation, not elapsed time. Document branches
and atomic commits for each step; creating or publishing commits is a separate
user-directed action. Keep live historical catchup off; backfills replay stored
artifacts. Review requirement coverage now; test retries, missing runs, and daily
coverage gates in their implementation steps. ORCH-004 wording is amended rather
than silently ignored.
