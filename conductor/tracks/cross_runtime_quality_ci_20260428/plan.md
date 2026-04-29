# Cross-Runtime Quality and CI Plan

Documentation scope: contributor, architecture, and release docs.

## Phase 1: Quality Matrix

- [ ] Task: Add tests or docs checks for the quality matrix.
    - [ ] Verify each runtime lists formatter, linter/static checker, test runner, mutation/fuzz/property tool, profiler/benchmark tool, and security scanner.
- [ ] Task: Document cross-runtime quality matrix.
    - [ ] Include Python, Rust, Go, TypeScript, C#, R, and Julia.
    - [ ] Mark each check as required, smoke-only, experimental, or deferred.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Quality Matrix' (Protocol in workflow.md)

## Phase 2: CI Smoke Jobs

- [ ] Task: Add CI smoke jobs for available runtime scaffolds.
    - [ ] Keep jobs conditional or lightweight until manifests exist.
    - [ ] Target .NET 11 for C# checks.
- [ ] Task: Add dependency automation coverage for new manifests.
    - [ ] Extend Renovate grouping for Cargo, Go, npm, NuGet, R, and Julia where applicable.
- [ ] Task: Conductor - Automated Review and Checkpoint 'CI Smoke Jobs' (Protocol in workflow.md)

## Phase 3: Security Profiling And Mutation Gates

- [ ] Task: Add Rust security and supply-chain checks.
    - [ ] Include `cargo-audit` and `cargo-deny` or documented equivalents.
- [ ] Task: Add runtime-specific profiling and mutation/fuzz gates.
    - [ ] Keep `scalene` and `mutmut` for Python.
    - [ ] Add `cargo-mutants` or equivalent for Rust, Go fuzzing where useful, and adapter-level smoke mutation only where tool support is practical.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Security Profiling And Mutation Gates' (Protocol in workflow.md)
