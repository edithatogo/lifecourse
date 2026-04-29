# Polars Internal Tabular Migration

## Overview
Migrate selected internal tabular transformations from pandas-compatible paths to
explicit Polars implementations where benchmarks and maintainability support it.

## Initial Candidate Areas
- Scenario grid expansion and scenario normalization.
- Parameter and demographic tabular transforms.
- Analysis summary tables that do not require Dask orchestration.

## Acceptance Criteria
- Each migrated boundary has equivalence tests against the current behavior.
- Optional Polars remains opt-in until a production decision is made.
- Full validation passes after each migrated boundary.
