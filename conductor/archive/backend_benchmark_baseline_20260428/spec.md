# Backend Benchmark Baseline

## Overview
Create a lightweight, executable benchmark baseline for backend migration
decisions. Later Polars, JAX, and Dask changes should compare against these
metrics instead of relying on intuition.

## Goals
- Add benchmark helpers for small tabular and numerical candidate workloads.
- Keep benchmarks deterministic and fast enough for local development.
- Summarize elapsed time, row/element count, throughput, and backend
  recommendation in structured data.
- Avoid hard performance assertions in CI.

## Functional Requirements
- Provide a tabular-transform benchmark for pandas-compatible transformations.
- Provide a numerical-vector benchmark for net monetary benefit calculations.
- Include backend recommendations using existing backend evaluation helpers.
- Expose serializable benchmark summary objects or dictionaries.

## Non-Functional Requirements
- Benchmarks must not require optional Polars or JAX packages.
- Tests must validate structure and determinism, not absolute wall-clock speed.
- Full validation must pass.

## Acceptance Criteria
- Focused benchmark tests pass.
- `uv run pytest` passes with configured coverage.
