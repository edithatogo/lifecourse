# Decision 0001: Start HEOML Embedded In lifecourse

## Status

Accepted for initial development.

## Context

HEOML needs real model outputs and VOI handoff requirements to avoid becoming an
abstract format with no users. `lifecourse` can produce health-economic run
bundles, and `voiage` can consume VOI artifacts.

## Decision

Start HEOML as an embedded, self-contained subtree in `lifecourse`.

The subtree must avoid depending on `lifecourse` internals and must be structured
so it can later move into a standalone repository.

## Consequences

- Early iteration is fast because schemas and examples can be tested against
  `lifecourse` outputs.
- The format can be coordinated with `voiage` immediately.
- Extraction into a standalone repo remains a planned milestone once v0.1 has
  examples, fixtures, validation, and documentation.

## Extraction Criteria

Move HEOML to a standalone repository when:

- at least one `lifecourse` run bundle validates against HEOML
- at least one `voiage` workflow consumes a HEOML VOI artifact
- schema validation exists in CI
- license, governance, changelog, docs, and release policy are explicit
- both `lifecourse` and `voiage` can reference the standalone spec version
