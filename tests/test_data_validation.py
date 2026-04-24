from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st
from lifecourse.data_loader import load_nz_population_distribution
from lifecourse.data_validation import validate_nz_population_distribution
from pandera.errors import SchemaError


def test_nz_population_distribution_schema_accepts_valid_frame() -> None:
    frame = pd.DataFrame(
        {
            "age": [0, 5],
            "sex": ["Male", "Female"],
            "count": [100, 120],
        }
    )

    validated = validate_nz_population_distribution(frame)

    assert list(validated.columns) == ["age", "sex", "count"]
    assert validated.iloc[0]["age"] == 0


def test_nz_population_distribution_schema_rejects_invalid_frame() -> None:
    frame = pd.DataFrame(
        {
            "age": [-1],
            "sex": ["Male"],
            "count": [100],
        }
    )

    with pytest.raises(SchemaError):
        validate_nz_population_distribution(frame)


@given(
    ages=st.lists(st.integers(min_value=0, max_value=110), min_size=1, max_size=10),
    counts=st.lists(st.integers(min_value=0, max_value=1_000), min_size=1, max_size=10),
)
def test_nz_population_distribution_schema_accepts_generated_inputs(
    ages: list[int], counts: list[int]
) -> None:
    size = min(len(ages), len(counts))
    frame = pd.DataFrame(
        {
            "age": ages[:size],
            "sex": ["Male"] * size,
            "count": counts[:size],
        }
    )

    validated = validate_nz_population_distribution(frame)

    assert len(validated) == size
    assert validated["count"].ge(0).all()


def test_load_nz_population_distribution_validates_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "Geography": ["New Zealand"],
            "Age": ["0-4"],
            "Sex": ["Male"],
            "Population": [100],
        }
    )

    monkeypatch.setattr(pd, "read_csv", lambda *_args, **_kwargs: frame)

    validated = load_nz_population_distribution()

    assert list(validated.columns) == ["age", "sex", "count"]
    assert validated.iloc[0]["count"] == 100
