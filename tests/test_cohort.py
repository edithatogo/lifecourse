import numpy as np
import pandas as pd
import dask.dataframe as dd
import pytest
from src.model.cohort import sample_ages, gen_population_dask, FERT_RATES_DF
from src.model.parameters import AGE_DIST, DISTRIBUTIONS, prepare_dask_params, EDUCATION_LEVELS, AGE_BANDS, INCOME_PARAMS

def test_sample_ages():
    n = 100
    ages = sample_ages(n, AGE_DIST)
    assert len(ages) == n
    assert np.all(ages >= 0)
    assert np.all(ages <= 99) # Max age in AGE_BREAKS is 90, plus 0-4 random int

def test_gen_population_dask():
    n = 100
    # Use a simplified set of parameters for testing gen_population_dask
    test_params = {
        'SEVERITY_DIST': np.array([0.7, 0.3]),
        'familial_prop': 0.2,
        'yield_wgs': 0.5,
        'EDUCATION_LEVELS': ['primary', 'secondary'],
        'AGE_BANDS': [(0, 10), (11, 20)],
        'INCOME_PARAMS': {
            'mild': {'primary': (10.0, 0.1), 'secondary': (10.5, 0.1)},
            'severe': {'primary': (9.0, 0.1), 'secondary': (9.5, 0.1)},
        }
    }
    pop_df = gen_population_dask(n, test_params, arm='prospective').compute()

    assert isinstance(pop_df, pd.DataFrame)
    assert len(pop_df) == n
    assert 'age' in pop_df.columns
    assert 'sex' in pop_df.columns
    assert 'severity' in pop_df.columns
    assert 'familial' in pop_df.columns
    assert 'diagnosed' in pop_df.columns
    assert 'education' in pop_df.columns
    assert 'age_band' in pop_df.columns
    assert 'income' in pop_df.columns

    # Test income imputation (basic check)
    assert np.all(pop_df['income'] > 0)

    # Test initial diagnosed status for prospective arm
    assert np.all(pop_df[pop_df['arm'] == 'prospective']['diagnosed'] == False)

    # Test initial diagnosed status for retrospective arm (should have some True values)
    pop_df_retrospective = gen_population_dask(n, test_params, arm='retrospective').compute()
    assert np.any(pop_df_retrospective['diagnosed'] == True)


def test_fert_rates_df_creation():
    assert isinstance(FERT_RATES_DF, pd.DataFrame)
    assert not FERT_RATES_DF.empty
    assert 'severity' in FERT_RATES_DF.columns
    assert 'age' in FERT_RATES_DF.columns
    assert 'rate' in FERT_RATES_DF.columns
