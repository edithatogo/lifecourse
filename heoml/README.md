# HEOML

HEOML is a provisional Health-Economic Output/Model Language profile.

The initial goal is pragmatic: define portable artifacts for health-economic
model outputs, assumptions, PSA samples, VOI handoff data, provenance,
diagnostics, and reporting bundles.

HEOML starts embedded in `lifecourse` so it can be developed against a working
model and the `voiage` VOI library. The subtree is intentionally self-contained
so it can later be extracted into its own repository.
See [docs/extraction-readiness.md](./docs/extraction-readiness.md) for the
current extraction checklist and target-repository assumptions.

## Validation

Validate the bundled example manifest against the local schema with:

```bash
python3 heoml/tools/validate_manifest.py
```

You can also point the validator at a different manifest path:

```bash
python3 heoml/tools/validate_manifest.py path/to/manifest.json
```

HEOML should remain a compact core profile. Sibling projects and future modules
should add optional extension profiles instead of pushing project-specific
fields into the core manifest.

## Scope

HEOML v0.1 is an interchange profile for:

- decision problem metadata
- strategies and interventions
- parameter values and parameter draws
- parameter provenance
- simulation/run metadata
- scenario metadata
- costs, QALYs, ICERs, net benefits, and PSA outputs
- VOI handoff artifacts for tools such as `voiage`
- diagnostics, warnings, checksums, and software versions
- links to tables, figures, and other result artifacts

Optional extension namespaces can cover adjacent modules such as `voiage`,
`innovate`, `mars`, simulation engines, evidence provenance, calibration, and
reporting.

## Non-Goals

HEOML v0.1 is not:

- an executable universal modelling language
- a replacement for `lifecourse` or `voiage`
- a clinical data model like OMOP CDM
- an ML model interchange format like ONNX or PMML
- a pharmacometrics model language like PharmML
- a pickle-based Python object dump

## Format Direction

- JSON for manifests, metadata, diagnostics, and small examples.
- JSON Schema for validation.
- Arrow or Parquet for typed tabular artifacts.
- CSV as a compatibility export.
- Checksummed image/report artifacts for figures and documents.

Pickle is explicitly outside the portable compatibility contract.

## Repository Extraction Path

The intended path is:

1. Develop HEOML v0.1 in this embedded subtree.
2. Prove it with `lifecourse` run bundles and `voiage` VOI ingestion.
3. Add validators, examples, and compatibility fixtures.
4. Extract the subtree into a standalone repository such as `edithatogo/heoml`.
5. Make `lifecourse` and `voiage` depend on the standalone spec through a
   versioned contract, not through copied internal files.

## Layout

```text
heoml/
  README.md
  decisions/
  docs/
  specs/
    v0.1/
      extensions/
      schemas/
      examples/
      fixtures/
  tools/
```
