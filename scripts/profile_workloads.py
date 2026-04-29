from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from lifecourse.analysis.run_helpers import run_sim
from lifecourse.backend_benchmarks import (
    benchmark_dask_independent_tasks,
    benchmark_evpi_value,
    benchmark_net_monetary_benefit,
    benchmark_tabular_groupby,
)
from lifecourse.data_loader import apply_scenario_overrides
from lifecourse.model.parameters import (
    DISTRIBUTIONS,
    START_YEAR,
    sample_params_from_dist,
)


def _run_benchmarks() -> None:
    benchmark_tabular_groupby(row_count=25_000)
    benchmark_net_monetary_benefit(item_count=25_000)
    benchmark_evpi_value(item_count=25_000)
    benchmark_dask_independent_tasks(task_count=20)


def _run_simulation() -> None:
    params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    run_sim(params, pop_size=100, years=range(START_YEAR, START_YEAR + 2), seed_idx=42)


def _run_input_boundary() -> None:
    base = {"familial_prop": 0.2, "yield_wgs": 0.6, "severity_mild_prop": 0.7}
    overrides = {"familial_prop": 0.05, "yield_wgs": 0.8, "severity_mild_prop": 0.6}
    apply_scenario_overrides(base, overrides)
    pd.DataFrame(
        {
            "group": np.repeat(["a", "b"], 500),
            "value": np.arange(1_000),
        }
    ).groupby("group")["value"].sum()


def main() -> None:
    parser = argparse.ArgumentParser(description="Representative profiling workloads.")
    parser.add_argument(
        "--workload",
        choices=["all", "benchmarks", "simulation", "inputs"],
        default="all",
    )
    args = parser.parse_args()

    if args.workload in {"all", "benchmarks"}:
        _run_benchmarks()
    if args.workload in {"all", "simulation"}:
        _run_simulation()
    if args.workload in {"all", "inputs"}:
        _run_input_boundary()


if __name__ == "__main__":
    main()
