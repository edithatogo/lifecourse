# Modernization Decision Register

## Purpose
This file keeps the first modernization track focused. It records which proposed tools are part of the foundation now, which are deferred to follow-up work, and which are not justified for this repository at present.

## Decision Principles
- Prefer tools that strengthen reproducibility, packaging, validation, and CI enforcement immediately.
- Do not replace stable execution or data engines without profiling or workflow evidence.
- Avoid overlapping tools unless their boundaries are explicit.
- Defer speculative stack changes rather than letting them bloat the foundation track.

## Adopt In This Track
- `uv`
  - Reason: directly improves environment and packaging workflows.
- `pyproject.toml` as the tooling authority
  - Reason: centralizes package and tool configuration.
- strict `ruff`
  - Reason: high-value linting and formatting gate with low conceptual overhead.
- strict `basedpyright`
  - Reason: improves type-safety enforcement for maintained code.
- `pydantic v2`
  - Reason: strong fit for explicit configuration boundaries.
- `pandera`
  - Reason: strong fit for high-value tabular validation boundaries.
- `Hypothesis` where it materially improves validation-boundary confidence
  - Reason: better fit for property-based boundary testing than example-only tests.

## Resolved During This Track
- `nox` or `tox`
  - Decision: defer both for this foundation track.
  - Reason: documented `uv` commands and explicit GitHub Actions jobs are sufficient
    for the current workflow; adding a session runner would increase scope without
    removing a concrete bottleneck.
- build smoke tooling
  - Decision: use the simplest reproducible build smoke path.
  - Reason: `tests/test_packaging_smoke.py` validates wheel and sdist builds, and
    CI runs `uv build`.
- version-source strategy
  - Decision: keep package version ownership in `[project]` metadata in
    `pyproject.toml`.
  - Reason: this makes the source of truth explicit without adopting release
    automation before the repository needs it.

## Explicitly Deferred To Follow-Up Tracks
- `polars`
- `plotnine`
- `JAX`
- `XLA`
- `BlackJAX`
- `Optuna`
- `Hydra`
- `DVC`
- `Renovate`
- `mutmut`
- publish automation for TestPyPI, PyPI, and Conda
- structured logging overhaul

Reason: each of these may be valuable, but none is required to establish the packaging, validation, and CI baseline for this first track.

## Not Recommended For The Current Foundation
- `Pachyderm`
  - Reason: too large a systems commitment for the current repository shape.
- `Buildbot`
  - Reason: GitHub Actions already covers the current CI need.
- `Vaex`
  - Reason: weak fit while `pandas` to `polars` migration is still undecided.
- `loguru`
  - Reason: standard `logging` should remain the default unless a concrete ergonomics gap appears.
- `pyjanitor`
  - Reason: useful only if a specific data-cleaning pain point emerges; not foundation-critical.

## Follow-Up Candidates After This Track
- a data-engine evaluation track for `pandas`, `polars`, and `dask`
- a numerical-performance track for `JAX`-class experimentation
- a release and distribution track for TestPyPI, PyPI, and Conda
- a reproducibility and artifact-lineage track for `DVC`
- a maintenance automation track for `Renovate`
