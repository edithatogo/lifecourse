import logging
import numpy as np
import pandas as pd
import dask.dataframe as dd

_LOG = logging.getLogger(__name__)


def ensure_known_divisions(ddf):
    """Return a ddf with explicit, non-overlapping RangeIndex divisions.

    This attempts to avoid Dask warnings about concatenating dataframes with
    unknown divisions by assigning each partition a global RangeIndex and
    setting the divisions tuple. It works by computing partition lengths
    (cheap), creating delayed reindexed partitions assigning a global
    RangeIndex, and rebuilding the Dask DataFrame via dd.from_delayed.

    Falls back to returning the original ddf if anything unexpected fails.
    """
    # reset index so partition-local indexing is predictable
    ddf = ddf.reset_index(drop=True).persist()
    try:
        part_lens = ddf.map_partitions(len).compute()
    except Exception:  # pragma: no cover - defensive
        _LOG.exception("Failed to compute partition lengths in ensure_known_divisions")
        return ddf

    part_lens = np.asarray(part_lens)
    total = int(part_lens.sum()) if part_lens.size > 0 else 0
    if total == 0:
        empty = ddf.repartition(npartitions=1)
        try:
            empty.divisions = (0, 0)
        except Exception:  # pragma: no cover - best-effort
            _LOG.debug("Could not set divisions on empty repartitioned ddf")
        return empty

    offsets = np.concatenate(([0], np.cumsum(part_lens)[:-1])).astype(int)
    try:
        parts = ddf.to_delayed()
        from dask import delayed

        new_parts = []
        for i, part in enumerate(parts):
            off = int(offsets[i])

            @delayed
            def _reindex_partition(df_part, off=off):
                if df_part is None:
                    return df_part
                ln = len(df_part)
                df_part.index = pd.RangeIndex(off, off + ln)
                return df_part

            new_parts.append(_reindex_partition(part))

        new_ddf = dd.from_delayed(new_parts, meta=ddf._meta)
        last_idx = int(offsets[-1] + part_lens[-1] - 1)
        divisions = tuple(list(offsets.tolist()) + [last_idx])
        try:
            new_ddf.divisions = divisions
        except Exception:  # pragma: no cover - best-effort
            _LOG.debug(
                "Failed to set divisions on rebuilt ddf; returning best-effort ddf"
            )
            return new_ddf
        return new_ddf
    except Exception:  # pragma: no cover - defensive
        _LOG.exception("Unexpected error while rebuilding ddf with known divisions")
        return ddf


def safe_from_pandas(df, npartitions=1):
    """Create a dask DataFrame from a pandas DataFrame and ensure known divisions.

    This is a small convenience wrapper used by factories that create small
    pandas DataFrames and return them as Dask DataFrames. It keeps the behavior
    lazy but assigns explicit RangeIndex divisions so downstream concatenation
    is safe and quiet.
    """
    ddf = dd.from_pandas(df, npartitions=npartitions)
    try:
        return ensure_known_divisions(ddf)
    except Exception:  # pragma: no cover - defensive
        _LOG.exception(
            "safe_from_pandas: ensure_known_divisions failed, returning original ddf"
        )
        return ddf
