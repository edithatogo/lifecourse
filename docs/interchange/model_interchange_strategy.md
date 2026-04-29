# Model and Data Interchange Strategy

## Purpose

`lifecourse` and `voiage` should exchange reproducible health-economic analysis
artifacts without sharing internal Python objects. The goal is to let a
`lifecourse` run bundle be consumed by `voiage`, language bindings, notebooks,
or review tools without requiring the original simulation process.

## Existing Standards Considered

- ONNX, PMML, and PFA are useful for predictive or machine-learning model
  interchange. They are not a natural representation for a health-economic
  microsimulation, PSA bundle, or VOI result set.
- PharmML is relevant to pharmacometrics and mathematical model exchange, but
  it does not directly cover this package's genomic testing policy model,
  scenario configuration, budget impact outputs, or VOI handoff.
- OMOP CDM is useful for source observational health data standardization. It
  is not a model-result or economic-evaluation interchange format.
- TreeAge and R health-economic model formats may be useful feature references
  later, especially for decision-tree, Markov, and operational-model
  capability mapping. They should not become the primary internal contract.

The practical approach is a project-owned, versioned artifact profile using
open file formats and JSON Schema. This profile now has a provisional name:
HEOML, the Health-Economic Output/Model Language.

The embedded HEOML subtree lives at `heoml/` and is designed for later
extraction into a standalone repository once fixtures, validators, docs, and
cross-repo usage are mature.

The control-plane and data-plane artifact policy is documented in
[artifact_formats.md](artifact_formats.md).

HEOML core should stay small. Adjacent health economics and outcomes research
(HEOR) projects should add namespaced extension profiles for project-specific
artifacts, including `voiage` VOI results, `innovate` health-intervention
diffusion/adoption traces, `mars` surrogate/metamodel references, future
simulation-engine traces, evidence provenance, and calibration outputs.

## Recommended Artifact Bundle

Use a directory or archive with a stable manifest:

```text
run-bundle/
  manifest.json
  schemas/
  inputs/
  parameters/
  scenarios/
  outputs/
  figures/
  diagnostics/
  voi/
```

Required metadata:

- producing package and version
- schema/profile version
- git revision when available
- run identifier
- scenario identifiers
- simulation engine and engine version
- cohort/model identifier
- seed policy
- time horizon and discount rate
- willingness-to-pay thresholds
- artifact checksums
- diagnostics and warnings

## Interchange Formats

- JSON: manifest, small metadata, schema references, diagnostics, and result
  summaries.
- JSON Schema: request, response, artifact, and VOI profile validation.
- Arrow or Parquet: typed tabular artifacts such as PSA samples, parameter
  draws, outcomes, long-form event outputs, and optionally event-log traces for
  operational modelling or process-mining use cases.
- CSV: compatibility export for simple workflows and review.
- PNG/SVG/PDF: figures as outputs, with metadata and checksums in the manifest.

Do not use pickle as an interchange format. Pickle is Python-specific, unsafe
for untrusted files, fragile across code versions, and unusable by R, Julia,
Go, Rust, TypeScript, or C# bindings. It can be used only for local debugging
when explicitly marked non-portable and excluded from compatibility guarantees.

## VOI Handoff To `voiage`

The VOI handoff should include:

- net-benefit matrix
- strategy names
- parameter samples aligned to PSA rows
- WTP thresholds
- population scaling metadata
- time horizon
- discount rate
- method settings
- run provenance

These artifacts should map cleanly to `voiage.ValueArray`, `voiage.ParameterSet`,
`voiage.TrialDesign` where applicable, and `voiage` EVPI, EVPPI, EVSI, and ENBS
result contracts.

## API Implications

- Public APIs should accept and return typed request/response models rather than
  raw CLI argument dictionaries.
- Output APIs should return structured result objects plus artifact references,
  not just write side-effect files.
- The CLI should remain a thin wrapper over the same reference API.
- Optional integrations such as `voiage` should consume artifacts through a
  narrow adapter, not by importing simulation internals.
- Sibling modules such as `innovate` and `mars` should consume or produce HEOML
  artifacts through adapters or extension profiles, not through required
  `lifecourse` runtime dependencies.
- Every artifact profile should include version fields so old bundles can be
  detected and migrated intentionally.
- Artifact references should record media type, schema version, relative path,
  and checksum where available.

## Promotion Criteria

The artifact profile is ready to rely on when:

- fixed-seed bundles are generated deterministically
- JSON Schema validation runs in CI
- at least one `lifecourse` bundle is consumed by `voiage`
- EVPI and EVPPI parity is proven against a shared fixture
- EVSI and ENBS include explicit method assumptions before being promoted
- docs identify which fields are stable, optional, experimental, or deferred
- TreeAge feature coverage should remain a reference-mapping concern, not a
  hard requirement for the core HEOML or `lifecourse` runtime.
