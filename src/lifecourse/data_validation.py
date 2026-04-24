from __future__ import annotations

import pandas as pd
from pandera.pandas import Check, Column, DataFrameSchema

NZPopulationDistributionSchema = DataFrameSchema(
    {
        "age": Column(int, Check.ge(0), nullable=False),  # pyright: ignore[reportUnknownMemberType]
        "sex": Column(str, nullable=False),
        "count": Column(int, Check.ge(0), nullable=False),  # pyright: ignore[reportUnknownMemberType]
    },
    coerce=True,
)


def validate_nz_population_distribution(population: pd.DataFrame) -> pd.DataFrame:
    """Validate the New Zealand population distribution dataframe."""

    return NZPopulationDistributionSchema.validate(population)
