#!/usr/bin/env python3
"""Run one deterministic case and diff per-individual outputs between step and step_fused

Outputs:
 - results/diff_case_{seed}_{pop}_{dur}_step.csv
 - results/diff_case_{seed}_{pop}_{dur}_fused.csv
 - results/diff_case_{seed}_{pop}_{dur}_report.txt
"""
import os
import sys
import time
import argparse
import pandas as pd

sys.path.insert(0, os.path.abspath("src"))

import numpy as np
from lifecourse.model.parameters import DISTRIBUTIONS, get_mean_params, prepare_dask_params, START_YEAR
from lifecourse.model.population_system import PopulationSystemDask


def run_case(seed: int, pop: int, dur: int, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    mean = get_mean_params(DISTRIBUTIONS)
    params = prepare_dask_params(mean)

    # Force numpy RNG seed and single-process mode by setting debug flag on systems if needed
    np.random.seed(int(seed))
    ps_step = PopulationSystemDask(pop, params, arm="prospective")
    np.random.seed(int(seed))
    ps_fused = PopulationSystemDask(pop, params, arm="prospective")

    years = [START_YEAR + i for i in range(dur)]

    # Run step (record time)
    t0 = time.perf_counter()
    for y in years:
        ps_step.step(y)
    t1 = time.perf_counter()
    wall_step = t1 - t0

    # Run fused
    t0 = time.perf_counter()
    for y in years:
        ps_fused.step_fused(y)
    t1 = time.perf_counter()
    wall_fused = t1 - t0

    # Compute final dataframes
    df_step = ps_step.pop.compute()
    df_fused = ps_fused.pop.compute()

    step_csv = os.path.join(out_dir, f"diff_case_{seed}_{pop}_{dur}_step.csv")
    fused_csv = os.path.join(out_dir, f"diff_case_{seed}_{pop}_{dur}_fused.csv")
    report_txt = os.path.join(out_dir, f"diff_case_{seed}_{pop}_{dur}_report.txt")

    df_step.to_csv(step_csv, index=False)
    df_fused.to_csv(fused_csv, index=False)

    # Build quick diff report
    with open(report_txt, "w") as rf:
        rf.write(f"Case seed={seed} pop={pop} dur={dur}\n")
        rf.write(f"wall_time_step_s: {wall_step:.6f}\n")
        rf.write(f"wall_time_fused_s: {wall_fused:.6f}\n")
        rf.write(f"n_step: {len(df_step)}\n")
        rf.write(f"n_fused: {len(df_fused)}\n")
        rf.write(f"delta_n: {len(df_fused)-len(df_step)}\n\n")

        # Align on unique id if present (try 'person_uid', 'person_id' then 'id' then index)
        key = None
        for cand in ["person_uid", "person_id", "id"]:
            if cand in df_step.columns and cand in df_fused.columns:
                key = cand
                break

        if key is None:
            rf.write("No explicit id column found; using row-wise alignment for diff (by position).\n")
            # Compare by position
            min_len = min(len(df_step), len(df_fused))
            diffs = []
            for i in range(min_len):
                row_s = df_step.iloc[i]
                row_f = df_fused.iloc[i]
                # select columns to compare (small set)
                cols = [c for c in df_step.columns if c in df_fused.columns]
                row_diff = {c: (row_s[c], row_f[c]) for c in cols if not pd.isna(row_s[c]) or not pd.isna(row_f[c]) and not (row_s[c] == row_f[c])}
                # record non-equal
                differences = {c: (row_s[c], row_f[c]) for c in cols if not pd.isna(row_s[c]) and not pd.isna(row_f[c]) and row_s[c] != row_f[c]}
                if differences:
                    diffs.append((i, differences))
            rf.write(f"Differences by position (first 50 shown): total differing rows={len(diffs)}\n")
            for idx, d in diffs[:50]:
                rf.write(f"pos {idx}: {d}\n")
        else:
            rf.write(f"Using key column '{key}' to align rows.\n")
            left = df_step.set_index(key)
            right = df_fused.set_index(key)
            # keys present in either
            all_keys = left.index.union(right.index)
            missing_in_step = [k for k in all_keys if k not in left.index]
            missing_in_fused = [k for k in all_keys if k not in right.index]
            rf.write(f"missing_in_step: {len(missing_in_step)}\n")
            rf.write(f"missing_in_fused: {len(missing_in_fused)}\n")
            # Compare common keys
            common = left.index.intersection(right.index)
            diffs = []
            for k in common:
                rs = left.loc[k]
                rf_row = right.loc[k]
                cols = [c for c in left.columns if c in right.columns]
                differences = {c: (rs[c], rf_row[c]) for c in cols if not pd.isna(rs[c]) and not pd.isna(rf_row[c]) and rs[c] != rf_row[c]}
                if differences:
                    diffs.append((k, differences))
            rf.write(f"common_keys_with_differences: {len(diffs)}\n")
            rf.write("First 50 differences:\n")
            for k, d in diffs[:50]:
                rf.write(f"key {k}: {d}\n")

    print("Wrote:", step_csv, fused_csv, report_txt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--pop", type=int, default=1000)
    parser.add_argument("--dur", type=int, default=3)
    parser.add_argument("--out-dir", default="results")
    args = parser.parse_args()

    run_case(args.seed, args.pop, args.dur, args.out_dir)


if __name__ == "__main__":
    main()
