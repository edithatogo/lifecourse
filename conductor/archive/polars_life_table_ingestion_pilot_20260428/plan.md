# Implementation Plan

## Phase 1: Tests and Backend Contract
- [x] Task: Add life-table backend tests
    - [x] Test explicit pandas behavior
    - [x] Test simulated Polars behavior without requiring Polars installation
    - [x] Test missing Polars and invalid backend failures
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 1: Tests and Backend Contract' (Protocol in workflow.md)

## Phase 2: Implementation and Documentation
- [x] Task: Implement optional Polars life-table ingestion
    - [x] Add backend selector to `load_nz_life_table_hazards`
    - [x] Add Polars helper with clear optional dependency failure
    - [x] Preserve sex-keyed numpy hazard arrays
- [x] Task: Update documentation
    - [x] Record life-table loading as a second Polars pilot
    - [x] Keep full data-engine migration as follow-up work
- [x] Task: Run validation
    - [x] Run focused tests
    - [x] Run formatting, linting, typing, and full tests
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 2: Implementation and Documentation' (Protocol in workflow.md)
