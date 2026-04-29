# Rust Kernel Migration

## Overview

Introduce a Rust core incrementally for pure, deterministic, performance-
sensitive kernels. Python remains the orchestration and reference layer until
Rust parity, benchmark, mutation, profiling, and security evidence justify
promotion.

## Functional Requirements

- Create a Cargo workspace or crate layout for candidate Rust kernels.
- Rank candidate kernels by purity, determinism, data volume, call frequency,
  benchmark evidence, and maintainability.
- Prefer parameter transforms, net-benefit or EVPI-class reductions, scenario
  expansion helpers, and tabular kernels before orchestration code.
- Bridge Rust back to Python with PyO3/maturin only after parity tests pass.
- Keep serde-compatible models aligned with the language-neutral contract.

## Non-Functional Requirements

- Require rustfmt, clippy, unit tests, property tests where useful, criterion
  benchmarks, mutation testing or a documented equivalent, and security checks.
- Do not replace Python execution paths without a feature flag or safe fallback.
- Preserve deterministic seeds and numeric tolerance rules.
- Keep unsafe Rust out of scope unless a separate design note justifies it.

## Acceptance Criteria

- Candidate ranking is documented before implementation starts.
- The first migrated kernel has Python-vs-Rust parity tests.
- Benchmarks compare Python baseline and Rust candidate on representative data.
- Python bridge packaging is reproducible through the project workflow.
- Promotion criteria identify whether the Rust path is experimental or default.

## Out Of Scope

- Full model rewrite in Rust.
- Native bindings for every target language.
- Replacing Dask or Python orchestration as part of the first Rust kernel work.
