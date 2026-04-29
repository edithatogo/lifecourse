# Artifact Formats

This project uses a two-layer artifact policy for health-economic model
exchange:

- control-plane data uses JSON and JSON Schema
- data-plane tables use Arrow or Parquet when typed tabular data is exchanged
- CSV is kept as a compatibility export for review and lightweight workflows

## Control-Plane Artifacts

Control-plane artifacts describe what was run and how to interpret the outputs.
These include request payloads, response payloads, manifests, artifact indexes,
diagnostics, and provenance records.

Recommended fields:

- `contract_version`
- `schema_version`
- `artifact_id`
- `media_type`
- relative `path`
- `checksum` when the artifact is portable and stable enough to hash

Control-plane artifacts should be validated with JSON Schema and should avoid
Python-specific values or pickle-style object graphs.

## Data-Plane Artifacts

Data-plane artifacts hold the large typed tables that drive analysis or can be
reused by downstream tools:

- PSA parameter draws
- net-benefit matrices
- long-form outcomes
- simulation traces
- event logs for operational modelling

Arrow or Parquet should be preferred for these data sets because they preserve
schema, types, and cross-language usability. CSV remains available as a
compatibility export when a human-readable or spreadsheet-friendly format is
needed.

## Metadata Rules

- Artifact references must use relative paths inside a run bundle.
- If an artifact reference includes `schema_ref`, it must also include a
  `schema_version`.
- Checksums, when present, should identify the algorithm explicitly, for
  example `sha256:<hex-digest>`.
- Figures and other binary assets should carry a checksum in the manifest or
  artifact index when they are intended to be portable.

## Current Contract Scope

The current `lifecourse` core API contract uses JSON Schema for request and
response objects, and the embedded HEOML profile carries the portable run
bundle payloads. The contract does not use pickle for interchange.
