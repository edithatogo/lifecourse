# HEOML Interchange Profile Plan

## Phase 1: Embedded HEOML Subtree

- [x] Task: Create the embedded `heoml/` structure.
    - [x] Add README, docs, decisions, specs, schemas, examples, and fixtures directories.
    - [x] Document that the subtree is designed for later extraction to a standalone repository.
- [x] Task: Define HEOML v0.1 scope.
    - [x] Keep v0.1 focused on portable health-economic output and VOI handoff artifacts.
    - [x] Explicitly exclude executable universal model semantics.
    - [x] Define non-goals and promotion criteria.
- [x] Task: Conductor - Automated Review and Checkpoint 'Embedded HEOML Subtree' (Protocol in workflow.md)

## Phase 2: First Schema And Example

- [x] Task: Add the v0.1 manifest schema.
    - [x] Include profile version, producer metadata, model metadata, run metadata, artifacts, checksums, diagnostics, and extensions.
    - [x] Keep the schema language-neutral and JSON Schema based.
- [x] Task: Add a minimal run-bundle manifest example.
    - [x] Include a small `lifecourse`-style decision problem with PSA and VOI artifact references.
    - [x] Reference tabular artifact paths without requiring the tables to exist yet.
- [x] Task: Document tabular artifact rules.
    - [x] Prefer Arrow/Parquet for typed tables and CSV for compatibility.
    - [x] Reject pickle as an interchange artifact.
- [x] Task: Conductor - Automated Review and Checkpoint 'First Schema And Example' (Protocol in workflow.md)

## Phase 3: Cross-Repo Alignment

- [x] Task: Link HEOML into `lifecourse` planning docs.
    - [x] Update model contract, reporting bundle, and `voiage` integration tracks.
    - [x] Update interchange documentation and README pointers.
- [x] Task: Link HEOML into `voiage` planning docs.
    - [x] Add HEOML as the candidate shared profile in the `voiage` integration docs and track.
    - [x] Keep `voiage` core API schemas as VOI-specific contracts that HEOML can reference.
- [x] Task: Conductor - Automated Review and Checkpoint 'Cross-Repo Alignment' (Protocol in workflow.md)

## Phase 4: Validation And Extraction Readiness

- [x] Task: Add a local schema validation command.
    - [x] Validate the manifest example against the schema.
    - [x] Keep dependencies optional or use existing validation tooling.
- [x] Task: Define extraction checklist.
    - [x] Define target repo name, package boundaries, docs site needs, license, governance, changelog, CI, and release policy.
    - [x] Define how `lifecourse` and `voiage` will depend on the extracted spec.
- [x] Task: Conductor - Automated Review and Checkpoint 'Validation And Extraction Readiness' (Protocol in workflow.md)
