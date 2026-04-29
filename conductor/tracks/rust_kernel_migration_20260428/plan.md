# Rust Kernel Migration Plan

## Phase 1: Candidate Ranking And Rust Workspace

- [ ] Task: Add tests or checks for candidate inventory documentation.
    - [ ] Verify candidates include purity, determinism, data shape, benchmark baseline, and promotion status.
- [ ] Task: Document ranked Rust kernel candidates.
    - [ ] Start with pure transformations and reductions before orchestration.
    - [ ] Record why excluded candidates are deferred.
- [ ] Task: Add Cargo workspace or crate scaffold.
    - [ ] Configure rustfmt, clippy, unit tests, and benchmark layout.
    - [ ] Add serde-compatible model types only where needed.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Candidate Ranking And Rust Workspace' (Protocol in workflow.md)

## Phase 2: First Kernel And Python Bridge

- [ ] Task: Add Python-vs-Rust parity tests for the first candidate kernel.
    - [ ] Cover fixed fixtures, edge cases, and numeric tolerances.
    - [ ] Confirm tests fail before Rust implementation exists.
- [ ] Task: Implement the first Rust kernel.
    - [ ] Keep Python as the reference implementation.
    - [ ] Avoid unsafe code.
- [ ] Task: Add PyO3/maturin bridge after parity is established.
    - [ ] Keep Python fallback available.
    - [ ] Gate Rust execution behind an explicit backend or feature flag.
- [ ] Task: Conductor - Automated Review and Checkpoint 'First Kernel And Python Bridge' (Protocol in workflow.md)

## Phase 3: Benchmark Profiling And Promotion Decision

- [ ] Task: Add benchmark and profiling evidence.
    - [ ] Compare Python baseline, optional JAX path where relevant, and Rust candidate.
    - [ ] Record workloads, hardware assumptions, and result interpretation.
- [ ] Task: Add Rust quality gates.
    - [ ] Run clippy, tests, criterion benchmark checks, mutation or documented equivalent, `cargo-audit`, and `cargo-deny`.
- [ ] Task: Decide promotion state.
    - [ ] Keep experimental if speed, simplicity, or reliability evidence is weak.
    - [ ] Promote only with parity, performance, and maintainability evidence.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Benchmark Profiling And Promotion Decision' (Protocol in workflow.md)
