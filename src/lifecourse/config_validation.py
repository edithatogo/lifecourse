from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SimulationConfig(BaseModel):
    """Validated simulation configuration for the maintained workflow."""

    model_config = ConfigDict(extra="allow")

    POP_SIZE: int = Field(ge=0)
    PSA_N: int = Field(ge=0)
    SIMULATION_YEARS: int = Field(gt=0)
    CALIBRATION_POP_SIZE: int = Field(ge=0)
    STRUCTURAL_UNCERTAINTY_POP_SIZE: int = Field(ge=0)
    parameter_set: str = Field(min_length=1)


class ScenarioFileConfig(BaseModel):
    """Validated structure for scenario YAML files."""

    model_config = ConfigDict(extra="allow")

    scenarios: dict[str, dict[str, Any | None]] = Field(default_factory=dict)
    scenario_grid: dict[str, list[Any]] = Field(default_factory=dict)
    dynamic_scenarios: dict[str, Any] | None = None
