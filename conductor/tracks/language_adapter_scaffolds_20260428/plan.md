# Language Adapter Scaffolds Plan

## Phase 1: Adapter Layout And Shared Fixtures

- [x] Task: Add tests that validate adapter scaffolds can locate shared schemas and fixtures.
    - [x] Cover path conventions from repo root and package contexts.
    - [x] Cover missing-schema failure diagnostics.
- [x] Task: Create adapter directory layout.
    - [x] Include `bindings/r`, `bindings/julia`, `bindings/go`, `bindings/typescript`, `bindings/csharp`, and `bindings/rust` or equivalent documented paths.
    - [x] Add README files that define each adapter support tier.
- [x] Task: Conductor - Automated Review and Checkpoint 'Adapter Layout And Shared Fixtures' (Protocol in workflow.md)

## Phase 2: R And Julia Wrappers

- [x] Task: Add R wrapper smoke tests.
    - [x] Use `testthat` conventions and a fixture-driven subprocess or CLI call.
    - [x] Document `R CMD check` expectations.
- [x] Task: Add Julia wrapper smoke tests.
    - [x] Use `Pkg.test` and `Test` conventions.
    - [x] Document package activation and fixture invocation.
- [x] Task: Implement minimal R and Julia wrappers.
    - [x] Keep wrappers schema-first and avoid duplicated model logic.
- [x] Task: Conductor - Automated Review and Checkpoint 'R And Julia Wrappers' (Protocol in workflow.md)

## Phase 3: Go TypeScript CSharp And Rust Consumers [checkpoint: d1ee5fc]

- [x] Task: Add Go adapter smoke tests.
    - [x] Use `go test` and fixture-based CLI or JSON invocation.
    - [x] Include generated or checked request/response structs where practical.
- [x] Task: Add TypeScript adapter smoke tests.
    - [x] Use generated types, `tsc`, and a small test runner.
    - [x] Validate schema-compatible request construction.
- [x] Task: Add C# adapter smoke tests targeting .NET 11.
    - [x] Use analyzer-friendly project defaults and a fixture-driven test.
    - [x] Keep interop through process or contract files before native calls.
- [x] Task: Add Rust consumer smoke tests.
    - [x] Use serde-compatible request/response models generated from or aligned to schemas.
    - [x] Treat Rust as a contract consumer before kernel migration.
- [x] Task: Implement minimal adapters for Go, TypeScript, C#, and Rust.
    - [x] Keep adapters wrapper-first and documented as experimental.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Go TypeScript CSharp And Rust Consumers' (Protocol in workflow.md)
