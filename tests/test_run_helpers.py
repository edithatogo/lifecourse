import numpy as np
import pandas as pd
import pytest
from src.analysis.run_helpers import run_sim, run_scenario
from src.model.parameters import DISTRIBUTIONS, sample_params_from_dist, YEARS

# Import the dask_client fixture
from tests.conftest import dask_client

# Class-based test structure to run the simulation once
@pytest.mark.usefixtures("dask_client")
class TestRunScenario:
    # Class attribute to store results
    results = None

    @classmethod
    def setup_class(cls):
        """Run the simulation once for the entire test class."""
        if cls.results is None:
            sampled_params = sample_params_from_dist(DISTRIBUTIONS, seed=42)
            # Use a minimal pop_size for quick test execution
            (dc, dq), df_output = run_scenario(sampled_params, pop_size=1)
            cls.results = {'dc': dc, 'dq': dq, 'df': df_output}

    def test_output_types(self):
        """Test the data types of the main outputs."""
        assert isinstance(self.results['dc'], (float, int))
        assert isinstance(self.results['dq'], (float, int))
        assert isinstance(self.results['df'], pd.DataFrame)

    def test_output_values(self):
        """Test that the simulation produces non-zero results."""
        assert self.results['dc'] != 0
        assert self.results['dq'] != 0

    def test_df_columns(self):
        """Check for the presence of all expected columns in the output DataFrame."""
        expected_cols = [
            'arm', 'year', 'annual_cost', 'annual_qaly', 'cost_health', 'cost_edu',
            'cost_respite', 'cost_mobility', 'cost_welfare', 'cost_emp', 'cost_morbidity',
            'costs', 'qalys', 'ses_q0_pct', 'ses_q1_pct', 'ses_q2_pct', 'ses_q3_pct', 'ses_q4_pct',
            'cost_ndis', 'cost_carer', 'cost_hospital', 'cost_common_other'
        ]
        for col in expected_cols:
            assert col in self.results['df'].columns

    def test_df_rows(self):
        """Ensure the DataFrame has the correct number of rows."""
        # Expect 2 arms * number of years rows
        assert len(self.results['df']) == 2 * len(YEARS)

    def test_arm_data_separation(self):
        """Verify that both arms have data and that cumulative values are increasing."""
        df = self.results['df']
        retrospective_data = df[df['arm'] == 'retrospective']
        prospective_data = df[df['arm'] == 'prospective']

        assert not retrospective_data.empty
        assert not prospective_data.empty
        assert len(retrospective_data) == len(YEARS)
        assert len(prospective_data) == len(YEARS)

        # Check that cumulative costs/qalys are increasing over time for each arm
        assert np.all(np.diff(retrospective_data['costs']) >= 0)
        assert np.all(np.diff(retrospective_data['qalys']) >= 0)
        assert np.all(np.diff(prospective_data['costs']) >= 0)
        assert np.all(np.diff(prospective_data['qalys']) >= 0)
