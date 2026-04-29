# Documentation and Stack Readiness

## Overview

Create a dedicated documentation and stack-readiness workflow so the repo can
scale from markdown-first planning docs to user-facing documentation without
misstating experimental features as production defaults. This track also keeps
the stack strategy explicit: core dependencies remain stable, optional SOTA
tools are promoted only with evidence, and docs tooling is added only when it
solves a concrete maintenance problem.

## Goals

- Keep documentation aligned with the product goal of credible, reproducible
  health-economic microsimulation for genomic testing policy analysis.
- Make production, experimental, planned, and deferred surfaces obvious.
- Add lightweight docs checks before introducing a generated docs site.
- Include Markdown prose linting as part of the lightweight docs checks.
- Define when MkDocs, mkdocstrings, link checking, or tested snippets should be
  added.
- Ensure future stack changes update architecture docs, stack strategy,
  README, Conductor tracks, and changelog consistently.

## Functional Requirements

- Maintain a documentation map covering user, contributor, architecture,
  scientific/model, API/contract, and release documentation.
- Add checks for stale filenames, missing required docs sections, and broken
  internal links.
- Add a docs-specific optional extra only when docs tooling is implemented.
- Add a docs CI job or nox session only after the first automated docs checks
  exist locally.
- Keep prose linting scoped to Markdown docs and repository-owned style rules.
- Define docs requirements for stack changes, schema contracts, language
  adapters, simulation engines, parameter provenance, validation targets, and
  reproducible reporting bundles.
- Keep generated docs tooling out of runtime dependencies.

## Non-Functional Requirements

- Avoid documentation sprawl by keeping docs ownership and status explicit.
- Avoid adding MkDocs or similar tooling before the docs surface justifies it.
- Keep examples testable where practical.
- Keep docs truthful about what is implemented, optional, experimental, or
  planned.

## Acceptance Criteria

- Documentation plan and stack strategy are linked from README and architecture
  status docs.
- A docs-check command exists and runs in local workflow tooling.
- CI has a docs-check job or a documented reason for deferring it.
- The docs plan defines when to add a generated docs site.
- Stack changes have a documented checklist for dependency, CI, docs, and
  changelog updates.

## Out Of Scope

- Publishing a documentation site immediately.
- Moving all historical design docs into a new docs framework.
- Adding docs tooling to the default runtime dependencies.
