# Changelog

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