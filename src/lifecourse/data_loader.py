import pandas as pd
import yaml


def load_scenarios_from_yaml(file_path):
    """Load scenarios and expand any scenario grid definitions and dynamic scenarios."""
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)

    scenarios = config.get("scenarios", {})

    # Handle legacy scenario_grid
    grid = config.get("scenario_grid")
    if grid:
        from itertools import product

        keys = list(grid.keys())
        value_lists = [grid[k] for k in keys]

        for combo in product(*value_lists):
            overrides = {}
            name_parts = []
            for k, v in zip(keys, combo):
                overrides[k] = v
                safe_v = str(v).replace(".", "_")
                name_parts.append(f"{k}_{safe_v}")
            scenarios["_".join(name_parts)] = overrides

    # Handle dynamic scenario generation
    dynamic_config = config.get("dynamic_scenarios")
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


def apply_scenario_overrides(base_params, overrides):
    """Apply scenario overrides to a base parameter dictionary."""
    updated = base_params.copy()
    for key, value in overrides.items():
        if value is None:
            continue
        if (
            isinstance(value, (int, float))
            and key in base_params
            and isinstance(base_params[key], (int, float))
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


def load_nz_population_distribution(url=None):  # For New Zealand data
    """
    Load NZ population distribution by age and sex from Stats NZ public CSV.
    Returns a DataFrame with columns ['age', 'sex', 'count'].
    """
    if url is None:
        url = (
            "https://www.stats.govt.nz/assets/Uploads/Population-estimates-at-"
            "year-end-March-2024/Download-data/population-estimates-at-year-end-"
            "march-2024-csv.csv"
        )
    pop = pd.read_csv(url)
    if "Geography" in pop.columns:
        pop = pop[pop["Geography"] == "New Zealand"]
    pop = pop.rename(columns={"Age": "age", "Sex": "sex", "Population": "count"})
    pop["age"] = pop["age"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    return pop[["age", "sex", "count"]]


def load_nz_life_table_hazards(url=None):  # For New Zealand data
    """
    Load NZ life table hazards (central mortality rates) from Stats NZ CSV.
    Returns dict hazards[sex] = array of hazard per age index.
    """
    if url is None:
        url = (
            "https://www.stats.govt.nz/assets/Uploads/Life-tables-Year-ended-"
            "December-2020/Life-tables-year-ended-December-2020.csv"
        )
    lt = pd.read_csv(url)
    lt = lt.rename(columns={"Sex": "sex", "Age": "age", "nMx": "hazard"})
    hazards = {
        sex: group.sort_values("age")["hazard"].values
        for sex, group in lt.groupby("sex")
    }
    return hazards
