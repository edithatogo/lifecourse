#!/usr/bin/env python3
"""Validation harness: compare PopulationSystemDask.step vs step_fused

Saves a CSV summarising timings and aggregate differences for each
seed / population size / duration combination.
"""

import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.abspath("src"))

import numpy as np

from lifecourse.model.parameters import (
    DISTRIBUTIONS,
    START_YEAR,
    get_mean_params,
    prepare_dask_params,
)
from lifecourse.model.population_system import PopulationSystemDask


def run_validation(seeds, pop_sizes, durations, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fieldnames = [
        "seed",
        "pop_size",
        "duration_years",
        "wall_time_step_s",
        "wall_time_fused_s",
        "n_step",
        "n_fused",
        "delta_n",
        "cost_step",
        "cost_fused",
        "delta_cost",
        "qaly_step",
        "qaly_fused",
        "delta_qaly",
    ]

    with open(out_path, "w", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()

        for seed in seeds:
            for pop in pop_sizes:
                # Build deterministic params for the run
                mean = get_mean_params(DISTRIBUTIONS)
                params = prepare_dask_params(mean)

                for dur in durations:
                    # Create fresh initial populations for comparability
                    np.random.seed(int(seed))
                    ps_step = PopulationSystemDask(pop, params, arm="prospective")
                    np.random.seed(int(seed))
                    ps_fused = PopulationSystemDask(pop, params, arm="prospective")

                    # Determine absolute years to run (START_YEAR .. START_YEAR+dur-1)
                    years = [START_YEAR + i for i in range(dur)]

                    # Run baseline step sequence
                    t0 = time.perf_counter()
                    for y in years:
                        ps_step.step(y)
                    t1 = time.perf_counter()
                    wall_step = t1 - t0

                    # Run fused sequence from same initial pop
                    t0 = time.perf_counter()
                    for y in years:
                        ps_fused.step_fused(y)
                    t1 = time.perf_counter()
                    wall_fused = t1 - t0

                    # Aggregate results (compute daskframes)
                    df_step = ps_step.pop.compute()
                    df_fused = ps_fused.pop.compute()

                    n_step = len(df_step)
                    n_fused = len(df_fused)
                    cost_step = (
                        float(df_step["annual_cost"].sum()) if n_step > 0 else 0.0
                    )
                    cost_fused = (
                        float(df_fused["annual_cost"].sum()) if n_fused > 0 else 0.0
                    )
                    qaly_step = (
                        float(df_step["annual_qaly"].sum()) if n_step > 0 else 0.0
                    )
                    qaly_fused = (
                        float(df_fused["annual_qaly"].sum()) if n_fused > 0 else 0.0
                    )

                    writer.writerow(
                        {
                            "seed": seed,
                            "pop_size": pop,
                            "duration_years": dur,
                            "wall_time_step_s": f"{wall_step:.6f}",
                            "wall_time_fused_s": f"{wall_fused:.6f}",
                            "n_step": n_step,
                            "n_fused": n_fused,
                            "delta_n": n_fused - n_step,
                            "cost_step": f"{cost_step:.6f}",
                            "cost_fused": f"{cost_fused:.6f}",
                            "delta_cost": f"{(cost_fused - cost_step):.6f}",
                            "qaly_step": f"{qaly_step:.6f}",
                            "qaly_fused": f"{qaly_fused:.6f}",
                            "delta_qaly": f"{(qaly_fused - qaly_step):.6f}",
                        }
                    )


def parse_list(arg):
    return [int(x) for x in str(arg).split(",") if x.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="42,100,7")
    parser.add_argument("--pop-sizes", default="100,1000")
    parser.add_argument("--durations", default="1,2,3")
    parser.add_argument("--out", default="results/validate_step_fused.csv")
    args = parser.parse_args()

    seeds = parse_list(args.seeds)
    pop_sizes = parse_list(args.pop_sizes)
    durations = parse_list(args.durations)

    print(
        "Running validation with seeds=",
        seeds,
        "pop_sizes=",
        pop_sizes,
        "durations=",
        durations,
    )
    run_validation(seeds, pop_sizes, durations, args.out)
    print("Wrote results to", args.out)


if __name__ == "__main__":
    main()
