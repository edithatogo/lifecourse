# Language Bindings and Rust Core Migration

## Overview

Define a migration path that exposes the `lifecourse` model through a stable,
language-neutral contract first, then layers bindings for R, Julia, Python,
Rust, Go, TypeScript, and C#, and only then migrates selected core kernels to
Rust. The maintained Python package remains the reference implementation until
Rust parity is proven by tests, benchmarks, and release policy.

## Goals

- Surface the model through a stable request/response boundary usable from
  multiple runtimes.
- Avoid premature handwritten native bindings before the contract is stable.
- Preserve scientific reproducibility, deterministic seeds, and current Python
  behavior during migration.
- Move pure, performance-sensitive kernels to Rust incrementally.
- Keep the public behavior of the current research package intact while
  migration proceeds.
- Split implementation into independently reviewable tracks so contract,
  bindings, Rust migration, cross-runtime quality, and release governance can
  progress without one large, high-risk change set.

## Functional Requirements

### Contract First

- Define a language-neutral input contract for:
  - model configuration
  - scenario selection
  - parameter overrides
  - run mode selection
  - seed and reproducibility policy
  - requested outputs and artifacts
- Define a language-neutral output contract for:
  - deterministic scenario results
  - PSA samples
  - summary statistics
  - uncertainty metrics
  - benchmark and diagnostic artifacts
- Make the contract serializable through structured formats that all target
  languages can consume.

### Python As Reference Implementation

- Expose a stable Python API for running the model without depending on CLI
  parsing internals.
- Keep CLI execution as a supported interface.
- Ensure Python remains the golden implementation for parity checks.

### Multi-Language Access Strategy

- Add a thin access path for each target language in priority order:
  - R
  - Julia
  - Python
  - Rust
  - Go
  - TypeScript
  - C#
- Prefer the least risky transport first:
  - CLI or JSON file contract
  - local service boundary if needed
  - native wrapper only after the contract has stabilized
- Do not require all languages to get native bindings simultaneously.

### Rust Migration

- Identify pure, deterministic kernels suitable for Rust migration.
- Keep Python orchestration in place until Rust replacements pass parity tests.
- Expose Rust kernels back into Python through a maintained bridge.
- Allow later C ABI, CLI, or WASM surfaces only if they become justified by the
  consumer languages.

### Track Decomposition

The migration must be delivered through child tracks:

- model contract and schema artifacts
- language adapter scaffolds for R, Julia, Go, TypeScript, C#, Python, and Rust
- Rust kernel migration and Python bridge
- cross-runtime quality, CI, profiling, mutation, and security tooling
- release, documentation, versioning, and support governance

### Tooling Equivalence

- Python remains governed by `uv`, `nox`, `ruff`, `basedpyright`, `pytest`,
  `Hypothesis`, `mutmut`, and `scalene`.
- Rust candidates must use Cargo, `rustfmt`, `clippy`, unit/property tests,
  criterion benchmarks, `cargo-mutants` or documented equivalent mutation
  checks, `cargo-audit`, and `cargo-deny`.
- Go adapters must use `gofmt`, `go vet`, `staticcheck`, `go test`, fuzz tests
  where appropriate, benchmarks, and `govulncheck`.
- TypeScript adapters must use generated types, `tsc`, linting, tests, and a
  package workflow that can run in CI.
- C# adapters must target .NET 11, use analyzers, tests, package validation,
  and benchmark tooling where native interop becomes performance-sensitive.
- R adapters must use `R CMD check`, `testthat`, and generated documentation.
- Julia adapters must use `Pkg.test`, `Test`, and generated package
  documentation.

### Contract Artifacts

- JSON Schema is the canonical request/response schema for control-plane data.
- Arrow or Parquet is the preferred cross-runtime format for tabular artifacts.
- CSV remains a compatibility export, not the primary typed artifact format.
- Golden fixtures must cover deterministic runs, seeded probabilistic runs,
  schema failures, and artifact metadata.

## Non-Functional Requirements

- Preserve reproducibility and numerical consistency across runtimes.
- Maintain >90% coverage for newly introduced code paths.
- Keep migration increments small enough to review and revert safely.
- Require explicit benchmark evidence before replacing working Python paths.
- Keep release and versioning discipline aligned with the existing Python
  packaging workflow.

## Acceptance Criteria

- A documented language-neutral contract exists and is tested.
- The Python API can run the model without depending on CLI argument parsing.
- At least one external-language access path is demonstrated using the new
  contract.
- Kernel parity tests prove that any Rust migration matches Python results on
  fixed-seed fixtures.
- Benchmark evidence exists before any Rust core claim is promoted.
- The repo documents which parts are reference Python, which are optional
  bindings, and which are Rust candidates.
- Child tracks exist for all major migration workstreams and define their own
  quality gates before implementation starts.

## Out Of Scope

- Rewriting the whole model in Rust immediately.
- Handwriting seven native bindings before a stable contract exists.
- Replacing Python orchestration before parity and maintainability evidence.
- Publishing language-specific packages until the interface and ownership model
  are settled.
