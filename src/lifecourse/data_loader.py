# pyright: reportUnknownMemberType=false
from collections.abc import Mapping
from importlib import import_module
from importlib.util import find_spec
from itertools import product
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
import yaml

from lifecourse.backend_evaluation import BackendUnavailableError
from lifecourse.config_validation import ScenarioFileConfig
from lifecourse.data_validation import validate_nz_population_distribution

ScenarioBackend = Literal["python", "polars"]


def _scenario_name_part(key: str, value: Any) -> str:
    safe_value = str(value).replace(".", "_")
    return f"{key}_{safe_value}"


def _expand_scenario_grid_python(
    grid: Mapping[str, list[Any]],
) -> dict[str, dict[str, Any]]:
    keys = list(grid.keys())
    value_lists = [grid[k] for k in keys]
    scenarios: dict[str, dict[str, Any]] = {}

    for combo in product(*value_lists):
        overrides = dict(zip(keys, combo, strict=True))
        name = "_".join(
            _scenario_name_part(key, value)
            for key, value in zip(keys, combo, strict=True)
        )
        scenarios[name] = overrides

    return scenarios


def _expand_scenario_grid_polars(
    grid: Mapping[str, list[Any]],
) -> dict[str, dict[str, Any]]:
    if find_spec("polars") is None:
        raise BackendUnavailableError(
            "Polars backend requested but `polars` is not installed. "
            "Install the optional `tabular` backend extra before using "
            "scenario_backend='polars'."
        )

    keys = list(grid.keys())
    rows: list[dict[str, Any]] = [
        dict(zip(keys, combo, strict=True))
        for combo in product(*(grid[key] for key in keys))
    ]
    pl = cast(Any, import_module("polars"))
    grid_frame = pl.DataFrame(rows)

    scenarios: dict[str, dict[str, Any]] = {}
    for row in grid_frame.iter_rows(named=True):
        overrides = dict(row)
        name = "_".join(_scenario_name_part(key, overrides[key]) for key in keys)
        scenarios[name] = overrides

    return scenarios


def _expand_scenario_grid(
    grid: Mapping[str, list[Any]], backend: ScenarioBackend
) -> dict[str, dict[str, Any]]:
    if backend == "python":
        return _expand_scenario_grid_python(grid)
    if backend == "polars":
        return _expand_scenario_grid_polars(grid)
    raise ValueError(f"Unsupported scenario backend: {backend}")


def load_scenarios_from_yaml(
    file_path: str,
    *,
    scenario_backend: ScenarioBackend = "python",
) -> dict[str, dict[str, Any]]:
    """Load scenarios and expand any scenario grid definitions and dynamic scenarios."""
    with open(file_path) as f:
        raw_config = cast(dict[str, Any], yaml.safe_load(f) or {})

    config = ScenarioFileConfig.model_validate(raw_config)

    scenarios: dict[str, dict[str, Any]] = {
        name: dict(overrides) for name, overrides in config.scenarios.items()
    }

    # Handle legacy scenario_grid
    grid = config.scenario_grid
    if grid:
        scenarios.update(_expand_scenario_grid(grid, scenario_backend))

    # Handle dynamic scenario generation
    dynamic_config = config.dynamic_scenarios
    if dynamic_config:
        try:
            from lifecourse.analysis.scenario_generator import get_scenario_manager

            manager = get_scenario_manager()
            dynamic_scenarios = manager.generate_scenarios(dynamic_config)
            scenarios.update(dynamic_scenarios)
        except ImportError:
            # Fallback if scenario generator is not available
            pass

    return scenarios


def apply_scenario_overrides(
    base_params: Mapping[str, Any], overrides: Mapping[str, Any]
) -> dict[str, Any]:
    """Apply scenario overrides to a base parameter dictionary."""
    updated = dict(base_params)
    for key, value in overrides.items():
        if value is None:
            continue
        if (
            isinstance(value, int | float)
            and key in base_params
            and isinstance(base_params[key], int | float)
        ):
            if abs(value) <= 0.5:
                updated[key] = base_params[key] + value
            else:
                updated[key] = value
        else:
            updated[key] = value

    if "severity_mild_prop" in updated:
        updated["severity_severe_prop"] = 1.0 - updated["severity_mild_prop"]

    return updated


PopulationBackend = Literal["pandas", "polars"]
LifeTableBackend = Literal["pandas", "polars"]


def _default_nz_population_url() -> str:
    return (
        "https://www.stats.govt.nz/assets/Uploads/Population-estimates-at-"
        "year-end-March-2024/Download-data/population-estimates-at-year-end-"
        "march-2024-csv.csv"
    )


def _default_nz_life_table_url() -> str:
    return (
        "https://www.stats.govt.nz/assets/Uploads/Life-tables-Year-ended-"
        "December-2020/Life-tables-year-ended-December-2020.csv"
    )


def _normalize_nz_population_distribution(pop: pd.DataFrame) -> pd.DataFrame:
    if "Geography" in pop.columns:
        pop = cast(pd.DataFrame, pop.loc[pop["Geography"] == "New Zealand"])
    renamed = cast(
        pd.DataFrame,
        pop.rename(columns={"Age": "age", "Sex": "sex", "Population": "count"}),
    )
    ages = renamed["age"].astype(str).str.extract(r"(\d+)", expand=False).astype(int)
    normalized = cast(
        pd.DataFrame,
        renamed.assign(age=ages).loc[:, ["age", "sex", "count"]],
    )
    return validate_nz_population_distribution(normalized)


def _load_nz_population_distribution_pandas(url: str) -> pd.DataFrame:
    return _normalize_nz_population_distribution(pd.read_csv(url))


def _load_nz_population_distribution_polars(url: str) -> pd.DataFrame:
    if find_spec("polars") is None:
        raise BackendUnavailableError(
            "Polars backend requested but `polars` is not installed. "
            "Install the optional `tabular` backend extra before using "
            "backend='polars'."
        )

    pl = cast(Any, import_module("polars"))
    pop = pl.read_csv(url)
    if "Geography" in pop.columns:
        pop = pop.filter(pl.col("Geography") == "New Zealand")

    normalized = cast(
        pd.DataFrame,
        pop.rename({"Age": "age", "Sex": "sex", "Population": "count"})
        .with_columns(pl.col("age").cast(pl.Utf8).str.extract(r"(\d+)").cast(pl.Int64))
        .select(["age", "sex", "count"])
        .to_pandas(),
    )
    return validate_nz_population_distribution(normalized)


def load_nz_population_distribution(
    url: str | None = None,
    *,
    backend: PopulationBackend = "pandas",
) -> pd.DataFrame:  # For New Zealand data
    """Load NZ population distribution by age and sex from Stats NZ public CSV."""
    if url is None:
        url = _default_nz_population_url()

    if backend == "pandas":
        return _load_nz_population_distribution_pandas(url)
    if backend == "polars":
        return _load_nz_population_distribution_polars(url)

    raise ValueError(f"Unsupported population backend: {backend}")


def _normalize_nz_life_table_hazards(life_table: pd.DataFrame) -> dict[str, np.ndarray]:
    normalized = cast(
        pd.DataFrame,
        life_table.rename(columns={"Sex": "sex", "Age": "age", "nMx": "hazard"}),
    )
    hazards: dict[str, np.ndarray] = {}
    for sex in normalized["sex"].dropna().unique():
        group = cast(pd.DataFrame, normalized.loc[normalized["sex"] == sex])
        hazards[str(sex)] = cast(
            np.ndarray,
            group.sort_values("age").loc[:, "hazard"].to_numpy(),
        )
    return hazards


def _load_nz_life_table_hazards_pandas(url: str) -> dict[str, np.ndarray]:
    return _normalize_nz_life_table_hazards(pd.read_csv(url))


def _load_nz_life_table_hazards_polars(url: str) -> dict[str, np.ndarray]:
    if find_spec("polars") is None:
        raise BackendUnavailableError(
            "Polars backend requested but `polars` is not installed. "
            "Install the optional `tabular` backend extra before using "
            "backend='polars'."
        )

    pl = cast(Any, import_module("polars"))
    normalized = (
        pl.read_csv(url)
        .rename({"Sex": "sex", "Age": "age", "nMx": "hazard"})
        .select(["sex", "age", "hazard"])
        .to_pandas()
    )
    return _normalize_nz_life_table_hazards(normalized)


def load_nz_life_table_hazards(
    url: str | None = None,
    *,
    backend: LifeTableBackend = "pandas",
) -> dict[str, np.ndarray]:  # For New Zealand data
    """
    Load NZ life table hazards (central mortality rates) from Stats NZ CSV.
    Returns dict hazards[sex] = array of hazard per age index.
    """
    if url is None:
        url = _default_nz_life_table_url()

    if backend == "pandas":
        return _load_nz_life_table_hazards_pandas(url)
    if backend == "polars":
        return _load_nz_life_table_hazards_polars(url)

    raise ValueError(f"Unsupported life-table backend: {backend}")
