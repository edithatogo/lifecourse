# Implementation Plan

## Phase 1: Baseline Audit, Decisions, and Safety Net
- [ ] Task: Audit the current packaging, CI, validation, and build surface
    - [ ] Review `pyproject.toml`, `requirements.txt`, CI workflows, version definitions, and CLI entry points
    - [ ] Identify the highest-value configuration and tabular boundaries for early validation
    - [ ] Record concrete migration success criteria and non-goals for this track
- [ ] Task: Create a modernization decision register for requested tools
    - [ ] Classify proposed tools into adopt now, defer, or reject for this track
    - [ ] Record rationale for boundary decisions such as `nox` or `tox`, `logging` or `loguru`, and deferred data-engine or simulation-engine migrations
    - [ ] Confirm the foundation track stays focused on packaging, gates, and validation rather than tool sprawl
- [ ] Task: Establish failing checks for the modernization foundation
    - [ ] Write or update tests that cover configuration loading, CLI execution, build or install smoke behavior, and validation boundary behavior
    - [ ] Add failing local or CI checks for linting, typing, and coverage expectations before implementation
    - [ ] Confirm the new checks fail where the brownfield baseline does not yet meet the target
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Baseline Audit, Decisions, and Safety Net' (Protocol in workflow.md)

## Phase 2: Package, Build, and Environment Authority
- [ ] Task: Migrate package and environment workflows to `uv` and `pyproject.toml`
    - [ ] Write failing install or smoke checks for the desired package workflow
    - [ ] Move authoritative dependency and tool configuration into `pyproject.toml`
    - [ ] Introduce the `uv` workflow and keep any necessary brownfield compatibility notes explicit
- [ ] Task: Make build and version behavior explicit
    - [ ] Write failing smoke checks for building and installing the maintained package
    - [ ] Make the package version source of truth explicit and documented
    - [ ] Confirm the documented build path remains reproducible after the tooling migration
- [ ] Task: Preserve supported CLI entry points during the tooling migration
    - [ ] Write failing tests for `lifecourse-cli` and `lifecourse-main` entry-point behavior
    - [ ] Update packaging configuration so both entry points still resolve correctly
    - [ ] Confirm documentation matches the implemented command surface
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Package, Build, and Environment Authority' (Protocol in workflow.md)

## Phase 3: Quality Gates and Continuous Integration
- [ ] Task: Decide the local and CI task-runner strategy
    - [ ] Evaluate whether `nox`, `tox`, or explicit command documentation is the right foundation choice for this repository
    - [ ] Implement the selected approach or document an explicit deferral in the decision register
    - [ ] Keep local workflow and CI commands aligned with the documented choice
- [ ] Task: Enforce strict linting and typing gates
    - [ ] Write failing checks for strict `ruff` and strict `basedpyright`
    - [ ] Configure the tools in `pyproject.toml`
    - [ ] Update the maintained codebase to satisfy the stricter rules
- [ ] Task: Enforce automated coverage above 90 percent for the maintained package
    - [ ] Write failing coverage gate expectations for local and CI execution
    - [ ] Scope the coverage gate explicitly to the maintained package and document any exclusions
    - [ ] Close the highest-value coverage gaps needed to pass the gate
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Quality Gates and Continuous Integration' (Protocol in workflow.md)

## Phase 4: Validation Boundaries and Documentation
- [ ] Task: Introduce `pydantic v2` configuration models
    - [ ] Write failing tests for configuration schema validation and error reporting
    - [ ] Implement `pydantic v2` models at the chosen configuration boundaries
    - [ ] Preserve compatibility with current scenario and config execution paths
- [ ] Task: Introduce `pandera` validation for selected tabular interfaces
    - [ ] Write failing tests for dataframe schema validation at high-value boundaries
    - [ ] Implement `pandera` schemas for the selected ingress or egress points
    - [ ] Update validation errors and contributor guidance so failures are diagnosable
- [ ] Task: Add property-based tests for the new validation boundaries
    - [ ] Identify which `pydantic v2` and `pandera` boundaries benefit from property-based test coverage
    - [ ] Introduce `Hypothesis`-based tests only where they protect boundary behavior better than example-based tests
    - [ ] Keep the new tests fast enough for routine local and CI use
- [ ] Task: Document the modernization foundation and remaining migration decisions
    - [ ] Update README and contributor-facing docs for the implemented workflow
    - [ ] Commit the decision register and record open follow-up items such as `polars`, `JAX`, plotting migration, data artifact versioning, and deferred automation work
    - [ ] Confirm the documented workflow matches the implemented commands and quality gates
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Validation Boundaries and Documentation' (Protocol in workflow.md)
