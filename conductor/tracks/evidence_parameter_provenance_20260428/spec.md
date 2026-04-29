# Evidence Parameter Provenance

## Overview

Add first-class provenance for model parameters and assumptions. The product goal
is credible policy evaluation, so each cost, utility, transition, yield, uptake,
and jurisdiction-specific assumption should be traceable to a source, evidence
grade, version, and transformation note.

## Functional Requirements

- Define a provenance schema for fixed parameters and sampled distributions.
- Capture source citation, jurisdiction, year, currency year, inflation method,
  evidence quality, owner, and review status.
- Validate that production parameters have provenance metadata or documented
  rationale for temporary gaps.
- Emit assumption audit artifacts with each model run.
- Support jurisdiction-specific parameter variants without hiding source
  differences.

## Non-Functional Requirements

- Keep provenance metadata machine-readable and reviewable in diffs.
- Avoid blocking exploratory parameters, but mark them explicitly as draft.
- Preserve existing parameter behavior while adding traceability.

## Acceptance Criteria

- Parameter provenance schema exists and is tested.
- A representative subset of current Australian and New Zealand parameters has
  provenance metadata.
- Model runs can emit an assumption audit file.
- Documentation explains how to add or update a parameter with evidence.

## Out Of Scope

- Full literature review for every historical parameter in the first increment.
- Automated evidence grading from papers or websites.
