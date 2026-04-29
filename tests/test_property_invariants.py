from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from lifecourse.backend_evaluation import (
    calculate_evpi_value,
    calculate_net_monetary_benefit,
)
from lifecourse.data_loader import apply_scenario_overrides, load_scenarios_from_yaml
from pydantic import ValidationError

finite_floats = st.floats(
    min_value=-1_000_000,
    max_value=1_000_000,
    allow_nan=False,
    allow_infinity=False,
    width=32,
)


@given(
    delta_qalys=st.lists(finite_floats, min_size=1, max_size=25),
    willingness_to_pay=st.floats(
        min_value=0,
        max_value=250_000,
        allow_nan=False,
        allow_infinity=False,
        width=32,
    ),
)
def test_net_monetary_benefit_matches_vector_formula(
    delta_qalys: list[float],
    willingness_to_pay: float,
) -> None:
    delta_costs = [value / 2 for value in delta_qalys]

    result = calculate_net_monetary_benefit(
        delta_qalys=delta_qalys,
        delta_costs=delta_costs,
        willingness_to_pay=willingness_to_pay,
    )

    expected = (np.asarray(delta_qalys) * willingness_to_pay) - np.asarray(delta_costs)
    np.testing.assert_allclose(result, expected)


@given(values=st.lists(finite_floats, min_size=1, max_size=25), shift=finite_floats)
def test_evpi_value_is_non_negative_and_shift_invariant(
    values: list[float], shift: float
) -> None:
    evpi = calculate_evpi_value(values)
    shifted_evpi = calculate_evpi_value([value + shift for value in values])

    assert evpi >= 0
    assert math.isclose(evpi, shifted_evpi, rel_tol=1e-6, abs_tol=1e-6)


@given(
    base_value=st.floats(
        min_value=-1_000,
        max_value=1_000,
        allow_nan=False,
        allow_infinity=False,
        width=32,
    ),
    relative_delta=st.floats(
        min_value=-0.5,
        max_value=0.5,
        allow_nan=False,
        allow_infinity=False,
        width=32,
    ),
)
def test_relative_scenario_overrides_are_additive(
    base_value: float, relative_delta: float
) -> None:
    result = apply_scenario_overrides({"x": base_value}, {"x": relative_delta})

    assert math.isclose(
        result["x"], base_value + relative_delta, rel_tol=1e-9, abs_tol=1e-9
    )


@given(
    absolute_value=st.one_of(
        st.floats(
            min_value=0.51,
            max_value=1_000,
            allow_nan=False,
            allow_infinity=False,
        ),
        st.floats(
            min_value=-1_000,
            max_value=-0.51,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
)
def test_large_numeric_scenario_overrides_replace_values(absolute_value: float) -> None:
    result = apply_scenario_overrides({"x": 10.0}, {"x": absolute_value})

    assert result["x"] == absolute_value


@given(mild_prop=st.floats(min_value=0, max_value=1, allow_nan=False))
def test_severity_scenario_override_preserves_complement(mild_prop: float) -> None:
    result = apply_scenario_overrides(
        {"severity_mild_prop": 0.7, "severity_severe_prop": 0.3},
        {"severity_mild_prop": mild_prop},
    )

    assert math.isclose(
        result["severity_mild_prop"] + result["severity_severe_prop"],
        1.0,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


def test_scenario_yaml_rejects_invalid_top_level_shapes(tmp_path) -> None:
    scenario_file = tmp_path / "bad_scenarios.yaml"
    scenario_file.write_text("scenarios:\n  - not-a-mapping\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        load_scenarios_from_yaml(str(scenario_file))
