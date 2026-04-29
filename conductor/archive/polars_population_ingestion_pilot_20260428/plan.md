# Implementation Plan

## Phase 1: Tests and Backend Contract
- [x] Task: Define the ingestion backend contract
    - [x] Keep pandas as default
    - [x] Require Polars to be explicit and optional
    - [x] Preserve pandas DataFrame return type for compatibility
- [x] Task: Add data-loader backend tests
    - [x] Test explicit pandas behavior
    - [x] Test simulated Polars behavior without requiring Polars installation
    - [x] Test missing Polars and invalid backend failures
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 1: Tests and Backend Contract' (Protocol in workflow.md)

## Phase 2: Implementation and Documentation
- [x] Task: Implement optional Polars ingestion path
    - [x] Add backend selector to `load_nz_population_distribution`
    - [x] Add a Polars helper with clear optional dependency failure
    - [x] Reuse existing pandera validation boundary
- [x] Task: Update documentation
    - [x] Document the opt-in Polars ingestion pilot
    - [x] Keep broader migration work listed as outstanding
- [x] Task: Run validation
    - [x] Run focused tests
    - [x] Run formatting, linting, typing, and full tests
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 2: Implementation and Documentation' (Protocol in workflow.md)
