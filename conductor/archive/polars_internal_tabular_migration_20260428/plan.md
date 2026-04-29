# Implementation Plan

## Phase 1: Candidate Selection
- [x] Task: Use benchmark evidence to choose the first internal tabular migration
    - [x] Compare current pandas-compatible path against a Polars prototype
    - [x] Select one boundary with clear equivalence criteria
    - [x] Record why other candidates are deferred
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 1: Candidate Selection' (Protocol in workflow.md)

## Phase 2: Boundary Migration
- [x] Task: Implement the selected Polars boundary
    - [x] Write equivalence tests first
    - [x] Implement explicit Polars path
    - [x] Preserve public return contracts
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 2: Boundary Migration' (Protocol in workflow.md)
