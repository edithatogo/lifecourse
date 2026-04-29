# Model Contract and Schema Artifacts Plan

Documentation scope: API/contract, architecture, and release docs.

## Phase 1: Contract Models

- [x] Task: Add tests for request and response model validation.
    - [x] Cover required fields, optional advanced analysis fields, engine identity, engine version, seed policy, and schema failures.
    - [x] Cover deterministic fixture serialization and deserialization.
- [x] Task: Implement pydantic request, response, diagnostics, and artifact models.
    - [x] Keep field names language-neutral and stable.
    - [x] Add explicit version fields for the contract.
    - [x] Add engine metadata and capability fields without exposing Dask internals.
- [x] Task: Generate and commit JSON Schema artifacts.
    - [x] Add a reproducible command or nox session for schema generation.
    - [x] Test that committed schemas match generated schemas.
    - [x] Align the contract artifacts with the embedded HEOML manifest profile.
- [x] Task: Conductor - Automated Review and Checkpoint 'Contract Models' (Protocol in workflow.md)

## Phase 2: Reference Execution Surface

- [x] Task: Add tests for a Python reference API that bypasses CLI parsing.
    - [x] Verify CLI and API produce equivalent outputs for fixed fixtures.
    - [x] Verify invalid contract inputs fail with useful diagnostics.
- [x] Task: Implement the Python reference run API.
    - [x] Keep existing CLI commands as thin wrappers.
    - [x] Return structured response models and artifact metadata.
- [x] Task: Add golden fixtures.
    - [x] Include deterministic runs, seeded probabilistic runs, diagnostics, and schema errors.
    - [x] Store fixture data in a location usable by other language tracks.
    - [x] Reuse HEOML-compatible manifest and fixture shapes where possible.
- [x] Task: Conductor - Automated Review and Checkpoint 'Reference Execution Surface' (Protocol in workflow.md)

## Phase 3: Artifact Format Documentation

- [x] Task: Document cross-runtime artifact formats.
    - [x] Specify JSON Schema for control-plane data.
    - [x] Specify Arrow or Parquet for typed tabular outputs.
    - [x] Keep CSV as a compatibility export.
- [x] Task: Add tests or checks for artifact metadata consistency.
    - [x] Verify artifact references include media type, schema version, path, and checksum where available.
- [x] Task: Conductor - Automated Review and Checkpoint 'Artifact Format Documentation' (Protocol in workflow.md)
