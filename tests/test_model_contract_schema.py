from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import lifecourse.model_contract as model_contract
import pytest
from lifecourse.model_contract import (
    AnalysisOptions,
    ArtifactKind,
    ArtifactReference,
    DiagnosticLevel,
    DiagnosticRecord,
    EngineMetadata,
    ModelRunRequest,
    ModelRunResponse,
    SeedPolicy,
    generate_contract_schemas,
)
from pydantic import ValidationError


def _valid_request_payload() -> dict[str, object]:
    return {
        "contract_version": "v1",
        "request_id": "req-001",
        "model_id": "lifecourse-genomics",
        "parameter_set": "australia",
        "engine": {
            "engine_id": "default-dtm",
            "engine_name": "Default Discrete-Time Microsimulation",
            "engine_version": "1.0.0",
            "capabilities": {
                "static": False,
                "discrete_time": True,
                "continuous_time": False,
                "markov": False,
                "semi_markov": False,
                "des": False,
                "hybrid": False,
                "supports_parallel_psa": True,
            },
        },
        "run_mode": "probabilistic",
        "population_size": 1000,
        "time_horizon_years": 10,
        "seed_policy": {"strategy": "fixed", "seed": 1234, "replicate_count": 10},
        "scenarios": [
            {
                "scenario_id": "base",
                "label": "Base case",
                "overrides": [
                    {"parameter_id": "discount_rate", "value": 0.03},
                ],
            }
        ],
        "parameter_overrides": [
            {"parameter_id": "utility_weight", "value": 0.95, "source": "demo"},
        ],
        "analysis_options": {
            "budget_impact": True,
            "equity_analysis": True,
            "subgroup_analysis": ["age", "sex"],
            "calculate_evpi": True,
            "calculate_evppi": True,
            "calculate_evsi": False,
            "calculate_enbs": True,
            "confidence_level": 0.9,
        },
    }


def _valid_response_payload() -> dict[str, object]:
    return json.loads(
        Path("specs/core-api/fixtures/v1/model-run-response.fixture.json").read_text(
            encoding="utf-8"
        )
    )


def test_request_validates_required_fields() -> None:
    request = ModelRunRequest.model_validate(_valid_request_payload())

    assert request.contract_version == "v1"
    assert request.engine.capabilities.discrete_time is True
    assert request.seed_policy.seed == 1234
    assert request.analysis_options.calculate_evpi is True


def test_request_rejects_missing_seed_for_fixed_policy() -> None:
    payload = _valid_request_payload()
    payload["seed_policy"] = {"strategy": "fixed"}

    with pytest.raises(ValidationError, match="seed is required"):
        ModelRunRequest.model_validate(payload)


def test_seed_policy_rejects_seed_for_random_strategy() -> None:
    with pytest.raises(ValidationError, match="seed must be omitted"):
        SeedPolicy.model_validate({"strategy": "random", "seed": 123})


def test_request_rejects_unknown_fields() -> None:
    payload = _valid_request_payload()
    payload["unexpected_field"] = True

    with pytest.raises(ValidationError, match="unexpected_field"):
        ModelRunRequest.model_validate(payload)


def test_request_round_trips_through_json() -> None:
    request = ModelRunRequest.model_validate(_valid_request_payload())
    round_tripped = ModelRunRequest.model_validate_json(request.model_dump_json())

    assert round_tripped == request


def test_response_round_trips_through_json() -> None:
    response = ModelRunResponse.model_validate(_valid_response_payload())
    round_tripped = ModelRunResponse.model_validate_json(response.model_dump_json())

    assert round_tripped == response
    assert round_tripped.artifacts[0].kind is ArtifactKind.summary
    assert round_tripped.diagnostics[0].level is DiagnosticLevel.info


def test_schema_generation_matches_committed_files(tmp_path: Path) -> None:
    written = generate_contract_schemas(tmp_path)

    for name, generated_path in written.items():
        committed_path = Path("specs/core-api/schemas/v1") / f"{name}.schema.json"
        assert committed_path.exists()
        assert json.loads(generated_path.read_text(encoding="utf-8")) == json.loads(
            committed_path.read_text(encoding="utf-8")
        )


def test_fixture_pair_matches_reference_api() -> None:
    request = ModelRunRequest.model_validate_json(
        Path("specs/core-api/fixtures/v1/model-run-request.fixture.json").read_text(
            encoding="utf-8"
        )
    )
    response = model_contract.run_model_request(request)
    committed_response = ModelRunResponse.model_validate_json(
        Path("specs/core-api/fixtures/v1/model-run-response.fixture.json").read_text(
            encoding="utf-8"
        )
    )

    assert response == committed_response


def test_validate_artifact_metadata_round_trips_valid_response() -> None:
    response = ModelRunResponse.model_validate(_valid_response_payload())

    assert model_contract.validate_artifact_metadata(response) == response


def test_schema_cli_writes_and_validates(tmp_path: Path) -> None:
    assert generate_contract_schemas(tmp_path)["model-run-request"].exists()
    assert generate_contract_schemas(tmp_path)["model-run-response"].exists()

    assert model_contract.main(["--schema-dir", str(tmp_path)]) == 0


def test_schema_cli_detects_mismatches(tmp_path: Path) -> None:
    generate_contract_schemas(tmp_path)
    schema_path = tmp_path / "model-run-request.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["request_id"]["title"] = "Changed"
    schema_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")

    with pytest.raises(AssertionError, match="schema mismatch"):
        model_contract.main(["--schema-dir", str(tmp_path)])


def test_reference_api_and_cli_match_for_fixture(tmp_path: Path) -> None:
    request_path = Path("specs/core-api/fixtures/v1/model-run-request.fixture.json")
    request = ModelRunRequest.model_validate_json(request_path.read_text())
    api_response = model_contract.run_model_request(request)

    stdout = StringIO()
    with redirect_stdout(stdout):
        assert model_contract.main(["--request", str(request_path)]) == 0
    cli_response = ModelRunResponse.model_validate_json(stdout.getvalue())

    assert cli_response == api_response


def test_reference_api_writes_output_file(tmp_path: Path) -> None:
    request_path = Path("specs/core-api/fixtures/v1/model-run-request.fixture.json")
    output_path = tmp_path / "response.json"

    assert (
        model_contract.main(
            ["--request", str(request_path), "--output", str(output_path)]
        )
        == 0
    )
    response = ModelRunResponse.model_validate_json(output_path.read_text())
    assert response.request_id == "req-001"
    assert response.status == "success"


def test_artifact_metadata_rejects_absolute_paths() -> None:
    payload = _valid_response_payload()
    payload["artifacts"][0]["path"] = "/tmp/summary.json"

    with pytest.raises(ValidationError, match="artifact path must be relative"):
        ModelRunResponse.model_validate(payload)


def test_artifact_metadata_requires_schema_version_when_schema_ref_present() -> None:
    payload = _valid_response_payload()
    payload["artifacts"][0]["schema_version"] = None

    with pytest.raises(ValidationError, match="schema_version is required"):
        ModelRunResponse.model_validate(payload)


def test_artifact_metadata_requires_algorithm_prefix_for_checksum() -> None:
    payload = _valid_response_payload()
    payload["artifacts"][0]["checksum"] = "abc123"

    with pytest.raises(ValidationError, match="checksum must include"):
        ModelRunResponse.model_validate(payload)


def test_engine_metadata_and_supporting_models_validate() -> None:
    engine = EngineMetadata.model_validate(_valid_request_payload()["engine"])
    seed_policy = SeedPolicy.model_validate(
        {"strategy": "derived", "seed": 42, "replicate_count": 2}
    )
    analysis = AnalysisOptions.model_validate({"confidence_level": 0.9})
    artifact = ArtifactReference.model_validate(
        {
            "artifact_id": "diagnostics",
            "kind": "diagnostics",
            "media_type": "application/json",
            "path": "artifacts/diagnostics.json",
        }
    )
    diagnostic = DiagnosticRecord.model_validate(
        {
            "level": "warning",
            "code": "DEMO",
            "message": "Illustrative warning.",
        }
    )

    assert engine.capabilities.supports_parallel_psa is True
    assert seed_policy.replicate_count == 2
    assert analysis.confidence_level == 0.9
    assert artifact.kind is ArtifactKind.diagnostics
    assert diagnostic.level is DiagnosticLevel.warning
