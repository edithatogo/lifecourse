# Multi-Cohort Architecture

## Overview

Refactor the current intellectual-disability-focused model toward a
multi-cohort architecture. The existing `docs/multi_cohort_architecture_plan.md`
is a strong design seed, but it needs production tests, typed interfaces, and an
incremental migration path. This track owns the disease/cohort axis; the
simulation-engine modularity track owns the simulation-formalism axis.

## Functional Requirements

- Define a typed disease/cohort strategy interface for diagnosis, progression,
  costs, QALYs, and optional pathway events.
- Extract the current intellectual disability model as the first concrete
  cohort strategy without changing output behavior.
- Move cohort-specific parameters toward cohort-owned configuration packages.
- Keep shared population, mortality, fertility, scenario, and economic
  evaluation infrastructure reusable across cohorts.
- Keep cohort strategies compatible with the simulation-engine interface so a
  cohort can later run through discrete-time, Markov, DES, or hybrid engines
  where appropriate.
- Support future cohorts such as Lynch syndrome, cystic fibrosis, or
  pharmacogenomics without editing core orchestration logic.

## Non-Functional Requirements

- Preserve regression outputs for the current maintained cohort.
- Keep migration incremental and reversible.
- Maintain typed boundaries and validation for cohort configuration.

## Acceptance Criteria

- A cohort strategy protocol exists and is tested.
- The current cohort runs through the new interface with parity tests.
- Cohort-specific parameters are separated enough to add a second cohort
  scaffold without touching core simulation orchestration.
- Documentation explains how to create a new cohort module.

## Out Of Scope

- Fully parameterizing a second disease cohort in the first increment.
- Replacing Dask or the current simulation runtime.
- Defining all simulation-engine types; that belongs to the simulation engine
  modularity track.
