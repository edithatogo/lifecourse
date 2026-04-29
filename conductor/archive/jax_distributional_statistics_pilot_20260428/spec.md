# JAX Distributional Statistics Pilot

## Overview
Introduce the first analysis-level JAX dispatch hook by routing distributional
net-benefit vector calculations through the backend utility. This remains an
explicit opt-in path and does not rewrite the simulation engine.

## Goals
- Preserve default `numpy` behavior in distributional statistics.
- Allow callers to request `backend="jax"` for net-benefit vector calculations.
- Reuse the tested backend utility so missing JAX dependencies fail clearly.
- Keep the analysis return shape unchanged.

## Functional Requirements
- `calculate_distributional_statistics(psa_results)` must keep existing default
  behavior.
- `calculate_distributional_statistics(psa_results, backend="jax")` must route
  net-benefit vectors through `calculate_net_monetary_benefit`.
- Tests must verify both default behavior and explicit backend dispatch.

## Non-Functional Requirements
- JAX must remain optional.
- No simulation-engine internals may be rewritten in this track.
- Full validation must pass.

## Out of Scope
- JIT-compiling full PSA or simulation workflows.
- Replacing Dask orchestration.
- GPU-specific acceleration or benchmarking.

## Acceptance Criteria
- Focused tests pass for default and requested backend behavior.
- `uv run pytest` passes with the configured coverage gate.
