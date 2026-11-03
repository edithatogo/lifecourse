## Lifecourse (LifeCourseID) — Copilot instructions for code changes

This file contains concise, actionable guidance for AI coding agents working in the `lifecourse` repository. Focus on the concrete patterns used here and reference the files that exemplify them.

1. Big picture
   - This repository implements a microsimulation model (LifeCourseID) for health economic evaluation. Core logic lives under `src/lifecourse/`.
   - Major components:
     - `src/lifecourse/model/` — parameter definitions (`parameters.py`), cohort generation (`cohort.py`), and the simulation engine (`population_system.py`).
     - `src/lifecourse/analysis/` — orchestration helpers (`run_helpers.py`), plotting and advanced analyses.
     - `src/lifecourse/cli.py` and `src/lifecourse/main.py` — entrypoints used for CI, ad-hoc runs, and `python -m lifecourse.main`.
   - Data flow: configuration -> parameter sampling (DISTRIBUTIONS) -> prepare dask params -> PopulationSystemDask instances -> run per-year steps -> aggregate outputs (deterministic & PSA CSVs in `results/`). See `main.py` and `analysis/run_helpers.py` for examples.

2. Developer workflows & common commands
   - Install deps: `pip install -r requirements.txt` (project requires Python >=3.10, see `pyproject.toml`).
   - Run full analysis locally (single-process debug):
     - `python -m lifecourse.main --config_name MINIMAL_TEST_CONFIG --debug`
   - Run a single scenario via CLI (fast, small pop):
     - `python -m lifecourse.cli base --pop-size 100 --debug`
   - Run tests: `pytest -q` (tests rely on `src` being importable; the test harness already adjusts sys.path in `run_tests.py`).
   - Use `--debug` flags to force single-threaded execution and verbose memory prints — helpful for reproducing or diagnosing issues (see `main.py` and `analysis/run_helpers.py`).

3. Project-specific conventions and patterns
   - Dask-first design: computations frequently return Dask objects (DataFrame/Series/arrays). Only call `.compute()` or `dd.compute(...)` at aggregation points. See `run_helpers.run_sim` and `run_scenario` for how Dask objects are collected and computed.
   - Parameter overrides from YAML: `config/scenarios.yaml` uses relative vs absolute overrides. Small magnitude numeric changes (within ~±0.5) are treated as relative deltas; large magnitudes are absolute replacements. `apply_scenario_overrides` is used in `cli.py` and `main.py`.
   - Random seeds: `run_sim` seeds numpy and python random with a base (42) + run index. When adding reproducible tests or debug runs, follow this seed pattern.
   - Resource-aware Dask config: `main.py` probes system CPUs and memory using `psutil` and configures `LocalCluster`. When changing parallelism, prefer tuning in `main.py` logic rather than hardcoding workers elsewhere.
   - Population arms: the engine creates two PopulationSystemDask instances with `arm` values `retrospective` and `prospective`. Most analyses compute difference (prospective - retrospective).

4. Integration points & external dependencies
   - External YAML scenarios: `config/scenarios.yaml` — used to drive deterministic runs and scenario grids. Example keys: `familial_prop`, `yield_wgs`, `min_test_age`.
   - Entry points (packaged scripts): defined in `pyproject.toml` under `[project.scripts]` — `lifecourse-cli` and `lifecourse-main` map to `lifecourse.cli:main` and `lifecourse.main:main`.
   - Key third-party libs to be mindful of: Dask (distributed), pandas, numpy, psutil (resource probing), scipy (distributions), matplotlib/seaborn (plotting).

5. When editing code, prefer small, well-scoped changes
   - Preserve Dask laziness. If you add new aggregation code, mirror existing pattern: collect Dask objects into a list, call `dd.compute(*list)` once, and then process pandas results.
   - If new CLI flags are added, register them in `cli.py` and `main.py` for symmetry and update any code paths that call `load_config` (see `config/config_loader.py`).
   - Unit tests: follow existing style in `tests/` — there is a mixture of pytest-based tests and custom `run_tests.py` harness that adjusts sys.path; prefer pytest-compatible tests for CI.

6. Examples & copy-paste snippets
   - Load scenarios and run deterministic scenarios (pattern used in `main.py`):
     ```py
     base_mean_params = get_mean_params(DISTRIBUTIONS)
     scenarios_config = load_scenarios_from_yaml("config/scenarios.yaml")
     for name, overrides in scenarios_config.items():
         params = apply_scenario_overrides(base_mean_params, overrides)
         dc, dq = run_sim(params, pop_size=current_pop_size, years=YEARS)
     ```

   - Collect Dask objects then compute (pattern used in `run_scenario`):
     ```py
     all = annual_list_r + annual_list_p + ses_r + ses_p
     computed = dd.compute(*all)
     # slice computed into respective year/arm lists
     ```

7. Files to inspect when you need context
   - `README.md` — high-level overview and common commands.
   - `pyproject.toml` — Python requirements, scripts, and metadata.
   - `src/lifecourse/main.py` — full-analysis entrypoint, Dask config, PSA orchestration.
   - `src/lifecourse/cli.py` — lightweight scenario CLI used in quick runs and CI.
   - `src/lifecourse/analysis/run_helpers.py` — canonical patterns for seeding, Dask scheduling, memory checks, and how run_sim/run_scenario return values are shaped.
   - `src/lifecourse/model/parameters.py` and `src/lifecourse/model/population_system.py` — parameter names and the main simulation primitives.
   - `config/scenarios.yaml` — scenario examples and grid definitions.

8. Safety and testing guidance for AI edits
   - Never remove the Dask/compute separation. Merging compute calls into per-iteration computes will drastically increase memory and time.
   - When adding parameters, update `parameters.py` DISTRIBUTIONS and `get_mean_params` helper so sampling and mean extraction remain consistent.
   - Keep `--debug` behavior: it is used heavily in tests and by developers to reproduce issues locally.

If any of this guidance is unclear or you want more code examples (e.g., how PopulationSystemDask is implemented or a minimal reproducible test), tell me which part to expand and I will update this file.
