# Genomic Testing Pathways Plan

## Phase 1: Test Type Contract

- [ ] Task: Add tests for configurable genomic test types.
    - [ ] Cover panel, exome, genome, and legacy WGS-compatible behavior.
    - [ ] Cover cost, yield, VUS, and incidental finding parameter validation.
- [ ] Task: Implement test type configuration.
    - [ ] Add typed parameter/configuration models.
    - [ ] Keep scenario overrides explicit and provenance-ready.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Test Type Contract' (Protocol in workflow.md)

## Phase 2: Pathway Events

- [ ] Task: Add tests for counseling, VUS, incidental finding, and uptake events.
    - [ ] Cover deterministic probability edge cases and seeded stochastic runs.
- [ ] Task: Implement pathway event logic.
    - [ ] Track event flags or counts needed for costs, QALYs, and audit outputs.
    - [ ] Preserve existing scenario outputs.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Pathway Events' (Protocol in workflow.md)

## Phase 3: Outputs And Documentation

- [ ] Task: Add pathway summary outputs.
    - [ ] Include test counts, diagnosis counts, counseling counts, VUS counts, incidental finding counts, costs, and QALY effects.
- [ ] Task: Document scenario examples.
    - [ ] Include panel vs exome vs genome and counseling vs no-counseling scenarios.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Outputs And Documentation' (Protocol in workflow.md)
