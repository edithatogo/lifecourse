# Stack Strategy

This document clarifies the intended stack direction so migration work does not
create avoidable dependency, API, or documentation debt.

## Current Production Stack

- Python remains the reference implementation.
- The production simulation engine is annual discrete-time individual
  microsimulation using `numpy`, `pandas`, `scipy`, and `dask`.
- `pydantic v2` and `pandera` define validation boundaries.
- `uv`, `pyproject.toml`, `nox`, `ruff`, `basedpyright`, `pytest`, `mutmut`,
  `Hypothesis`, `scalene`, Renovate, CodeQL, and release dry-runs are the
  current engineering foundation.

## Migration Direction

- Use `polars` for tabular ingestion and transformations where benchmark,
  readability, and compatibility evidence justify promotion.
- Use JAX/XLA for pure numerical kernels where vectorization or JIT materially
  helps and reproducibility tests pass.
- Use Rust for pure deterministic kernels only after Python parity, benchmark,
  profiling, mutation/security, and packaging evidence exists.
- Use `voiage` as an optional Value of Information backend once shared
  net-benefit and parameter-sample artifacts are stable.
- Treat `innovate` as the optional diffusion/adoption modelling sibling, and
  `mars` as the optional surrogate/metamodel sibling with a fixed core API.
- Keep Dask for current population simulation and PSA-style orchestration until
  an alternative has equivalent behavior and evidence.
- Keep async at orchestration boundaries only. It may help for service adapters,
  subprocess language bindings, progress streaming, or remote execution, but it
  is not the right tool for CPU-bound kernels.

## Dependency Policy

- Do not add future-engine packages to core dependencies speculatively.
- Add new technology through optional extras first.
- Promote an optional dependency only after compatibility tests, benchmark or
  validation evidence, documentation, CI coverage, and ownership are clear.
- Prefer dependency-free scaffolds for static decision and cohort Markov engines
  before adding specialized packages.
- Treat DES, ABM/network, survival-analysis, and workflow-orchestration
  packages as deferred until a concrete model requirement needs them.
- Keep `voiage` optional because its advanced VOI methods can bring heavier
  dependencies; prefer a `lifecourse[voiage]` extra after the integration
  contract and version policy are stable.
- Keep ecosystem sibling modules optional and artifact-first. New ideas should
  start as design notes or Conductor tracks, move to embedded subtrees only when
  real schemas or fixtures must mature next to `lifecourse`, and become
  standalone repositories only after contracts, docs, validators, ownership, and
  release policy are stable.
- Do not modify stable sibling APIs to satisfy `lifecourse`; use adapters or
  HEOML extension profiles instead.

## Documentation Requirements For Stack Changes

Each stack change must update:

- `docs/architecture_status.md` for current/default/experimental status.
- `conductor/tech-stack.md` for stack policy and migration rationale.
- `docs/stack_change_checklist.md` for the update checklist itself.
- `README.md` only when user-facing setup or usage changes.
- The relevant Conductor track `spec.md` and `plan.md`.
- `CHANGELOG.md` when behavior, dependencies, or workflows change.

The executable documentation and stack-readiness work is tracked in
`conductor/tracks/documentation_stack_readiness_20260428/plan.md`.

## Current Setup Assessment

The repo is correctly set up for the planned incremental migration, with one
important caveat: documentation is currently markdown-first and not yet backed by
a formal docs build. That is acceptable for near-term planning, but a dedicated
documentation system should be added before public multi-language bindings,
schema contracts, or multiple simulation engines become user-facing.
