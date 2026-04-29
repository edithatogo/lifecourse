# Genomic Testing Pathways

## Overview

Expand the genomic testing intervention model beyond a single WGS-style pathway.
The existing advanced scenario planning document identifies high-value pathway
features: test types, pre/post-test counseling, VUS, incidental findings, and
pathway-specific costs and QALY effects.

## Functional Requirements

- Model configurable genomic test types such as panel, exome, and genome.
- Support test-type-specific costs, diagnostic yields, VUS probabilities,
  incidental finding probabilities, follow-up costs, and utility effects.
- Add pre-test and post-test genetic counseling events with uptake,
  differential probabilities, costs, and optional QALY effects.
- Support testing uptake assumptions instead of assuming universal testing where
  that is not appropriate.
- Add pathway event outputs so reviewers can inspect testing, counseling, VUS,
  incidental finding, and diagnosis counts.
- Consider cascade testing as a later pathway increment if family-level logic is
  available.

## Non-Functional Requirements

- Keep all new pathway assumptions scenario-configurable and provenance-ready.
- Preserve existing WGS behavior as a compatibility scenario.
- Avoid adding pathway complexity without regression tests and clear outputs.

## Acceptance Criteria

- At least two genomic test types can be compared through scenario config.
- Counseling can be enabled or disabled by scenario.
- VUS and incidental finding events are tracked in outputs.
- Existing baseline scenarios remain reproducible.

## Out Of Scope

- Full clinical genetics workflow simulation.
- Patient-facing decision support.
- Full family pedigree simulation unless a separate cascade-testing design is
  approved.
