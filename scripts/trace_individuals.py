#!/usr/bin/env python3
"""Trace specified person_uids through step and fused runs and print per-year snapshots."""

import os
import sys

sys.path.insert(0, os.path.abspath("src"))
import numpy as np

from lifecourse.model.parameters import (
    DISTRIBUTIONS,
    START_YEAR,
    get_mean_params,
    prepare_dask_params,
)
from lifecourse.model.population_system import PopulationSystemDask


def trace_uids(uids, seed=42, pop=1000, dur=3):
    mean = get_mean_params(DISTRIBUTIONS)
    params = prepare_dask_params(mean)

    np.random.seed(int(seed))
    ps_step = PopulationSystemDask(pop, params, arm="prospective")
    np.random.seed(int(seed))
    ps_fused = PopulationSystemDask(pop, params, arm="prospective")

    years = [START_YEAR + i for i in range(dur)]

    traces = {"step": [], "fused": []}

    # Run step (which currently delegates to fused) year by year
    for y in years:
        ps_step.step(y)
        df = ps_step.pop.compute()
        traces["step"].append((y, df[df["person_uid"].isin(uids)].copy()))

    # Run fused independently
    for y in years:
        ps_fused.step_fused(y)
        df = ps_fused.pop.compute()
        traces["fused"].append((y, df[df["person_uid"].isin(uids)].copy()))

    # Print results
    for mode in ["step", "fused"]:
        print(f"--- TRACE {mode.upper()} ---")
        for y, df in traces[mode]:
            print(f"YEAR {y}, rows: {len(df)}")
            if df.empty:
                print(" (no rows for these uids)")
            else:
                print(df.to_string(index=False))
            print()


if __name__ == "__main__":
    # uids discovered from diff report
    uids = [8193267225911134810, 8314658796149861502]
    trace_uids(uids, seed=42, pop=1000, dur=3)
