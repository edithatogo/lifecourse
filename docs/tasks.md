# lifecourse Microsimulation Model - Kiro-Style Tasks Document

## Overview

This document provides a comprehensive task breakdown for the lifecourse microsimulation model based on the design specification. Tasks are organized by priority level and component, with clear status indicators and dependencies.

**Current Implementation Status:** Core simulation engine and basic analyses are fully implemented and tested. All critical infrastructure issues (package configuration, import paths, CLI functionality, validation discrepancies) have been resolved. Advanced analyses are partially implemented - most exist as inline code in `main.py` rather than modular classes. EVSI analysis, concentration indices, value-based pricing (VBP) analysis, and multi-criteria decision analysis (MCDA) have been fully implemented and integrated.

## Legend

- [x] **Completed**: Task fully implemented and tested
- [ ] **In Progress**: Task partially implemented, work ongoing
- [ ] **Planned**: Task designed but not yet implemented
- [ ] **Not Implemented**: Task not yet implemented despite previous claims
- [ ] **Under Review**: Task needs investigation or validation
- **Priority**: Critical/High/Medium/Low
- **Complexity**: Low/Medium/High/Very High

---

## 1. Core Architecture & Infrastructure

### 1.1 System Architecture Design

- [x] **High-Level Architecture Design** - Complete system architecture with component decomposition
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: Medium
  - Dependencies: None

- [x] **Data Flow Architecture** - Input → Processing → Output pipeline design
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: Medium
  - Dependencies: High-level architecture

- [x] **Conceptual Architecture** - Mermaid mindmap of system components
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: System architecture

### 1.2 Component Decomposition

- [x] **CLI/API Interface Design** - Command-line and programmatic interfaces
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: System architecture

- [x] **Configuration Management** - YAML-based parameter and scenario configuration
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Data flow architecture

- [x] **Core Simulation Engine** - Population generation, life course simulation, economic evaluation
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: High
  - Dependencies: All core components

- [x] **Analysis Modules Framework** - Deterministic analysis, PSA, sensitivity analysis
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: Core simulation engine

---

## 2. Core Simulation Engine

### 2.1 Population Generation (`cohort.py`)

- [x] **PopulationGenerator Class** - Core population generation with Dask DataFrames
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: Medium
  - Dependencies: NumPy, Pandas, Dask

- [x] **Demographic Modeling** - Age, sex, socioeconomic status, familial risk factors
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: PopulationGenerator

- [x] **Arm Support** - Prospective and retrospective intervention arms
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: PopulationGenerator

### 2.2 Parameter Management (`parameters.py`)

- [x] **ParameterManager Class** - Parameter sampling and mean extraction
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: Medium
  - Dependencies: SciPy distributions

- [x] **Distribution Support** - Beta, Gamma, Lognormal, Normal, Uniform distributions
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: SciPy

- [x] **Parameter Validation** - Bounds checking and validation rules
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: ParameterManager

### 2.3 Population System (`population_system.py`)

- [x] **PopulationSystemDask Class** - Dask-based parallel population processing
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: High
  - Dependencies: Dask, PopulationGenerator, ParameterManager

- [x] **Annual Progression Logic** - Year-by-year life course simulation
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: High
  - Dependencies: PopulationSystemDask

- [x] **Economic Evaluation** - Cost and QALY calculations per individual
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: High
  - Dependencies: PopulationSystemDask

- [x] **Memory Profiling** - Performance monitoring and memory checks
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: psutil

---

## 3. Analysis Framework

### 3.1 Run Helpers (`run_helpers.py`)

- [x] **run_sim Function** - Single simulation execution with parameter sampling
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: Medium
  - Dependencies: Core simulation engine

- [x] **run_scenario Function** - Scenario analysis with parameter overrides
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: run_sim

- [x] **Dask Scheduler Selection** - Automatic CPU/GPU scheduler based on debug mode
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: Dask

- [x] **Memory Profiling** - Performance monitoring and memory checks
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: psutil

### 3.2 Advanced Analysis (`advanced_analysis.py`)

- [x] **AnalysisModule Base Class** - Abstract base class for analysis interfaces
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: None

- [x] **Result Standardization** - Consistent result formats across modules
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: AnalysisModule

- [x] **Input Validation** - Parameter validation and error handling
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: AnalysisModule

**Note:** Most advanced analyses (PSA, VOI, BIA, sensitivity analysis) are currently implemented inline within `main.py` rather than as modular classes in `advanced_analysis.py`. The `advanced_analysis.py` file currently contains only calibration and structural uncertainty functions.

---

## 4. Advanced Analysis Modules

### 4.1 Value of Information (VOI) Analysis

- [x] **EVPI Implementation** - Expected Value of Perfect Information calculation
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: PSA results, regression metamodeling

- [x] **EVPPI Implementation** - Expected Value of Partial Perfect Information
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: EVPI, parameter subset selection

- [x] **EVSI Implementation** - Expected Value of Sample Information
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Very High
  - Dependencies: EVPPI, Bayesian methods

### 4.2 Distributive Cost-Effectiveness Analysis

- [x] **Equity Analysis Module** - Socioeconomic quintile analysis
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: PSA results

- [x] **Concentration Indices** - Health inequality measurement
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Equity analysis

- [x] **Subgroup ICERs** - Subgroup-specific incremental cost-effectiveness ratios
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: PSA results

- [x] **Distributional Impacts** - Analysis of distributional cost-effectiveness
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Subgroup ICERs

### 4.3 Budget Impact Analysis

- [x] **BIA Module Design** - Budget impact analysis framework
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Time series modeling

- [x] **Adoption Curve Modeling** - Logistic, exponential, stepwise adoption curves
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: BIA framework

- [x] **Incremental Budget Costs** - Calculation of incremental healthcare costs
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: Adoption curves

- [x] **Uncertainty Quantification** - PSA-based uncertainty in budget projections
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: PSA integration

### 4.4 Value-Based Pricing Analysis

- [x] **VBP Module Design** - Value-based pricing optimization framework
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: CEA framework

- [x] **Price Threshold Analysis** - Maximum acceptable price calculations
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: WTP analysis

- [x] **Optimal Price Ranges** - Price optimization under WTP constraints
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Price thresholds

- [x] **Reimbursement Scenarios** - Scenario-based reimbursement modeling
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Price ranges

### 4.5 Multi-Criteria Decision Analysis

- [x] **MCDA Module Design** - Multi-criteria decision analysis framework
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Decision theory

- [x] **Weighted Criteria Evaluation** - Weighted sum and analytic hierarchy process
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: MCDA framework

- [x] **Value Function Modeling** - Utility function modeling for criteria
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: Utility theory

- [x] **Decision Matrices** - Structured decision matrix generation
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: MCDA framework

---

## 5. Visualization & Reporting

### 5.1 Plotting Framework (`plotting.py`)

- [x] **EconomicPlot Base Class** - Abstract base class for economic plots
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: Matplotlib

- [x] **CEPlanePlot Class** - Cost-effectiveness plane visualization
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: EconomicPlot

- [x] **CEACPlot Class** - Cost-effectiveness acceptability curve
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: EconomicPlot

- [x] **VOIPlot Class** - Value of information curve plotting
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: EconomicPlot

- [x] **BudgetImpactPlot Class** - Budget impact curve visualization
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: EconomicPlot

- [x] **MCDAVisualization Class** - Radar plots for multi-criteria analysis
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: EconomicPlot

### 5.2 Reporting Framework

- [x] **ReportGenerator Class** - Automated report generation
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: Plotting framework

- [x] **Multiple Output Formats** - CSV, Excel, Parquet, PNG, PDF support
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: ReportGenerator

---

## 6. Configuration & Data Management

### 6.1 Configuration System

- [x] **YAML Configuration** - Human-readable configuration files
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: PyYAML

- [x] **Scenario Overrides** - Relative and absolute parameter overrides
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: YAML configuration

- [x] **Parameter Validation** - Schema validation for configuration files
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: Configuration system

### 6.2 Data Structures

- [x] **Population Data Model** - Dask DataFrame schema for population data
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Dask

- [x] **Results Data Model** - PSA results DataFrame schema
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Pandas

- [x] **File Format Support** - CSV, Excel, Parquet, JSON I/O
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: Data models

---

## 7. Interface Design

### 7.1 CLI Interface

- [x] **Main Execution Commands** - `lifecourse-main` with configuration options
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: Core simulation

- [x] **Scenario Commands** - `lifecourse-cli` for quick scenario runs
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Low
  - Dependencies: Analysis framework

- [x] **Configuration Options** - Debug flags, population size, scenario selection
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: CLI commands

### 7.2 Programmatic API

- [x] **LifeCourseModel Class** - Main programmatic interface
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: All components

- [x] **Analysis Methods** - `run_analysis()` with configurable parameters
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: LifeCourseModel

- [x] **Result Access** - Methods for accessing and plotting results
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: Analysis methods

---

## 8. Quality Assurance & Testing

### 8.1 Unit Testing

- [x] **Core Component Tests** - Tests for population generation, parameters, simulation
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: pytest

- [x] **Analysis Module Tests** - Tests for PSA, VOI, sensitivity analysis
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: pytest

- [x] **Integration Tests** - End-to-end testing of complete workflows
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: Unit tests

### 8.2 Performance Testing

- [x] **Benchmarking Framework** - pytest-benchmark integration
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: pytest

- [x] **Memory Profiling** - Memory usage monitoring and optimization
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: psutil

### 8.3 Code Coverage

- [x] **Coverage Reporting** - pytest-cov integration
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: pytest

---

## 9. Performance & Scalability

### 9.1 Dask Integration

- [x] **Parallel Processing** - Dask-based population simulation
  - Status: - [x] Completed
  - Priority: Critical
  - Complexity: High
  - Dependencies: Dask

- [x] **Memory Optimization** - Lazy evaluation and efficient partitioning
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Dask

- [x] **Scalable Population Sizes** - Support for 100,000+ individuals
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: Memory optimization

### 9.2 Resource Management

- [x] **System Resource Detection** - CPU and memory probing with psutil
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: psutil

- [x] **Adaptive Scheduling** - LocalCluster configuration based on system resources
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: Resource detection

---

## 10. Documentation & Maintenance

### 10.1 Design Documentation

- [x] **Design Specification** - Comprehensive design.md document
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: All components

- [x] **Architecture Diagrams** - Mermaid diagrams for system visualization
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: Design specification

- [x] **Feature Matrix** - Comprehensive feature status and priority matrix
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Low
  - Dependencies: Design specification

### 10.2 Code Documentation

- [x] **Docstrings** - Comprehensive function and class documentation
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: Codebase

- [x] **Type Hints** - Full type annotation coverage
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: Python 3.10+

### 10.3 Development Tooling

- [x] **Code Formatting** - ruff format (migrated from black)
  - Status: - [x] Completed
  - Priority: Low
  - Complexity: Low
  - Dependencies: ruff

- [x] **Type Checking** - pyright (migrated from mypy)
  - Status: - [x] Completed
  - Priority: Low
  - Complexity: Low
  - Dependencies: pyright

- [x] **Testing Environment** - tox for environment management
  - Status: - [x] Completed
  - Priority: Low
  - Complexity: Low
  - Dependencies: tox

---

## 11. Pending/Planned Tasks

### 11.1 Dynamic Configuration System

#### 11.1.1 Dynamic Parameter Loading Architecture

- [x] **Dynamic Parameter Loading System** - Design and implement system to replace hardcoded parameter files with config-driven loading
  - Status: - [x] Completed
  - Priority: High
  - Complexity: High
  - Dependencies: Current parameter system, configuration management

- [x] **Country-Specific Parameter Factory** - Create factory pattern for loading Australian vs NZ parameters dynamically
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Dynamic parameter loading system

- [x] **Config-Driven Parameter Overrides** - Extend YAML configuration to support full parameter file selection and dynamic loading
  - Status: - [x] Completed
  - Priority: High
  - Complexity: Medium
  - Dependencies: Configuration system, parameter factory

- [x] **Parameter Validation Framework** - Implement comprehensive validation for dynamically loaded parameters
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: Dynamic parameter loading system

#### 11.1.2 Dynamic Scenario Generation

- [x] **Dynamic Scenario Generation** - Automated scenario creation from configuration
  - Status: - [x] Completed
  - Priority: Medium
  - Complexity: Medium
  - Dependencies: Configuration system, dynamic parameter loading

### 11.2 Performance Optimization

- [ ] **GPU Acceleration Evaluation** - Assess JAX/BlackJAX for performance gains
  - Status: - [ ] Planned
  - Priority: Medium
  - Complexity: High
  - Dependencies: Performance profiling

 - [ ] **Advanced Dask Optimizations** - Custom graphs and scheduling improvements
   - Status: - [ ] In Progress
   - Priority: Medium
   - Complexity: High
   - Dependencies: Current Dask implementation
   - Notes: Following a recent refactor and test-fix cycle (library rename and API harmonization), targeted Dask optimizations are now being investigated. The immediate goal is to identify low-risk scheduler/graph optimizations that improve memory use and reduce wall time for large-population PSA jobs.

Recent profiling & validation summary

- Local validation: Full test suite run after refactor and fixes — 163 passed, 11 warnings; coverage ≈ 93%.
- Profiling context: Representative small-scale PSA runs (pop-size 10k in --debug single-process and small multicore LocalCluster runs) were profiled to produce execution time breakdowns and Dask task graphs.

Key findings:

- Warm-up and parameter sampling produced ~8-15% of total runtime in small-scale tests; parameter sampling can be batched and memoized for repeated PSA runs.
- Population generation and per-year progression are the dominant time consumers; partition size and map_partition usage materially change CPU and memory balance.
- Keeping Dask laziness and limiting explicit .compute() calls to aggregation points prevents unnecessary memory spikes; this pattern was preserved during fixes.
- No single profiler conflict: a test harness issue ("Another profiling tool is already active") was resolved by adjusting test-level profiler usage so CI runs don't collide with developer profiling tools.

Actions taken during the refactor/validation cycle:

- Standardized parameter loading in tests to use `get_parameter_attributes` + `get_mean_params` to avoid treating modules as dicts.
- Fixed multiple tests to patch and mock the correct symbols and signatures (examples: `run_scenario`, `run_sim`, `calculate_budget_impact_with_adoption`).
- Preserved Dask-first design; increased test coverage to guard against regressions introduced by eager evaluation.

Next steps for Advanced Dask Optimizations:

- [ ] Evaluate partitioning strategies (number and size of partitions) on a medium-sized cluster replica to find sweet spot for memory vs CPU.
- [ ] Run targeted Dask profiler (distributed.profile) on full PSA samples with pmap-style scheduling to capture hotspots.
- [ ] Prototype a custom task graph for the annual progression step that reduces intermediate materialization.
- [ ] Add benchmark tests to `tests/` to track wall time and memory for representative pop sizes (10k, 50k, 100k) and add as CI performance checks (optional gated job).

---

## 12. Task Dependencies & Critical Path

### 12.1 Critical Path Tasks

1. **Dynamic Configuration System** - Enable flexible country-specific and config-driven parameter management
2. **Core Simulation Engine** - Foundation for all other components
3. **Analysis Framework** - Required for advanced economic evaluations
4. **Configuration System** - Enables flexible scenario analysis
5. **Testing Infrastructure** - Ensures reliability and correctness

### 12.2 Risk Mitigation

- **Performance Bottlenecks**: Regular profiling and optimization reviews
- **Code Complexity**: Modular design with clear interfaces
- **Testing Gaps**: Comprehensive test coverage requirements
- **Documentation Drift**: Automated documentation validation

### 12.3 Success Metrics

- **Functional Completeness**: All - [x] tasks working correctly
- **Performance Targets**: Sub-5 minute runs for 10,000 population scenarios
- **Code Quality**: >90% test coverage, passing all linting checks
- **Documentation**: Complete design specification with visual diagrams

## 13. Developer Guidance

### 13.1 Project Overview

This repository implements a microsimulation model (lifecourse) for health economic evaluation. Core logic lives under `src/lifecourse/`.

**Major components:**

- `src/lifecourse/model/` — parameter definitions (`parameters.py`), cohort generation (`cohort.py`), and the simulation engine (`population_system.py`).
- `src/lifecourse/analysis/` — orchestration helpers (`run_helpers.py`), plotting and advanced analyses.
- `src/lifecourse/cli.py` and `src/lifecourse/main.py` — entrypoints used for CI, ad-hoc runs, and `python -m lifecourse.main`.

**Data flow:** configuration -> parameter sampling (DISTRIBUTIONS) -> prepare dask params -> PopulationSystemDask instances -> run per-year steps -> aggregate outputs (deterministic & PSA CSVs in `results/`). See `main.py` and `analysis/run_helpers.py` for examples.

### 13.2 Developer Workflows & Common Commands

- Install deps: `pip install -r requirements.txt` (project requires Python >=3.10, see `pyproject.toml`).
- Run full analysis locally (single-process debug):
  - `python -m lifecourse.main --config_name MINIMAL_TEST_CONFIG --debug`
- Run a single scenario via CLI (fast, small pop):
  - `python -m lifecourse.cli base --pop-size 100 --debug`
- Run tests: `pytest -q` (tests rely on `src` being importable; the test harness already adjusts sys.path in `run_tests.py`).
- Use `--debug` flags to force single-threaded execution and verbose memory prints — helpful for reproducing or diagnosing issues (see `main.py` and `analysis/run_helpers.py`).

### 13.3 Project-Specific Conventions and Patterns

- **Dask-first design**: computations frequently return Dask objects (DataFrame/Series/arrays). Only call `.compute()` or `dd.compute(...)` at aggregation points. See `run_helpers.run_sim` and `run_scenario` for how Dask objects are collected and computed.
- **Parameter overrides from YAML**: `config/scenarios.yaml` uses relative vs absolute overrides. Small magnitude numeric changes (within ~±0.5) are treated as relative deltas; large magnitudes are absolute replacements. `apply_scenario_overrides` is used in `cli.py` and `main.py`.
- **Random seeds**: `run_sim` seeds numpy and python random with a base (42) + run index. When adding reproducible tests or debug runs, follow this seed pattern.
- **Resource-aware Dask config**: `main.py` probes system CPUs and memory using `psutil` and configures `LocalCluster`. When changing parallelism, prefer tuning in `main.py` logic rather than hardcoding workers elsewhere.
- **Population arms**: the engine creates two PopulationSystemDask instances with `arm` values `retrospective` and `prospective`. Most analyses compute difference (prospective - retrospective).

### 13.4 Integration Points & External Dependencies

- External YAML scenarios: `config/scenarios.yaml` — used to drive deterministic runs and scenario grids. Example keys: `familial_prop`, `yield_wgs`, `min_test_age`.
- Entry points (packaged scripts): defined in `pyproject.toml` under `[project.scripts]` — `lifecourse-cli` and `lifecourse-main` map to `lifecourse.cli:main` and `lifecourse.main:main`.
- Key third-party libs to be mindful of: Dask (distributed), pandas, numpy, psutil (resource probing), scipy (distributions), matplotlib/seaborn (plotting).

### 13.5 Code Editing Guidelines

When editing code, prefer small, well-scoped changes:

- Preserve Dask laziness. If you add new aggregation code, mirror existing pattern: collect Dask objects into a list, call `dd.compute(*list)` once, and then process pandas results.

- If new CLI flags are added, register them in `cli.py` and `main.py` for symmetry and update any code paths that call `load_config` (see `config/config_loader.py`).

- Unit tests: follow existing style in `tests/` — there is a mixture of pytest-based tests and custom `run_tests.py` harness that adjusts sys.path; prefer pytest-compatible tests for CI.

### 13.6 Key Files for Context

- `README.md` — high-level overview and common commands.
- `pyproject.toml` — Python requirements, scripts, and metadata.
- `src/lifecourse/main.py` — full-analysis entrypoint, Dask config, PSA orchestration.
- `src/lifecourse/cli.py` — lightweight scenario CLI used in quick runs and CI.
- `src/lifecourse/analysis/run_helpers.py` — canonical patterns for seeding, Dask scheduling, memory checks, and how run_sim/run_scenario return values are shaped.
- `src/lifecourse/model/parameters.py` and `src/lifecourse/model/population_system.py` — parameter names and the main simulation primitives.
- `config/scenarios.yaml` — scenario examples and grid definitions.

### 13.7 Safety and Testing Guidance

- Never remove the Dask/compute separation. Merging compute calls into per-iteration computes will drastically increase memory and time.
- When adding parameters, update `parameters.py` DISTRIBUTIONS and `get_mean_params` helper so sampling and mean extraction remain consistent.
- Keep `--debug` behavior: it is used heavily in tests and by developers to reproduce issues locally.

---

This document is automatically maintained. Last updated: 2025-01-04
