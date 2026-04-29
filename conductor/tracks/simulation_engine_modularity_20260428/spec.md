# Simulation Engine Modularity

## Overview

The current maintained model is an annual discrete-time individual
microsimulation. That is appropriate for the current life-course use case, but
the repo should separate simulation orchestration from disease/cohort logic and
from the chosen simulation formalism. This track defines a modular engine layer
so future models can use static decision analysis, cohort Markov models,
individual discrete-time microsimulation, continuous-time simulation,
discrete-event simulation, agent-based extensions, or hybrid approaches without
rewriting the entire package. Operational modelling questions such as pathways,
queues, capacity, and waiting time should map naturally to DES.

## Recommended Simulation Approaches

- Static decision model: useful for one-shot diagnostic testing evaluations,
  simple decision trees, threshold analysis, and early scoping where time is not
  a central driver.
- Cohort Markov or semi-Markov model: useful for aggregate state-transition
  disease models, guideline-style economic evaluation, and faster probabilistic
  analysis where individual heterogeneity is limited.
- Individual discrete-time microsimulation: the current default; useful for
  annual life-course progression, heterogeneous parameters, subgroup equity
  analysis, and person-level event histories.
- Continuous-time individual simulation: useful when event timing within a year
  materially affects outcomes, such as diagnosis timing, mortality, pregnancy,
  treatment initiation, or competing risks.
- Discrete-event simulation: useful for pathway, capacity, waiting-time,
  queueing, diagnostic odyssey, and cascade-testing workflows where event order
  and resource constraints matter.
- Agent-based or network simulation: useful only if interactions between
  individuals matter, such as family cascade testing, contact networks, or
  behavior diffusion. It should not be adopted for independent individuals.
- Hybrid model: useful when a decision tree feeds a Markov model, a DES handles
  testing pathways, or a microsimulation uses Markov submodels for disease
  progression.

## Functional Requirements

- Define a typed simulation engine interface with common run inputs, outputs,
  artifacts, diagnostics, seed policy, and validation hooks.
- Preserve the existing annual discrete-time microsimulation as the first engine
  implementation.
- Add an engine registry that can select engines by configuration without
  special-case CLI logic.
- Define compatibility rules between engines, cohort strategies, parameter
  packages, and output schemas.
- Add a small static decision-model or cohort Markov proof of concept only after
  the engine interface is tested.
- Keep continuous-time, DES, agent-based, and hybrid engines as explicit future
  candidates until a concrete model need justifies implementation.
- Define dependency rules for each engine class before adding new runtime
  packages.

## Dependency Implications

- The default install should not gain new simulation-framework dependencies just
  because future engines are planned.
- Static decision models should initially use existing `numpy`, `pandas`, and
  `scipy` capabilities unless a clear package need emerges.
- Cohort Markov and semi-Markov engines should initially use existing numerical
  dependencies; specialized transition-model packages should remain deferred
  until they prove maintainability or validation value.
- Continuous-time engines may need survival, hazard, or competing-risk helpers,
  but should first prototype with existing `scipy` primitives and explicit
  tests.
- Discrete-event simulation may justify an optional dependency such as a DES
  framework only when pathway timing, queues, or resource constraints are part
  of an approved model requirement.
- Agent-based or network simulation may justify optional graph or ABM
  dependencies only when interaction between individuals is modeled.
- Any new engine dependency must be introduced behind an optional extra, added
  to Renovate coverage, documented in the quality matrix, and covered by at
  least smoke CI before promotion.

## Non-Functional Requirements

- Preserve current outputs and reproducibility for the default engine.
- Keep the engine interface narrow enough that new engines do not need to mimic
  internal Dask dataframe details.
- Require parity or acceptance tests for any engine that claims to implement an
  existing analytical workflow.
- Keep performance benchmarks engine-specific and workload-specific.
- Avoid dependency sprawl by requiring a documented reason, benchmark or
  validation advantage, CI coverage, and fallback strategy for each new engine
  package.
- Treat TreeAge as a feature reference taxonomy for decision-tree, Markov, and
  operational-model capabilities, not as a required runtime dependency of the
  engine layer.

## Acceptance Criteria

- The current discrete-time microsimulation runs through a typed engine
  interface and registry.
- CLI and Python reference APIs can select the default engine without changing
  current behavior.
- Documentation explains which simulation approach is appropriate for which
  health-economic question.
- At least one lightweight non-default engine scaffold exists, or a documented
  deferral explains why it should wait.
- The model contract can represent engine identity, engine version, seed policy,
  and engine-specific diagnostics.
- The dependency policy identifies which engine packages are core, optional,
  experimental, or deferred.

## Out Of Scope

- Replacing the current annual microsimulation as the production default.
- Building every simulation approach immediately.
- Adopting agent-based modeling without a use case involving interaction between
  individuals.
- Adding a new disease cohort as part of the engine abstraction itself.
- Binding the engine contract to a specific commercial tool format.
