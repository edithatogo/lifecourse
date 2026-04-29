# Bindings Versioning And Support Policy

This document defines the documentation policy for the schema contract,
language adapters, and Rust migration surfaces.

## Versioning Rules

- The Python reference package is the source of truth for the contract runtime.
- The contract schema version follows semantic versioning:
  - `MAJOR` changes for incompatible request or response shape changes.
  - `MINOR` changes for backward-compatible additions to the contract or new
    optional fields.
  - `PATCH` changes for documentation fixes, wrapper-only fixes, and other
    backward-compatible refinements that do not alter the contract payload.
- Generated clients and wrapper adapters should align their `MAJOR` version
  with the contract schema `MAJOR` version when they encode contract-shape
  assumptions. They may release `MINOR` or `PATCH` updates independently when
  they only change wrapper behavior, build metadata, or documentation.
- Rust core migration work must remain behind explicit parity and benchmark
  gates before it can be treated as a default execution path.

## Support Tiers

- `reference`: the maintained Python contract and reference API.
- `experimental`: scaffolds, pilots, and optional paths that may change without
  broad compatibility guarantees.
- `smoke-tested`: package-shaped wrappers that have deterministic fixture
  coverage but are not promoted as production defaults.
- `production-supported`: only surfaces with explicit compatibility policy,
  release governance, and maintained CI.
- `deprecated`: supported for a warning window only, with migration guidance.
- `unsupported`: historical or exploratory surfaces with no compatibility
  promise.

## Documentation Expectations

- Document schema, Python, Rust, and adapter version relationships in the
  architecture and release docs.
- Keep adapter README files clear about support tier and invocation path.
- Keep release documentation explicit about what is experimental, smoke-tested,
  or production-supported.

## References

- [Architecture status](architecture_status.md)
- [Documentation plan](documentation_plan.md)
- [Bindings release governance track](../conductor/tracks/bindings_release_docs_governance_20260428/plan.md)
