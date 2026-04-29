# Reproducible Reporting Bundle

## Overview

Create an auditable analysis bundle for each substantive run. Policy and
research users need outputs that are reproducible, reviewable, and easy to hand
to collaborators without reconstructing hidden CLI state.

## Functional Requirements

- Emit a run manifest with package version, schema version, git revision when
  available, command/API entry point, config paths, scenario IDs, seeds,
  dependency summary, and runtime environment metadata.
- Generate an output index covering tables, figures, diagnostics, logs,
  assumption audits, and validation reports.
- Add checksums for important input and output artifacts.
- Support publication-ready summary tables for deterministic, PSA, budget impact,
  equity, and VOI outputs.
- Include a portable model/data interchange manifest that can be consumed by
  `voiage`, language bindings, notebooks, and review tools.
- Align the manifest shape with the provisional HEOML v0.1 profile under
  `heoml/specs/v0.1/`.
- Export VOI handoff artifacts containing net benefits, strategy names,
  parameter samples, WTP thresholds, scaling metadata, method settings, and
  provenance.
- Keep bundle structure stable for downstream notebooks or reporting tools.

## Non-Functional Requirements

- Do not require external services for local reproducibility.
- Avoid storing sensitive local paths where relative paths are sufficient.
- Keep bundles deterministic for fixed inputs where practical.
- Do not rely on pickle for interchange; use JSON, JSON Schema, Arrow/Parquet,
  CSV compatibility exports, and checksummed figure files.

## Acceptance Criteria

- A fixed-seed run produces a manifest and output index.
- Important artifacts include checksums and schema/version metadata.
- Documentation explains the bundle layout and review workflow.
- A bundle can be validated as a portable artifact profile without importing
  `lifecourse` internals.
- Existing result files remain accessible through current paths or documented
  compatibility aliases.

## Out Of Scope

- Building a hosted dashboard.
- Replacing existing plotting functions.
- Publishing results to external repositories automatically.
