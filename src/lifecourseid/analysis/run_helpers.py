import random  # Added for setting Python's global random seed
import numpy as np
import pandas as pd
import dask.dataframe as dd
import dask.array as da
import dask

from src.model.population_system import PopulationSystemDask
from src.model.parameters import POP_SIZE, prepare_dask_params


def run_sim(sampled_params, pop_size=POP_SIZE, seed_idx=None, years=None):
    actual_seed = 42
    if seed_idx is not None:
        actual_seed += seed_idx

    np.random.seed(actual_seed)
    random.seed(actual_seed)  # Also seed Python's built-in random module
    dask.config.set(
        scheduler="synchronous"
    )  # Enforce single-threaded execution for determinism

    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(pop_size, dask_params, "retrospective")
    sim_p = PopulationSystemDask(pop_size, dask_params, "prospective")

    annual_costs_r = []
    annual_qalys_r = []
    annual_costs_p = []
    annual_qalys_p = []

    individual_qalys_r = []  # New list to store individual QALYs
    individual_qalys_p = []  # New list to store individual QALYs

    for yr in years:
        sim_r.step(yr)
        if sim_r.pop.npartitions > 0:  # Check if population is not empty
            annual_costs_r.append(sim_r.pop["annual_cost"].sum())
            annual_qalys_r.append(sim_r.pop["annual_qaly"].sum())
            individual_qalys_r.append(
                sim_r.pop["annual_qaly"]
            )  # Store individual QALYs
        else:
            annual_costs_r.append(da.from_array(np.array(0.0)))
            annual_qalys_r.append(da.from_array(np.array(0.0)))
            individual_qalys_r.append(
                dd.from_pandas(pd.Series([], dtype=float), npartitions=1)
            )  # Empty Series for individual QALYs

        sim_p.step(yr)
        if sim_p.pop.npartitions > 0:  # Check if population is not empty
            annual_costs_p.append(sim_p.pop["annual_cost"].sum())
            annual_qalys_p.append(sim_p.pop["annual_qaly"].sum())
            individual_qalys_p.append(
                sim_p.pop["annual_qaly"]
            )  # Store individual QALYs
        else:
            annual_costs_p.append(da.from_array(np.array(0.0)))
            annual_qalys_p.append(da.from_array(np.array(0.0)))
            individual_qalys_p.append(
                dd.from_pandas(pd.Series([], dtype=float), npartitions=1)
            )  # Empty Series for individual QALYs

    cum_r_c_dask = sum(annual_costs_r)
    cum_r_q_dask = sum(annual_qalys_r)
    cum_p_c_dask = sum(annual_costs_p)
    cum_p_q_dask = sum(annual_qalys_p)

    # Compute all Dask objects at once
    computed_results = dd.compute(
        cum_r_c_dask,
        cum_r_q_dask,
        cum_p_c_dask,
        cum_p_q_dask,
        *individual_qalys_r,
        *individual_qalys_p,
    )

    # Extract computed results
    cum_r_c, cum_r_q, cum_p_c, cum_p_q = computed_results[0:4]
    computed_individual_qalys_r = computed_results[4 : 4 + len(years)]
    computed_individual_qalys_p = computed_results[4 + len(years) :]

    # Debugging individual QALYs
    print(
        "DEBUG: Individual QALYs for Retrospective Arm (first 5 individuals, first year):"
    )
    if len(computed_individual_qalys_r[0]) > 0:
        print(computed_individual_qalys_r[0].head(5).tolist())
    else:
        print("Empty population for retrospective arm in first year.")

    print(
        "DEBUG: Individual QALYs for Prospective Arm (first 5 individuals, first year):"
    )
    if len(computed_individual_qalys_p[0]) > 0:
        print(computed_individual_qalys_p[0].head(5).tolist())
    else:
        print("Empty population for prospective arm in first year.")

    return (cum_p_c - cum_r_c, cum_p_q - cum_r_q)


def run_scenario(sampled_params, pop_size=POP_SIZE, years=None):
    if pop_size == 0:
        # Return empty DataFrame and zero costs/qalys for empty population
        empty_df = pd.DataFrame(
            columns=[
                "arm",
                "year",
                "annual_cost",
                "cost_health",
                "cost_edu",
                "cost_respite",
                "cost_mobility",
                "cost_welfare",
                "cost_emp",
                "cost_morbidity",
                "costs",
                "qalys",
                "ses_q0_pct",
                "ses_q1_pct",
                "ses_q2_pct",
                "ses_q3_pct",
                "ses_q4_pct",
            ]
        )
        return (0.0, 0.0), empty_df

    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(pop_size, dask_params, "retrospective")
    sim_p = PopulationSystemDask(pop_size, dask_params, "prospective")

    annual_series_r_dask_list = []  # Changed name
    annual_series_p_dask_list = []  # Changed name
    ses_r_dask_list = []
    ses_p_dask_list = []

    cols_to_sum = [
        "annual_cost",
        "annual_qaly",
        "cost_health",
        "cost_edu",
        "cost_respite",
        "cost_mobility",
        "cost_welfare",
        "cost_emp",
        "cost_morbidity",
    ]

    for yr in years:
        sim_r.step(yr)
        if sim_r.pop.npartitions > 0:
            annual_series_r_dask_list.append(
                sim_r.pop[cols_to_sum].sum()
            )  # Store Dask Series
            ses_r_dask_list.append(sim_r.pop["ses"])
        else:
            annual_series_r_dask_list.append(
                dd.from_pandas(
                    pd.Series([0.0] * len(cols_to_sum), index=cols_to_sum, name=yr),
                    npartitions=1,
                )
            )
            ses_r_dask_list.append(
                dd.from_pandas(
                    pd.Series([0] * pop_size, dtype=int, name=f"ses_{yr}_r"),
                    npartitions=1,
                )
            )

        sim_p.step(yr)
        if sim_p.pop.npartitions > 0:
            annual_series_p_dask_list.append(
                sim_p.pop[cols_to_sum].sum()
            )  # Store Dask Series
            ses_p_dask_list.append(sim_p.pop["ses"])
        else:
            annual_series_p_dask_list.append(
                dd.from_pandas(
                    pd.Series([0.0] * len(cols_to_sum), index=cols_to_sum, name=yr),
                    npartitions=1,
                )
            )
            ses_p_dask_list.append(
                dd.from_pandas(
                    pd.Series([0] * pop_size, dtype=int, name=f"ses_{yr}_p"),
                    npartitions=1,
                )
            )

    all_dask_objects = (
        annual_series_r_dask_list
        + annual_series_p_dask_list
        + ses_r_dask_list
        + ses_p_dask_list
    )
    computed_results = dd.compute(*all_dask_objects)

    num_years = len(years)
    all_annual_r_computed_series = computed_results[
        0:num_years
    ]  # List of pandas Series
    all_annual_p_computed_series = computed_results[
        num_years : 2 * num_years
    ]  # List of pandas Series
    ses_r_computed_list = computed_results[2 * num_years : 3 * num_years]
    ses_p_computed_list = computed_results[3 * num_years : 4 * num_years]

    outputs = []
    final_totals = {}

    for arm_idx, (arm, annual_computed_series_list, ses_computed_list) in enumerate(
        [
            ("retrospective", all_annual_r_computed_series, ses_r_computed_list),
            ("prospective", all_annual_p_computed_series, ses_p_computed_list),
        ]
    ):
        cum_c = 0.0
        cum_q = 0.0
        for yr_idx, yr in enumerate(years):
            annual_sums_series = annual_computed_series_list[
                yr_idx
            ]  # This is a pandas Series
            ses_series = ses_computed_list[yr_idx]

            if isinstance(
                annual_sums_series, pd.DataFrame
            ):  # Should not happen with current dd.from_pandas for empty
                if not annual_sums_series.empty:
                    annual_sums_series = annual_sums_series.iloc[0]
                else:
                    annual_sums_series = pd.Series(
                        [0.0] * len(cols_to_sum), index=cols_to_sum
                    )

            if not isinstance(ses_series, pd.Series):
                ses_series = pd.Series(ses_series)

            cum_c += annual_sums_series.get("annual_cost", 0.0)
            cum_q += annual_sums_series.get("annual_qaly", 0.0)

            ses_q_pct = {
                f"ses_q{i}_pct": (ses_series == i).mean() * 100
                if not ses_series.empty
                else 0.0
                for i in range(5)
            }

            row_data = {
                "arm": arm,
                "year": yr,
                "annual_cost": annual_sums_series.get("annual_cost", 0.0),
                "cost_health": annual_sums_series.get("cost_health", 0.0),
                "cost_edu": annual_sums_series.get("cost_edu", 0.0),
                "cost_respite": annual_sums_series.get("cost_respite", 0.0),
                "cost_mobility": annual_sums_series.get("cost_mobility", 0.0),
                "cost_welfare": annual_sums_series.get("cost_welfare", 0.0),
                "cost_emp": annual_sums_series.get("cost_emp", 0.0),
                "cost_morbidity": annual_sums_series.get("cost_morbidity", 0.0),
                "costs": cum_c,
                "qalys": cum_q,
                **ses_q_pct,
            }
            outputs.append(row_data)

        final_totals[arm] = {"cost": cum_c, "qaly": cum_q}

    d_cost = final_totals["prospective"]["cost"] - final_totals["retrospective"]["cost"]
    d_qaly = final_totals["prospective"]["qaly"] - final_totals["retrospective"]["qaly"]

    return (d_cost, d_qaly), pd.DataFrame(outputs)
