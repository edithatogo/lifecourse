# Contributing to Lifecourse

Thanks for contributing! This file contains the minimal developer guidance to get started, test changes, and follow repository conventions.

## Quick start

- Install dependencies: `pip install -r requirements.txt` (or use the preferred environment described in `pyproject.toml`).
- Run the fast tests locally:

```bash
pytest -q tests -k "not slow"  # run quick unit tests; adjust -k as needed
```

Use `--maxfail=1` for faster feedback on test failures.

## Commit & pre-commit

This repository uses pre-commit hooks (formatting + linting). Please run or let the hooks run automatically on commit. To avoid accidental big commits, stage only relevant files.

If your local environment has a pre-commit configuration that interferes with the working tree during partial commits, consider creating a focused branch for your change.

## Dask DataFrame guidance (important)

To avoid noisy runtime warnings and unsafe index alignment assumptions when concatenating Dask DataFrames, follow these patterns.

- Use `lifecourse.model.dask_utils.safe_from_pandas(df, npartitions=...)` when returning small pandas DataFrames from factories. This wraps `dd.from_pandas` and ensures explicit RangeIndex divisions.
- Before concatenating Dask DataFrames that might have lost division metadata (for example after merges or `map_partitions` that reset indices), call `lifecourse.model.dask_utils.ensure_known_divisions(ddf)` on each input.

Examples:

```py
from lifecourse.model.dask_utils import safe_from_pandas, ensure_known_divisions

# Factory returning small pandas frame as Dask
def gen_population_dask(...):
    df = pd.DataFrame(...)
    return safe_from_pandas(df, npartitions=4)

# Before concat
left = ensure_known_divisions(left)
right = ensure_known_divisions(right)
result = dd.concat([left, right], interleave_partitions=True)
```

If you find a new source of Dask "unknown divisions" warnings, add a regression test (see `tests/test_dask_warnings.py` for an example) and fix the origin by ensuring known divisions at producers where possible.

## PR process

- Open a pull request against `main` with a short description and link any relevant issue.
- Small docs or test-only changes may be auto-merged after approvals; feature changes should include tests.

## Coding conventions

- Use the `src/` layout — put packages under `src/lifecourse/`.
- Keep large generated artifacts (plots, results) out of commits — use `results/` and keep only `results/.gitkeep` tracked.

Thanks for improving Lifecourse! If you're unsure where to make a change, open an issue first.
