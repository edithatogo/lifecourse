# Validation Calibration Targets

## Overview

Add explicit calibration and validation artifacts so model changes can be judged
against target epidemiologic, economic, and published-reference outputs rather
than only against internal unit tests.

## Functional Requirements

- Define calibration target schemas for rates, counts, costs, QALYs, ICERs,
  event frequencies, and jurisdiction-specific benchmarks.
- Add baseline comparison artifacts for deterministic and PSA runs.
- Support tolerance rules by metric type and evidence quality.
- Integrate deterministic calibration search outputs with validation reporting.
- Document when a model change intentionally shifts a baseline.

## Non-Functional Requirements

- Keep target data versioned and provenance-linked.
- Distinguish calibration targets from validation holdout targets.
- Keep validation failures explainable in CI and local runs.

## Acceptance Criteria

- Calibration and validation target schemas exist.
- Representative targets are checked in tests or a nox session.
- Baseline comparison output is generated for fixed-seed runs.
- Documentation explains how to update targets after a justified model change.

## Out Of Scope

- Claiming external validation without curated target data.
- Bayesian posterior calibration unless a separate methodology track approves it.
