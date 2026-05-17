# Starlight Documentation Site Migration

## Overview

Migrate the project documentation from a flat markdown-first structure in
`docs/` to a Starlight-generated documentation site with automated API
reference generation, link validation, versioning, LLM-friendly export, and
GitHub Pages CI/CD deployment.

## Motivation

- **REQ-MIG-004**: Documentation must be navigable and machine-readable.
- The current flat markdown structure (`docs/*.md`) becomes unwieldy as the
  documentation surface grows with architecture, API, engine, and scientific
  model docs.
- A generated site provides sidebar navigation, search, version switching, link
  validation, and automated API reference from Python source.
- GitHub Pages deployment keeps the site close to the repository with no
  additional hosting infrastructure.

## Goals

- Serve Starlight-built documentation from GitHub Pages at
  `https://edithatogo.github.io/lifecourse/`.
- Auto-generate Python API reference from `src/lifecourse` using
  `starlight-polyglot`.
- Validate internal and external links on each build via
  `starlight-links-validator`.
- Support versioned documentation via `starlight-versions`.
- Export LLM-consumable documentation via `starlight-llms-txt`.
- Deploy automatically on pushes to `main` via GitHub Actions.

## Functional Requirements

- Starlight site must be buildable with `pnpm install && pnpm build`.
- Site must be deployable to GitHub Pages with the `actions/deploy-pages` workflow.
- API reference must be generated from `src/lifecourse` Python source.
- Link validation must run during `astro build` and fail the build on broken
  links.
- Sidebar must include Home, Getting Started, Design, Requirements, Architecture,
  Simulation Engine, and API Reference sections.
- Documentation content must be authored in MDX, support React components for
  interactive elements, and allow Astro islands where needed.

## Non-Functional Requirements

- Build time should stay under 5 minutes on CI.
- Site must be statically generated (no server-side rendering).
- No additional hosting costs beyond GitHub Pages.
- Documentation dependencies (Astro, Starlight, plugins) must not leak into the
  Python runtime dependency set.
- Prose linting and link checking should continue to work alongside the
  generated site.

## Acceptance Criteria

- `pnpm build` succeeds and produces a `dist/` directory with valid HTML.
- GitHub Pages deployment succeeds via the `docs.yml` workflow.
- Sidebar navigation matches the defined structure.
- Python API reference pages are generated and navigable.
- Link validation catches at least one broken link during build.
- The site is accessible at the expected GitHub Pages URL.

## Out Of Scope

- Content conversion of existing markdown docs into MDX (separate track).
- Adding search functionality beyond what Starlight provides by default.
- Custom theme development or heavy CSS customization.
- Adding Dark/Light mode toggles beyond Starlight defaults.
- Automated test snippet execution in documentation.
