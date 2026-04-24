from __future__ import annotations

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
