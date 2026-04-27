# lifecourse Microsimulation Model - Requirements Specification

## 1. Introduction

### 1.1 Purpose

lifecourse is a comprehensive microsimulation model designed to evaluate the cost-effectiveness and budget impact of interventions related to a specific health condition. The model simulates individual life courses over a defined time horizon, incorporating demographic events, disease progression, associated costs, and quality-adjusted life years (QALYs).

### 1.2 Scope

The system will provide:

- Individual-level microsimulation of health trajectories
- Economic evaluation capabilities (cost-effectiveness analysis)
- Probabilistic sensitivity analysis (PSA) for uncertainty quantification
- Value of information analysis (EVPI, EVPPI, EVSI)
- Distributive cost-effectiveness analysis and equity assessment
- Budget impact analysis for financial planning
- Value-based pricing and price threshold analysis
- Multi-criteria decision analysis (MCDA) frameworks
- Scenario analysis with configurable parameters
- Comprehensive visualization and reporting of results
- Parallel processing using Dask for computational efficiency

### 1.3 Definitions and Acronyms

- **QALY**: Quality-Adjusted Life Year
- **ICER**: Incremental Cost-Effectiveness Ratio
- **PSA**: Probabilistic Sensitivity Analysis
- **WGS**: Whole Genome Sequencing
- **VUS**: Variants of Uncertain Significance
- **IF**: Incidental Findings
- **EVPI**: Expected Value of Perfect Information
- **EVPPI**: Expected Value of Partial Perfect Information
- **EVSI**: Expected Value of Sample Information
- **MCDA**: Multi-Criteria Decision Analysis
- **CEA**: Cost-Effectiveness Analysis
- **BIA**: Budget Impact Analysis
- **VBP**: Value-Based Pricing

## 2. Functional Requirements

### 2.1 Core Simulation Engine

#### 2.1.1 Population Generation

- **REQ-001**: System shall generate synthetic populations based on demographic distributions
- **REQ-002**: System shall support configurable population sizes (minimum 100, maximum 100,000+)
- **REQ-003**: System shall initialize individuals with baseline characteristics (age, sex, socioeconomic status)

#### 2.1.2 Life Course Simulation

- **REQ-004**: System shall simulate annual progression through life stages
- **REQ-005**: System shall model demographic events (mortality, fertility, aging)
- **REQ-006**: System shall track disease progression and diagnosis events
- **REQ-007**: System shall calculate costs and QALYs for each individual annually

#### 2.1.3 Economic Evaluation

- **REQ-008**: System shall calculate total healthcare costs (diagnosis, treatment, monitoring)
- **REQ-009**: System shall calculate productivity losses and informal care costs
- **REQ-010**: System shall compute QALYs based on health state utilities
- **REQ-011**: System shall generate ICERs for intervention comparisons

### 2.2 Analysis Capabilities

#### 2.2.1 Deterministic Analysis

- **REQ-012**: System shall perform point estimate analyses using mean parameter values
- **REQ-013**: System shall support scenario comparisons with different parameter sets
- **REQ-014**: System shall generate deterministic cost-effectiveness results

#### 2.2.2 Probabilistic Sensitivity Analysis

- **REQ-015**: System shall perform Monte Carlo simulations (minimum 1,000 iterations)
- **REQ-016**: System shall sample parameters from statistical distributions
- **REQ-017**: System shall generate uncertainty intervals for all outcomes
- **REQ-018**: System shall create cost-effectiveness acceptability curves (CEAC)

#### 2.2.3 Sensitivity Analysis

- **REQ-019**: System shall perform one-way sensitivity analysis (tornado diagrams)
- **REQ-020**: System shall perform multi-way sensitivity analysis
- **REQ-021**: System shall identify influential parameters

#### 2.2.4 Value of Information Analysis

- **REQ-022**: System shall calculate expected value of perfect information (EVPI)
- **REQ-023**: System shall calculate expected value of partial perfect information (EVPPI) for parameter subsets
- **REQ-024**: System shall calculate expected value of sample information (EVSI) for proposed research designs

#### 2.2.5 Distributive Cost-Effectiveness Analysis

- **REQ-025**: System shall perform equity analysis across socioeconomic groups
- **REQ-026**: System shall analyze cost-effectiveness distribution by demographic subgroups
- **REQ-027**: System shall calculate concentration indices for health outcomes
- **REQ-028**: System shall assess distributional impacts of interventions

#### 2.2.6 Budget Impact Analysis

- **REQ-029**: System shall project budget impact over defined time horizons (1-5 years)
- **REQ-030**: System shall calculate incremental budget costs by year
- **REQ-031**: System shall model adoption curves and market penetration
- **REQ-032**: System shall analyze budget impact uncertainty through sensitivity analysis

#### 2.2.7 Value-Based Pricing Analysis

- **REQ-033**: System shall determine optimal prices based on cost-effectiveness thresholds
- **REQ-034**: System shall calculate value-based price ranges for different willingness-to-pay levels
- **REQ-035**: System shall analyze pricing strategies under different reimbursement scenarios
- **REQ-036**: System shall assess price elasticity and market dynamics

#### 2.2.8 Price Threshold Analysis

- **REQ-037**: System shall calculate maximum cost-effective prices (threshold prices)
- **REQ-038**: System shall perform threshold analysis across different willingness-to-pay values
- **REQ-039**: System shall generate price threshold curves and acceptability frontiers
- **REQ-040**: System shall analyze threshold sensitivity to key parameters

#### 2.2.9 Multi-Criteria Decision Analysis (MCDA)

- **REQ-041**: System shall support weighted criteria evaluation frameworks
- **REQ-042**: System shall perform multi-attribute utility analysis
- **REQ-043**: System shall generate MCDA value functions and preference weights
- **REQ-044**: System shall create decision matrices for intervention comparison
- **REQ-045**: System shall perform sensitivity analysis on MCDA weights and scores

### 2.3 Visualization and Reporting

#### 2.3.1 Economic Evaluation Plots

- **REQ-046**: System shall generate cost-effectiveness plane plots
- **REQ-047**: System shall create CEAC and cost-effectiveness acceptability frontier (CEAF) curves
- **REQ-048**: System shall produce expected net monetary benefit (ENMB) curves
- **REQ-049**: System shall generate expected value of perfect information (EVPI) curves
- **REQ-050**: System shall generate expected value of partial perfect information (EVPPI) curves
- **REQ-051**: System shall generate expected value of sample information (EVSI) curves

#### 2.3.2 Additional Visualizations

- **REQ-052**: System shall create tornado sensitivity analysis plots
- **REQ-053**: System shall generate PSA scatter plots and histograms
- **REQ-054**: System shall produce cost-mix stacked area plots
- **REQ-055**: System shall create equity analysis plots by socioeconomic quintile
- **REQ-056**: System shall generate budget impact curves over time
- **REQ-057**: System shall create price threshold acceptability curves
- **REQ-058**: System shall produce MCDA radar plots and value function curves

### 2.4 Configuration and Scenarios

#### 2.4.1 Parameter Management

- **REQ-059**: System shall load parameters from YAML configuration files
- **REQ-060**: System shall support parameter overrides for scenario analysis
- **REQ-061**: System shall validate parameter ranges and types

#### 2.4.2 Scenario Analysis

- **REQ-062**: System shall support multiple intervention scenarios
- **REQ-063**: System shall allow relative and absolute parameter modifications
- **REQ-064**: System shall support automated scenario grid generation

### 2.5 User Interface

#### 2.5.1 Command Line Interface

- **REQ-065**: System shall provide CLI for scenario execution
- **REQ-066**: System shall support configuration file specification
- **REQ-067**: System shall provide debug and verbose output options

#### 2.5.2 Programmatic Interface

- **REQ-068**: System shall provide Python API for integration
- **REQ-069**: System shall support custom parameter sets programmatically

## 3. Non-Functional Requirements

### 3.1 Performance

- **PERF-001**: System shall complete PSA with 1,000 iterations in < 30 minutes on standard hardware
- **PERF-002**: System shall scale linearly with population size
- **PERF-003**: System shall utilize all available CPU cores efficiently
- **PERF-004**: Memory usage shall remain bounded for large populations

### 3.2 Reliability

- **REL-001**: System shall produce reproducible results with fixed random seeds
- **REL-002**: System shall handle edge cases gracefully (empty populations, invalid parameters)
- **REL-003**: System shall provide clear error messages for invalid inputs

### 3.3 Usability

- **USAB-001**: System shall provide clear documentation and examples
- **USAB-002**: System shall support standard YAML configuration formats
- **USAB-003**: System shall generate publication-ready plots and tables

### 3.4 Maintainability

- **MAINT-001**: Code shall achieve >90% test coverage
- **MAINT-002**: System shall follow modular architecture principles
- **MAINT-003**: Dependencies shall be explicitly declared and versioned

## 4. Technical Requirements

### 4.1 Platform Requirements

- **TECH-001**: System shall run on Python 3.10+
- **TECH-002**: System shall support Windows, macOS, and Linux platforms
- **TECH-003**: System shall work in standard Python environments (conda, venv, system Python)

### 4.2 Dependencies

- **DEP-001**: Core scientific computing: NumPy, Pandas, SciPy
- **DEP-002**: Parallel processing: Dask with distributed scheduler
- **DEP-003**: Data visualization: Matplotlib, Seaborn
- **DEP-004**: Configuration: PyYAML
- **DEP-005**: Data formats: PyArrow, openpyxl
- **DEP-006**: Testing: pytest, pytest-cov

### 4.3 Data Formats

- **DATA-001**: System shall read/write CSV files for results
- **DATA-002**: System shall read/write Excel files for results
- **DATA-003**: System shall read YAML files for configuration
- **DATA-004**: System shall support Parquet format for large datasets

### 4.4 Architecture

- **ARCH-001**: System shall follow object-oriented design principles
- **ARCH-002**: System shall separate data, logic, and presentation layers
- **ARCH-003**: System shall use Dask for lazy evaluation and parallel execution
- **ARCH-004**: System shall support modular parameter and scenario management

## 5. Constraints and Assumptions

### 5.1 Technical Constraints

- **CONST-001**: Maximum simulation horizon: 100 years
- **CONST-002**: Minimum population size: 100 individuals
- **CONST-003**: Maximum PSA iterations: Limited by available memory
- **CONST-004**: Parameter distributions: Limited to supported SciPy distributions

### 5.2 Business Constraints

- **CONST-005**: Health economic evaluation follows NICE reference case
- **CONST-006**: QALY calculations use standard utility weights
- **CONST-007**: Cost calculations include healthcare and societal perspectives

### 5.3 Assumptions

- **ASSUM-001**: Population characteristics follow specified demographic distributions
- **ASSUM-002**: Disease progression follows Markov model assumptions
- **ASSUM-003**: Costs and utilities are time-invariant (except inflation)
- **ASSUM-004**: No interaction between simulated individuals
- **ASSUM-005**: Perfect adherence to prescribed interventions

## 6. Testing Requirements

### 6.1 Unit Testing

- **TEST-001**: All core functions shall have unit tests
- **TEST-002**: Parameter sampling shall be tested for correctness
- **TEST-003**: Population generation shall be validated against known distributions

### 6.2 Integration Testing

- **TEST-004**: End-to-end simulation workflows shall be tested
- **TEST-005**: Configuration loading and validation shall be tested
- **TEST-006**: Parallel execution shall be verified

### 6.3 Performance Testing

- **TEST-007**: System shall be benchmarked for various population sizes
- **TEST-008**: Memory usage shall be monitored during long simulations
- **TEST-009**: Parallel scaling shall be validated

## 7. Deployment and Distribution

### 7.1 Packaging

- **DEPLOY-001**: System shall be distributed as Python package
- **DEPLOY-002**: System shall provide command-line entry points
- **DEPLOY-003**: System shall include comprehensive documentation

### 7.2 Installation

- **DEPLOY-004**: System shall install via pip from source or PyPI
- **DEPLOY-005**: System shall support development installation with dev dependencies
- **DEPLOY-006**: System shall verify platform compatibility during installation

## 8. Future Considerations

### 8.1 Extensibility

- **FUTURE-001**: System shall support additional disease models
- **FUTURE-002**: System shall allow custom cost and utility functions
- **FUTURE-003**: System shall support additional visualization types

### 8.2 Performance Enhancements

- **FUTURE-004**: System may implement GPU acceleration for large simulations
- **FUTURE-005**: System may support distributed computing clusters
- **FUTURE-006**: System may implement advanced caching strategies

## 9. Developer Guidance

### 9.1 Project Overview

This repository implements a microsimulation model (lifecourse) for health economic evaluation. Core logic lives under `src/lifecourse/`.

**Major components:**

- `src/lifecourse/model/` — parameter definitions (`parameters.py`), cohort generation (`cohort.py`), and the simulation engine (`population_system.py`).
- `src/lifecourse/analysis/` — orchestration helpers (`run_helpers.py`), plotting and advanced analyses.
- `src/lifecourse/cli.py` and `src/lifecourse/main.py` — entrypoints used for CI, ad-hoc runs, and `python -m lifecourse.main`.

**Data flow:** configuration -> parameter sampling (DISTRIBUTIONS) -> prepare dask params -> PopulationSystemDask instances -> run per-year steps -> aggregate outputs (deterministic & PSA CSVs in `results/`). See `main.py` and `analysis/run_helpers.py` for examples.

### 9.2 Developer Workflows & Common Commands

- Install deps: `pip install -r requirements.txt` (project requires Python >=3.10, see `pyproject.toml`).
- Run full analysis locally (single-process debug):
  - `python -m lifecourse.main --config_name MINIMAL_TEST_CONFIG --debug`
- Run a single scenario via CLI (fast, small pop):
  - `python -m lifecourse.cli base --pop-size 100 --debug`
- Run tests: `pytest -q` (tests rely on `src` being importable; the test harness already adjusts sys.path in `run_tests.py`).
- Use `--debug` flags to force single-threaded execution and verbose memory prints — helpful for reproducing or diagnosing issues (see `main.py` and `analysis/run_helpers.py`).

### 9.3 Project-Specific Conventions and Patterns

- **Dask-first design**: computations frequently return Dask objects (DataFrame/Series/arrays). Only call `.compute()` or `dd.compute(...)` at aggregation points. See `run_helpers.run_sim` and `run_scenario` for how Dask objects are collected and computed.
- **Parameter overrides from YAML**: `config/scenarios.yaml` uses relative vs absolute overrides. Small magnitude numeric changes (within ~±0.5) are treated as relative deltas; large magnitudes are absolute replacements. `apply_scenario_overrides` is used in `cli.py` and `main.py`.
- **Random seeds**: `run_sim` seeds numpy and python random with a base (42) + run index. When adding reproducible tests or debug runs, follow this seed pattern.
- **Resource-aware Dask config**: `main.py` probes system CPUs and memory using `psutil` and configures `LocalCluster`. When changing parallelism, prefer tuning in `main.py` logic rather than hardcoding workers elsewhere.
- **Population arms**: the engine creates two PopulationSystemDask instances with `arm` values `retrospective` and `prospective`. Most analyses compute difference (prospective - retrospective).

### 9.4 Integration Points & External Dependencies

- External YAML scenarios: `config/scenarios.yaml` — used to drive deterministic runs and scenario grids. Example keys: `familial_prop`, `yield_wgs`, `min_test_age`.
- Entry points (packaged scripts): defined in `pyproject.toml` under `[project.scripts]` — `lifecourse-cli` and `lifecourse-main` map to `lifecourse.cli:main` and `lifecourse.main:main`.
- Key third-party libs to be mindful of: Dask (distributed), pandas, numpy, psutil (resource probing), scipy (distributions), matplotlib/seaborn (plotting).

### 9.5 Code Editing Guidelines

When editing code, prefer small, well-scoped changes:

- Preserve Dask laziness. If you add new aggregation code, mirror existing pattern: collect Dask objects into a list, call `dd.compute(*list)` once, and then process pandas results.

- If new CLI flags are added, register them in `cli.py` and `main.py` for symmetry and update any code paths that call `load_config` (see `config/config_loader.py`).

- Unit tests: follow existing style in `tests/` — there is a mixture of pytest-based tests and custom `run_tests.py` harness that adjusts sys.path; prefer pytest-compatible tests for CI.

### 9.6 Key Files for Context

- `README.md` — high-level overview and common commands.
- `pyproject.toml` — Python requirements, scripts, and metadata.
- `src/lifecourse/main.py` — full-analysis entrypoint, Dask config, PSA orchestration.
- `src/lifecourse/cli.py` — lightweight scenario CLI used in quick runs and CI.
- `src/lifecourse/analysis/run_helpers.py` — canonical patterns for seeding, Dask scheduling, memory checks, and how run_sim/run_scenario return values are shaped.
- `src/lifecourse/model/parameters.py` and `src/lifecourse/model/population_system.py` — parameter names and the main simulation primitives.
- `config/scenarios.yaml` — scenario examples and grid definitions.

### 9.7 Safety and Testing Guidance

- Never remove the Dask/compute separation. Merging compute calls into per-iteration computes will drastically increase memory and time.
- When adding parameters, update `parameters.py` DISTRIBUTIONS and `get_mean_params` helper so sampling and mean extraction remain consistent.
- Keep `--debug` behavior: it is used heavily in tests and by developers to reproduce issues locally.

---

*Document Version: 1.0*
*Last Updated: October 2025*
*Author: lifecourse Development Team*
