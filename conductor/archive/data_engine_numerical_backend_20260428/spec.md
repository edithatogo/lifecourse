# Data Engine and Numerical Backend Evaluation

## Overview
Establish the next modernization step toward `polars` and `JAX`/`XLA` without
destabilizing the maintained microsimulation workflow. The track should make
backend direction explicit, add executable decision support, and introduce a
small, safe implementation slice that can be expanded by later migration tracks.

The current maintained runtime still depends on `numpy`, `pandas`, and `dask`.
This track must not replace the simulation engine wholesale. It should instead
identify where `polars` and JAX-class tooling fit, expose optional backend
capabilities, and preserve deterministic results and CI reliability.

## Goals
- Provide a documented and tested backend-evaluation surface for tabular and
  numerical workloads.
- Add optional dependency groups for `polars` and JAX-class experimentation
  without forcing all users to install heavyweight acceleration packages.
- Implement an initial numerical backend utility that uses `numpy` by default
  and can use JAX when explicitly requested and installed.
- Keep `dask` as the current orchestration backend until profiling evidence
  supports reducing or replacing it.
- Record the next migration decisions and outstanding work clearly.

## Functional Requirements
- The repository must expose a backend-readiness API that reports availability
  for `polars`, `jax`, `jaxlib`, `blackjax`, `dask`, `pandas`, and `numpy`.
- The repository must expose deterministic recommendation helpers for:
  - tabular workloads: `pandas`, `polars`, or `dask`;
  - numerical workloads: `numpy`, `jax`, or `dask`.
- The repository must expose a small numerical helper for net monetary benefit
  style vector calculations with a `numpy` default and optional JAX execution.
- Optional backend dependencies must be declared in `pyproject.toml` so users can
  install them deliberately.
- Tests must cover recommendation behavior, optional dependency detection, and
  numerical equivalence between the default path and a simulated JAX path.

## Non-Functional Requirements
- Existing CLI and simulation behavior must remain unchanged.
- The default install path must remain practical for research contributors who
  do not need JAX-class acceleration.
- The new code must pass the current formatting, linting, typing, test, and
  coverage gates.
- Optional imports must fail clearly and predictably when a requested backend is
  not installed.

## Out of Scope
- Full migration from `pandas` to `polars`.
- Replacement of `dask` orchestration.
- Rewriting the simulation engine around JAX arrays.
- GPU-specific CI, CUDA installation, or XLA benchmarking in this track.
- Replacing plotting or reporting libraries.

## Acceptance Criteria
- `uv run pytest` passes with the configured coverage gate.
- The backend-readiness API can be used without installing optional acceleration
  packages.
- Requesting JAX execution when JAX is absent raises a clear backend error.
- A simulated JAX module can exercise the JAX code path in tests without making
  JAX mandatory in CI.
- `conductor/tech-stack.md` reflects the new status: optional backend evaluation
  infrastructure exists, while production execution remains `numpy`/`pandas`/
  `dask`.
