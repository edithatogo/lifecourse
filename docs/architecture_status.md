# Architecture Status

This document separates production defaults from optional pilots and engineering
workflow gates.

## Production Defaults

- Environment and packaging: `uv`, `pyproject.toml`, `setuptools`, and `uv.lock`.
- Simulation runtime: `numpy`, `pandas`, and `dask`.
- Validation boundaries: `pydantic v2` for configuration and scenario YAML shape;
  `pandera` for dataframe schemas at data-loading boundaries.
- Quality gates: `ruff`, `basedpyright`, `pytest`, coverage enforcement, package
  build checks, and CodeQL.
- Workflow runner: `nox` sessions backed by `uv`.

## Optional Pilots

- `polars` is available for selected ingestion and scenario-grid expansion paths.
  Public contracts still return pandas-compatible objects or existing dict shapes.
- `jax`/XLA is available for selected pure numerical analysis kernels. Simulation
  execution remains NumPy/Dask by default.
- `plotnine` is available for the deterministic ICER pilot. Matplotlib remains the
  default plotting runtime.
- `BlackJAX` is available as an optional dependency for future posterior-model
  workflows, but no posterior calibration model is active.

## Quality And Maintenance Workflows

- `nox -s lint` runs formatting and lint checks.
- `nox -s typecheck` runs strict static type checks for the typed maintained slice.
- `nox -s tests` runs the full pytest suite with coverage.
- `nox -s build` builds package artifacts.
- `nox -s mutation` runs the scoped `mutmut` baseline for high-value boundary code.
- `nox -s profile` runs representative Scalene profiling workloads.
- Renovate is configured for conservative grouped dependency updates.

## Promotion Criteria

Promote an optional pilot to a production default only when it has:

- API compatibility tests against the existing default path.
- Benchmark evidence for realistic model sizes.
- Reproducibility notes for random number generation and numerical precision.
- CI coverage for the relevant optional extra.
- Documentation for users and contributors.

## Deferred Items

- DVC should wait until model inputs and outputs have a stable artifact retention
  policy.
- TestPyPI, PyPI, and Conda publishing should wait until release ownership and
  credential policy are explicit.
- Optuna should wait until adaptive calibration search has a real objective and
  evidence that it outperforms deterministic candidate search.

## Planned Migration Tracks

- Language-neutral contracts and bindings are planned as a multi-track migration:
  contract/schema artifacts first, wrapper-first language adapters second, Rust
  kernel migration only after parity and benchmark evidence, and separate
  cross-runtime CI and release governance tracks.
- Product-goal-aligned feature tracks are also planned for parameter provenance,
  simulation-engine modularity, multi-cohort architecture, richer genomic
  testing pathways, calibration and external validation targets, and
  reproducible reporting bundles.
- `voiage` integration is planned as an optional Value of Information backend
  through shared net-benefit and parameter-sample artifacts, not as a required
  runtime dependency.
- Language adapter scaffolds now exist under `bindings/` for R, Julia, Go,
  TypeScript, C#, and Rust. They are wrapper-first placeholders that consume
  the core API contract and shared fixtures.
- Bindings versioning, support tiers, and release governance are documented in
  `docs/bindings_versioning.md` and the bindings release governance track.
- Adapter examples and invocation assumptions are documented in
  `docs/bindings_examples.md`.
- Broader ecosystem modules are planned through an incubation strategy:
  `innovate` remains the diffusion/adoption sibling, `mars` remains the
  fixed-API surrogate/metamodel sibling, and new advanced concerns should move
  through design notes, embedded subtrees, standalone repos, and optional
  adapters only when their contracts and dependencies are justified.
- These tracks support the repo goal of credible, reproducible health-economic
  microsimulation. They are not production defaults until their Conductor plans
  and acceptance criteria are completed.

## Language Bindings And Rust

- Python remains the reference implementation and the current default execution
  path.
- The R, Julia, Go, TypeScript, C#, and Rust scaffolds under `bindings/` are
  wrapper-first and experimental; they invoke the Python reference contract
  rather than reimplementing model logic.
- Rust kernel candidates should stay limited to pure, deterministic kernels
  until parity, benchmarks, and support policy are in place.
- Native bindings are deferred until the contract, release policy, and
  cross-runtime quality gates are stable enough to justify them.

## Simulation Approach Direction

- The current production model is an annual discrete-time individual
  microsimulation backed by Dask.
- Future simulation approaches should be added behind an engine interface rather
  than mixed into `PopulationSystemDask`.
- Recommended future candidates are static decision models for one-shot testing
  questions, cohort Markov or semi-Markov models for aggregate state-transition
  analyses, continuous-time individual simulation for event-timing questions,
  discrete-event simulation for pathway and queueing questions, agent-based or
  network simulation only when individual interaction matters, and hybrid models
  where different subproblems need different formalisms.
- Dependency policy for future engines is conservative: no new simulation
  framework should enter the core install until a concrete engine implementation
  needs it, and new engine packages should start as optional extras with smoke
  CI, Renovate coverage, documentation, and promotion criteria.

## Interchange Direction

- Portable model/data exchange should use versioned run bundles with JSON
  metadata, JSON Schema validation, Arrow/Parquet typed tables, CSV
  compatibility exports, and checksummed figures.
- Pickle is not an interchange format for this project. It may be used only for
  explicitly labelled local debugging artifacts outside compatibility promises.
- Control-plane versus data-plane artifact rules are documented in
  `docs/interchange/artifact_formats.md`.
- `voiage` integration should consume bundle artifacts rather than importing
  simulation internals.

## Documentation Status

- Documentation is currently markdown-first and lives in `README.md`, `docs/`,
  `conductor/`, `CONTRIBUTING.md`, `RELEASE.md`, `CHANGELOG.md`, and
  `FUTURE_ROADMAP.md`.
- The maintained documentation map and status labels live in
  `docs/documentation_plan.md`.
- `docs/stack_strategy.md` is the dependency and migration-policy reference.
- `docs/stack_change_checklist.md` is the stack-change update checklist.
- `docs/documentation_plan.md` is the documentation roadmap.
- `docs/simulation_engine_status.md` and `docs/scientific_model_status.md`
  capture the current simulation and scientific/model documentation boundary.
- `scripts/check_docs.py` is the repo-local markdown docs check, and `nox -s docs`
  runs it.
- CI runs both the repo docs check and Markdown prose linting.
- `RELEASE.md` is the release automation and deprecation-policy reference.
- `conductor/tracks/documentation_stack_readiness_20260428/plan.md` is the
  executable plan for docs checks, docs tooling, and stack-change documentation
  requirements.
- A generated docs site is deferred until schema contracts, language adapters,
  multiple engines, or public release workflows make markdown-only docs too hard
  to navigate.
