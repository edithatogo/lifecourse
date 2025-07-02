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
