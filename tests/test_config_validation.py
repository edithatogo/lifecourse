from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from lifecourse.config_validation import SimulationConfig
from pydantic import ValidationError

from config.config_loader import load_config


def test_simulation_config_validates_required_fields() -> None:
    config = SimulationConfig.model_validate(
        {
            "POP_SIZE": 100,
            "PSA_N": 0,
            "SIMULATION_YEARS": 5,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
            "parameter_set": "australia",
        }
    )

    assert config.POP_SIZE == 100
    assert config.SIMULATION_YEARS == 5


def test_simulation_config_rejects_negative_population() -> None:
    with pytest.raises(ValidationError):
        SimulationConfig.model_validate(
            {
                "POP_SIZE": -1,
                "PSA_N": 0,
                "SIMULATION_YEARS": 5,
                "CALIBRATION_POP_SIZE": 100,
                "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
                "parameter_set": "australia",
            }
        )


@given(
    pop_size=st.integers(min_value=0, max_value=100_000),
    sim_years=st.integers(min_value=1, max_value=120),
)
def test_simulation_config_accepts_valid_generated_inputs(
    pop_size: int, sim_years: int
) -> None:
    config = SimulationConfig.model_validate(
        {
            "POP_SIZE": pop_size,
            "PSA_N": 0,
            "SIMULATION_YEARS": sim_years,
            "CALIBRATION_POP_SIZE": 100,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 100,
            "parameter_set": "australia",
        }
    )

    assert pop_size == config.POP_SIZE
    assert sim_years == config.SIMULATION_YEARS


def test_load_config_uses_pydantic_validation() -> None:
    config = load_config(config_name="MINIMAL_TEST_CONFIG")

    assert config["POP_SIZE"] == 100
    assert config["SIMULATION_YEARS"] == 5
