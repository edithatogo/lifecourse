# Implementation Plan

Repair note, 2026-04-27: this archived plan was reconciled against the current
repository state and the implementation commits. The registry already marked
the track complete, but this file still had stale unchecked boxes. The completed
work is primarily evidenced by commit `6ca8853` (`feat(modernization): implement
foundation track`) and follow-up documentation cleanup in `250aca0`.

## Phase 1: Baseline Audit, Decisions, and Safety Net
- [x] Task: Audit the current packaging, CI, validation, and build surface `[6ca8853]`
    - [x] Review `pyproject.toml`, `requirements.txt`, CI workflows, version definitions, and CLI entry points
    - [x] Identify the highest-value configuration and tabular boundaries for early validation
    - [x] Record concrete migration success criteria and non-goals for this track
- [x] Task: Create a modernization decision register for requested tools `[5f2bc01]`
    - [x] Classify proposed tools into adopt now, defer, or reject for this track
    - [x] Record rationale for boundary decisions such as `nox` or `tox`, `logging` or `loguru`, and deferred data-engine or simulation-engine migrations
    - [x] Confirm the foundation track stays focused on packaging, gates, and validation rather than tool sprawl
- [x] Task: Establish failing checks for the modernization foundation `[6ca8853]`
    - [x] Write or update tests that cover configuration loading, CLI execution, build or install smoke behavior, and validation boundary behavior
    - [x] Add failing local or CI checks for linting, typing, and coverage expectations before implementation
    - [x] Confirm the new checks fail where the brownfield baseline does not yet meet the target
- [x] Task: Conductor - User Manual Verification 'Phase 1: Baseline Audit, Decisions, and Safety Net' (Protocol in workflow.md) `[reconciled-20260427]`

## Phase 2: Package, Build, and Environment Authority
- [x] Task: Migrate package and environment workflows to `uv` and `pyproject.toml` `[6ca8853]`
    - [x] Write failing install or smoke checks for the desired package workflow
    - [x] Move authoritative dependency and tool configuration into `pyproject.toml`
    - [x] Introduce the `uv` workflow and keep any necessary brownfield compatibility notes explicit
- [x] Task: Make build and version behavior explicit `[6ca8853]`
    - [x] Write failing smoke checks for building and installing the maintained package
    - [x] Make the package version source of truth explicit and documented
    - [x] Confirm the documented build path remains reproducible after the tooling migration
- [x] Task: Preserve supported CLI entry points during the tooling migration `[6ca8853]`
    - [x] Write failing tests for `lifecourse-cli` and `lifecourse-main` entry-point behavior
    - [x] Update packaging configuration so both entry points still resolve correctly
    - [x] Confirm documentation matches the implemented command surface
- [x] Task: Conductor - User Manual Verification 'Phase 2: Package, Build, and Environment Authority' (Protocol in workflow.md) `[reconciled-20260427]`

## Phase 3: Quality Gates and Continuous Integration
- [x] Task: Decide the local and CI task-runner strategy `[6ca8853]`
    - [x] Evaluate whether `nox`, `tox`, or explicit command documentation is the right foundation choice for this repository
    - [x] Implement the selected approach or document an explicit deferral in the decision register
    - [x] Keep local workflow and CI commands aligned with the documented choice
- [x] Task: Enforce strict linting and typing gates `[6ca8853]`
    - [x] Write failing checks for strict `ruff` and strict `basedpyright`
    - [x] Configure the tools in `pyproject.toml`
    - [x] Update the maintained codebase to satisfy the stricter rules
- [x] Task: Enforce automated coverage above 90 percent for the maintained package `[6ca8853]`
    - [x] Write failing coverage gate expectations for local and CI execution
    - [x] Scope the coverage gate explicitly to the maintained package and document any exclusions
    - [x] Close the highest-value coverage gaps needed to pass the gate
- [x] Task: Conductor - User Manual Verification 'Phase 3: Quality Gates and Continuous Integration' (Protocol in workflow.md) `[reconciled-20260427]`

## Phase 4: Validation Boundaries and Documentation
- [x] Task: Introduce `pydantic v2` configuration models `[6ca8853]`
    - [x] Write failing tests for configuration schema validation and error reporting
    - [x] Implement `pydantic v2` models at the chosen configuration boundaries
    - [x] Preserve compatibility with current scenario and config execution paths
- [x] Task: Introduce `pandera` validation for selected tabular interfaces `[6ca8853]`
    - [x] Write failing tests for dataframe schema validation at high-value boundaries
    - [x] Implement `pandera` schemas for the selected ingress or egress points
    - [x] Update validation errors and contributor guidance so failures are diagnosable
- [x] Task: Add property-based tests for the new validation boundaries `[6ca8853]`
    - [x] Identify which `pydantic v2` and `pandera` boundaries benefit from property-based test coverage
    - [x] Introduce `Hypothesis`-based tests only where they protect boundary behavior better than example-based tests
    - [x] Keep the new tests fast enough for routine local and CI use
- [x] Task: Document the modernization foundation and remaining migration decisions `[250aca0]`
    - [x] Update README and contributor-facing docs for the implemented workflow
    - [x] Commit the decision register and record open follow-up items such as `polars`, `JAX`, plotting migration, data artifact versioning, and deferred automation work
    - [x] Confirm the documented workflow matches the implemented commands and quality gates
- [x] Task: Conductor - User Manual Verification 'Phase 4: Validation Boundaries and Documentation' (Protocol in workflow.md) `[reconciled-20260427]`

## Outstanding Work
No implementation tasks remain outstanding in this archived foundation track.
Follow-up candidates remain intentionally deferred to future tracks and are listed
in `decision-register.md`.
