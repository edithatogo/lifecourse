# Polars Population Ingestion Pilot

## Overview
Introduce the first production-adjacent `polars` pilot at a constrained tabular
ingestion boundary: New Zealand population distribution loading. The default
runtime must remain unchanged, but contributors should be able to opt into a
Polars-backed load path when the optional `tabular` extra is installed.

## Goals
- Add an explicit backend selector to `load_nz_population_distribution`.
- Preserve the existing default pandas behavior and return type.
- Add a Polars-backed ingestion path that performs the same normalization and
  validation before returning a pandas DataFrame.
- Fail clearly when `backend="polars"` is requested but Polars is not installed.

## Functional Requirements
- `load_nz_population_distribution()` must keep its current pandas behavior.
- `load_nz_population_distribution(backend="pandas")` must be equivalent to the
  default call.
- `load_nz_population_distribution(backend="polars")` must use the optional
  Polars path and return the same validated columns: `age`, `sex`, `count`.
- Invalid backend names must raise `ValueError`.
- Missing Polars must raise `BackendUnavailableError`.

## Non-Functional Requirements
- Existing callers must not need code changes.
- The Polars package must remain optional.
- Tests must not require Polars to be installed in the default CI environment.
- Full repository validation must still pass.

## Out of Scope
- Replacing all pandas ingestion code.
- Replacing Dask orchestration.
- Returning Polars DataFrames from public APIs.
- Benchmarking production-scale CSV performance in this track.

## Acceptance Criteria
- Focused data-loader tests cover default, explicit pandas, simulated Polars,
  missing Polars, and invalid backend behavior.
- `uv run pytest` passes with the configured coverage gate.
- Documentation records this as the first Polars pilot, not a completed
  data-engine migration.
