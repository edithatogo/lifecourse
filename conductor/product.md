# Product Guide

## Product Summary
`lifecourse` is a modular Python microsimulation model for evaluating the cost-effectiveness and budget impact of genomic testing interventions across simulated individual life courses. The maintained package supports deterministic analysis, scenario comparison, probabilistic sensitivity analysis, equity-related analysis, budget impact estimation, and publication-oriented outputs for research and policy evaluation.

## Decision Context
The current maintained model is centered on familial intellectual disability and related genomic testing decisions. The default parameterization is Australian, with a New Zealand parameter variant also present in the codebase. The product is intended to support structured comparison of intervention strategies, costs, QALYs, ICERs, and uncertainty under configurable assumptions.

This is research and policy evaluation software. It is not a clinical diagnostic system, not a bedside decision-support tool, and not a substitute for expert methodological judgment.

## Primary Users
- Health economists and policy analysts evaluating cost-effectiveness, uncertainty, and budget impact.
- Research collaborators validating assumptions, extending methodology, or comparing results against published work.
- Technical users running scenarios, PSA workflows, diagnostics, and automated tests locally or in CI.

## Core User Needs
- Run repeatable analyses from explicit configuration rather than ad hoc notebook edits.
- Compare baseline and intervention scenarios with transparent assumptions.
- Quantify uncertainty through PSA and sensitivity analyses.
- Generate outputs suitable for technical review, stakeholder interpretation, and downstream reporting.
- Extend model behavior safely without obscuring parameter provenance or breaking regression expectations.

## Product Goals
- Provide a credible and maintainable simulation platform for health-economic evaluation.
- Keep the analytical pipeline modular so simulation logic, parameter loading, scenario definition, and plotting can evolve independently.
- Preserve traceability between assumptions, configuration, outputs, and tests.
- Support both exploratory research workflows and disciplined package-based development.

## Primary Outputs
A successful analysis workflow should be able to produce:
- Scenario-level incremental cost, incremental QALY, and ICER outputs.
- Deterministic summary artifacts for core scenario comparisons.
- PSA sample outputs and uncertainty summaries.
- Budget impact projections over the configured horizon.
- Visualization artifacts such as CE planes, CEAC/CEAF, ENMB, EVPI/EVPPI, tornado plots, histograms, cost-mix plots, and related economic evaluation charts.
- Debuggable intermediate structures and logs that help contributors validate runs and investigate regressions.

## Scope
### In Scope
- Individual-level life-course microsimulation.
- Cost, QALY, and economic outcome estimation.
- Deterministic, subgroup, and grid-based scenario analysis.
- Probabilistic sensitivity analysis and advanced economic evaluation methods.
- Command-line execution for full workflows and targeted scenario runs.
- Extensible parameter, scenario, plotting, and analysis modules.

### Out of Scope
- Interactive clinician-facing or public-facing web applications.
- Real-time operational decision systems.
- Multi-tenant product features such as accounts, permissions, or hosted dashboards.
- Replacing expert interpretation with automated policy recommendations.
- Clinical-grade patient diagnosis, treatment selection, or regulated medical-device behavior.

## Source of Truth
The authoritative implementation lives in:
- `src/lifecourse/` for model logic, orchestration, CLI behavior, and analysis code.
- `config/` for scenario definitions and runtime configuration.
- `tests/` for regression protection and executable expectations.

Supporting but secondary context lives in:
- `docs/` for requirements, design notes, and planning material.
- `scripts/` for diagnostics and benchmarking helpers.

Historical reference material lives in:
- `archive/old_notebooks/` and `drafts/`, which may be useful for background but are not the source of truth for current behavior.

## Configuration Hierarchy
Runtime behavior should be understood in this order:
1. Base maintained model logic in `src/lifecourse/`.
2. Default parameter sets in the parameter modules.
3. Jurisdiction-specific parameter variants such as the New Zealand parameter set.
4. Scenario definitions and overrides in `config/scenarios.yaml`.
5. CLI or run-level configuration choices that select named configs or external config files.

Contributors should prefer extending configuration and parameter definitions before introducing special-case logic into the simulation engine.

## Artifact Conventions
- Generated analysis outputs belong in `results/` unless an explicitly documented alternative is needed.
- Scenario definitions belong in `config/`.
- Maintained implementation belongs in `src/lifecourse/`.
- Regression expectations belong in `tests/`.
- Exploratory or superseded work should not silently become production behavior.

## Product Principles
- Scientific credibility over convenience.
- Reproducibility over ad hoc execution.
- Explicit configuration over hidden defaults.
- Modular package code over notebook-bound business logic.
- Transparent assumptions, outputs, and validation paths over opaque model behavior.
- Clear separation between maintained code, supporting documentation, and historical experimentation.

## Non-Functional Expectations
- Analyses should be reproducible with controlled seeds and explicit parameter sources.
- Core workflows should remain practical to run on standard developer hardware, with Dask used where parallel execution materially helps.
- Results should be inspectable and diagnosable when assumptions or outputs change.
- CI and local tests should protect model orchestration, configuration handling, and major analytical behaviors.
- Documentation should be sufficient for a new contributor to locate where to modify parameters, scenarios, simulation logic, and plots.

## Validation and Governance
Changes to the model should be judged by:
- Whether they preserve or intentionally update documented assumptions.
- Whether scenario and parameter changes are traceable in code and configuration.
- Whether tests cover the changed behavior and prevent silent regressions.
- Whether important output shifts can be explained through model logic, parameter updates, or corrected methodology.
- Whether comparisons to prior baselines, reference outputs, or published benchmarks remain possible.

## Current Boundaries and Conventions
- The maintained package name is `lifecourse`.
- Some existing documentation and historical material still use `LifeCourseID` or related naming; these should be treated as legacy references unless updated.
- The product currently reflects a research-model workflow: configuration-driven execution, generated result artifacts, and code-reviewed changes rather than interactive end-user product flows.

## Success Criteria
- Users can run defined scenarios without editing core model code.
- Contributors can identify where to add or modify parameters, scenarios, model behavior, and analyses.
- Core outputs for cost, QALY, ICER, uncertainty, and budget impact are generated reliably.
- Model changes are reviewable, explainable, and regression-tested.
- The repo remains usable as both a research analysis tool and a maintained software package.

## Constraints and Risks
- Model credibility depends on the transparency and quality of assumptions, parameter sources, and jurisdiction-specific choices.
- Computational cost can increase materially for large population sizes and PSA runs.
- Legacy docs and archived notebooks can diverge from the maintained package if naming and ownership boundaries are not kept clear.
- Research-grade outputs require disciplined validation, not just successful execution.
