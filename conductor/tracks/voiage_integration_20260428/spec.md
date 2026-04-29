# `voiage` Integration

## Overview

Define and implement a narrow integration between `lifecourse` and
`edithatogo/voiage`. `lifecourse` remains the disease and policy
microsimulation package. `voiage` remains the Value of Information methods
library. The two should interoperate through net-benefit, parameter-sample, and
run-provenance artifacts rather than shared internal simulation objects.

## Functional Requirements

- Define a VOI artifact contract for PSA net benefits, strategy names,
  parameter samples, willingness-to-pay thresholds, population scaling, time
  horizon, discount rate, and provenance.
- Define how that VOI contract fits into the broader run-bundle interchange
  profile documented in `docs/interchange/model_interchange_strategy.md`.
- Align the VOI contract with the provisional HEOML v0.1 profile under
  `heoml/specs/v0.1/`.
- Add optional `voiage` integration behind an extra or adapter gate.
- Convert `lifecourse` PSA outputs into `voiage.ValueArray` and
  `voiage.ParameterSet` objects when `voiage` is installed.
- Support EVPI, EVPPI, EVSI, and ENBS through `voiage` without removing the
  internal fallback until parity is proven.
- Store `voiage` version, method settings, diagnostics, and result metadata in
  reproducible reporting bundles.
- Add pointers to the corresponding `voiage` track and docs so both repos stay
  aligned:
  - `/Users/doughnut/GitHub/voiage/conductor/tracks/lifecourse-integration-contract_20260429/`
  - `/Users/doughnut/GitHub/voiage/docs/integrations/lifecourse.md`
  - `/Users/doughnut/GitHub/voiage/specs/integrations/lifecourse/v1/`
- Document required upstream changes in `voiage`, including dependency extras,
  stable result schemas, and compatibility fixtures.

## Non-Functional Requirements

- Do not add `voiage` to core runtime dependencies.
- Keep integration optional and fail with clear installation guidance when
  `voiage` is unavailable.
- Avoid importing experimental `voiage` internals.
- Require numerical parity/tolerance tests before making `voiage` the default
  VOI backend.
- Keep dependency ownership and version compatibility explicit.

## Acceptance Criteria

- `docs/voiage_integration_strategy.md` documents project boundaries,
  dependency policy, integration contract, and promotion criteria.
- `docs/interchange/model_interchange_strategy.md` documents portable bundle
  formats and explains why pickle is not an interchange format.
- A small fixture can be exported from `lifecourse` and consumed by `voiage`.
- Optional adapter tests prove EVPI parity on a fixed fixture.
- The integration can be enabled without changing base `lifecourse` installs.
- The plan identifies concrete changes needed in both repositories.

## Out Of Scope

- Merging `voiage` into `lifecourse`.
- Making `voiage` a required dependency for base model execution.
- Promoting experimental `voiage` methods as production features before
  validation.
- Replacing all current `lifecourse` VOI code in the first increment.
