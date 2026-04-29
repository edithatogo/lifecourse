# Implementation Plan

## Phase 1: Tests and Dispatch Contract
- [x] Task: Add distributional statistics backend tests
    - [x] Test default net-benefit statistics remain unchanged
    - [x] Test explicit backend dispatch reaches the backend utility
    - [x] Keep tests independent of a real JAX installation
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 1: Tests and Dispatch Contract' (Protocol in workflow.md)

## Phase 2: Implementation and Documentation
- [x] Task: Implement analysis-level backend dispatch
    - [x] Add a backend parameter to `calculate_distributional_statistics`
    - [x] Route net-benefit vectors through `calculate_net_monetary_benefit`
    - [x] Preserve existing return structure
- [x] Task: Update documentation
    - [x] Record this as the first JAX-class analysis hook
    - [x] Keep full simulation acceleration as follow-up work
- [x] Task: Run validation
    - [x] Run focused tests
    - [x] Run formatting, linting, typing, and full tests
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 2: Implementation and Documentation' (Protocol in workflow.md)
