# GEMINI.md

This file provides specific instructions and context for the Gemini CLI agent when interacting with the LifeCourseID project.

## Project Overview
LifeCourseID is a microsimulation model designed to evaluate the cost-effectiveness and budget impact of interventions related to a specific health condition over a lifetime. It simulates individual life courses, incorporating demographic events, disease progression, costs, and quality-adjusted life years (QALYs).

## Project Structure

The project now follows a modular Python package structure:

-   `src/`:
    -   `src/model/`: Contains the core simulation logic.
        -   `parameters.py`: Defines all global parameters, constants, and parameter distributions.
        -   `cohort.py`: Handles the generation of the initial population cohort.
        -   `population_system.py`: Implements the annual step-by-step simulation logic (mortality, fertility, diagnosis, cost/QALY calculation).
    -   `src/analysis/`: Contains functions for running simulations and performing various analyses.
        -   `run_helpers.py`: Provides `run_sim` and `run_scenario` functions to execute the microsimulation and collect results.
        -   `advanced_analysis.py`: Contains modules for calibration and structural uncertainty analysis.
    -   `src/data_loader.py`: Contains functions for loading external demographic data (currently NZ data preserved).
-   `main.py`: The main entry point for executing the full workflow.
-   `requirements.txt`: Lists all Python package dependencies.
-   `data/`: Intended for any input data files required by the simulation (e.g., local Australian demographic data).
-   `results/`: All generated output CSVs and plots are saved here.
-   `tests/`: Location for unit and integration tests.
-   `config/`: For externalized configuration files (e.g., `scenarios.yaml`).
-   `archive/old_notebooks/`: Contains previous versions of the code (Jupyter notebooks and Python scripts) for historical reference.

## Key Features Implemented (from v7):

-   **Microsimulation Core:** Individual-level simulation of life courses.
-   **Probabilistic Sensitivity Analysis (PSA):** Quantifies uncertainty using sampled parameters from defined distributions.
-   **Cost-Effectiveness Analysis:** Calculates incremental costs and QALYs, and derives ICERs.
-   **Visualizations:** Generates various plots including CE-Plane, CEAC, EVPI, ENMB, Tornado plots, Cost-Mix stacked areas, and PSA histograms.
-   **Scenario Analysis:** Supports running deterministic and subgroup scenarios defined in external YAML configuration files, allowing for flexible definition of intervention yields, familial prevalence, age-at-test, and time horizons.
-   **Budget Impact Analysis:** Estimates financial impact over a specified period.
-   **Equity Analysis:** Assesses outcomes by socioeconomic quintile.
-   **Publication Comparison:** Facilitates comparison of simulation results with external published data.
-   **Dask Integration:** Utilizes Dask for efficient parallel processing of simulations, especially for PSA.
-   **Enhanced Parameters:** Integrated NDIS cost, carer costs, hospitalization costs/rates, other common costs, income imputation parameters, education levels, and age bands.
-   **Calibration Analysis:** Placeholder module for model calibration.
-   **Structural Uncertainty Analysis:** Placeholder module for exploring structural variations.

## How to Run

To execute the full microsimulation and generate all analysis results (CSVs and plots), run the `main.py` script from the project root directory:

```bash
python main.py
```

Output files (e.g., `deterministic_summary.csv`, `psa_samples.csv`, and various `.png` plots) will be saved in the `results/` directory.

## Development Guidelines for Gemini

-   **Prioritize `src/` files:** When making changes, always refer to the modularized code in `src/` and `main.py`.
-   **Maintain Modularity:** Ensure any new features or refactorings adhere to the established module boundaries.
-   **Update Documentation:** If significant changes are made to the model logic or parameters, update relevant sections in `GEMINI.md`, `README.md`, `ROADMAP.md`, and `CHANGELOG.md`.
-   **Testing:** When implementing new features or fixing bugs, consider adding corresponding tests in the `tests/` directory.
-   **Output Management:** Ensure all generated output files (CSVs, plots) are saved to the `results/` directory.
-   **Dependencies:** If new Python packages are introduced, update `requirements.txt`.

## Parallel Development Strategy

To avoid conflicts and confusion when working with multiple sessions (or multiple developers), we will adhere to the following Git-based strategy:

1.  **Feature Branches:** For any new feature, bug fix, or significant integration task, always create a new Git branch from `main`.
    *   Example: `git checkout -b feature/my-new-feature`
2.  **Isolated Work:** Perform all work related to that task exclusively within its dedicated branch.
3.  **Frequent Commits:** Make small, logical commits within your branch as you progress.
4.  **Regular Pulls (from `main`):** Periodically pull the latest changes from the `main` branch into your feature branch to keep it up-to-date and resolve conflicts early.
    *   Example: `git pull origin main` (while on your feature branch)
5.  **Merge to `main`:** Once a task is complete and thoroughly tested (all tests pass on your feature branch), merge your feature branch back into `main`.
    *   Example: `git checkout main` -> `git pull` -> `git merge feature/my-new-feature` -> `git push`
6.  **Delete Feature Branch:** After a successful merge, delete the feature branch (optional, but good practice).
    *   Example: `git branch -d feature/my-new-feature`

This strategy ensures that work remains isolated, conflicts are managed systematically, and the `main` branch always contains stable, working code.
