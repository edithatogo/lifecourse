# Implementation Plan

## Phase 1: Backend Direction and Decision Surface
- [x] Task: Define the backend migration decision scope
    - [x] Confirm `polars` and JAX-class tooling are evaluation targets, not immediate whole-engine replacements
    - [x] Identify the tabular, numerical, and orchestration boundaries that need separate decisions
    - [x] Record explicit non-goals for this track
- [x] Task: Add backend readiness and recommendation tests
    - [x] Write tests for optional dependency availability reporting
    - [x] Write tests for tabular backend recommendations
    - [x] Write tests for numerical backend recommendations
- [x] Task: Implement backend readiness and recommendation helpers
    - [x] Add typed helper APIs under the maintained package
    - [x] Keep recommendations deterministic and independent of optional package installation
    - [x] Ensure unavailable optional packages are reported without import-time failures
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 1: Backend Direction and Decision Surface' (Protocol in workflow.md)

## Phase 2: Optional Acceleration Slice
- [x] Task: Declare optional backend dependency groups
    - [x] Add deliberate optional extras for `polars`, JAX-class experimentation, and combined backend evaluation
    - [x] Keep default dependencies unchanged unless required by current production code
    - [x] Document install intent in the package metadata or README
- [x] Task: Add numerical backend tests
    - [x] Write tests for default `numpy` vector calculations
    - [x] Write tests for clear failure when JAX is requested but unavailable
    - [x] Write tests for a simulated JAX execution path with equivalent numerical output
- [x] Task: Implement numerical backend utility
    - [x] Add a net monetary benefit style vector helper using `numpy` by default
    - [x] Add optional JAX dispatch behind an explicit backend argument
    - [x] Keep returned values interoperable with existing `numpy`/`pandas` analysis code
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 2: Optional Acceleration Slice' (Protocol in workflow.md)

## Phase 3: Documentation, Validation, and Follow-Up Track Definition
- [x] Task: Update project documentation for backend migration status
    - [x] Update tech-stack guidance to distinguish current runtime, implemented evaluation infrastructure, and future migration candidates
    - [x] Add README guidance for optional backend extras
    - [x] Record outstanding follow-up work for actual `polars` and JAX migration tracks
- [x] Task: Run full validation
    - [x] Run formatting and linting checks for changed files
    - [x] Run type checking
    - [x] Run the full test suite with coverage
- [x] Task: Conductor - Automated Review and Checkpoint 'Phase 3: Documentation, Validation, and Follow-Up Track Definition' (Protocol in workflow.md)
