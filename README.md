# LifeCourseID Microsimulation Model

## Overview

LifeCourseID is a comprehensive microsimulation model designed to evaluate the cost-effectiveness and budget impact of interventions related to a specific health condition. It simulates individual life courses over a defined time horizon, incorporating demographic events, disease progression, associated costs, and quality-adjusted life years (QALYs). The model is built with a modular Python package structure and leverages Dask for efficient parallel processing of simulations, particularly for probabilistic sensitivity analysis.

## Features

-   **Microsimulation Core:** Simulates individual life trajectories, including age progression, mortality, fertility, and diagnosis.
-   **Economic Evaluation:** Calculates health, education, social care, and employment-related costs, as well as QALYs.
-   **Parameter Uncertainty:** Incorporates probabilistic sampling of uncertain parameters from various statistical distributions (Beta, Gamma, Lognormal, Normal, Uniform).
-   **Scenario Analysis:** Supports running deterministic and subgroup scenarios defined in external YAML configuration files, allowing for flexible definition of intervention yields, familial prevalence, age-at-test, and time horizons.
-   **Probabilistic Sensitivity Analysis (PSA):** Performs Monte Carlo simulations to quantify the impact of parameter uncertainty on outcomes, utilizing Dask for parallel execution.
-   **Comprehensive Visualizations:** Generates a suite of plots for economic evaluation and sensitivity analysis:
    -   Cost-Effectiveness Plane
    -   Cost-Effectiveness Acceptability Curve (CEAC)
    -   Expected Value of Perfect Information (EVPI)
    -   Expected Net Monetary Benefit (ENMB) Curve
    -   One-Way Sensitivity (Tornado) Analysis
    -   Cost-Mix Stacked Area Plots (Prospective and Retrospective arms)
    -   PSA Histograms for Incremental Cost and QALYs
    -   Cost-Effectiveness Acceptability Frontier (CEAF)
    -   Sensitivity to Familial ID Prevalence
    -   Expected Value of Partial Perfect Information (EVPPI) Curves
-   **Budget Impact Analysis:** Estimates the incremental budget impact of interventions over a 5-year horizon.
-   **Equity Analysis:** Assesses the distribution of outcomes by socioeconomic quintile.
-   **Publication Comparison:** Facilitates comparison of simulation results with external published data.

## Project Structure

The project is organized into a modular Python package to enhance maintainability, reusability, and scalability:

```
LifeCourseID/
├── src/
��   ├── __init__.py
│   ├── model/
│   │   ├── __init__.py
│   │   ├── parameters.py
│   │   ├── cohort.py
│   │   └── population_system.py
│   └── analysis/
│       ├── __init__.py
│       └── run_helpers.py
├── main.py
├── requirements.txt
├── data/                 # For input data files (currently not used, but reserved)
├── results/              # All generated output CSVs and plots
├── tests/                # For unit and integration tests (future development)
├── config/               # For externalized configuration (future development)
├── archive/              # Contains older versions of notebooks and scripts
│   └── old_notebooks/
├── .gitignore
├── LICENSE
├── README.md
├── ROADMAP.md
└── CHANGELOG.md
```

### Module Breakdown:

-   **`src/model/parameters.py`**: Defines all global constants, fixed parameters, and the statistical distributions for uncertain parameters used in the microsimulation. It also includes helper functions for parameter sampling.
-   **`src/model/cohort.py`**: Contains functions responsible for generating the initial synthetic population cohort based on demographic distributions and other baseline characteristics.
-   **`src/model/population_system.py`**: Implements the core logic of the microsimulation. This class manages the population state and defines the annual step-by-step processes, including mortality, fertility, diagnosis, and the calculation of costs and QALYs for each individual.
-   **`src/analysis/run_helpers.py`**: Provides high-level functions (`run_sim` and `run_scenario`) to orchestrate the execution of the microsimulation model for different analytical purposes (e.g., single runs, scenario comparisons, data collection for detailed outputs).
-   **`main.py`**: The primary entry point for the application. It orchestrates the entire simulation and analysis workflow, calling functions from the `src/model` and `src/analysis` modules, and handling output generation.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/LifeCourseID.git
    cd LifeCourseID
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

To execute the full microsimulation and generate all analysis results (CSVs and plots), run the `main.py` script from the project root directory:

```bash
python main.py
```

Output files (e.g., `deterministic_summary.csv`, `psa_samples.csv`, and various `.png` plots) will be saved in the `results/` directory.

### Command Line Interface

You can also run a specific scenario using the lightweight CLI:

```bash
python cli.py base --pop-size 100
```

This reads `config/scenarios.yaml` and prints the incremental cost, QALY, and ICER for the chosen scenario.

### Running Tests

After installing dependencies, run the unit test suite with:

```bash
pytest -q
```

## Roadmap

For future development plans and upcoming features, please refer to the [ROADMAP.md](ROADMAP.md) file.

## Changelog

For a detailed history of changes and updates, please refer to the [CHANGELOG.md](CHANGELOG.md) file.

## License

This project is licensed under the [LICENSE](LICENSE) file.