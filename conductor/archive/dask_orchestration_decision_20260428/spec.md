# Dask Orchestration Decision

## Overview
Decide whether Dask remains the long-term orchestration layer, is reduced to PSA
or distributed workloads, or is replaced in selected paths.

## Acceptance Criteria
- Decision is based on benchmark and profiling evidence.
- Any replacement keeps deterministic behavior and existing CLI workflows.
- Dask is not removed without equivalent tests for current orchestration behavior.
