# Engineering Hardening Plan

## Phase 1: Workflow And Automation

- [x] Add `nox` sessions for linting, typing, tests, builds, mutation testing, and profiling.
- [x] Add Renovate dependency update automation.
- [x] Add CodeQL static analysis workflow.
- [x] Harden CI with scheduled runs, lockfile checks, and nox-backed sessions.

## Phase 2: Typed Boundaries And Tests

- [x] Add Pydantic validation for scenario YAML shape.
- [x] Add property-based tests for numerical backend invariants.
- [x] Add property-based tests for scenario override semantics.
- [x] Add invalid-input tests for scenario file validation.

## Phase 3: Documentation

- [x] Document production defaults, optional pilots, promotion criteria, and deferred items.
- [x] Update release automation scope.
- [x] Update roadmap and tech-stack guidance.
