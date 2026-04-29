from __future__ import annotations

import pytest
from lifecourse.analysis.run_helpers import run_sim
from lifecourse.engine_contract import (
    DEFAULT_ENGINE_ID,
    EngineResolution,
    UnknownEngineError,
    default_engine_metadata,
    resolve_engine_selection,
    run_registered_simulation,
    select_engine,
)
from lifecourse.model.parameters import (
    DISTRIBUTIONS,
    START_YEAR,
    sample_params_from_dist,
)
from lifecourse.model_contract import SeedPolicy


def test_default_engine_metadata_matches_current_discrete_time_engine() -> None:
    metadata = default_engine_metadata()

    assert metadata.engine_id == DEFAULT_ENGINE_ID
    assert metadata.capabilities.discrete_time is True
    assert metadata.capabilities.static is False
    assert metadata.capabilities.continuous_time is False


def test_select_engine_uses_default_when_no_name_is_provided() -> None:
    engine = select_engine()

    assert engine.metadata.engine_id == DEFAULT_ENGINE_ID
    assert engine.metadata.engine_name == "Default Discrete-Time Microsimulation"


def test_select_engine_rejects_unknown_names() -> None:
    with pytest.raises(UnknownEngineError, match="unknown simulation engine"):
        select_engine("not-a-real-engine")


def test_resolve_engine_selection_includes_diagnostic_metadata() -> None:
    resolution = resolve_engine_selection(
        seed_policy=SeedPolicy.model_validate(
            {"strategy": "derived", "seed": 42, "replicate_count": 3}
        )
    )

    assert isinstance(resolution, EngineResolution)
    assert resolution.selection_source == "default"
    assert resolution.diagnostic.code == "ENGINE_SELECTION"
    assert resolution.diagnostic.details["engine_id"] == DEFAULT_ENGINE_ID
    assert resolution.diagnostic.details["seed_strategy"] == "derived"
    assert resolution.diagnostic.details["replicate_count"] == 3


def test_resolve_engine_selection_marks_explicit_requests() -> None:
    resolution = resolve_engine_selection(DEFAULT_ENGINE_ID)

    assert resolution.selection_source == "explicit"
    assert resolution.diagnostic.details["requested_engine_id"] == DEFAULT_ENGINE_ID


def test_registry_run_matches_direct_run_for_fixed_seed() -> None:
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=123)
    years = list(range(START_YEAR, START_YEAR + 2))

    direct = run_sim(sampled_params, pop_size=10, seed_idx=5, years=years)
    registry_run = run_registered_simulation(
        sampled_params,
        pop_size=10,
        seed_idx=5,
        years=years,
    )

    assert registry_run.d_cost == direct[0]
    assert registry_run.d_qaly == direct[1]
    assert registry_run.resolution.metadata.engine_id == DEFAULT_ENGINE_ID
    assert registry_run.diagnostics[0].code == "ENGINE_SELECTION"
    assert registry_run.diagnostics[1].code == "ENGINE_EXECUTION"
