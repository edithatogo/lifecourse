# Release Automation

This project currently uses a dry-run release workflow before any publishing
automation is enabled.

## Current Scope

- Build package artifacts with `uv build`.
- Inspect the generated source distribution and wheel.
- Run packaging smoke tests and release workflow contract tests.
- Avoid publishing, package-index credentials, OIDC publishing permissions, or
  external service mutation.
- Use Renovate for grouped dependency update proposals.
- Use CodeQL for static security analysis.
- Use `uv lock --check` in CI to catch dependency metadata drift.
- Expose the installed package version through `lifecourse.__version__`,
  `lifecourse.version.get_version()`, and CLI `--version` flags.
- Check that `pyproject.toml` has a matching `CHANGELOG.md` release section.

## Release Dry-Run Prerequisites

Before any external publication is attempted, the release process must confirm:

- Source distributions and wheels build successfully.
- The changelog contains a matching version section.
- The schema contract, Python package, adapter scaffolds, and Rust migration
  surfaces have compatible version notes.
- Artifact provenance is recorded for generated release assets.
- Checksums for release artifacts are available and verified.
- Package-specific dry-run checks pass for the relevant registry target:
  - PyPI
  - crates.io
  - npm
  - NuGet
  - CRAN
  - Julia registry
  - Go module tooling, when applicable

## Deprecation Policy

- Breaking schema or adapter changes require a warning period and migration
  notes before removal.
- Release notes must identify compatibility windows for deprecated surfaces.
- Deprecated surfaces remain available for at least one documented warning
  cycle unless the change is security-related or otherwise urgent.
- Adapter support tiers should move from experimental to smoke-tested to
  production-supported only when the docs, CI, and ownership policy are in
  place.

## Version Workflow

1. Update `project.version` in `pyproject.toml`.
2. Add a matching `## <version>` section to `CHANGELOG.md`.
3. Run `uv run nox -s version`.
4. Run `uv run nox -s lint typecheck build` and `uv run pytest`.
5. Create the release tag only after dry-run artifacts have been reviewed.

## Deferred Scope

- DVC or heavier artifact lineage is deferred until model input/output artifacts
  have a stable retention policy.
- TestPyPI, PyPI, and Conda publishing are deferred until dry-run artifacts are
  reviewed and release ownership is explicit.
- Automated version bumping and tag publishing are deferred until release
  ownership is explicit.
