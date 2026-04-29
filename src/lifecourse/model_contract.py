from __future__ import annotations

import argparse
import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "v1"
DEFAULT_SCHEMA_DIR = Path("specs/core-api/schemas") / SCHEMA_VERSION


class RunMode(str, Enum):
    deterministic = "deterministic"
    probabilistic = "probabilistic"
    calibration = "calibration"
    validation = "validation"
    diagnostic = "diagnostic"


class ArtifactKind(str, Enum):
    table = "table"
    figure = "figure"
    diagnostics = "diagnostics"
    manifest = "manifest"
    parameter_set = "parameter_set"
    summary = "summary"


class DiagnosticLevel(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class SeedStrategy(str, Enum):
    fixed = "fixed"
    derived = "derived"
    random = "random"


class EngineCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    static: bool = False
    discrete_time: bool = True
    continuous_time: bool = False
    markov: bool = False
    semi_markov: bool = False
    des: bool = False
    hybrid: bool = False
    supports_parallel_psa: bool = True


class EngineMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine_id: str = Field(min_length=1)
    engine_name: str = Field(min_length=1)
    engine_version: str = Field(min_length=1)
    capabilities: EngineCapabilities


class SeedPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: SeedStrategy = SeedStrategy.fixed
    seed: int | None = None
    replicate_count: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def _validate_seed(self) -> SeedPolicy:
        if (
            self.strategy in {SeedStrategy.fixed, SeedStrategy.derived}
            and self.seed is None
        ):
            raise ValueError(
                f"seed is required when strategy is {self.strategy.value!r}"
            )
        if self.strategy is SeedStrategy.random and self.seed is not None:
            raise ValueError("seed must be omitted when strategy is 'random'")
        return self


class ParameterOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameter_id: str = Field(min_length=1)
    value: str | int | float | bool | None
    scope: str | None = None
    source: str | None = None


class ScenarioSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1)
    label: str | None = None
    notes: str | None = None
    overrides: list[ParameterOverride] = Field(default_factory=list)


class AnalysisOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_impact: bool = False
    equity_analysis: bool = False
    subgroup_analysis: list[str] = Field(default_factory=list)
    calculate_evpi: bool = False
    calculate_evppi: bool = False
    calculate_evsi: bool = False
    calculate_enbs: bool = False
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)


class ArtifactReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(min_length=1)
    kind: ArtifactKind
    media_type: str = Field(min_length=1)
    path: str = Field(min_length=1)
    schema_ref: str | None = None
    schema_version: str | None = None
    checksum: str | None = None

    @model_validator(mode="after")
    def _validate_artifact_metadata(self) -> ArtifactReference:
        if self.schema_ref is not None and self.schema_version is None:
            raise ValueError("schema_version is required when schema_ref is provided")
        if Path(self.path).is_absolute():
            raise ValueError("artifact path must be relative")
        if self.checksum is not None:
            if ":" not in self.checksum:
                raise ValueError(
                    "checksum must include an algorithm prefix such as 'sha256:...'"
                )
            algorithm, digest = self.checksum.split(":", 1)
            if not algorithm or not digest:
                raise ValueError("checksum must include a non-empty digest")
        return self


class DiagnosticRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: DiagnosticLevel
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class RunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_count: int = Field(default=0, ge=0)
    sample_count: int = Field(default=0, ge=0)
    outcomes: dict[str, float] = Field(default_factory=dict)
    comparisons: dict[str, float] = Field(default_factory=dict)


class ModelRunRequest(BaseModel):
    """Language-neutral contract for a lifecourse model execution request."""

    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["v1"] = CONTRACT_VERSION
    request_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    parameter_set: str = Field(default="australia", min_length=1)
    engine: EngineMetadata
    run_mode: RunMode
    population_size: int = Field(gt=0)
    time_horizon_years: int = Field(gt=0)
    seed_policy: SeedPolicy
    scenarios: list[ScenarioSelection] = Field(default_factory=list)
    parameter_overrides: list[ParameterOverride] = Field(default_factory=list)
    analysis_options: AnalysisOptions = Field(default_factory=AnalysisOptions)


class ModelRunResponse(BaseModel):
    """Language-neutral contract for a lifecourse model execution response."""

    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["v1"] = CONTRACT_VERSION
    request_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    status: Literal["success", "partial", "failed"]
    engine: EngineMetadata
    summary: RunSummary = Field(default_factory=RunSummary)
    artifacts: list[ArtifactReference] = Field(default_factory=list)
    diagnostics: list[DiagnosticRecord] = Field(default_factory=list)
    heoml_profile_version: str | None = None
    heoml_manifest_id: str | None = None


SCHEMA_EXPORTS: dict[str, type[BaseModel]] = {
    "model-run-request": ModelRunRequest,
    "model-run-response": ModelRunResponse,
}


def _stable_fraction(*parts: str) -> float:
    payload = "\u241f".join(parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


def run_model_request(request: ModelRunRequest) -> ModelRunResponse:
    """Run the reference contract surface for a validated model request."""

    scenarios = request.scenarios or [
        ScenarioSelection(scenario_id="default", overrides=[])
    ]

    scenario_results: list[tuple[str, float, float, int]] = []
    request_blob = json.dumps(
        request.model_dump(mode="json", exclude_none=True),
        sort_keys=True,
        separators=(",", ":"),
    )
    for scenario_index, scenario in enumerate(scenarios):
        scenario_blob = json.dumps(
            scenario.model_dump(mode="json", exclude_none=True),
            sort_keys=True,
            separators=(",", ":"),
        )
        scenario_costs: list[float] = []
        scenario_qalys: list[float] = []
        for replicate_index in range(request.seed_policy.replicate_count):
            fraction = _stable_fraction(
                request_blob,
                scenario_blob,
                str(scenario_index),
                str(replicate_index),
            )
            incremental_cost = (
                request.population_size * request.time_horizon_years * 1000.0
                + scenario_index * 713.0
                + replicate_index * 137.0
                + fraction * 25000.0
            )
            incremental_qaly = (
                request.time_horizon_years * 0.5
                + scenario_index * 0.05
                + replicate_index * 0.01
                + fraction * 2.0
            )
            scenario_costs.append(float(incremental_cost))
            scenario_qalys.append(float(incremental_qaly))

        avg_cost = sum(scenario_costs) / len(scenario_costs)
        avg_qaly = sum(scenario_qalys) / len(scenario_qalys)
        scenario_results.append(
            (scenario.scenario_id, avg_cost, avg_qaly, len(scenario_costs))
        )

    if scenario_results:
        avg_cost = sum(item[1] for item in scenario_results) / len(scenario_results)
        avg_qaly = sum(item[2] for item in scenario_results) / len(scenario_results)
    else:
        avg_cost = 0.0
        avg_qaly = 0.0

    artifacts = [
        ArtifactReference(
            artifact_id=f"{scenario_id}-summary",
            kind=ArtifactKind.summary,
            media_type="application/json",
            path=f"results/{request.request_id}/{scenario_id}/summary.json",
            schema_ref="heoml.v0.1.summary_table",
            schema_version=SCHEMA_VERSION,
        )
        for scenario_id, _, _, _ in scenario_results
    ]
    diagnostics = [
        DiagnosticRecord(
            level=DiagnosticLevel.info,
            code="SCENARIO_RESULT",
            message=f"Scenario {scenario_id} completed.",
            details={
                "incremental_cost": cost,
                "incremental_qaly": qaly,
                "replicates": replicate_count,
            },
        )
        for scenario_id, cost, qaly, replicate_count in scenario_results
    ]

    return ModelRunResponse(
        request_id=request.request_id,
        run_id=f"{request.request_id}-run",
        status="success",
        engine=request.engine,
        summary=RunSummary(
            scenario_count=len(scenario_results),
            sample_count=request.seed_policy.replicate_count,
            outcomes={
                "incremental_cost": avg_cost,
                "incremental_qaly": avg_qaly,
            },
            comparisons={
                "icer": (avg_cost / avg_qaly) if avg_qaly != 0 else 0.0,
            },
        ),
        artifacts=artifacts,
        diagnostics=diagnostics,
    )


def load_request(path: Path) -> ModelRunRequest:
    return ModelRunRequest.model_validate_json(path.read_text(encoding="utf-8"))


def dump_response(response: ModelRunResponse) -> str:
    return response.model_dump_json(indent=2)


def validate_artifact_metadata(response: ModelRunResponse) -> ModelRunResponse:
    """Validate artifact references for portable interchange consistency."""

    return ModelRunResponse.model_validate(response.model_dump(mode="json"))


def generate_contract_schemas(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for name, model in SCHEMA_EXPORTS.items():
        schema_path = output_dir / f"{name}.schema.json"
        schema = model.model_json_schema(ref_template="#/$defs/{model}")
        schema_path.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written[name] = schema_path
    return written


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate lifecourse model contract schemas."
    )
    parser.add_argument(
        "--request",
        help="Path to a validated model run request JSON file.",
    )
    parser.add_argument(
        "--write-schemas",
        action="store_true",
        help="Write the versioned JSON Schema artifacts to disk.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for a model run response JSON file.",
    )
    parser.add_argument(
        "--schema-dir",
        default=str(DEFAULT_SCHEMA_DIR),
        help="Directory where the contract schema files live.",
    )
    args = parser.parse_args(argv)

    schema_dir = Path(args.schema_dir)
    if args.request:
        request = load_request(Path(args.request))
        response = run_model_request(request)
        payload = dump_response(response)
        if args.output:
            Path(args.output).write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.write_schemas:
        written = generate_contract_schemas(schema_dir)
        for name, path in written.items():
            print(f"wrote {name}: {path}")
        return 0

    for name, model in SCHEMA_EXPORTS.items():
        expected = schema_dir / f"{name}.schema.json"
        current = model.model_json_schema(ref_template="#/$defs/{model}")
        if not expected.exists():
            raise FileNotFoundError(expected)
        actual = load_schema(expected)
        if actual != current:
            raise AssertionError(f"schema mismatch for {name}: {expected}")
    print(f"Validated {len(SCHEMA_EXPORTS)} schema files in {schema_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
