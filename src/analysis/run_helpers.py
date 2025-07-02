import numpy as np
import pandas as pd
import dask.dataframe as dd
import dask.array as da
from dask.distributed import LocalCluster, Client, progress

from src.model.population_system import PopulationSystemDask
from src.model.parameters import POP_SIZE, YEARS, DISTRIBUTIONS, prepare_dask_params, sample_params_from_dist

def run_sim(sampled_params, pop_size=POP_SIZE, seed_idx=None):
    if seed_idx is not None:
        np.random.seed(42 + seed_idx)
    else:
        np.random.seed(42)

    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(pop_size, dask_params, 'retrospective')
    sim_p = PopulationSystemDask(pop_size, dask_params, 'prospective')

    annual_costs_r = []
    annual_qalys_r = []
    annual_costs_p = []
    annual_qalys_p = []

    for yr in YEARS:
        sim_r.step(yr)
        if sim_r.pop.npartitions > 0: # Check if population is not empty
            annual_costs_r.append(sim_r.pop['annual_cost'].sum())
            annual_qalys_r.append(sim_r.pop['annual_qaly'].sum())
        else:
            annual_costs_r.append(da.from_array(np.array(0.0)))
            annual_qalys_r.append(da.from_array(np.array(0.0)))

        sim_p.step(yr)
        if sim_p.pop.npartitions > 0: # Check if population is not empty
            annual_costs_p.append(sim_p.pop['annual_cost'].sum())
            annual_qalys_p.append(sim_p.pop['annual_qaly'].sum())
        else:
            annual_costs_p.append(da.from_array(np.array(0.0)))
            annual_qalys_p.append(da.from_array(np.array(0.0)))

    cum_r_c_dask = sum(annual_costs_r)
    cum_r_q_dask = sum(annual_qalys_r)
    cum_p_c_dask = sum(annual_costs_p)
    cum_p_q_dask = sum(annual_qalys_p)

    cum_r_c, cum_r_q, cum_p_c, cum_p_q = dd.compute(
        cum_r_c_dask,
        cum_r_q_dask,
        cum_p_c_dask,
        cum_p_q_dask
    )

    return (cum_p_c - cum_r_c, cum_p_q - cum_r_q)

def run_scenario(sampled_params, pop_size=POP_SIZE):
    dask_params = prepare_dask_params(sampled_params)

    sim_r = PopulationSystemDask(pop_size, dask_params, 'retrospective')
    sim_p = PopulationSystemDask(pop_size, dask_params, 'prospective')

    annual_data_r_dask_list = []
    annual_data_p_dask_list = []
    ses_r_dask_list = []
    ses_p_dask_list = []

    for yr in YEARS:
        sim_r.step(yr)
        if sim_r.pop.npartitions > 0:
            annual_data_r_dask_list.append(sim_r.pop[['annual_cost', 'annual_qaly', 'cost_health', 'cost_edu', 'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity']].sum().to_frame(name=yr).T)
            ses_r_dask_list.append(sim_r.pop['ses'])
        else:
            empty_df = pd.DataFrame([[0.0]*9], columns=['annual_cost', 'annual_qaly', 'cost_health', 'cost_edu', 'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity'], index=[yr])
            annual_data_r_dask_list.append(dd.from_pandas(empty_df, npartitions=1))
            ses_r_dask_list.append(dd.from_pandas(pd.Series([0]*pop_size, dtype=int), npartitions=1))

        sim_p.step(yr)
        if sim_p.pop.npartitions > 0:
            annual_data_p_dask_list.append(sim_p.pop[['annual_cost', 'annual_qaly', 'cost_health', 'cost_edu', 'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity']].sum().to_frame(name=yr).T)
            ses_p_dask_list.append(sim_p.pop['ses'])
        else:
            empty_df = pd.DataFrame([[0.0]*9], columns=['annual_cost', 'annual_qaly', 'cost_health', 'cost_edu', 'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity'], index=[yr])
            annual_data_p_dask_list.append(dd.from_pandas(empty_df, npartitions=1))
            ses_p_dask_list.append(dd.from_pandas(pd.Series([0]*pop_size, dtype=int), npartitions=1))

    all_dask_objects = annual_data_r_dask_list + annual_data_p_dask_list + ses_r_dask_list + ses_p_dask_list
    computed_results = dd.compute(*all_dask_objects)

    num_years = len(YEARS)
    all_annual_r_computed = computed_results[0:num_years]
    all_annual_p_computed = computed_results[num_years:2*num_years]
    ses_r_computed_list = computed_results[2*num_years:3*num_years]
    ses_p_computed_list = computed_results[3*num_years:4*num_years]

    outputs = []
    final_totals = {}

    for arm_idx, (arm, annual_computed_list, ses_computed_list) in enumerate([
        ('retrospective', all_annual_r_computed, ses_r_computed_list),
        ('prospective', all_annual_p_computed, ses_p_computed_list)
    ]):
        cum_c = 0.0
        cum_q = 0.0
        for yr_idx, yr in enumerate(YEARS):
            annual_sums = annual_computed_list[yr_idx].iloc[0]
            ses_series = ses_computed_list[yr_idx]

            cum_c += annual_sums['annual_cost']
            cum_q += annual_sums['annual_qaly']

            ses_q_pct = {f'ses_q{i}_pct': (ses_series == i).mean() * 100 for i in range(5)}

            row_data = {
                'arm': arm, 'year': yr,
                'annual_cost': annual_sums['annual_cost'], 'cost_health': annual_sums['cost_health'], 'cost_edu': annual_sums['cost_edu'],
                'cost_respite': annual_sums['cost_respite'], 'cost_mobility': annual_sums['cost_mobility'], 'cost_welfare': annual_sums['cost_welfare'],
                'cost_emp': annual_sums['cost_emp'], 'cost_morbidity': annual_sums['cost_morbidity'],
                'costs': cum_c, 'qalys': cum_q,
                **ses_q_pct
            }
            outputs.append(row_data)

        final_totals[arm] = {'cost': cum_c, 'qaly': cum_q}

    d_cost = final_totals['prospective']['cost'] - final_totals['retrospective']['cost']
    d_qaly = final_totals['prospective']['qaly'] - final_totals['retrospective']['qaly']

    return (d_cost, d_qaly), pd.DataFrame(outputs)
