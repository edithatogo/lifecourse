# Starlight Documentation Site — Full Content and Plugin Configuration

## Overview

Complete the Starlight documentation site by populating it with real,
comprehensive documentation content and configuring all planned plugins.

## Motivation

- The Starlight scaffold exists but has only stub landing pages.
- Users and contributors need complete documentation: getting started, usage
  guides, API reference overviews, and contributing guidelines.
- `starlight-polyglot` requires a configured Python entry point pointing at
  `src/lifecourse` to auto-generate API reference pages.
- `starlight-versions`, `starlight-links-validator`, and `starlight-llms-txt`
  need to be wired into `astro.config.mjs`.
- A dedicated conductor track ensures traceability for the migration work.

## Goals

- Provide real, complete documentation content covering project overview,
  installation, quick start, detailed usage, API reference, and contributing.
- Configure `starlight-polyglot` with a Python handler pointing at
  `src/lifecourse` for auto-generated API docs.
- Enable `starlight-links-validator` to catch broken links during build.
- Enable `starlight-versions` for future versioned documentation.
- Enable `starlight-llms-txt` for LLM-consumable documentation exports.
- Create a conductor track `conductor/tracks/migrate_starlight/` with
  metadata.json, spec.md, and plan.md.
- Update `.gitignore` as needed.
- Commit all changes and push to the remote repository.

## Functional Requirements

- All documentation pages must be authored in MDX and use Starlight frontmatter.
- `astro.config.mjs` must import and configure all plugins listed above.
- `starlight-polyglot` Python handler must point at `src/lifecourse`.
- Sidebar must include Home, Getting Started, Usage, API Reference, and
  Contributing entries.
- The site must build with `pnpm build` without errors.

## Non-Functional Requirements

- Documentation must be truthful about what is implemented, optional,
  experimental, or planned.
- Code examples must match the actual API surface in `src/lifecourse`.
- Build time should stay under 5 minutes on CI.

## Acceptance Criteria

- `pnpm build` succeeds.
- All five documentation pages render correctly.
- Sidebar navigation is complete and links work.
- API reference pages are generated (even if from a limited public surface).
- Link validation does not fail on internal links.
- The conductor track files exist with correct metadata.
- Changes are committed and pushed to the remote.
