# `lifecourse` Microsimulation Model

## Overview

`lifecourse` is a Python microsimulation model for evaluating the cost-effectiveness and budget impact of genomic testing interventions across simulated life courses. It models individual-level trajectories, uncertainty, and scenario comparisons for research and policy evaluation.

The maintained implementation is a standard Python package under `src/lifecourse/`. It currently uses `uv` for environment management and package execution, `pydantic v2` and `pandera` for validation boundaries, `ruff` for linting and formatting, `basedpyright` for strict type checking, and `pytest` for tests.

## Current Capabilities

- Individual-level microsimulation with retrospective and prospective arms
- Deterministic scenario analysis and scenario grids
- Probabilistic sensitivity analysis
- Budget impact and equity-related analysis
- Publication-oriented plots and summary outputs
- CLI entry points for scenario runs and full workflow execution

## Repository Layout

```text
lifecourse/
├── src/
│   └── lifecourse/
│       ├── cli.py
│       ├── main.py
│       ├── data_loader.py
│       ├── data_validation.py
│       ├── config_validation.py
│       ├── analysis/
│       └── model/
├── config/
│   ├── config_loader.py
│   ├── scenarios.yaml
│   └── simulation_configs.py
├── conductor/
├── tests/
├── scripts/
├── docs/
├── archive/
└── pyproject.toml
```

## Installation

The preferred development workflow uses `uv`:

```bash
uv sync --all-extras --dev
```

Optional backend evaluation extras are available for contributors working on
future data-engine or numerical-acceleration tracks:

```bash
uv sync --extra tabular      # includes polars
uv sync --extra jax          # includes JAX/XLA and BlackJAX
uv sync --extra visualization # includes plotnine
uv sync --extra backends     # includes both backend evaluation groups
```

These extras are not required for the default maintained workflow, which still
uses `numpy`, `pandas`, and `dask`.

## Running the Model

Run the full workflow:

```bash
uv run lifecourse-main
```

Run the lightweight scenario CLI:

```bash
uv run lifecourse-cli base --pop-size 100 --debug
```

Inspect the installed package version:

```bash
uv run lifecourse-cli --version
uv run lifecourse-main --version
```

Run the main module directly:

```bash
uv run python -m lifecourse.main --config_name MINIMAL_TEST_CONFIG
```

Provide an external configuration file:

```bash
uv run python -m lifecourse.main --config_file path/to/your_config.yaml
```

## Testing

Run the test suite:

```bash
uv run pytest
```

The repository also enforces linting, type checking, and coverage gates in CI. The current modernization foundation uses:

- `ruff`
- `vale` for prose linting in Markdown docs
- `basedpyright`
- `pytest-cov`
- `nox` workflow sessions
- `mutmut` for scoped mutation testing
- `scalene` for representative profiling runs
- Renovate for grouped dependency update automation
- CodeQL for static security analysis
- a `>90%` coverage threshold for the maintained foundation scope

Language adapter scaffolds live under `bindings/` and locate shared schemas and
fixtures from `specs/core-api/` rather than duplicating model logic.

Runtime diagnostics use standard-library logging. CLI entry points configure
logging from `--log-level`, `--debug`, or `LIFECOURSE_LOG_LEVEL`.

Version checks require `project.version` in `pyproject.toml` to have a matching
`CHANGELOG.md` section before release work proceeds.

Common workflow sessions:

```bash
uv run nox -s lint
uv run nox -s typecheck
uv run nox -s version
uv run nox -s tests
uv run nox -s build
uv run nox -s mutation
uv run nox -s profile
```

The backend modernization direction is incremental. The package includes
`lifecourse.backend_evaluation` to report optional backend availability,
recommend candidate backends for workload shapes, and run a small net monetary
benefit vector calculation through `numpy` by default or JAX when explicitly
requested and installed.

The first opt-in Polars pilot is available at the New Zealand population
ingestion boundary:

```python
from lifecourse.data_loader import load_nz_population_distribution

population = load_nz_population_distribution(backend="polars")
```

This path still returns a validated pandas DataFrame so existing simulation code
does not need to change.

The New Zealand life-table hazard loader also supports the same opt-in backend
style:

```python
from lifecourse.data_loader import load_nz_life_table_hazards

hazards = load_nz_life_table_hazards(backend="polars")
```

This still returns the existing `dict[str, numpy.ndarray]` shape expected by the
model.

Analysis-level JAX hooks are available in distributional statistics and EVPI:

```python
from lifecourse.analysis.advanced_analysis import (
    calculate_distributional_statistics,
    calculate_evpi,
)

stats = calculate_distributional_statistics(psa_results, backend="jax")
evpi = calculate_evpi(psa_results, backend="jax")
```

JAX remains opt-in. The default call still uses `numpy`.

Backend migration benchmark helpers are available for local decision support:

```python
from lifecourse.backend_benchmarks import (
    benchmark_dask_independent_tasks,
    benchmark_dask_scheduler_overhead,
    benchmark_evpi_value,
    benchmark_net_monetary_benefit,
    benchmark_tabular_groupby,
)

tabular = benchmark_tabular_groupby(row_count=10_000).as_dict()
numeric = benchmark_net_monetary_benefit(item_count=10_000).as_dict()
evpi = benchmark_evpi_value(item_count=10_000).as_dict()
dask_small = benchmark_dask_scheduler_overhead(item_count=1_000).as_dict()
dask_psa = benchmark_dask_independent_tasks(task_count=100).as_dict()
```

Current Dask guidance is conservative: keep it for the population/dataframe
simulation runtime and larger independent PSA-style orchestration, but use
synchronous scheduling for small deterministic simulation runs to avoid
unnecessary threaded scheduling overhead.

Calibration backend evaluation is also explicit and opt-in. The current pilot is
a dependency-free deterministic candidate search:

```python
from lifecourse.analysis.advanced_analysis import (
    evaluate_calibration_backend_options,
    run_deterministic_calibration_search,
)

decision = evaluate_calibration_backend_options(
    use_case="parameter_search",
    stochastic_model=False,
    requires_posterior_sampling=False,
)
search = run_deterministic_calibration_search(candidates, objective)
```

`BlackJAX` remains reserved for future posterior-model workflows. `Optuna` is not
required by the current runtime.

The first optional plotnine visualization pilot is available for deterministic
ICER bar charts:

```python
from lifecourse.analysis.plotting import plot_deterministic_icers

plot_deterministic_icers(det_df, backend="plotnine")
```

The default call still uses matplotlib and writes the same output path.

Release automation is currently dry-run safe. The `Release Dry Run` workflow
builds and inspects package artifacts without publishing. See `RELEASE.md` for
the current automation scope and deferred publishing prerequisites.

These helpers report timings and recommendations, but they are not hard CI
performance gates.

Scenario-grid expansion has an opt-in internal Polars path for migration
experiments:

```python
from lifecourse.data_loader import load_scenarios_from_yaml

scenarios = load_scenarios_from_yaml(
    "config/scenarios.yaml",
    scenario_backend="polars",
)
```

The return contract remains `dict[str, dict[str, Any]]`.

## Configuration

Simulation settings live in `config/simulation_configs.py`, `config/config_loader.py`, and `config/scenarios.yaml`.

- Numeric scenario overrides within `±0.5` are treated as relative adjustments.
- Larger numeric values replace the base value.
- Non-numeric values are applied as absolute overrides.

## Documentation

- `conductor/` contains the project context, tech stack, workflow, and completed track history.
- `docs/architecture_status.md` describes production defaults, optional pilots, quality gates, and promotion criteria.
- `docs/stack_strategy.md` clarifies production dependencies, optional migration tools, async boundaries, and promotion rules.
- `docs/documentation_plan.md` describes the documentation roadmap and maintenance rules.
- `docs/interchange/model_interchange_strategy.md` describes portable bundle and VOI interchange expectations.
- `docs/ecosystem/module_incubation_strategy.md` describes how sibling modules,
  embedded subtrees, adapters, and future repos should be separated.
- `heoml/` contains the provisional embedded HEOML interchange profile for portable health-economic model artifacts.
- `FUTURE_ROADMAP.md` contains future product direction.
- `CHANGELOG.md` captures released changes.
- `CONTRIBUTING.md` describes collaboration expectations.

## Notes

- `archive/old_notebooks/` contains historical research material and should be treated as reference only.
- The repository is actively being modernized, so the live implementation should be treated as the source of truth over archived notebooks and drafts.

## License

This project is licensed under the [LICENSE](LICENSE) file.
