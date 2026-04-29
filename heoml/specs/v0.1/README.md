# HEOML v0.1

HEOML v0.1 defines the first portable artifact profile for health-economic
model outputs and VOI handoff workflows.

## Profile Goals

- Represent the identity and provenance of a model run.
- Describe the decision problem, model, scenario, and simulation engine.
- Link to output artifacts such as tables, figures, diagnostics, and VOI data.
- Provide enough metadata for downstream tools to validate and interpret
  artifacts without importing the producing Python package.

## Required Manifest Sections

- `heoml_version`
- `profile`
- `producer`
- `model`
- `run`
- `decision_problem`
- `artifacts`
- `diagnostics`
- `extensions`

## Artifact Categories

- `input`
- `parameter`
- `scenario`
- `outcome`
- `psa`
- `voi`
- `figure`
- `diagnostic`
- `report`

## First Schema

The first schema is:

`schemas/manifest.schema.json`

The first example is:

`examples/minimal-run-bundle.manifest.json`

The normative fixture is:

`fixtures/normative/minimal-run-bundle.manifest.json`

The local validation command is:

`python3 heoml/tools/validate_manifest.py`

## Compatibility Notes

HEOML v0.1 is experimental. Consumers should validate the `heoml_version` and
`profile` fields before relying on an artifact bundle.

## Extensions

Project-specific fields should use optional extension namespaces rather than
changing the HEOML core profile. Initial reserved namespaces are documented in
`extensions/README.md` and cover `voiage`, `innovate`, `mars`, future simulation
engines, evidence provenance, and calibration workflows.
