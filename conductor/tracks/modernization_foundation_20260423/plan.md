# Implementation Plan

## Phase 1: Baseline Audit and Safety Net
- [ ] Task: Audit the current packaging, CI, and validation boundaries
    - [ ] Review `pyproject.toml`, `requirements.txt`, CI workflows, and CLI entry points
    - [ ] Identify the highest-value configuration and tabular boundaries for early validation
    - [ ] Record concrete migration success criteria for this track
- [ ] Task: Establish failing checks for the modernization foundation
    - [ ] Write or update tests that cover configuration loading, CLI execution, and validation boundary behavior
    - [ ] Add failing local or CI checks for linting, typing, and coverage expectations before implementation
    - [ ] Confirm the new checks fail where the brownfield baseline does not yet meet the target
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Baseline Audit and Safety Net' (Protocol in workflow.md)

## Phase 2: Package and Environment Authority
- [ ] Task: Migrate package and environment workflows to `uv` and `pyproject.toml`
    - [ ] Write failing install or smoke checks for the desired package workflow
    - [ ] Move authoritative dependency and tool configuration into `pyproject.toml`
    - [ ] Introduce the `uv` workflow and keep any necessary brownfield compatibility notes explicit
- [ ] Task: Preserve supported CLI entry points during the tooling migration
    - [ ] Write failing tests for `lifecourse-cli` and `lifecourse-main` entry-point behavior
    - [ ] Update packaging configuration so both entry points still resolve correctly
    - [ ] Confirm documentation matches the implemented command surface
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Package and Environment Authority' (Protocol in workflow.md)

## Phase 3: Quality Gates and Continuous Integration
- [ ] Task: Enforce strict linting and typing gates
    - [ ] Write failing checks for strict `ruff` and strict `basedpyright`
    - [ ] Configure the tools in `pyproject.toml`
    - [ ] Update the maintained codebase to satisfy the stricter rules
- [ ] Task: Enforce automated coverage above 90 percent
    - [ ] Write failing coverage gate expectations for local and CI execution
    - [ ] Update test tooling and CI workflows to enforce the new threshold
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
- [ ] Task: Document the modernization foundation and remaining migration decisions
    - [ ] Update README and contributor-facing docs for the implemented workflow
    - [ ] Record open follow-up items such as `polars`, `JAX`, plotting migration, and data artifact versioning
    - [ ] Confirm the documented workflow matches the implemented commands and quality gates
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Validation Boundaries and Documentation' (Protocol in workflow.md)
