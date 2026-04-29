# Reproducible Reporting Bundle Plan

## Phase 1: Manifest And Output Index

- [ ] Task: Add tests for run manifest creation.
    - [ ] Cover version, schema, git revision, command/API entry point, config paths, seeds, and runtime metadata.
- [ ] Task: Implement run manifest and output index models.
    - [ ] Use pydantic models and JSON serialization.
    - [ ] Include stable artifact identifiers and media types.
    - [ ] Include HEOML profile version, schema reference, and manifest identifier.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Manifest And Output Index' (Protocol in workflow.md)

## Phase 2: Checksums And Audit Artifacts

- [ ] Task: Add tests for checksum generation and artifact indexing.
    - [ ] Cover input configs, generated tables, figures, diagnostics, and logs.
- [ ] Task: Implement checksum and bundle writing helpers.
    - [ ] Use relative paths where possible.
    - [ ] Preserve compatibility with existing result directories.
    - [ ] Keep HEOML bundle layout stable for downstream consumers.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Checksums And Audit Artifacts' (Protocol in workflow.md)

## Phase 3: Reporting Summaries

- [ ] Task: Add tests for publication summary table generation.
    - [ ] Cover deterministic, PSA, budget impact, equity, and VOI outputs where available.
- [ ] Task: Implement bundle documentation and report examples.
    - [ ] Explain review workflow and expected artifacts.
    - [ ] Document how HEOML manifests index report artifacts and diagnostics.
- [ ] Task: Conductor - Automated Review and Checkpoint 'Reporting Summaries' (Protocol in workflow.md)
