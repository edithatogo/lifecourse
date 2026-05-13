from __future__ import annotations

from pathlib import Path

from lifecourse.engine_contract import STATIC_ENGINE_ID, run_engine_request
from lifecourse.engine_scaffolds import STATIC_ENGINE_METADATA
from lifecourse.model_contract import ModelRunRequest, ModelRunResponse


def _static_request() -> ModelRunRequest:
    return ModelRunRequest.model_validate_json(
        Path("specs/core-api/fixtures/v1/model-run-request.fixture.json").read_text(
            encoding="utf-8"
        )
    ).model_copy(update={"engine": STATIC_ENGINE_METADATA.model_copy()})


def test_static_engine_is_registered_and_experimental() -> None:
    request = _static_request()

    response = run_engine_request(request)

    assert response.engine.engine_id == STATIC_ENGINE_ID
    assert response.engine.capabilities.static is True
    assert response.summary.scenario_count == 1
    assert response.summary.sample_count == request.seed_policy.replicate_count
    assert response.diagnostics[0].code == "ENGINE_SELECTION"
    assert response.diagnostics[1].code == "STATIC_SCENARIO_RESULT"


def test_static_engine_run_is_deterministic_and_schema_compatible() -> None:
    request = _static_request()

    response_a = run_engine_request(request)
    response_b = run_engine_request(request)

    assert response_a == response_b
    assert response_a.artifacts[0].path.startswith("results/")
    assert response_a.artifacts[0].schema_ref == "heoml.v0.1.static_summary_table"
    assert ModelRunResponse.model_validate_json(response_a.model_dump_json()) == response_a
