# Bindings Release Documentation and Governance Plan

## Phase 1: Versioning And Support Policy

- [x] Task: Add docs checks for versioning and support policy.
    - [x] Verify schema, Python, Rust, and adapter version relationships are documented.
- [x] Task: Document semantic versioning rules.
    - [x] Define contract schema compatibility rules.
    - [x] Define generated client and adapter version alignment.
- [x] Task: Document support tiers.
    - [x] Distinguish reference, experimental, smoke-tested, production-supported, deprecated, and unsupported surfaces.
- [x] Task: Conductor - Automated Review and Checkpoint 'Versioning And Support Policy' (Protocol in workflow.md) [checkpoint: ee68c41]

## Phase 2: Architecture And User Documentation

- [ ] Task: Update architecture documentation.
    - [x] Identify Python reference behavior, optional bindings, Rust candidates, and current defaults.
    - [x] Explain why wrapper-first binding paths precede native bindings.
- [ ] Task: Maintain the documentation plan.
    - [x] Define user, contributor, architecture, scientific/model, API/contract, and release documentation responsibilities.
    - [x] Add docs checks for stale links or missing required sections before adding a generated docs site.
- [x] Task: Add adapter examples.
    - [x] Include installation assumptions, minimal run, expected output, and limitations for each supported runtime.
- [x] Task: Conductor - Automated Review and Checkpoint 'Architecture And User Documentation' (Protocol in workflow.md) [checkpoint: 229adbd]

## Phase 3: Release Governance

- [ ] Task: Define release dry-run prerequisites.
    - [ ] Cover PyPI, crates.io, npm, NuGet, CRAN, Julia registry, and Go module usage as applicable.
    - [ ] Require checksums, changelog entries, schema compatibility notes, and artifact provenance.
- [ ] Task: Define deprecation policy.
    - [ ] Specify warning periods, compatibility windows, and migration notes for schema or adapter breaking changes.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Release Governance' (Protocol in workflow.md)
