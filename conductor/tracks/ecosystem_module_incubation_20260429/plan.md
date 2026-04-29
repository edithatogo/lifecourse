# Ecosystem Module Incubation Plan

## Phase 1: Ecosystem Boundary Strategy

- [ ] Task: Document current ecosystem roles.
    - [ ] Define the boundary for `lifecourse`, `voiage`, `innovate`, `mars`, and HEOML.
    - [ ] Mark `mars` as a stable-API package that must not absorb unrelated ecosystem responsibilities.
    - [ ] State that sibling projects integrate through artifacts, schemas, and adapters rather than direct internal imports.
- [ ] Task: Document candidate future modules.
    - [ ] Include engine, evidence, calibration, reporting, policy, registry, workflow, and quality modules.
    - [ ] Classify each candidate as embedded subtree, future standalone repo, optional adapter, or deferred idea.
    - [ ] Identify where each candidate should not live.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Ecosystem Boundary Strategy' (Protocol in workflow.md)

## Phase 2: Dependency And Promotion Policy

- [ ] Task: Define module-incubation promotion stages.
    - [ ] Start from design note or track.
    - [ ] Promote to embedded subtree only when real fixtures and docs are needed before extraction.
    - [ ] Promote to standalone repo only after contracts, examples, validators, and ownership are stable.
    - [ ] Promote to supported integration only after compatibility tests and release/version policy exist.
- [ ] Task: Define dependency gates.
    - [ ] Require optional extras for non-core integrations.
    - [ ] Require Renovate, smoke CI, security checks, docs, and removal paths.
    - [ ] For Rust or multi-language modules, require cross-runtime contract fixtures before public support.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Dependency And Promotion Policy' (Protocol in workflow.md)

## Phase 3: HEOML Extension Strategy

- [ ] Task: Define extension namespace guidance.
    - [ ] Reserve HEOML core for stable health-economic run-bundle fields.
    - [ ] Use namespaced extension profiles for `voiage`, `innovate`, `mars`, and future modules.
    - [ ] Require extension schemas to declare version, owner, compatibility, and artifact references.
- [ ] Task: Document interchange implications.
    - [ ] Keep pickle excluded from portable interchange.
    - [ ] Prefer JSON Schema for metadata and Arrow/Parquet for typed tabular artifacts.
    - [ ] Allow modules to produce or consume HEOML bundles without depending on `lifecourse` internals.
- [ ] Task: Conductor - Automated Review and Checkpoint 'HEOML Extension Strategy' (Protocol in workflow.md)

## Phase 4: Repo Documentation Updates

- [ ] Task: Link the strategy into stack and architecture docs.
    - [ ] Update `docs/stack_strategy.md`.
    - [ ] Update `conductor/tech-stack.md`.
    - [ ] Update HEOML docs.
- [ ] Task: Add implementation follow-up guidance.
    - [ ] Identify which future modules should receive dedicated tracks first.
    - [ ] Keep `lifecourse` implementation work focused on current simulation, artifacts, and adapters.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Repo Documentation Updates' (Protocol in workflow.md)
