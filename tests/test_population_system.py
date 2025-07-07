import numpy as np
import pandas as pd
import dask.dataframe as dd
import pytest
from src.model.population_system import PopulationSystemDask
from src.model.parameters import (
    START_YEAR, ABS_MORT, LIFE_EXP_NP, EMP_NP, MORB_KEYS, DISCOUNT, NDIS_COST,
    CARER_HOURS_NP, WAGE_HR, HOSP_COST, HOSP_RATE_NP, MENTAL_HEALTH_COST, INFORMAL_CARE_COST,
    DISTRIBUTIONS, prepare_dask_params, sample_params_from_dist
)

# Fixture for a basic PopulationSystemDask instance
@pytest.fixture
def basic_pop_system():
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    dask_params = prepare_dask_params(sampled_params)
    return PopulationSystemDask(pop_size=1, current_params=dask_params, arm='prospective')

@pytest.fixture
def retrospective_pop_system():
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    dask_params = prepare_dask_params(sampled_params)
    return PopulationSystemDask(pop_size=1, current_params=dask_params, arm='retrospective')

def test_population_system_init(basic_pop_system):
    assert basic_pop_system.arm == 'prospective'
    assert isinstance(basic_pop_system.pop, dd.DataFrame)
    assert len(basic_pop_system.pop.columns) > 0
    assert basic_pop_system.pop.npartitions > 0

def test_mortality(basic_pop_system):
    initial_pop_size = len(basic_pop_system.pop.compute())
    basic_pop_system._mortality()
    current_pop_size = len(basic_pop_system.pop.compute())
    assert current_pop_size <= initial_pop_size # Population should not increase
    # More specific tests would require mocking random or specific age/severity distributions

def test_fertility(basic_pop_system):
    initial_pop_size = len(basic_pop_system.pop.compute())
    basic_pop_system._fertility()
    current_pop_size = len(basic_pop_system.pop.compute())
    assert current_pop_size >= initial_pop_size # Population can increase due to births

def test_diagnosis_prospective(basic_pop_system):
    # Ensure that diagnosis happens for familial individuals in prospective arm
    initial_diagnosed_count = basic_pop_system.pop['diagnosed'].sum().compute()
    basic_pop_system._diagnosis()
    final_diagnosed_count = basic_pop_system.pop['diagnosed'].sum().compute()
    assert final_diagnosed_count >= initial_diagnosed_count
    # If there are familial individuals, some should become diagnosed
    familial_count = basic_pop_system.pop['familial'].sum().compute()
    if familial_count > 0:
        assert final_diagnosed_count > 0 or basic_pop_system.params['yield_wgs'] == 0 # If yield is 0, no diagnosis

def test_diagnosis_retrospective(retrospective_pop_system):
    # Ensure diagnosis does NOT happen in retrospective arm (it's seeded at init)
    initial_diagnosed_count = retrospective_pop_system.pop['diagnosed'].sum().compute()
    retrospective_pop_system._diagnosis()
    final_diagnosed_count = retrospective_pop_system.pop['diagnosed'].sum().compute()
    assert final_diagnosed_count == initial_diagnosed_count

def test_cost_qaly(basic_pop_system):
    # Test that cost and QALY columns are populated and non-zero (for a non-empty population)
    initial_pop_size = len(basic_pop_system.pop.compute())
    if initial_pop_size > 0:
        basic_pop_system._cost_qaly(START_YEAR)
        df_computed = basic_pop_system.pop.compute()
        assert np.all(df_computed['annual_cost'] >= 0) # Costs should be non-negative
        assert np.all(df_computed['annual_qaly'] >= 0) # QALYs should be non-negative
        assert df_computed['annual_cost'].sum() > 0 # Total cost should be > 0 for a living pop
        assert df_computed['annual_qaly'].sum() > 0 # Total QALYs should be > 0 for a living pop

def test_step(basic_pop_system):
    initial_pop_size = len(basic_pop_system.pop.compute())
    initial_age = basic_pop_system.pop['age'].max().compute()
    basic_pop_system.step(START_YEAR)
    current_pop_size = len(basic_pop_system.pop.compute())
    assert current_pop_size >= 0 # Population can shrink or grow
    assert 'age' in basic_pop_system.pop.columns
    if current_pop_size > 0:
        assert basic_pop_system.pop['age'].max().compute() == initial_age + 1 # Ages should have incremented
    assert 'annual_cost' in basic_pop_system.pop.columns
    assert 'annual_qaly' in basic_pop_system.pop.columns