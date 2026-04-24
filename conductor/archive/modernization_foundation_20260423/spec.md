# Track Specification

## Track Summary
Establish a safe modernization baseline for the existing `lifecourse` repository by making package and tool configuration explicit, strengthening automated quality gates, and adding typed validation boundaries without disrupting current research workflows.

## Problem Statement
The repository currently works, but its packaging, environment management, linting, typing, coverage enforcement, and validation boundaries are only partially formalized. That makes later migrations to a more modern stack harder to execute safely because there is no strong baseline for reproducibility, static analysis, CI enforcement, or schema validation.

## Objectives
- Make `uv` and `pyproject.toml` the authoritative packaging and tooling interface for day-to-day development.
- Preserve the existing package and CLI behavior while the tooling authority changes.
- Make package build and install behavior explicit, reproducible, and smoke-tested.
- Enforce strict `ruff` and `basedpyright` checks in local workflows and CI.
- Raise automated coverage enforcement above 90 percent for the maintained package.
- Introduce `pydantic v2` models for configuration boundaries and `pandera` schemas for selected tabular interfaces.
- Add high-value property-based tests for the new validation boundaries.
- Create an explicit modernization decision register so requested tools are classified as adopt now, defer, or reject for this track.
- Document the implemented modernization baseline and the migration decisions that remain open.

## In Scope
- Packaging and environment workflow updates centered on `uv` and `pyproject.toml`.
- Build and install smoke validation for the maintained package and CLI entry points.
- Version-source clarification required to make packaging behavior predictable.
- Tool configuration for linting, typing, and testing.
- CI updates required to enforce the new quality gates.
- Configuration validation with `pydantic v2`.
- Dataframe boundary validation with `pandera` at high-value ingress or egress points.
- Property-based tests for configuration and schema validation behavior where they add confidence.
- A written decision register that classifies proposed modernization tools by implementation status for this track.
- Documentation updates needed to keep contributor workflows accurate.

## Out of Scope
- Full migration from `pandas` to `polars`.
- Replacement of `dask` with `JAX`, `XLA`, `BlackJAX`, or another execution model.
- Full plotting migration from `matplotlib`/`seaborn` to `plotnine`.
- Data and artifact lineage systems such as `DVC` or `Pachyderm`.
- Release publishing automation to TestPyPI, PyPI, or Conda.
- Mutation testing, large-scale experiment orchestration, and dependency automation beyond what is needed to define follow-up work.
- Logging-stack replacement, session-runner expansion, or versioning automation unless required to support the foundation directly.
- Broad architectural rewrites unrelated to the modernization foundation.

## Current Constraints
- The repository is a brownfield Python project and must keep current simulation and CLI workflows working during the migration.
- The workflow requires test-first implementation, explicit coverage verification, and phase checkpoint tasks.
- The project should remain understandable to research collaborators, not just tooling specialists.
- Historical notebooks and drafts are not the source of truth and should not drive implementation decisions.
- This track must avoid tool sprawl: it should establish a foundation, not attempt every modernization idea at once.

## Functional Requirements
- A developer can install, sync, and run the project using the documented `uv`-based workflow.
- `pyproject.toml` becomes the authoritative home for package metadata and tool configuration.
- The package can be built and installed through a documented smoke path, and the version source is explicit.
- CLI entry points remain available and documented after the packaging migration.
- CI enforces strict `ruff`, strict `basedpyright`, and a coverage gate above 90 percent.
- Configuration loading fails clearly and predictably when invalid input violates `pydantic v2` models.
- Selected dataframe boundaries fail clearly and predictably when invalid tabular data violates `pandera` schemas.
- Property-based tests protect the most important validation boundaries.
- The track includes a decision register that records which requested tools are implemented now, deferred, or excluded from the foundation.
- Documentation explains the supported commands, gates, and validation boundaries introduced by this track.

## Acceptance Criteria
- Running the documented environment setup and test commands works with the new `uv`-centered workflow.
- `pyproject.toml` contains the authoritative configuration for the selected tooling, with compatibility choices documented where necessary.
- A documented build/install smoke path succeeds for the maintained package, and the version source of truth is unambiguous.
- The main CI workflow blocks merges when linting, typing, or coverage requirements fail.
- Coverage enforcement is configured above 90 percent for the maintained package and the codebase passes the new threshold.
- Configuration and tabular validation tests exist and pass, including property-based tests where they add boundary confidence.
- Existing maintained CLI entry points still execute successfully.
- A committed decision register classifies proposed tools into adopt now, defer, or reject for this track.
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
- Risk: the track expands into too many unrelated tool adoptions and stalls.
  Mitigation: require explicit decisions in the decision register and defer non-foundational tools to follow-up tracks.

## Dependencies
- Existing tests and CLI entry points in the maintained package.
- CI workflow definitions in `.github/workflows/`.
- Current configuration loaders, scenario definitions, and tabular data paths in `src/lifecourse/` and `config/`.
- The approved technology direction in `conductor/tech-stack.md`, especially the open evaluation items and near-term sequence.

## Done Definition
This track is complete when the repository has an implemented, documented, and CI-enforced modernization foundation that supports future migrations without ambiguity about package management, tooling gates, or validation boundaries.
