# Changelog

## Unreleased (Current Date - Please fill in)

### Added
- Comprehensive testing framework (Roadmap Phase 2):
  - Unit tests for `src/model/parameters.py`.
  - Unit tests for `src/model/cohort.py`.
  - Unit tests for `src/model/population_system.py`.
  - Integration tests for `src/analysis/run_helpers.py`.
  - Created `tests/__init__.py` to enable test discovery.
- GitHub Actions CI pipeline (`.github/workflows/ci.yml`):
  - Triggers on push/pull_request.
  - Installs dependencies from `requirements.txt`.
  - Runs all tests using `python -m unittest discover` across Python 3.10, 3.11, and 3.12.
- Project management and session tracking files:
  - `TODO.md` for listing pending tasks and future work.
  - `SESSION_SUMMARY.md` detailing work performed in the current session.

### Changed
- Updated `requirements.txt`:
  - Added `dask[distributed]` for full Dask capabilities.
  - Added `pyarrow` as an optional Dask dependency often needed for full performance/compatibility.
- `src/model/cohort.py`: Modified `gen_population_dask` to initialize all cost columns (including new ones like `cost_ndis`, `cost_carer`, `cost_hospital`, `cost_common_other`) to `0.0`. This resolved a Dask metadata error encountered during testing of `_cost_qaly`.
- `src/analysis/run_helpers.py`:
  - Refactored `run_scenario` to collect Dask Series for annual data and perform DataFrame structuring using pandas after computation. This resolved an `AttributeError` related to Dask DataFrame transpose operations.
  - Modified `run_sim` to seed Python's built-in `random` module in addition to `numpy.random`, enhancing reproducibility.

### Fixed
- Ensured deterministic behavior in `run_sim` for tests using `seed_idx` by seeding both `numpy.random` and `random`.
- Corrected typos in `tests/test_run_helpers.py` during development.
- Addressed various issues to enable successful generation of `deterministic_summary.csv` during validation attempts (though validation itself highlighted model discrepancies).

### Removed
- (Internal) Temporary modifications to `main.py` and `config/scenarios.yaml` made for validation debugging were reverted after the `reset_all` command and subsequent controlled re-application of changes.

### Process Note
- Used `reset_all()` to recover from persistent test timeouts after extensive `main.py` debugging for validation. All features and fixes from the session were then systematically re-applied to a clean repository state.

## 2025-07-02
- Initial project setup with modular Python package structure.
- Refactored `LifeCourseID, v7, 20250623.py` into:
    - `src/model/parameters.py`: Global parameters and distribution definitions.
    - `src/model/cohort.py`: Cohort generation logic.
    - `src/model/population_system.py`: Core population simulation steps.
    - `src/analysis/run_helpers.py`: Functions for running simulations and scenarios.
    - `main.py`: Main entry point for executing the full workflow.
- Created `src/__init__.py`, `src/model/__init__.py`, `src/analysis/__init__.py`.
- Updated `requirements.txt` with necessary dependencies.
- Configured output paths to save results (CSVs and plots) into the `results/` directory.
- Added comments to `pop_size` parameters in `LifeCourseID, v7, 20250623.py` to indicate testing values.
- Created `ROADMAP.md`.
- Archived old notebooks to `archive/old_notebooks/`.

## 2025-07-03
- Integrated maximum input parameters from older notebooks into `src/model/parameters.py`.
    - Added NDIS cost, carer costs, hospitalization costs/rates, other common costs.
    - Included income imputation parameters, education levels, and age bands for demographic distributions.
- Updated `src/model/cohort.py` to incorporate education, age bands, and income imputation during population generation.
- Updated `src/model/population_system.py` to utilize the new cost parameters in the `_cost_qaly` method.
- Optimized Dask usage by ensuring `compute()` calls are minimized and the Dask graph is maximized for parallelization (existing good practices confirmed).
- Externalized deterministic scenarios to `config/scenarios.yaml`.
- Modified `main.py` to dynamically load and apply scenario-specific parameter overrides from `config/scenarios.yaml`.
- Added placeholder `run_calibration` and `run_structural_uncertainty` functions in `src/analysis/advanced_analysis.py`.
- Integrated calls to `run_calibration` and `run_structural_uncertainty` in `main.py`.
- Refined the `run_structural_uncertainty` function in `src/analysis/advanced_analysis.py`.
- Updated Module 10 (Sub-group Analyses) in `main.py` to dynamically load and apply subgroup-specific parameter overrides from `config/scenarios.yaml`.
- Updated `README.md` to reflect the enhanced scenario analysis capabilities.
- Created `src/data_loader.py` for external demographic data loading.
- Updated `src/model/parameters.py` to load `AGE_DIST` and `ABS_MORT` from `src/data_loader.py`.

## 2025-07-28
- Added `drafts/__init__.py` to package the drafts directory for imports.
- Fixed `get_beta_params` to return `fixed` when mean is 0 or 1.
- Updated `run_sim` to set the Dask scheduler to single-threaded for reproducible tests.
- Enhanced the draft `PopulationSystem` step to apply mapped functions if callables.
- Adjusted parameter tests for clamped variance and lowercase keys.
- Added `pyarrow` and `dask[distributed]` to `requirements.txt`.
