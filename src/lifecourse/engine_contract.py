from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from lifecourse.engine_runner import run_discrete_time_simulation
from lifecourse.model_contract import (
    DiagnosticLevel,
    DiagnosticRecord,
    EngineCapabilities,
    EngineMetadata,
    ModelRunRequest,
    ModelRunResponse,
    SeedPolicy,
    run_model_request,
)

DEFAULT_ENGINE_ID = "default-dtm"
DEFAULT_ENGINE_NAME = "Default Discrete-Time Microsimulation"
DEFAULT_ENGINE_VERSION = "1.0.0"


@runtime_checkable
class SimulationEngine(Protocol):
    """Typed interface for a simulation engine implementation."""

    metadata: EngineMetadata

    def run(self, request: ModelRunRequest) -> ModelRunResponse: ...


@dataclass(frozen=True, slots=True)
class SimulationEngineSpec:
    """Registry entry for a named simulation engine."""

    metadata: EngineMetadata
    runner: Callable[[ModelRunRequest], ModelRunResponse]


@dataclass(frozen=True, slots=True)
class EngineResolution:
    """Resolved engine metadata plus a diagnostic selection record."""

    metadata: EngineMetadata
    selection_source: Literal["default", "explicit"]
    diagnostic: DiagnosticRecord


@dataclass(frozen=True, slots=True)
class EngineRunResult:
    """Execution result for a registry-mediated simulation run."""

    resolution: EngineResolution
    d_cost: float
    d_qaly: float
    diagnostics: tuple[DiagnosticRecord, ...] = ()


class UnknownEngineError(ValueError):
    """Raised when a requested engine is not available."""


def _default_engine_spec() -> SimulationEngineSpec:
    metadata = EngineMetadata(
        engine_id=DEFAULT_ENGINE_ID,
        engine_name=DEFAULT_ENGINE_NAME,
        engine_version=DEFAULT_ENGINE_VERSION,
        capabilities=EngineCapabilities(),
    )
    return SimulationEngineSpec(metadata=metadata, runner=run_model_request)


_ENGINE_REGISTRY: dict[str, SimulationEngineSpec] = {
    DEFAULT_ENGINE_ID: _default_engine_spec(),
}


def register_engine(spec: SimulationEngineSpec) -> None:
    """Register or replace a simulation engine specification."""

    _ENGINE_REGISTRY[spec.metadata.engine_id] = spec


def list_engine_ids() -> tuple[str, ...]:
    """Return the registered engine ids in sorted order."""

    return tuple(sorted(_ENGINE_REGISTRY))


def get_engine(engine_id: str) -> SimulationEngineSpec:
    """Return the registered engine spec for a concrete engine id."""

    try:
        return _ENGINE_REGISTRY[engine_id]
    except KeyError as exc:  # pragma: no cover - defensive branch
        available = ", ".join(list_engine_ids())
        raise UnknownEngineError(
            f"unknown simulation engine {engine_id!r}; available engines: {available}"
        ) from exc


def default_engine_metadata() -> EngineMetadata:
    """Return the default maintained simulation-engine metadata."""

    return _ENGINE_REGISTRY[DEFAULT_ENGINE_ID].metadata


def select_engine(engine_id: str | None = None) -> SimulationEngineSpec:
    """Resolve the engine specification for a request."""

    return get_engine(DEFAULT_ENGINE_ID if engine_id is None else engine_id)


def resolve_engine_selection(
    engine_id: str | None = None,
    seed_policy: SeedPolicy | None = None,
) -> EngineResolution:
    """Return resolved engine metadata and a selection diagnostic."""

    selection_source: Literal["default", "explicit"] = (
        "default" if engine_id is None else "explicit"
    )
    spec = select_engine(engine_id)
    details: dict[str, object] = {
        "requested_engine_id": engine_id,
        "engine_id": spec.metadata.engine_id,
        "engine_name": spec.metadata.engine_name,
        "engine_version": spec.metadata.engine_version,
        "selection_source": selection_source,
        "available_engine_ids": list_engine_ids(),
    }
    if seed_policy is not None:
        strategy = getattr(seed_policy, "strategy", None)
        replicate_count = getattr(seed_policy, "replicate_count", None)
        seed = getattr(seed_policy, "seed", None)
        details.update(
            {
                "seed_strategy": getattr(strategy, "value", strategy),
                "replicate_count": replicate_count,
                "seed": seed,
            }
        )
    diagnostic = DiagnosticRecord(
        level=DiagnosticLevel.info,
        code="ENGINE_SELECTION",
        message=f"Selected engine {spec.metadata.engine_id}.",
        details=details,
    )
    return EngineResolution(
        metadata=spec.metadata,
        selection_source=selection_source,
        diagnostic=diagnostic,
    )


def run_registered_simulation(
    sampled_params: Any,
    *,
    pop_size: int,
    seed_idx: int | None = None,
    years: list[int] | tuple[int, ...] | None = None,
    debug: bool = False,
    engine_id: str | None = None,
) -> EngineRunResult:
    """Execute the current simulation through the engine registry."""

    resolution = resolve_engine_selection(engine_id=engine_id)
    d_cost, d_qaly = run_discrete_time_simulation(
        sampled_params,
        pop_size=pop_size,
        seed_idx=seed_idx,
        years=years,
        debug=debug,
    )
    diagnostics = (
        resolution.diagnostic,
        DiagnosticRecord(
            level=DiagnosticLevel.info,
            code="ENGINE_EXECUTION",
            message=f"Executed engine {resolution.metadata.engine_id}.",
            details={
                "engine_id": resolution.metadata.engine_id,
                "selection_source": resolution.selection_source,
                "seed_idx": seed_idx,
                "pop_size": pop_size,
                "year_count": len(years) if years is not None else None,
                "debug": debug,
            },
        ),
    )
    return EngineRunResult(
        resolution=resolution,
        d_cost=float(d_cost),
        d_qaly=float(d_qaly),
        diagnostics=diagnostics,
    )
