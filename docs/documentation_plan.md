# Documentation Plan

## Goal

Keep documentation aligned with the repo's product goal: credible,
reproducible, health-economic microsimulation for genomic testing policy
analysis. Documentation should make current behavior clear, label experimental
work honestly, and provide migration guidance without implying that planned
features are production-ready.

## Documentation Sets

- User docs: installation, running scenarios, interpreting outputs, result
  bundles, and troubleshooting.
- Contributor docs: development workflow, testing, Conductor process, code
  layout, style, and release checks.
- Architecture docs: production defaults, optional pilots, simulation-engine
  strategy, cohort strategy, language bindings, Rust migration, and dependency
  policy.
- Scientific/model docs: assumptions, parameter provenance, jurisdictions,
  calibration/validation targets, and model limitations.
- API/contract docs: Python reference API, CLI contract, JSON Schema artifacts,
  output formats, and language adapter examples.
- Release docs: versioning, support tiers, deprecation policy, package
  publication prerequisites, and changelog discipline.

## Near-Term Documentation Tracks

1. Stabilize markdown docs and fix stale references.
2. Add docs checks for broken links, required sections, stale roadmap names, and
   lightweight prose linting.
   The current repo-local check is `uv run python scripts/check_docs.py`.
3. Add contract and schema docs when the model contract track is implemented.
4. Add simulation-engine docs before non-default engines become user-facing.
5. Add parameter provenance and validation target docs before claiming external
   validation or jurisdiction-specific evidence maturity.
6. Add binding-specific docs only after adapter scaffolds exist.
   The current binding-specific docs include adapter examples and release
   governance for the wrapper-first scaffolds.
7. Add `voiage` integration docs only after the artifact contract and optional
   adapter exist.

## Implementation Plan

The executable plan lives in
`conductor/tracks/documentation_stack_readiness_20260428/plan.md`.

The implementation sequence is:

1. Documentation map and status tracking.
2. Lightweight markdown checks.
3. Stack-change checklist and migration-track documentation requirements.
4. Generated docs site decision.
5. Public-surface documentation for contracts, engines, scientific assumptions,
   validation, reporting bundles, bindings, and `voiage` integration.

## Future Docs Tooling

The repo does not need a docs generator in the core install. When docs become
large enough to require a site, prefer an optional docs extra and CI docs build.
The likely direction is:

- MkDocs Material for a lightweight documentation site.
- `mkdocstrings` for Python API reference pages.
- Markdown link checking in CI.
- Example snippets that are tested where practical.

These tools should be added through a docs-specific track rather than bundled
into the default runtime dependencies.

## Maintenance Rules

- Every feature track must state whether docs need user, contributor,
  architecture, scientific/model, API/contract, or release updates.
- Experimental features must be labeled experimental in README or architecture
  docs if users can access them.
- Planned features must not be documented as production defaults.
- Documentation changes should be reviewed with the same rigor as code when they
  describe model behavior, assumptions, or validation status.
