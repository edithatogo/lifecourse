# HEOML Interchange Rationale

## Why HEOML

Health-economic models often produce a bundle of artifacts: assumptions,
parameter draws, scenario definitions, cost and QALY tables, ICER summaries, PSA
outputs, VOI inputs and outputs, figures, diagnostics, and provenance. These
outputs are commonly exchanged as ad hoc folders of CSV files, images, and
reports.

HEOML aims to provide a small, explicit, versioned profile for those artifacts.
The first target is interoperability between `lifecourse` and `voiage`, with a
path toward use by other health-economic tools.

## Standards Considered

- ONNX, PMML, and PFA focus on predictive or machine-learning model
  interchange. They are useful references for portability but are not natural
  containers for health-economic run bundles.
- PharmML focuses on pharmacometrics and mathematical model exchange. It is
  relevant background but not a direct fit for genomic-testing policy models,
  scenario bundles, or VOI outputs.
- OMOP CDM standardizes observational health data. It is a source-data standard,
  not a health-economic model-output or VOI interchange profile.
- TreeAge-style feature mapping may become a useful reference taxonomy, but
  should not define the internal contract between `lifecourse` and `voiage`.

## Pickle Policy

Pickle is not a HEOML interchange format. It is Python-specific, unsafe for
untrusted files, fragile across versions, and unusable by non-Python bindings.

Local debug workflows may emit pickle files only when they are clearly labelled
non-portable and excluded from compatibility guarantees.

## Initial Design Choice

HEOML v0.1 starts with:

- JSON manifests
- JSON Schema validation
- Arrow/Parquet typed tables
- CSV compatibility exports
- checksummed figures and reports

This is enough to support reproducible run bundles and VOI handoff without
claiming to be a universal executable modelling language.
