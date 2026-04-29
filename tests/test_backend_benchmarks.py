from __future__ import annotations

from lifecourse.backend_benchmarks import (
    benchmark_dask_independent_tasks,
    benchmark_dask_scheduler_overhead,
    benchmark_evpi_value,
    benchmark_net_monetary_benefit,
    benchmark_tabular_groupby,
)


def test_tabular_groupby_benchmark_reports_serializable_summary() -> None:
    result = benchmark_tabular_groupby(row_count=100, group_count=5)
    payload = result.as_dict()

    assert payload["name"] == "tabular_groupby"
    assert payload["backend"] == "pandas"
    assert payload["item_count"] == 100
    assert payload["elapsed_seconds"] >= 0
    assert payload["throughput_per_second"] >= 0
    assert payload["recommendation"]["backend"] in {"pandas", "polars", "dask"}
    assert payload["metadata"]["group_count"] == 5
    assert payload["metadata"]["result_rows"] == 5


def test_nmb_benchmark_reports_serializable_summary() -> None:
    result = benchmark_net_monetary_benefit(item_count=100)
    payload = result.as_dict()

    assert payload["name"] == "net_monetary_benefit"
    assert payload["backend"] == "numpy"
    assert payload["item_count"] == 100
    assert payload["elapsed_seconds"] >= 0
    assert payload["throughput_per_second"] >= 0
    assert payload["recommendation"]["backend"] in {"numpy", "jax", "dask"}
    assert payload["metadata"]["result_size"] == 100
    assert payload["metadata"]["mean_result"] > 0


def test_evpi_benchmark_reports_selected_kernel_summary() -> None:
    result = benchmark_evpi_value(item_count=100)
    payload = result.as_dict()

    assert payload["name"] == "evpi_value"
    assert payload["backend"] == "numpy"
    assert payload["item_count"] == 100
    assert payload["elapsed_seconds"] >= 0
    assert payload["throughput_per_second"] >= 0
    assert payload["recommendation"]["backend"] in {"numpy", "jax", "dask"}
    assert payload["metadata"]["selected_for_jax_pilot"] is True
    assert payload["metadata"]["evpi"] > 0


def test_dask_scheduler_overhead_benchmark_reports_decision_evidence() -> None:
    result = benchmark_dask_scheduler_overhead(item_count=25)
    payload = result.as_dict()

    assert payload["name"] == "dask_scheduler_overhead"
    assert payload["backend"] == "dask"
    assert payload["item_count"] == 25
    assert payload["elapsed_seconds"] >= 0
    assert payload["throughput_per_second"] >= 0
    assert payload["recommendation"]["backend"] in {"numpy", "dask"}
    assert payload["metadata"]["scheduler"] == "synchronous"
    assert payload["metadata"]["matches_numpy"] is True


def test_dask_independent_tasks_benchmark_reports_psa_style_evidence() -> None:
    result = benchmark_dask_independent_tasks(task_count=8)
    payload = result.as_dict()

    assert payload["name"] == "dask_independent_tasks"
    assert payload["backend"] == "dask"
    assert payload["item_count"] == 8
    assert payload["elapsed_seconds"] >= 0
    assert payload["throughput_per_second"] >= 0
    assert payload["recommendation"]["backend"] in {"numpy", "dask"}
    assert payload["metadata"]["scheduler"] == "threads"
    assert payload["metadata"]["result_sum"] == sum(index * index for index in range(8))
