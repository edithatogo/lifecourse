# Project Roadmap

This document outlines the future development plans for the LifeCourseID microsimulation project.

## Phase 1: Core Refactoring & Documentation (Completed)
- Modularize existing codebase into a Python package structure.
- Centralize parameters and simulation logic.
- Improve code readability and maintainability.
- Comprehensive documentation of project structure, setup, and usage.
- Establish clear output directories for results.

## Phase 2: Testing & Validation
- Implement unit tests for core simulation components (e.g., `PopulationSystemDask` methods, parameter sampling).
- Develop integration tests for `run_sim` and `run_scenario` functions.
- Validate simulation outputs against known benchmarks or previous versions.
- Set up a continuous integration (CI) pipeline for automated testing.

## Phase 3: Configuration & Extensibility
- Externalize simulation parameters and scenario definitions into configuration files (e.g., YAML, JSON).
- Implement a robust configuration loading mechanism.
- Explore options for dynamic scenario generation from configuration.
- Enhance flexibility for adding new cost categories, morbidity states, or policy interventions.

## Phase 4: Performance Optimization
- Investigate further Dask optimizations (e.g., custom Dask graphs, advanced scheduling).
- Profile code to identify bottlenecks and optimize critical sections.
- Explore alternative parallelization strategies if necessary.

## Phase 5: User Interface & Reporting
- Develop a simple command-line interface (CLI) for easier execution and scenario selection.
- Create more sophisticated reporting tools or dashboards for visualizing results.
- Automate report generation (e.g., PDF, HTML).

## Phase 6: Advanced Features
- Incorporate additional demographic complexities (e.g., migration, more detailed household structures).
- Implement more advanced disease progression models.
- Explore uncertainty analysis beyond PSA (e.g., value of information analysis for specific parameters).
