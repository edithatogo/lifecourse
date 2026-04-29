# Multi-Cohort Architecture Plan

Documentation scope: architecture and scientific/model docs.

## Phase 1: Cohort Strategy Contract

- [ ] Task: Add tests for the cohort strategy contract.
    - [ ] Cover diagnosis, progression, cost/QALY calculation, and lifecycle hooks.
    - [ ] Verify deterministic call ordering in the simulation step.
- [ ] Task: Implement typed cohort strategy interfaces.
    - [ ] Keep shared simulation orchestration independent of disease-specific logic.
    - [ ] Use pydantic configuration boundaries for cohort metadata.
    - [ ] Avoid coupling cohort strategies to Dask-specific internals where the engine interface can mediate.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Cohort Strategy Contract' (Protocol in workflow.md)

## Phase 2: Current Cohort Extraction

- [ ] Task: Add parity tests for the current intellectual disability cohort.
    - [ ] Compare old and new paths for fixed seeds and representative scenarios.
- [ ] Task: Extract current cohort-specific logic.
    - [ ] Move diagnosis, disease-specific progression, and cost/QALY adjustments behind the cohort strategy.
    - [ ] Preserve public APIs and CLI behavior.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Current Cohort Extraction' (Protocol in workflow.md)

## Phase 3: New Cohort Scaffold

- [ ] Task: Add a second-cohort scaffold without full parameterization.
    - [ ] Use Lynch syndrome, cystic fibrosis, or pharmacogenomics as a documented placeholder.
    - [ ] Prove the architecture supports separate parameter and pathway modules.
- [ ] Task: Document cohort authoring workflow.
    - [ ] Explain required parameters, tests, validation, and provenance.
- [ ] Task: Conductor - Automated Review and Checkpoint 'New Cohort Scaffold' (Protocol in workflow.md)
