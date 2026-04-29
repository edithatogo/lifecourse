from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from typing import Literal

import numpy as np
from numpy.typing import NDArray

BackendName = Literal["numpy", "pandas", "dask", "polars", "jax"]
NumericalBackend = Literal["numpy", "jax"]


class BackendUnavailableError(RuntimeError):
    """Raised when an explicitly requested optional backend is unavailable."""


@dataclass(frozen=True)
class BackendReadiness:
    """Availability and intended role for a candidate backend."""

    name: str
    available: bool
    purpose: str
    required_for_default_runtime: bool = False


@dataclass(frozen=True)
class BackendRecommendation:
    """A deterministic backend recommendation with the reason attached."""

    backend: BackendName
    reason: str


_BACKEND_PURPOSES: dict[str, tuple[str, bool]] = {
    "numpy": ("default numerical array runtime", True),
    "pandas": ("default tabular runtime", True),
    "dask": ("current distributed orchestration runtime", True),
    "polars": ("optional tabular evaluation target", False),
    "jax": ("optional array acceleration", False),
    "jaxlib": ("optional XLA runtime for JAX", False),
    "blackjax": ("optional Bayesian and Monte Carlo experimentation", False),
}


def evaluate_backend_readiness() -> dict[str, BackendReadiness]:
    """Report availability for current and candidate backend packages."""

    return {
        name: BackendReadiness(
            name=name,
            available=find_spec(name) is not None,
            purpose=purpose,
            required_for_default_runtime=required,
        )
        for name, (purpose, required) in _BACKEND_PURPOSES.items()
    }


def recommend_tabular_backend(
    *,
    row_count: int,
    operations: Sequence[str] = (),
    requires_distributed: bool = False,
) -> BackendRecommendation:
    """Recommend a tabular backend without importing optional packages."""

    if requires_distributed:
        return BackendRecommendation(
            backend="dask",
            reason="distributed orchestration is still required for this workload",
        )

    heavy_tabular_ops = {"groupby", "join", "scan", "aggregate", "filter"}
    if row_count >= 1_000_000 and heavy_tabular_ops.intersection(operations):
        return BackendRecommendation(
            backend="polars",
            reason="large eager tabular transforms are a strong Polars pilot candidate",
        )

    return BackendRecommendation(
        backend="pandas",
        reason="small or compatibility-sensitive tabular work should stay on pandas",
    )


def recommend_numerical_backend(
    *,
    pop_size: int,
    simulation_years: int,
    psa_iterations: int,
    pure_array_kernel: bool,
) -> BackendRecommendation:
    """Recommend a numerical backend for a workload shape."""

    work_units = pop_size * max(simulation_years, 1) * max(psa_iterations, 1)

    if psa_iterations >= 100 and not pure_array_kernel:
        return BackendRecommendation(
            backend="dask",
            reason="many independent PSA runs currently fit Dask orchestration",
        )

    if pure_array_kernel and work_units >= 1_000_000:
        return BackendRecommendation(
            backend="jax",
            reason="large pure-array kernels are suitable for JAX/XLA evaluation",
        )

    return BackendRecommendation(
        backend="numpy",
        reason="default NumPy execution is simplest for this workload",
    )


def calculate_net_monetary_benefit(
    *,
    delta_qalys: Iterable[float],
    delta_costs: Iterable[float],
    willingness_to_pay: float,
    backend: NumericalBackend = "numpy",
) -> NDArray[np.float64]:
    """Calculate net monetary benefit with NumPy or an explicit optional JAX path."""

    if backend == "numpy":
        qaly_array = np.asarray(delta_qalys, dtype=np.float64)
        cost_array = np.asarray(delta_costs, dtype=np.float64)
        return (qaly_array * willingness_to_pay) - cost_array

    if find_spec("jax") is None:
        raise BackendUnavailableError(
            "JAX backend requested but `jax` is not installed. "
            "Install the optional `jax` backend extra before using backend='jax'."
        )

    jax = import_module("jax")
    jnp = jax.numpy
    qaly_array = jnp.asarray(delta_qalys, dtype=np.float64)
    cost_array = jnp.asarray(delta_costs, dtype=np.float64)
    result = (qaly_array * willingness_to_pay) - cost_array
    return np.asarray(jax.device_get(result), dtype=np.float64)


def calculate_evpi_value(
    net_benefits: Iterable[float],
    *,
    backend: NumericalBackend = "numpy",
) -> float:
    """Calculate scalar EVPI from a pure net-benefit vector."""

    if backend == "numpy":
        values = np.asarray(net_benefits, dtype=np.float64)
        evpi = np.maximum(0.0, np.max(values) - np.mean(values))
        return float(evpi)

    if find_spec("jax") is None:
        raise BackendUnavailableError(
            "JAX backend requested but `jax` is not installed. "
            "Install the optional `jax` backend extra before using backend='jax'."
        )

    jax = import_module("jax")
    jnp = jax.numpy
    values = jnp.asarray(net_benefits, dtype=np.float64)
    evpi = jnp.maximum(0.0, jnp.max(values) - jnp.mean(values))
    return float(jax.device_get(evpi))
