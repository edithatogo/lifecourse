#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lifecourseid.model.parameters import (
    DISTRIBUTIONS,
    get_mean_params,
    prepare_dask_params,
)
from lifecourseid.model.population_system import PopulationSystemDask


def debug_qaly_calculation():
    # Get mean parameters
    mean_params = get_mean_params(DISTRIBUTIONS)
    dask_params = prepare_dask_params(mean_params)

    print("Parameter values:")
    print(f"U_BASE_NP (mild, severe): {dask_params['U_BASE_NP']}")
    print(f"U_DIAG: {dask_params['U_DIAG']}")
    print(f"WGS_DIAG_QALY_ADJUSTMENT: {dask_params['WGS_DIAG_QALY_ADJUSTMENT']}")
    print(f"U_CARER: {dask_params['U_CARER']}")
    print(f"U_DECAY: {dask_params['U_DECAY']}")

    # Create small populations
    pop_size = 10
    sim_r = PopulationSystemDask(pop_size, dask_params, "retrospective")
    sim_p = PopulationSystemDask(pop_size, dask_params, "prospective")

    print("\nInitial populations:")
    print("Retrospective arm:")
    print(sim_r.pop.compute())
    print("\nProspective arm:")
    print(sim_p.pop.compute())

    # Run one step
    year = 2020
    sim_r.step(year)
    sim_p.step(year)

    print(f"\nAfter step {year}:")
    print("Retrospective arm:")
    retro_pop = sim_r.pop.compute()
    print(retro_pop)
    print(f"Total QALYs (retrospective): {retro_pop['annual_qaly'].sum()}")

    print("\nProspective arm:")
    pros_pop = sim_p.pop.compute()
    print(pros_pop)
    print(f"Total QALYs (prospective): {pros_pop['annual_qaly'].sum()}")

    # Check diagnosed individuals
    retro_diagnosed = retro_pop[retro_pop["diagnosed"]]
    pros_diagnosed = pros_pop[pros_pop["diagnosed"]]

    print("\nDiagnosed individuals:")
    print(f"Retrospective: {len(retro_diagnosed)}")
    print(f"Prospective: {len(pros_diagnosed)}")

    if len(retro_diagnosed) > 0:
        print(
            f"Retrospective diagnosed QALYs: {retro_diagnosed['annual_qaly'].tolist()}"
        )
    if len(pros_diagnosed) > 0:
        print(f"Prospective diagnosed QALYs: {pros_diagnosed['annual_qaly'].tolist()}")


if __name__ == "__main__":
    debug_qaly_calculation()
