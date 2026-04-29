# Simulation Engine Status

## Scope

This document describes the current simulation-engine boundary for
`lifecourse`. It is a status page, not a promise that every candidate engine is
implemented.

## Taxonomy

The current ecosystem treats the following model families as distinct options:

- Static decision models for one-shot questions where no time evolution is
  needed.
- Cohort Markov and semi-Markov models for aggregate state-transition
  analysis.
- Individual discrete-time microsimulation for the current maintained
  production path.
- Continuous-time simulation for event-timing questions.
- Discrete-event simulation for pathways, queues, waiting times, and capacity
  constraints.
- Agent-based and network simulation for interaction-driven questions.
- Hybrid models when one formalism is not sufficient for the whole problem.

TreeAge is treated as a feature reference taxonomy for decision-tree, Markov,
and operational-model capabilities. It is not a runtime dependency or a
required interchange target.

## Current Production Engine

- The maintained production runtime is the annual discrete-time individual
  microsimulation path backed by Dask.
- The default path remains the reference implementation for policy analysis,
  regression testing, and release validation.
- The maintained engine is exposed through a typed registry-mediated helper so
  selection metadata and diagnostics can travel with the run result.
- Public contracts should continue to work against this default path even when
  future engines are added.

## Future Engine Candidates

- Static decision models for diagnostic scoping and other one-shot policy
  questions.
- Cohort Markov and semi-Markov models for aggregate state-transition analyses.
- Continuous-time individual simulation for event-timing questions.
- Discrete-event simulation for operational modelling of pathways, queues,
  waiting times, and capacity constraints.
- Agent-based or network models only where interaction structure matters.
- Hybrid models where one formalism is not a good fit for the whole problem.

## Selection Contract

- Engine selection should default to the maintained discrete-time engine when
  no engine name is supplied.
- Explicit engine names should resolve through the registry and fail clearly
  when they are not registered.
- Selection diagnostics should record the requested engine id, resolved engine
  id, selection source, available ids, and seed-policy summary where relevant.

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
