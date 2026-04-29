from __future__ import annotations

import types
from collections.abc import Iterable
from typing import Any

import numpy as np
import pytest
from lifecourse.backend_evaluation import (
    BackendUnavailableError,
    calculate_evpi_value,
    calculate_net_monetary_benefit,
    evaluate_backend_readiness,
    recommend_numerical_backend,
    recommend_tabular_backend,
)


def test_backend_readiness_reports_known_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    available = {"numpy", "pandas", "dask"}

    def fake_find_spec(name: str) -> object | None:
        return object() if name in available else None

    monkeypatch.setattr("lifecourse.backend_evaluation.find_spec", fake_find_spec)

    readiness = evaluate_backend_readiness()

    assert readiness["numpy"].available is True
    assert readiness["pandas"].available is True
    assert readiness["dask"].available is True
    assert readiness["polars"].available is False
    assert readiness["jax"].purpose == "optional array acceleration"


def test_tabular_recommendations_are_deterministic() -> None:
    assert recommend_tabular_backend(row_count=10_000).backend == "pandas"
    assert (
        recommend_tabular_backend(
            row_count=2_000_000, operations=("groupby", "join")
        ).backend
        == "polars"
    )
    assert (
        recommend_tabular_backend(
            row_count=2_000_000,
            operations=("groupby",),
            requires_distributed=True,
        ).backend
        == "dask"
    )


def test_numerical_recommendations_separate_orchestration_from_kernels() -> None:
    assert (
        recommend_numerical_backend(
            pop_size=1_000,
            simulation_years=5,
            psa_iterations=0,
            pure_array_kernel=False,
        ).backend
        == "numpy"
    )
    assert (
        recommend_numerical_backend(
            pop_size=100_000,
            simulation_years=20,
            psa_iterations=0,
            pure_array_kernel=True,
        ).backend
        == "jax"
    )
    assert (
        recommend_numerical_backend(
            pop_size=10_000,
            simulation_years=10,
            psa_iterations=1_000,
            pure_array_kernel=False,
        ).backend
        == "dask"
    )


def test_net_monetary_benefit_uses_numpy_by_default() -> None:
    result = calculate_net_monetary_benefit(
        delta_qalys=[1.0, 2.0],
        delta_costs=[1_000.0, 5_000.0],
        willingness_to_pay=50_000.0,
    )

    np.testing.assert_allclose(result, np.array([49_000.0, 95_000.0]))


def test_net_monetary_benefit_fails_clearly_when_jax_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_find_spec(name: str) -> object | None:
        return None

    monkeypatch.setattr("lifecourse.backend_evaluation.find_spec", fake_find_spec)

    with pytest.raises(BackendUnavailableError, match="JAX backend requested"):
        calculate_net_monetary_benefit(
            delta_qalys=[1.0],
            delta_costs=[1_000.0],
            willingness_to_pay=50_000.0,
            backend="jax",
        )


def test_net_monetary_benefit_can_dispatch_to_jax_like_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeJaxNumpy:
        @staticmethod
        def asarray(values: Iterable[float], dtype: Any | None = None) -> np.ndarray:
            calls.append("asarray")
            return np.asarray(values, dtype=dtype)

    def fake_device_get(value: Any) -> Any:
        return value

    def fake_find_spec(name: str) -> object | None:
        return object()

    def fake_import_module(name: str) -> types.SimpleNamespace:
        return fake_jax

    fake_jax = types.SimpleNamespace(
        numpy=FakeJaxNumpy(),
        device_get=fake_device_get,
    )

    monkeypatch.setattr("lifecourse.backend_evaluation.find_spec", fake_find_spec)
    monkeypatch.setattr(
        "lifecourse.backend_evaluation.import_module", fake_import_module
    )

    result = calculate_net_monetary_benefit(
        delta_qalys=[1.0, 2.0],
        delta_costs=[1_000.0, 5_000.0],
        willingness_to_pay=50_000.0,
        backend="jax",
    )

    np.testing.assert_allclose(result, np.array([49_000.0, 95_000.0]))
    assert calls == ["asarray", "asarray"]


def test_evpi_value_uses_numpy_by_default() -> None:
    result = calculate_evpi_value([10.0, 20.0, 40.0])

    assert result == 40.0 - np.mean(np.array([10.0, 20.0, 40.0]))


def test_evpi_value_fails_clearly_when_jax_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_find_spec(name: str) -> object | None:
        return None

    monkeypatch.setattr("lifecourse.backend_evaluation.find_spec", fake_find_spec)

    with pytest.raises(BackendUnavailableError, match="JAX backend requested"):
        calculate_evpi_value([10.0, 20.0], backend="jax")


def test_evpi_value_can_dispatch_to_jax_like_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeJaxNumpy:
        @staticmethod
        def asarray(values: Iterable[float], dtype: Any | None = None) -> np.ndarray:
            calls.append("asarray")
            return np.asarray(values, dtype=dtype)

        @staticmethod
        def mean(values: np.ndarray) -> float:
            calls.append("mean")
            return float(np.mean(values))

        @staticmethod
        def max(values: np.ndarray) -> float:
            calls.append("max")
            return float(np.max(values))

        @staticmethod
        def maximum(left: float, right: float) -> float:
            calls.append("maximum")
            return float(np.maximum(left, right))

    def fake_device_get(value: Any) -> Any:
        return value

    def fake_find_spec(name: str) -> object | None:
        return object()

    def fake_import_module(name: str) -> types.SimpleNamespace:
        return fake_jax

    fake_jax = types.SimpleNamespace(
        numpy=FakeJaxNumpy(),
        device_get=fake_device_get,
    )

    monkeypatch.setattr("lifecourse.backend_evaluation.find_spec", fake_find_spec)
    monkeypatch.setattr(
        "lifecourse.backend_evaluation.import_module", fake_import_module
    )

    result = calculate_evpi_value([10.0, 20.0, 40.0], backend="jax")

    assert result == 40.0 - np.mean(np.array([10.0, 20.0, 40.0]))
    assert calls == ["asarray", "max", "mean", "maximum"]
