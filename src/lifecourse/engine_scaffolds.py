from __future__ import annotations

import hashlib
import json
from typing import cast

from lifecourse.model_contract import (
    ArtifactKind,
    ArtifactReference,
    DiagnosticLevel,
    DiagnosticRecord,
    EngineCapabilities,
    EngineMetadata,
    ModelRunRequest,
    ModelRunResponse,
    RunSummary,
)

STATIC_ENGINE_ID = "static-decision"
STATIC_ENGINE_NAME = "Static Decision Model Scaffold"
STATIC_ENGINE_VERSION = "0.1.0"

STATIC_ENGINE_METADATA = EngineMetadata(
    engine_id=STATIC_ENGINE_ID,
    engine_name=STATIC_ENGINE_NAME,
    engine_version=STATIC_ENGINE_VERSION,
    capabilities=EngineCapabilities(
        static=True,
        discrete_time=False,
        continuous_time=False,
        markov=False,
        semi_markov=False,
        des=False,
        hybrid=False,
        supports_parallel_psa=False,
    ),
)


def _stable_fraction(*parts: str) -> float:
    payload = "\u241f".join(parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


def _scenario_payload(request: ModelRunRequest) -> list[dict[str, str | float | int]]:
    scenarios = request.scenarios or []
    if not scenarios:
        return [{"scenario_id": "default", "label": "", "index": 0}]
    return [
        {
            "scenario_id": scenario.scenario_id,
            "label": scenario.label or "",
            "index": index,
        }
        for index, scenario in enumerate(scenarios)
    ]


def run_static_decision_model(request: ModelRunRequest) -> ModelRunResponse:
    """Execute the experimental static decision-model scaffold."""

    request_blob = json.dumps(
        request.model_dump(mode="json", exclude_none=True),
        sort_keys=True,
        separators=(",", ":"),
    )
    scenario_payload = _scenario_payload(request)
    per_scenario_results: list[tuple[str, float, float, int]] = []

    for scenario in scenario_payload:
        scenario_blob = json.dumps(
            scenario,
            sort_keys=True,
            separators=(",", ":"),
        )
        scenario_costs: list[float] = []
        scenario_qalys: list[float] = []
        for replicate_index in range(request.seed_policy.replicate_count):
            fraction = _stable_fraction(
                request_blob,
                scenario_blob,
                str(replicate_index),
                STATIC_ENGINE_ID,
            )
            incremental_cost = (
                request.population_size * 250.0
                + float(scenario["index"]) * 53.0
                + replicate_index * 11.0
                + fraction * 1000.0
            )
            incremental_qaly = (
                request.time_horizon_years * 0.2
                + float(scenario["index"]) * 0.02
                + replicate_index * 0.005
                + fraction * 0.4
            )
            scenario_costs.append(float(incremental_cost))
            scenario_qalys.append(float(incremental_qaly))

        avg_cost = sum(scenario_costs) / len(scenario_costs)
        avg_qaly = sum(scenario_qalys) / len(scenario_qalys)
        per_scenario_results.append(
            (cast(str, scenario["scenario_id"]), avg_cost, avg_qaly, len(scenario_costs))
        )

    if per_scenario_results:
        avg_cost = sum(item[1] for item in per_scenario_results) / len(
            per_scenario_results
        )
        avg_qaly = sum(item[2] for item in per_scenario_results) / len(
            per_scenario_results
        )
    else:
        avg_cost = 0.0
        avg_qaly = 0.0

    artifacts = [
        ArtifactReference(
            artifact_id=f"{scenario_id}-summary",
            kind=ArtifactKind.summary,
            media_type="application/json",
            path=f"results/{request.request_id}/{scenario_id}/summary.json",
            schema_ref="heoml.v0.1.static_summary_table",
            schema_version="v1",
        )
        for scenario_id, _, _, _ in per_scenario_results
    ]
    diagnostics = [
        DiagnosticRecord(
            level=DiagnosticLevel.info,
            code="STATIC_SCENARIO_RESULT",
            message=f"Static scenario {scenario_id} completed.",
            details={
                "incremental_cost": cost,
                "incremental_qaly": qaly,
                "replicates": replicate_count,
            },
        )
        for scenario_id, cost, qaly, replicate_count in per_scenario_results
    ]

    return ModelRunResponse(
        request_id=request.request_id,
        run_id=f"{request.request_id}-static",
        status="success",
        engine=STATIC_ENGINE_METADATA,
        summary=RunSummary(
            scenario_count=len(per_scenario_results),
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
