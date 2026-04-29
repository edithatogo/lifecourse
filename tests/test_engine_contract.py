from __future__ import annotations

import pytest
from lifecourse.engine_contract import (
    DEFAULT_ENGINE_ID,
    EngineResolution,
    UnknownEngineError,
    default_engine_metadata,
    resolve_engine_selection,
    select_engine,
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
