# Track Specification

## Track Summary
Establish a safe modernization baseline for the existing `lifecourse` repository by making package and tool configuration explicit, strengthening automated quality gates, and adding typed validation boundaries without disrupting current research workflows.

## Problem Statement
The repository currently works, but its packaging, environment management, linting, typing, coverage enforcement, and validation boundaries are only partially formalized. That makes later migrations to a more modern stack harder to execute safely because there is no strong baseline for reproducibility, static analysis, CI enforcement, or schema validation.

## Objectives
- Make `uv` and `pyproject.toml` the authoritative packaging and tooling interface for day-to-day development.
- Preserve the existing package and CLI behavior while the tooling authority changes.
- Enforce strict `ruff` and `basedpyright` checks in local workflows and CI.
- Raise automated coverage enforcement above 90 percent for the maintained package.
- Introduce `pydantic v2` models for configuration boundaries and `pandera` schemas for selected tabular interfaces.
- Document the implemented modernization baseline and the migration decisions that remain open.

## In Scope
- Packaging and environment workflow updates centered on `uv` and `pyproject.toml`.
- Tool configuration for linting, typing, and testing.
- CI updates required to enforce the new quality gates.
- Configuration validation with `pydantic v2`.
- Dataframe boundary validation with `pandera` at high-value ingress or egress points.
- Documentation updates needed to keep contributor workflows accurate.

## Out of Scope
- Full migration from `pandas` to `polars`.
- Replacement of `dask` with `JAX`, `XLA`, `BlackJAX`, or another execution model.
- Full plotting migration from `matplotlib`/`seaborn` to `plotnine`.
- Data and artifact lineage systems such as `DVC` or `Pachyderm`.
- Release publishing automation to TestPyPI, PyPI, or Conda.
- Broad architectural rewrites unrelated to the modernization foundation.

## Current Constraints
- The repository is a brownfield Python project and must keep current simulation and CLI workflows working during the migration.
- The workflow requires test-first implementation, explicit coverage verification, and phase checkpoint tasks.
- The project should remain understandable to research collaborators, not just tooling specialists.
- Historical notebooks and drafts are not the source of truth and should not drive implementation decisions.

## Functional Requirements
- A developer can install, sync, and run the project using the documented `uv`-based workflow.
- `pyproject.toml` becomes the authoritative home for package metadata and tool configuration.
- CLI entry points remain available and documented after the packaging migration.
- CI enforces strict `ruff`, strict `basedpyright`, and a coverage gate above 90 percent.
- Configuration loading fails clearly and predictably when invalid input violates `pydantic v2` models.
- Selected dataframe boundaries fail clearly and predictably when invalid tabular data violates `pandera` schemas.
- Documentation explains the supported commands, gates, and validation boundaries introduced by this track.

## Acceptance Criteria
- Running the documented environment setup and test commands works with the new `uv`-centered workflow.
- `pyproject.toml` contains the authoritative configuration for the selected tooling, with compatibility choices documented where necessary.
- The main CI workflow blocks merges when linting, typing, or coverage requirements fail.
- Coverage enforcement is configured above 90 percent and the codebase passes the new threshold.
- Configuration and tabular validation tests exist and pass.
- Existing maintained CLI entry points still execute successfully.
- README and contributor-facing docs reflect the implemented toolchain rather than the legacy baseline.

## Risks and Mitigations
- Risk: tool migration introduces friction for contributors who still rely on the current workflow.
  Mitigation: document compatibility expectations clearly and migrate incrementally.
- Risk: stricter linting and typing expose widespread issues that delay delivery.
  Mitigation: scope the cleanup to the maintained package and sequence fixes by highest-value gates first.
- Risk: schema validation introduces runtime overhead or rigid boundaries in exploratory code paths.
  Mitigation: apply validation first at high-value boundaries and document where it is intentionally enforced.
- Risk: coverage goals drive low-value tests.
  Mitigation: prioritize tests that protect configuration loading, CLI behavior, and analytical core behavior.

## Dependencies
- Existing tests and CLI entry points in the maintained package.
- CI workflow definitions in `.github/workflows/`.
- Current configuration loaders, scenario definitions, and tabular data paths in `src/lifecourse/` and `config/`.

## Done Definition
This track is complete when the repository has an implemented, documented, and CI-enforced modernization foundation that supports future migrations without ambiguity about package management, tooling gates, or validation boundaries.
