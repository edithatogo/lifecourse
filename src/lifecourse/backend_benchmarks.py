from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

import dask
import numpy as np
import pandas as pd

from lifecourse.backend_evaluation import (
    BackendRecommendation,
    calculate_evpi_value,
    calculate_net_monetary_benefit,
    recommend_numerical_backend,
    recommend_tabular_backend,
)

BenchmarkBackend = Literal["pandas", "numpy", "dask"]


@dataclass(frozen=True)
class BackendBenchmarkResult:
    """Serializable summary for lightweight backend migration benchmarks."""

    name: str
    backend: BenchmarkBackend
    item_count: int
    elapsed_seconds: float
    throughput_per_second: float
    recommendation: BackendRecommendation
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable benchmark summary."""

        return {
            "name": self.name,
            "backend": self.backend,
            "item_count": self.item_count,
            "elapsed_seconds": self.elapsed_seconds,
            "throughput_per_second": self.throughput_per_second,
            "recommendation": {
                "backend": self.recommendation.backend,
                "reason": self.recommendation.reason,
            },
            "metadata": self.metadata,
        }


def _throughput(item_count: int, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return float("inf")
    return item_count / elapsed_seconds


def benchmark_tabular_groupby(
    *, row_count: int = 10_000, group_count: int = 10
) -> BackendBenchmarkResult:
    """Benchmark a deterministic pandas groupby transform candidate."""

    groups = np.arange(row_count) % group_count
    frame = pd.DataFrame(
        {
            "group": groups,
            "value": np.arange(row_count, dtype=np.float64),
            "weight": (groups + 1).astype(np.float64),
        }
    )

    start = time.perf_counter()
    grouped = frame.groupby("group", as_index=False).agg(
        weighted_value=("value", "mean"),
        total_weight=("weight", "sum"),
    )
    elapsed = time.perf_counter() - start

    return BackendBenchmarkResult(
        name="tabular_groupby",
        backend="pandas",
        item_count=row_count,
        elapsed_seconds=elapsed,
        throughput_per_second=_throughput(row_count, elapsed),
        recommendation=recommend_tabular_backend(
            row_count=row_count,
            operations=("groupby", "aggregate"),
        ),
        metadata={
            "group_count": group_count,
            "result_rows": int(len(grouped)),
        },
    )


def benchmark_net_monetary_benefit(
    *, item_count: int = 10_000, willingness_to_pay: float = 50_000.0
) -> BackendBenchmarkResult:
    """Benchmark a deterministic NumPy net monetary benefit vector."""

    delta_qalys = np.linspace(0.1, 1.0, item_count, dtype=np.float64)
    delta_costs = np.linspace(1_000.0, 10_000.0, item_count, dtype=np.float64)

    start = time.perf_counter()
    result = calculate_net_monetary_benefit(
        delta_qalys=delta_qalys,
        delta_costs=delta_costs,
        willingness_to_pay=willingness_to_pay,
    )
    elapsed = time.perf_counter() - start

    return BackendBenchmarkResult(
        name="net_monetary_benefit",
        backend="numpy",
        item_count=item_count,
        elapsed_seconds=elapsed,
        throughput_per_second=_throughput(item_count, elapsed),
        recommendation=recommend_numerical_backend(
            pop_size=item_count,
            simulation_years=1,
            psa_iterations=0,
            pure_array_kernel=True,
        ),
        metadata={
            "result_size": int(result.size),
            "mean_result": float(np.mean(result)),
        },
    )


def benchmark_evpi_value(*, item_count: int = 10_000) -> BackendBenchmarkResult:
    """Benchmark the selected pure NumPy EVPI kernel for JAX migration."""

    net_benefits = np.linspace(-10_000.0, 25_000.0, item_count, dtype=np.float64)

    start = time.perf_counter()
    evpi = calculate_evpi_value(net_benefits)
    elapsed = time.perf_counter() - start

    return BackendBenchmarkResult(
        name="evpi_value",
        backend="numpy",
        item_count=item_count,
        elapsed_seconds=elapsed,
        throughput_per_second=_throughput(item_count, elapsed),
        recommendation=recommend_numerical_backend(
            pop_size=item_count,
            simulation_years=1,
            psa_iterations=0,
            pure_array_kernel=True,
        ),
        metadata={
            "evpi": evpi,
            "selected_for_jax_pilot": True,
        },
    )


def benchmark_dask_scheduler_overhead(
    *, item_count: int = 1_000
) -> BackendBenchmarkResult:
    """Benchmark small deterministic Dask orchestration against NumPy output."""

    values = np.arange(item_count, dtype=np.float64)
    expected = values + 1.0

    start = time.perf_counter()
    delayed_values = [
        dask.delayed(lambda value: value + 1.0)(value) for value in values
    ]
    result = np.asarray(dask.compute(*delayed_values, scheduler="synchronous"))
    elapsed = time.perf_counter() - start

    return BackendBenchmarkResult(
        name="dask_scheduler_overhead",
        backend="dask",
        item_count=item_count,
        elapsed_seconds=elapsed,
        throughput_per_second=_throughput(item_count, elapsed),
        recommendation=recommend_numerical_backend(
            pop_size=item_count,
            simulation_years=1,
            psa_iterations=0,
            pure_array_kernel=True,
        ),
        metadata={
            "scheduler": "synchronous",
            "matches_numpy": bool(np.array_equal(result, expected)),
        },
    )


def benchmark_dask_independent_tasks(
    *, task_count: int = 100
) -> BackendBenchmarkResult:
    """Benchmark PSA-style independent Dask tasks with threaded scheduling."""

    def square(index: int) -> int:
        return index * index

    start = time.perf_counter()
    tasks = [dask.delayed(square)(index) for index in range(task_count)]
    result = dask.compute(*tasks, scheduler="threads")
    elapsed = time.perf_counter() - start

    return BackendBenchmarkResult(
        name="dask_independent_tasks",
        backend="dask",
        item_count=task_count,
        elapsed_seconds=elapsed,
        throughput_per_second=_throughput(task_count, elapsed),
        recommendation=recommend_numerical_backend(
            pop_size=1,
            simulation_years=1,
            psa_iterations=task_count,
            pure_array_kernel=False,
        ),
        metadata={
            "scheduler": "threads",
            "result_sum": int(sum(result)),
        },
    )
