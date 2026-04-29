# Model Contract and Schema Artifacts

## Overview

Define the stable language-neutral request, response, artifact, diagnostics, and
reproducibility contract that all future bindings and Rust kernels must use.
Python remains the reference implementation and the CLI becomes a thin wrapper
around the same API.

## Functional Requirements

- Define pydantic v2 models for model run requests, scenarios, parameter
  overrides, run modes, seeds, output selections, diagnostics, and artifact
  metadata.
- Include simulation engine identity, engine version, engine capabilities, and
  engine-specific diagnostics in the run contract.
- Generate JSON Schema artifacts from the pydantic models and commit them as
  versioned contract files.
- Define tabular artifact conventions using Arrow or Parquet as the preferred
  typed format and CSV as a compatibility export.
- Define a model/data interchange profile for run bundles, including manifest,
  schemas, parameters, scenarios, outputs, diagnostics, figures, and VOI
  artifacts.
- Treat HEOML as the provisional shared name for the portable health-economic
  artifact profile.
- Explicitly exclude pickle from portable interchange contracts except for
  labelled local debugging artifacts.
- Add deterministic golden fixtures for successful runs, schema failures,
  seeded probabilistic runs, and diagnostic output.
- Expose a stable Python API that can run the model without depending on CLI
  argument parsing internals.
- Keep existing CLI behavior available by delegating through the new Python API.

## Non-Functional Requirements

- Preserve current Python behavior and deterministic seeds.
- Keep schemas language-neutral and avoid Python-only field semantics.
- Keep numeric precision, null handling, enum naming, and path conventions
  explicit.
- Maintain test coverage above the project threshold for new code.

## Acceptance Criteria

- JSON Schema artifacts exist for request and response contracts.
- The schema can represent the default discrete-time microsimulation engine and
  future static, Markov, continuous-time, DES, or hybrid engines.
- Golden fixtures are tested from the Python reference API.
- CLI and Python API runs share the same contract path.
- Documentation explains schema versioning, artifact formats, and determinism
  rules.
- Documentation compares the project-owned artifact profile with existing
  standards such as ONNX, PMML, PharmML, OMOP CDM, and TreeAge-style exports.

## Out Of Scope

- Native R, Julia, Go, TypeScript, C#, or Rust bindings.
- Replacing pandas, NumPy, Dask, or existing simulation orchestration.
- Publishing generated client packages.
