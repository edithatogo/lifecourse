# Future Project Roadmap

This document outlines the future development plans for the lifecourse microsimulation project.

## Phase 3: Configuration & Extensibility
- Explore options for dynamic scenario generation from configuration.
- Enhance flexibility for adding new cost categories, morbidity states, or policy interventions.

## Phase 4: Performance Optimization
- Investigate further Dask optimizations (e.g., custom Dask graphs, advanced scheduling).
- Profile code to identify bottlenecks and optimize critical sections.
- Explore alternative parallelization strategies if necessary.
- Promote Polars or JAX pilots only after benchmark evidence, backend-equivalence
  tests, and reproducibility notes are in place.
- Keep future simulation-engine dependencies optional until a concrete static,
  Markov, continuous-time, DES, ABM/network, or hybrid engine implementation
  justifies them.

## Phase 5: User Interface & Reporting
- Develop a simple command-line interface (CLI) for easier execution and scenario selection.
- Create more sophisticated reporting tools or dashboards for visualizing results.
- Automate report generation (e.g., PDF, HTML).

## Phase 6: Advanced Features
- Incorporate additional demographic complexities (e.g., migration, more detailed household structures).
- Implement more advanced disease progression models.
- Explore uncertainty analysis beyond PSA (e.g., value of information analysis for specific parameters).
  - *Status: Expected Value of Sample Information (EVSI) analysis has been implemented and integrated into the main workflow.*
  - *Status: Concentration Index analysis for socioeconomic-related health inequality measurement has been implemented and integrated into the main workflow.*

## Engineering Hardening
- Expand strict typing from the maintained boundary modules toward all production
  modules.
- Expand property-based tests to cover stochastic and outcome invariants.
- Use scoped mutation testing as a regression guard for input validation,
  scenario expansion, and backend dispatch code.
- Keep Renovate, CodeQL, dry-run release builds, and lockfile checks active in CI.
- Add documentation checks and a docs site only when the markdown-first docs no
  longer provide enough structure for users and contributors.
