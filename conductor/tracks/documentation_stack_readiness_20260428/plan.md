# Documentation and Stack Readiness Plan

## Phase 1: Documentation Map And Status [checkpoint: 3fbc6b7]

- [x] Task: Add tests or checks for required documentation files.
    - [x] Verify `README.md`, `CONTRIBUTING.md`, `RELEASE.md`, `CHANGELOG.md`, `FUTURE_ROADMAP.md`, `docs/architecture_status.md`, `docs/stack_strategy.md`, and `docs/documentation_plan.md` exist.
    - [x] Verify stale references such as missing roadmap filenames are reported.
- [x] Task: Expand the documentation plan into a maintained documentation map.
    - [x] Identify user, contributor, architecture, scientific/model, API/contract, and release docs.
    - [x] Mark each documentation set as current, experimental, planned, or deferred.
    - [x] Define which docs each major Conductor track must update.
- [x] Task: Update README and architecture status from the documentation map.
    - [x] Keep user-facing links short and accurate.
    - [x] Keep planned features separate from production defaults.
- [x] Task: Conductor - Automated Review and Checkpoint 'Documentation Map And Status' (Protocol in workflow.md)

## Phase 2: Lightweight Docs Checks [checkpoint: c473047]

- [x] Task: Add a local docs-check command.
    - [x] Prefer a small repository script before adopting a full docs generator.
    - [x] Check internal markdown links, required docs files, and stale references.
    - [x] Fail clearly with actionable messages.
- [x] Task: Add Markdown prose linting to the docs-check workflow.
    - [x] Keep the initial rule set small and repository-local.
    - [x] Fail only on Markdown content, not source or generated artifacts.
- [x] Task: Add docs-check workflow integration.
    - [x] Add a nox session for docs checks.
    - [x] Add CI coverage once the local check is stable.
- [x] Task: Document docs-check usage.
    - [x] Add commands to README or CONTRIBUTING only if contributors need them.
    - [x] Keep docs-check dependencies out of the runtime dependency set.
- [x] Task: Conductor - Automated Review and Checkpoint 'Lightweight Docs Checks' (Protocol in workflow.md)

## Phase 3: Stack Change Checklist [checkpoint: 1f49bea]

- [x] Task: Add stack-change checklist documentation.
    - [x] Require updates to `docs/architecture_status.md`, `docs/stack_strategy.md`, `conductor/tech-stack.md`, relevant Conductor plans, README when user-facing, and CHANGELOG when behavior or dependencies change.
    - [x] Include dependency classification as core, optional, experimental, or deferred.
    - [x] Include CI, Renovate, security, and ownership requirements for new dependencies.
- [x] Task: Add docs requirements to active migration tracks.
    - [x] Cover model contract/schema, language adapters, Rust kernel migration, cross-runtime CI, simulation-engine modularity, multi-cohort architecture, parameter provenance, validation targets, and reporting bundles.
    - [x] Ensure each track says whether it needs user, contributor, architecture, scientific/model, API/contract, or release docs.
- [x] Task: Conductor - Automated Review and Checkpoint 'Stack Change Checklist' (Protocol in workflow.md)

## Phase 4: Generated Docs Site Decision

- [ ] Task: Define docs site adoption criteria.
    - [ ] Add MkDocs Material only when markdown-first docs become hard to navigate or public API/contract docs need a site.
    - [ ] Add `mkdocstrings` only when Python API reference pages are useful and stable.
    - [ ] Add tested snippets for examples that users are expected to copy.
- [ ] Task: Add optional docs extra if tooling is adopted.
    - [ ] Keep docs tooling out of the default runtime dependencies.
    - [ ] Add Renovate and CI coverage for docs tooling.
- [ ] Task: Document the decision.
    - [ ] Record whether generated docs are adopted or explicitly deferred with rationale.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Generated Docs Site Decision' (Protocol in workflow.md)

## Phase 5: Public-Surface Documentation

- [ ] Task: Add contract and schema docs when the contract track lands.
    - [ ] Document request and response schemas, artifact formats, engine metadata, seed policy, and diagnostics.
- [ ] Task: Add simulation-engine docs before non-default engines become user-facing.
    - [ ] Document static, Markov, discrete-time, continuous-time, DES, ABM/network, and hybrid engine status and use cases.
- [ ] Task: Add scientific/model docs before evidence maturity claims.
    - [ ] Document parameter provenance, jurisdictions, calibration targets, validation targets, and limitations.
- [ ] Task: Add binding docs after adapter scaffolds exist.
    - [ ] Include install assumptions, minimal run, expected output, status, and limitations for each adapter.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Public-Surface Documentation' (Protocol in workflow.md)
