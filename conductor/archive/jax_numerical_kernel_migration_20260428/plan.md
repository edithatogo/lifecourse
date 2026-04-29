# Implementation Plan

## Phase 1: Kernel Selection
- [x] Task: Identify pure numerical kernels
    - [x] Exclude pandas/Dask-dependent paths
    - [x] Benchmark candidate numpy kernels
    - [x] Select one kernel for optional JAX dispatch
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 1: Kernel Selection' (Protocol in workflow.md)

## Phase 2: Kernel Migration
- [x] Task: Implement selected optional JAX kernel
    - [x] Write numpy/JAX equivalence tests
    - [x] Add explicit backend argument or helper
    - [x] Preserve default numpy behavior
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 2: Kernel Migration' (Protocol in workflow.md)
