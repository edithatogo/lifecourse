# Tech Stack

## Purpose
This document distinguishes the repo's current brownfield implementation from the target modernization direction. Until migration work is completed, the current stack remains the source of truth for how the project actually runs.

## Current Brownfield Baseline

### Runtime and Packaging
- Python 3.10+
- `setuptools`-based packaging via `pyproject.toml`
- dependency installation currently driven by `requirements.txt`

### Core Data and Numerical Stack
- `numpy`
- `pandas`
- `scipy`

### Parallel and Simulation Execution
- `dask` is currently used for parallel and distributed execution in the maintained codebase

### Visualization
- `matplotlib`
- `seaborn`

### Configuration and Data I/O
- `pyyaml`
- `pyarrow`
- `openpyxl`

### Quality and Developer Tooling
- `pytest`
- `pytest-cov`
- `ruff`
- `pre-commit`
- GitHub Actions CI

### Interfaces
- Python package API
- command-line interfaces for scenario runs and full workflow execution

## Implemented Foundation
The modernization foundation track has established these parts of the target stack as active project conventions:

### Package and Environment Management
- `uv` for dependency resolution, environment sync, build, and workflow execution
- `pyproject.toml` as the central location for runtime and tooling configuration

### Configuration and Validation
- `pydantic v2` for typed runtime configuration validation
- `pandera` for dataframe schema validation at data boundaries

### Quality Gates
- `ruff` as the main formatter and linter for the maintained modernization slice
- `basedpyright` in strict mode for checked modules
- `pytest` coverage enforcement above 90% for the maintained foundation scope

## Implemented Backend Evaluation Layer
The backend migration track has introduced an opt-in evaluation layer without
changing the production simulation runtime:

### Optional Backend Extras
- `tabular` extra for `polars` experimentation
- `jax` extra for JAX/XLA and `BlackJAX` experimentation
- `visualization` extra for `plotnine` experimentation
- `backends` extra for installing both optional backend groups

### Backend Decision Support
- `lifecourse.backend_evaluation.evaluate_backend_readiness` reports availability
  for current and candidate backend packages
- `lifecourse.backend_evaluation.recommend_tabular_backend` distinguishes
  `pandas`, `polars`, and `dask` candidates by workload shape
- `lifecourse.backend_evaluation.recommend_numerical_backend` distinguishes
  `numpy`, JAX, and `dask` candidates by workload shape
- `lifecourse.backend_evaluation.calculate_net_monetary_benefit` provides a
  small numerical pilot with default `numpy` execution and explicit optional JAX
  dispatch
- `lifecourse.backend_evaluation.calculate_evpi_value` provides the same
  default-NumPy, explicit-JAX dispatch pattern for the pure EVPI value kernel

### First Polars Pilot
- `lifecourse.data_loader.load_nz_population_distribution(..., backend="polars")`
  can use a Polars-backed CSV and normalization path when the optional `tabular`
  extra is installed
- the public return type remains a validated pandas DataFrame while downstream
  simulation code still depends on pandas and Dask
- `lifecourse.data_loader.load_nz_life_table_hazards(..., backend="polars")`
  can use the same opt-in Polars ingestion style while preserving the existing
  `dict[str, numpy.ndarray]` return shape

### First JAX-Class Analysis Hook
- `lifecourse.analysis.advanced_analysis.calculate_distributional_statistics`
  accepts `backend="jax"` for net-benefit vector calculations
- `lifecourse.analysis.advanced_analysis.calculate_evpi` accepts `backend="jax"`
  for the pure EVPI vector reduction
- this is an explicit analysis-level dispatch hook only; simulation execution
  remains `numpy`/`pandas`/`dask` by default

### Backend Benchmark Baseline
- `lifecourse.backend_benchmarks.benchmark_tabular_groupby` provides a
  deterministic pandas-compatible tabular benchmark with backend recommendation
  metadata
- `lifecourse.backend_benchmarks.benchmark_net_monetary_benefit` provides a
  deterministic NumPy vector benchmark with backend recommendation metadata
- `lifecourse.backend_benchmarks.benchmark_evpi_value` provides the selected
  EVPI kernel benchmark with recommendation metadata
- `lifecourse.backend_benchmarks.benchmark_dask_scheduler_overhead` and
  `benchmark_dask_independent_tasks` provide deterministic Dask evidence for
  small orchestration overhead and PSA-style independent task scheduling
- these benchmarks support migration decisions but are not CI performance gates

### Dask Orchestration Decision
- keep Dask for the current population/dataframe simulation runtime and larger
  independent PSA-style orchestration
- reduce Dask overhead for small deterministic simulation runs by selecting the
  synchronous scheduler through `lifecourse.analysis.run_helpers.select_dask_scheduler`
- do not replace Dask wholesale until there are equivalent tests for current
  population orchestration behavior

### Calibration Backend Decision
- keep existing `run_calibration` behavior available as the stable calibration
  entrypoint
- use `lifecourse.analysis.advanced_analysis.evaluate_calibration_backend_options`
  to separate deterministic parameter-search use cases from future Bayesian
  posterior workflows
- use `lifecourse.analysis.advanced_analysis.run_deterministic_calibration_search`
  as the current dependency-free deterministic pilot
- keep `BlackJAX` optional for future posterior-model work; defer `Optuna` until
  there is evidence that adaptive search materially improves calibration
  workflows

### Plotnine Visualization Pilot
- keep matplotlib as the default plotting runtime
- use `lifecourse.analysis.plotting.plot_deterministic_icers(..., backend="plotnine")`
  as the first optional grammar-of-graphics pilot
- keep `plotnine` behind the optional `visualization` extra until broader
  plotting migration evidence exists

### Release Automation Decision
- use `.github/workflows/release-dry-run.yml` to build and inspect artifacts
  without publishing
- use Renovate for grouped dependency update proposals
- use CodeQL for static security analysis
- keep DVC and package-index publishing deferred until operational ownership and
  artifact policies are explicit
- keep release automation dry-run safe before enabling TestPyPI, PyPI, or Conda
  publication

### Workflow, Mutation, and Profiling
- use `nox` as the local and CI workflow runner, backed by `uv`
- use scoped `mutmut` configuration for boundary modules before expanding to
  simulation-heavy code paths
- use `scalene` through representative profiling workloads before major
  performance rewrites
- keep Hypothesis focused on invariants and backend equivalence properties that
  example tests are unlikely to exhaust

### Internal Polars Tabular Pilot
- `lifecourse.data_loader.load_scenarios_from_yaml(..., scenario_backend="polars")`
  can expand scenario grids through an explicit Polars path
- the public return contract remains `dict[str, dict[str, Any]]`

## Target Modernization Direction

### Package and Environment Management
- adopt `uv` for dependency management, lockfile-driven installs, and virtual environment workflows
- consolidate tool configuration into `pyproject.toml`
- use `nox` or `tox` for repeatable local and CI session orchestration
- formalize versioning and release discipline instead of relying on manual version edits
- add publish automation for TestPyPI, PyPI, and Conda

### Data and Tabular Processing
- migrate tabular workflows from `pandas` toward `polars` where it improves performance and code clarity
- use `pandera` for dataframe-level validation while tabular interfaces remain central
- consider `pyjanitor` for well-scoped data-cleaning ergonomics, but keep it optional rather than foundational
- avoid standardizing both `polars` and `vaex` unless profiling shows a clear need for both

### Numerical Performance and Probabilistic Computation
- evaluate `JAX` and `XLA` for performance-sensitive numerical paths
- evaluate `BlackJAX` where Bayesian or Monte Carlo workflows justify it
- use `Optuna` for calibration, tuning, and controlled search over model or experimental parameters
- reassess whether `dask` remains necessary after profiling and architecture review
- do not assume `JAX`, `BlackJAX`, or `Optuna` are direct replacements for the current execution model

### Visualization
- migrate charting toward `plotnine` where grammar-of-graphics patterns improve consistency and publication quality
- retain the ability to generate clear static research figures suitable for papers, reports, and review

### Configuration, Validation, and Boundaries
- adopt `pydantic v2` for configuration models, schema validation, and explicit interfaces
- consider `hydra` for structured experiment configuration and composition if scenario complexity continues to grow
- separate configuration, parameter definitions, simulation logic, analysis pipelines, and reporting concerns more rigorously
- keep the CLI as a first-class supported interface

### Logging, Reliability, and Diagnostics
- standardize structured logging and clearer runtime diagnostics
- prefer the standard `logging` stack unless `loguru` solves a concrete ergonomics problem that justifies the extra dependency
- use `tenacity` for retryable boundaries such as file, network, or subprocess operations where transient failure is plausible
- use `scalene` for profiling and performance investigations before major architectural rewrites

### Quality Gates
- run `ruff` with strict rules enabled and use its formatting and linting capabilities as the primary Python quality gate
- adopt `basedpyright` in strict mode for type-checking
- raise required automated test coverage above 90%
- add mutation testing with `mutmut`
- add property-based testing with `Hypothesis`
- add prose linting with the selected prose tool
- keep CI responsible for enforcing formatting, linting, typing, tests, and coverage thresholds

### Data and Experiment Reproducibility
- use `DVC` for dataset and artifact versioning if model inputs and outputs need reproducible lineage
- consider `Pachyderm` only if the project evolves into larger-scale collaborative data pipelines that exceed what `DVC` and standard CI can support
- make experiment inputs, configs, outputs, and release artifacts traceable

### Automation and Maintenance
- use `Renovate` for dependency update automation
- keep GitHub Actions as the primary CI/CD system unless a concrete limitation forces a change
- do not introduce `Buildbot` unless there is a specific operational need that GitHub Actions cannot satisfy

### Multi-Language and Rust Migration
- keep Python as the reference implementation until cross-runtime contract tests,
  parity checks, benchmarks, and release governance justify promotion
- define JSON Schema as the control-plane contract for model requests and
  responses, with Arrow or Parquet preferred for typed tabular artifacts
- add wrapper-first adapters for R, Julia, Go, TypeScript, C#, Python, and Rust
  before native binding work
- target .NET 11 for C# adapter work
- use Cargo, rustfmt, clippy, criterion, cargo-audit, cargo-deny, and mutation
  or equivalent checks for Rust kernel candidates
- migrate only pure, deterministic, performance-sensitive kernels to Rust after
  Python parity and benchmark evidence

### Product-Credibility Roadmap
- add machine-readable parameter provenance, evidence metadata, and assumption
  audit outputs
- introduce a simulation engine interface so the current annual discrete-time
  microsimulation remains the default while static, cohort Markov,
  continuous-time, discrete-event, agent-based/network, and hybrid approaches can
  be evaluated as future engines
- keep future simulation-engine dependencies out of the core install until an
  approved engine implementation needs them; use optional extras, smoke CI,
  Renovate coverage, and benchmark or validation evidence before promotion
- refactor toward cohort strategy modules so future disease cohorts can share
  the same simulation infrastructure without editing core orchestration logic
- expand genomic testing pathways to model test type, counseling, VUS,
  incidental findings, uptake, and later cascade testing where justified
- add calibration and validation target artifacts with tolerance rules and
  baseline comparison reports
- emit reproducible reporting bundles with run manifests, checksums, output
  indexes, diagnostics, and publication-ready summaries
- incubate ecosystem modules outside the core package when they have a distinct
  dependency profile, public API, or reuse story; current sibling boundaries are
  `voiage` for VOI, `innovate` for diffusion/adoption, `mars` for stable
  surrogate/metamodel APIs, and HEOML for interchange
- keep future module integrations artifact-first and optional; use embedded
  subtrees only for schemas, fixtures, and docs that must mature with real
  `lifecourse` outputs before extraction

## Open Evaluation Items
These should remain explicitly undecided until validated by profiling, migration planning, or workflow pressure:

- whether `dask` should remain part of the long-term architecture
- whether `nox` or `tox` is the better task/session runner for this repository
- how far `polars` should replace existing `pandas` code versus coexist during migration
- whether `plotnine` should fully replace current plotting code or coexist with `matplotlib`
- whether `hydra` adds enough configuration leverage to justify its complexity
- whether simulation-framework alternatives such as `mesa` are actually beneficial for this model class
- whether any DES framework, graph library, survival-analysis package, or Markov
  modeling helper provides enough value to justify an optional engine extra
- whether `vaex`, `loguru`, `pyjanitor`, `Pachyderm`, or `Buildbot` solve real bottlenecks instead of adding stack sprawl

## Simulation Engine Dependency Policy

- Core dependencies remain tied to the current production engine: `numpy`,
  `pandas`, `scipy`, `dask`, validation libraries, plotting defaults, and data
  I/O.
- Static decision-model and cohort Markov scaffolds should start with existing
  numerical dependencies before adding specialized packages.
- Continuous-time engines should first use explicit hazard and competing-risk
  code with existing `scipy` primitives; survival-analysis packages should be
  optional and justified by validation or maintainability.
- Discrete-event engines should not add a DES framework until pathway timing,
  queues, capacity, or resource constraints are approved requirements.
- Agent-based or network engines should not add ABM or graph dependencies unless
  individual interactions, family cascade testing, or network diffusion are
  actually modeled.
- Hybrid engines should compose existing engine implementations before adding a
  separate orchestration framework.
- Every new engine dependency must have a documented owner, optional extra,
  Renovate coverage, CI smoke check, security posture, and removal path if it
  does not prove useful.

## Migration Principles
- prefer incremental migration over full rewrites
- require profiling, maintainability evidence, or workflow pressure before replacing core infrastructure
- preserve reproducibility and testability throughout the migration
- keep current and target stack definitions visible until migration is complete
- pair every stack transition with matching CI, packaging, validation, and documentation updates
- avoid adopting overlapping tools unless their boundaries are explicit

## Recommended Near-Term Sequence
1. Move packaging and tooling authority into `pyproject.toml` and adopt `uv`.
2. Add `basedpyright` strict mode, stricter `ruff`, and a >90% coverage gate.
3. Introduce `pydantic v2`, `pandera`, and structured configuration cleanup.
4. Add `Hypothesis`, `mutmut`, `scalene`, and `Optuna` where they improve confidence or calibration workflows.
5. Evaluate `polars` migration and profile whether `dask` is still justified before adopting `JAX`-class replacements.
6. Add release automation for TestPyPI, PyPI, and Conda, plus `Renovate` and data/artifact versioning with `DVC` if needed.
