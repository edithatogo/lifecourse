# Validation Calibration Targets Plan

## Phase 1: Target Schema

- [ ] Task: Add tests for calibration and validation target schemas.
    - [ ] Cover metric types, tolerances, jurisdictions, provenance links, and holdout flags.
- [ ] Task: Implement target models and loaders.
    - [ ] Use typed validation for target files.
    - [ ] Distinguish calibration targets from validation targets.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Target Schema' (Protocol in workflow.md)

## Phase 2: Baseline Comparison

- [ ] Task: Add tests for fixed-seed baseline comparisons.
    - [ ] Cover pass, warn, and fail tolerance outcomes.
- [ ] Task: Implement validation report generation.
    - [ ] Compare run outputs to target values and tolerances.
    - [ ] Emit machine-readable and human-readable reports.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Baseline Comparison' (Protocol in workflow.md)

## Phase 3: Calibration Integration

- [ ] Task: Integrate deterministic calibration search with targets.
    - [ ] Record candidate scores, selected parameters, and validation impact.
- [ ] Task: Document target update governance.
    - [ ] Require rationale, provenance, and changelog notes for target changes.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Calibration Integration' (Protocol in workflow.md)
