import numpy as np
import pandas as pd
import pytest
from src.model.parameters import (
    get_gamma_params, get_beta_params, sample_params_from_dist, prepare_dask_params,
    DISTRIBUTIONS, FERT_AGE_SPEC, INFLATION_FACTOR, EMP_NP, MORB_KEYS, ABS_MORT, LIFE_EXP_NP
)

def test_get_gamma_params():
    # Test with valid mean and std_dev
    params = get_gamma_params(100, 20)
    assert params['dist'] == 'gamma'
    assert params['shape'] == pytest.approx(25.0)
    assert params['scale'] == pytest.approx(4.0)

    # Test with zero std_dev (should return fixed)
    params = get_gamma_params(50, 0)
    assert params['dist'] == 'fixed'
    assert params['value'] == 50

    # Test with zero mean (should return fixed)
    params = get_gamma_params(0, 10)
    assert params['dist'] == 'fixed'
    assert params['value'] == 0

def test_get_beta_params():
    # Test with valid mean and std_dev
    params = get_beta_params(0.5, 0.1)
    assert params['dist'] == 'beta'
    assert params['alpha'] == pytest.approx(12.0)
    assert params['beta'] == pytest.approx(12.0)

    # Test with mean outside [0, 1] (should return fixed)
    params = get_beta_params(1.5, 0.1)
    assert params['dist'] == 'fixed'
    assert params['value'] == 1.5

    # Test with std_dev = 0 (should return fixed)
    params = get_beta_params(0.7, 0)
    assert params['dist'] == 'fixed'
    assert params['value'] == 0.7

    # Test with variance too large (should return beta after adjustment)
    params = get_beta_params(0.5, 0.5) # variance = 0.25, mean*(1-mean) = 0.25
    assert params['dist'] == 'beta'

def test_sample_params_from_dist():
    # Test that all parameters are sampled and severity_severe_prop is calculated
    sampled = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    assert 'cost_inp_mild' in sampled
    assert 'u_base_severe' in sampled
    assert 'familial_prop' in sampled
    assert 'severity_mild_prop' in sampled
    assert 'severity_severe_prop' in sampled
    assert sampled['severity_mild_prop'] + sampled['severity_severe_prop'] == pytest.approx(1.0)

def test_prepare_dask_params():
    # Test that prepare_dask_params correctly structures the sampled parameters
    sampled = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    dask_params = prepare_dask_params(sampled)

    assert 'COST_INP_NP' in dask_params
    assert isinstance(dask_params['COST_INP_NP'], np.ndarray)
    assert dask_params['COST_INP_NP'][0] == sampled['cost_inp_mild']

    assert 'FERT_RATES_DF' in dask_params
    assert isinstance(dask_params['FERT_RATES_DF'], pd.DataFrame)
    assert 'rate' in dask_params['FERT_RATES_DF'].columns
    assert dask_params['FERT_RATES_DF']['rate'].iloc[0] == FERT_AGE_SPEC[(0, (15, 19))] * sampled['fertility_multiplier']

    assert 'MORB_KEYS' in dask_params
    assert dask_params['MORB_KEYS'] == MORB_KEYS
