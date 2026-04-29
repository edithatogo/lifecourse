# Engineering Hardening

## Goal

Address remaining modernization gaps after the backend migration by making SOTA
engineering practices explicit, configured, tested, and documented.

## Requirements

- Add workflow management for local and CI quality gates.
- Add dependency automation configuration.
- Add static security analysis in CI.
- Configure scoped mutation testing.
- Add representative profiling workflow entrypoints.
- Strengthen typed input boundaries with Pydantic.
- Expand property-based testing beyond the initial validation foundation.
- Update documentation so production defaults, optional pilots, and deferred
  items are clearly separated.

## Non-Goals

- Do not force a wholesale migration from pandas to Polars.
- Do not force a wholesale migration from NumPy/Dask to JAX/XLA.
- Do not enable publishing to package indexes until release ownership and
  credentials are explicit.
- Do not add DVC before artifact retention policy exists.
