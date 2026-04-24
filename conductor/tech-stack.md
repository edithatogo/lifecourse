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

## Open Evaluation Items
These should remain explicitly undecided until validated by profiling, migration planning, or workflow pressure:

- whether `dask` should remain part of the long-term architecture
- whether `nox` or `tox` is the better task/session runner for this repository
- how far `polars` should replace existing `pandas` code versus coexist during migration
- whether `plotnine` should fully replace current plotting code or coexist with `matplotlib`
- whether `hydra` adds enough configuration leverage to justify its complexity
- whether simulation-framework alternatives such as `mesa` are actually beneficial for this model class
- whether `vaex`, `loguru`, `pyjanitor`, `Pachyderm`, or `Buildbot` solve real bottlenecks instead of adding stack sprawl

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
