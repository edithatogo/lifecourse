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
-   `main.py`: The main entry point to run the entire simulation and analysis workflow.
-   `requirements.txt`: Lists all Python package dependencies.
-   `data/`: Intended for any input data files required by the simulation.
-   `results/`: All generated output CSVs and plots are saved here.
-   `tests/`: Future location for unit and integration tests.
-   `config/`: Future location for externalized configuration files.
-   `archive/old_notebooks/`: Contains previous versions of the code (Jupyter notebooks and Python scripts) for historical reference.

## Key Features Implemented (from v7):

-   **Microsimulation Core:** Individual-level simulation of life courses.
-   **Probabilistic Sensitivity Analysis (PSA):** Quantifies uncertainty using sampled parameters from defined distributions.
-   **Cost-Effectiveness Analysis:** Calculates incremental costs and QALYs, and derives ICERs.
-   **Visualizations:** Generates various plots including CE-Plane, CEAC, EVPI, ENMB, Tornado plots, Cost-Mix stacked areas, and PSA histograms.
-   **Scenario Analysis:** Supports deterministic and subgroup analyses.
-   **Budget Impact Analysis:** Estimates financial impact over a specified period.
-   **Equity Analysis:** Assesses outcomes by socioeconomic quintile.
-   **Dask Integration:** Utilizes Dask for parallel processing of simulations, especially for PSA.

## How to Run

To run the full simulation and analysis, execute `python main.py` from the project root directory.

## Development Guidelines for Gemini

-   **Prioritize `src/` files:** When making changes, always refer to the modularized code in `src/` and `main.py`.
-   **Maintain Modularity:** Ensure any new features or refactorings adhere to the established module boundaries.
-   **Update Documentation:** If significant changes are made to the model logic or parameters, update relevant sections in `GEMINI.md`, `README.md`, `ROADMAP.md`, and `CHANGELOG.md`.
-   **Testing:** When implementing new features or fixing bugs, consider adding corresponding tests in the `tests/` directory.
-   **Output Management:** Ensure all generated output files (CSVs, plots) are saved to the `results/` directory.
-   **Dependencies:** If new Python packages are introduced, update `requirements.txt`.
