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

## Running the Model

Run the full workflow:

```bash
uv run lifecourse-main
```

Run the lightweight scenario CLI:

```bash
uv run lifecourse-cli base --pop-size 100 --debug
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
- `basedpyright`
- `pytest-cov`
- a `>90%` coverage threshold for the maintained foundation scope

## Configuration

Simulation settings live in `config/simulation_configs.py`, `config/config_loader.py`, and `config/scenarios.yaml`.

- Numeric scenario overrides within `±0.5` are treated as relative adjustments.
- Larger numeric values replace the base value.
- Non-numeric values are applied as absolute overrides.

## Documentation

- `conductor/` contains the project context, tech stack, workflow, and completed track history.
- `ROADMAP.md` contains future product direction.
- `CHANGELOG.md` captures released changes.
- `CONTRIBUTING.md` describes collaboration expectations.

## Notes

- `archive/old_notebooks/` contains historical research material and should be treated as reference only.
- The repository is actively being modernized, so the live implementation should be treated as the source of truth over archived notebooks and drafts.

## License

This project is licensed under the [LICENSE](LICENSE) file.
