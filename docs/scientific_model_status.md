# Scientific And Model Status

## Scope

This page records the scientific and model-documentation boundary for
`lifecourse`. It focuses on what needs to be documented before claims about
evidence maturity, calibration, or external validation are made.

## Parameter Provenance

- Model inputs should carry source traceability, jurisdiction, effective date,
  and units.
- Assumption changes should be auditable rather than buried in implementation
  details.
- Evidence metadata should distinguish original sources from derived inputs.

## Jurisdiction Evidence

- Jurisdiction-specific inputs should identify the reference population and the
  source table or data extract they came from.
- Cross-jurisdiction reuse should be explicit about what was adapted and what
  was preserved.

## Calibration And Validation

- Calibration targets and validation targets should be documented separately.
- A calibration target is a parameter or outcome the model tries to fit.
- A validation target is a benchmark used to check model plausibility or
  external agreement.
- The model documentation should state the tolerance rules and the calibration
  method used.

## Limitations And Maturity

- Document known structural assumptions, data gaps, and approximate mappings.
- Do not treat planned calibration or validation work as completed evidence.
- Keep scientific-model claims aligned with the current track status and the
  release notes.

## Related Tracks

- `conductor/tracks/evidence_parameter_provenance_20260428`
- `conductor/tracks/validation_calibration_targets_20260428`
- `conductor/tracks/multi_cohort_architecture_20260428`
- `conductor/tracks/reproducible_reporting_bundle_20260428`
