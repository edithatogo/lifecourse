# Language Bindings and Rust Core Migration Umbrella Plan

## Phase 1: Decompose Migration Into Child Tracks

- [ ] Task: Create contract/schema child track.
    - [ ] Scope JSON Schema, pydantic boundary models, artifact formats, golden fixtures, and Python reference API.
    - [ ] Make this the required predecessor for all adapter and Rust tracks.
- [ ] Task: Create language adapter scaffold child track.
    - [ ] Scope R, Julia, Go, TypeScript, C#, Python, and Rust access paths around the stable contract.
    - [ ] Require wrapper-first implementations before native bindings.
- [ ] Task: Create Rust kernel migration child track.
    - [ ] Scope Cargo workspace, PyO3/maturin bridge, kernel ranking, parity tests, and benchmarks.
    - [ ] Require benchmark and parity evidence before replacing Python execution paths.
- [ ] Task: Create cross-runtime quality and CI child track.
    - [ ] Scope Rust, Go, TypeScript, C#, R, and Julia equivalents for linting, testing, mutation, profiling, and security checks.
    - [ ] Keep CI smoke checks small until each runtime surface is production-ready.
- [ ] Task: Create release, docs, versioning, and governance child track.
    - [ ] Scope semantic versioning, generated schema/client versioning, package support tiers, release dry-runs, and migration documentation.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Decompose Migration Into Child Tracks' (Protocol in workflow.md)

## Phase 2: Coordinate Sequencing And Dependencies

- [ ] Task: Sequence child tracks around stable contract artifacts.
    - [ ] Block language adapters on the initial request/response schema and golden fixtures.
    - [ ] Block Rust promotion on Python parity tests and benchmark baselines.
    - [ ] Block release publishing on support-tier and versioning governance.
- [ ] Task: Maintain the umbrella migration matrix.
    - [ ] Track which languages are wrapper-only, generated-client, native-binding, or unsupported.
    - [ ] Track the current state of Rust kernels as candidate, bridged, parity-proven, or promoted.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Coordinate Sequencing And Dependencies' (Protocol in workflow.md)

## Phase 3: Final Migration Readiness Review

- [ ] Task: Confirm all child tracks meet acceptance criteria.
    - [ ] Verify contract tests pass across at least one non-Python runtime.
    - [ ] Verify Rust migration has parity, benchmark, mutation, profiling, and security evidence.
    - [ ] Verify docs identify production, experimental, and deferred surfaces.
- [ ] Task: Decide whether to archive the umbrella track.
    - [ ] Archive only when child tracks are complete or explicitly deferred with documented rationale.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Final Migration Readiness Review' (Protocol in workflow.md)
