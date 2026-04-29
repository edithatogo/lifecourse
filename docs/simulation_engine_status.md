# Simulation Engine Status

## Scope

This document describes the current simulation-engine boundary for
`lifecourse`. It is a status page, not a promise that every candidate engine is
implemented.

## Current Production Engine

- The maintained production runtime is the annual discrete-time individual
  microsimulation path backed by Dask.
- The default path remains the reference implementation for policy analysis,
  regression testing, and release validation.
- Public contracts should continue to work against this default path even when
  future engines are added.

## Future Engine Candidates

- Static decision models for one-shot policy questions.
- Cohort Markov and semi-Markov models for aggregate state-transition analyses.
- Continuous-time individual simulation for event-timing questions.
- Discrete-event simulation for pathways, waiting times, and capacity
  constraints.
- Agent-based or network models only where interaction structure matters.
- Hybrid models where one formalism is not a good fit for the whole problem.

## Dependency Policy

- Do not add a new simulation framework to the core install until there is a
  concrete engine implementation that needs it.
- Treat new engine packages as optional extras first.
- Add smoke CI, promotion criteria, and documentation before promoting an
  optional engine to the default path.
- Keep the simulation-engine interface stable so cohorts, contracts, provenance
  artifacts, and reporting bundles can remain compatible.

## Promotion Criteria

- API compatibility tests against the existing production path.
- Benchmark evidence for realistic model sizes.
- Reproducibility notes for random-number generation and numerical precision.
- CI coverage for the relevant optional extra.
- User-facing and contributor-facing documentation for the engine boundary.

## Related Tracks

- `conductor/tracks/simulation_engine_modularity_20260428`
- `conductor/tracks/multi_cohort_architecture_20260428`
- `conductor/tracks/validation_calibration_targets_20260428`
