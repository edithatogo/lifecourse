# HEOML Extraction Readiness

This document captures the minimum structure HEOML should have before it is
extracted from the `lifecourse` repository into its own project.

## Target Repository

- Proposed repository: `edithatogo/heoml`
- Proposed primary package name: `heoml`
- Proposed scope: specification, schemas, examples, fixtures, validation tools,
  changelog, and governance for the HEOML artifact profile

## Package Boundaries

HEOML should remain a specification-first repository.

- The embedded `lifecourse` subtree may contain helper validation tooling while
  HEOML is being proven.
- The extracted repository should not own `lifecourse` simulation logic or
  `voiage` VOI algorithms.
- The extracted repository should publish only the shared artifact contract,
  schema files, examples, fixtures, and lightweight validation utilities.
- Optional adapters for producing or consuming HEOML artifacts should remain in
  the owning application repositories.

## Documentation Site Needs

The extracted repository should include:

- a top-level README describing scope, non-goals, and compatibility rules
- versioned profile documentation for each supported HEOML release
- schema documentation for each artifact namespace
- examples and fixture documentation
- an extraction and migration guide for downstream projects
- a changelog with user-visible schema and contract changes

## License And Governance

- Keep the license aligned with the parent ecosystem unless a later governance
  decision changes it explicitly.
- Name maintainers and a review policy before extraction.
- Require an explicit process for approving schema breaking changes.
- Keep ownership of the core profile separate from downstream adapters.

## CI Requirements

The extracted repository should have CI that validates:

- schema syntax and example manifests
- fixture bundles against the current schema
- documentation links for versioned profile pages
- changelog and release metadata consistency

## Release Policy

- Use semantic versioning for the repository package and versioned profile
  pages.
- Treat breaking schema changes as a new profile version, not a silent update.
- Keep clarification-only changes inside the existing profile version when the
  schema contract does not change.
- Publish migration notes whenever the profile or fixtures change in a way that
  affects consumers.

## Dependency Expectations For Consumers

- `lifecourse` should depend on the extracted spec through a versioned contract,
  not by copying files.
- `voiage` should reference the same contract version when consuming HEOML
  bundles.
- Both projects should keep their own adapters, package-specific schemas, and
  result contracts, with HEOML acting as the shared portable layer.

## Extraction Checklist

Before extraction, confirm that:

1. at least one `lifecourse` bundle validates against the HEOML schema
2. at least one `voiage` workflow consumes a HEOML bundle
3. fixture bundles are deterministic and documented
4. the spec versioning policy is written down
5. release notes and migration guidance exist
6. governance and maintainership are explicit
7. the extracted repository can build and validate independently
