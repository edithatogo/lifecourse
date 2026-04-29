# HEOML Interchange Profile

## Overview

Create an embedded `heoml/` subtree that defines HEOML v0.1, a portable
Health-Economic Output/Model Language profile. HEOML should start as a narrow
artifact interchange format for health-economic model outputs, assumptions,
PSA samples, VOI handoff data, provenance, diagnostics, and reporting bundles.
It should not start as a universal executable modelling language.

The initial subtree lives in this repository so `lifecourse` can use it quickly,
but it must be structured so it can later move into a standalone HEOML
repository with minimal path and governance changes.

## Functional Requirements

- Create a self-contained `heoml/` subtree with docs, versioned specs, schemas,
  examples, fixtures, and decisions.
- Define HEOML v0.1 as an artifact profile for:
  - decision problems
  - strategies/interventions
  - parameter values and parameter draws
  - parameter provenance
  - simulation/run metadata
  - scenario metadata
  - outcomes including cost, QALY, ICER, and net benefit
  - PSA outputs
  - VOI handoff artifacts for `voiage`
  - diagnostics, warnings, checksums, and software versions
- Use JSON metadata plus JSON Schema validation for control-plane artifacts.
- Use Arrow or Parquet for typed tabular artifacts, with CSV as compatibility
  export.
- Explicitly exclude pickle from the portable interchange contract.
- Document why existing standards such as ONNX, PMML/PFA, PharmML, OMOP CDM,
  and TreeAge-style exports are references or future adapters rather than the
  primary HEOML contract.
- Define extraction criteria for moving `heoml/` into a standalone repo.

## Non-Functional Requirements

- Keep v0.1 small enough to validate and explain.
- Prefer readable examples over broad coverage in the first version.
- Keep HEOML language-neutral and binding-friendly.
- Avoid tying HEOML to `lifecourse` implementation internals.
- Maintain clear compatibility with the `voiage` integration profile.

## Acceptance Criteria

- `heoml/README.md` explains purpose, scope, non-goals, and extraction path.
- `heoml/specs/v0.1/README.md` defines the first profile.
- `heoml/specs/v0.1/schemas/manifest.schema.json` exists as the first schema
  artifact.
- `heoml/specs/v0.1/examples/minimal-run-bundle.manifest.json` exists as a
  small human-reviewable example.
- `heoml/docs/interchange-rationale.md` records standards considered and why
  HEOML is needed.
- `heoml/decisions/0001-embedded-first.md` records the decision to start
  embedded before extracting to a standalone repository.
- Conductor tracks for `lifecourse` interchange, reporting bundles, and
  `voiage` integration point to HEOML as the future shared profile.

## Out Of Scope

- Building a standalone `heoml` package or CLI in this increment.
- Claiming HEOML is a universal executable model format.
- Implementing import/export adapters for third-party software.
- Replacing `lifecourse` or `voiage` schemas before v0.1 is proven useful.
