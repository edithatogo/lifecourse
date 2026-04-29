# Bindings Release Documentation and Governance

## Overview

Define how the schema contract, language adapters, and Rust core are versioned,
documented, supported, released, deprecated, and promoted. This prevents
experimental bindings from being mistaken for production APIs.

## Functional Requirements

- Define semantic versioning rules for the Python package, schema contract,
  generated clients, adapters, and Rust crates.
- Define support tiers such as reference, experimental, smoke-tested,
  production-supported, and deprecated.
- Document release dry-run and publication prerequisites for PyPI, crates.io,
  npm, NuGet, CRAN, Julia registry, and Go module usage.
- Update architecture documentation to identify reference Python behavior,
  optional bindings, Rust candidates, and default execution paths.
- Add user-facing examples for contract invocation and each supported adapter.
- Maintain documentation sets for users, contributors, architecture,
  scientific/model assumptions, API/contracts, and releases.
- Add a docs site and docs CI only when the documentation surface grows beyond
  markdown-first maintenance.

## Non-Functional Requirements

- Avoid publishing packages before ownership and support obligations are clear.
- Keep docs honest about experimental status and current limitations.
- Align package versioning with schema compatibility and deprecation policy.
- Preserve reproducibility and artifact lineage in release notes.

## Acceptance Criteria

- Versioning and support-tier policy is documented.
- Architecture docs identify production, experimental, and deferred surfaces.
- Release dry-run workflows are defined before external publication.
- Adapter docs include installation, minimal run, expected output, and known
  limitations.
- Documentation status is tracked so planned features are not described as
  production defaults.

## Out Of Scope

- Actually publishing packages to external registries.
- Making all adapters production-supported immediately.
- Changing the scientific model semantics as part of documentation cleanup.
