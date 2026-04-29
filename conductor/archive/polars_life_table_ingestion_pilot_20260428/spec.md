# Polars Life Table Ingestion Pilot

## Overview
Extend the opt-in Polars ingestion approach to the New Zealand life-table hazard
loader. This gives the project a second real Polars-backed data boundary while
preserving the public pandas/numpy-compatible return contract.

## Goals
- Add an explicit backend selector to `load_nz_life_table_hazards`.
- Preserve current default pandas behavior.
- Add a Polars-backed CSV normalization path that returns the existing
  `dict[str, np.ndarray]` shape.
- Fail clearly when Polars is requested but unavailable.

## Functional Requirements
- `load_nz_life_table_hazards()` must keep current behavior.
- `load_nz_life_table_hazards(backend="pandas")` must be equivalent to default.
- `load_nz_life_table_hazards(backend="polars")` must use the optional Polars
  path and return sex-keyed hazard arrays sorted by age.
- Invalid backend names must raise `ValueError`.
- Missing Polars must raise `BackendUnavailableError`.

## Non-Functional Requirements
- Polars must remain optional.
- Existing callers must not need code changes.
- Tests must not require Polars to be installed.
- Full validation must pass.

## Out of Scope
- Returning Polars objects from public APIs.
- Replacing Dask or simulation internals.
- Benchmarking full-scale ingestion performance.

## Acceptance Criteria
- Focused life-table loader tests pass for pandas, simulated Polars, missing
  Polars, and invalid backend behavior.
- `uv run pytest` passes with the configured coverage gate.
