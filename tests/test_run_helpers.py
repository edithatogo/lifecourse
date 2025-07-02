import numpy as np
import pandas as pd
import pytest
from dask.distributed import LocalCluster, Client
from src.analysis.run_helpers import run_sim, run_scenario
from src.model.parameters import DISTRIBUTIONS, sample_params_from_dist, POP_SIZE, YEARS

# Fixture for Dask client (session-scoped to avoid re-creating for each test)
@pytest.fixture(scope='session')
def dask_client():
    cluster = LocalCluster(n_workers=1, threads_per_worker=1) # Use single worker for predictable testing
    client = Client(cluster)
    yield client
    client.close()
    cluster.close()

def test_run_sim_output_type(dask_client):
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    dc, dq = run_sim(sampled_params, pop_size=100) # Use small pop_size for quick test
    assert isinstance(dc, (float, int))
    assert isinstance(dq, (float, int))

def test_run_sim_values(dask_client):
    # Basic check that values are non-zero for a typical run
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    dc, dq = run_sim(sampled_params, pop_size=100)
    assert dc != 0 # Expect some cost difference
    assert dq != 0 # Expect some QALY difference

def test_run_scenario_output_type(dask_client):
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    (dc, dq), df_output = run_scenario(sampled_params, pop_size=100)
    assert isinstance(dc, (float, int))
    assert isinstance(dq, (float, int))
    assert isinstance(df_output, pd.DataFrame)

def test_run_scenario_df_columns_and_rows(dask_client):
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    (_, _), df_output = run_scenario(sampled_params, pop_size=100)

    expected_cols = [
        'arm', 'year', 'annual_cost', 'annual_qaly', 'cost_health', 'cost_edu',
        'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity',
        'costs', 'qalys', 'ses_q0_pct', 'ses_q1_pct', 'ses_q2_pct', 'ses_q3_pct', 'ses_q4_pct'
    ]
    # Add new cost columns from recent integration
    expected_cols.extend(['cost_ndis', 'cost_carer', 'cost_hospital', 'cost_common_other'])

    for col in expected_cols:
        assert col in df_output.columns

    # Expect 2 arms * number of years rows
    assert len(df_output) == 2 * len(YEARS)

def test_run_scenario_arm_data_separation(dask_client):
    sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
    (_, _), df_output = run_scenario(sampled_params, pop_size=100)

    retrospective_data = df_output[df_output['arm'] == 'retrospective']
    prospective_data = df_output[df_output['arm'] == 'prospective']

    assert not retrospective_data.empty
    assert not prospective_data.empty
    assert len(retrospective_data) == len(YEARS)
    assert len(prospective_data) == len(YEARS)

    # Check that cumulative costs/qalys are increasing over time for each arm
    assert np.all(np.diff(retrospective_data['costs']) >= 0)
    assert np.all(np.diff(retrospective_data['qalys']) >= 0)
    assert np.all(np.diff(prospective_data['costs']) >= 0)
    assert np.all(np.diff(prospective_data['qalys']) >= 0)
