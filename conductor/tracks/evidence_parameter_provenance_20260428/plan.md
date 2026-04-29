# Evidence Parameter Provenance Plan

## Phase 1: Provenance Schema

- [ ] Task: Add tests for parameter provenance validation.
    - [ ] Cover fixed parameters, distributions, jurisdiction variants, and missing metadata.
    - [ ] Cover source-year and currency-year validation.
- [ ] Task: Implement provenance models.
    - [ ] Use pydantic models for provenance entries.
    - [ ] Support draft, reviewed, superseded, and deprecated assumption states.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Provenance Schema' (Protocol in workflow.md)

## Phase 2: Parameter Metadata And Audits

- [ ] Task: Add provenance metadata for representative production parameters.
    - [ ] Start with test costs, diagnostic yields, utilities, discount rates, and jurisdiction-specific values.
    - [ ] Mark unknown historical sources explicitly rather than silently omitting them.
- [ ] Task: Emit assumption audit artifacts.
    - [ ] Include parameter value, provenance key, source, status, jurisdiction, and transformation note.
    - [ ] Attach audit metadata to run outputs.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Parameter Metadata And Audits' (Protocol in workflow.md)

## Phase 3: Documentation And Governance

- [ ] Task: Document the parameter evidence workflow.
    - [ ] Explain how to add, review, supersede, and deprecate parameter assumptions.
    - [ ] Include examples for Australian and New Zealand parameters.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Documentation And Governance' (Protocol in workflow.md)
