import unittest
from unittest.mock import patch
import pandas as pd
from io import StringIO
import os
from src.data_loader import (
    load_nz_population_distribution,
    load_nz_life_table_hazards,
    apply_scenario_overrides,
    load_scenarios_from_yaml,
)
from src.model.parameters import get_mean_params, DISTRIBUTIONS

class TestDataLoader(unittest.TestCase):

    def test_load_nz_population_distribution(self):
        # Sample CSV data mimicking the real file structure
        csv_data = """Geography,Age,Sex,Population
New Zealand,"0 years",Male,100
New Zealand,"1 year",Male,110
New Zealand,"0 years",Female,90
New Zealand,"1 year",Female,105
Other,"0 years",Male,50
"""
        # Mock pd.read_csv to use our sample data
        with patch('pandas.read_csv', return_value=pd.read_csv(StringIO(csv_data))):
            pop_dist = load_nz_population_distribution(url="mock_url")
            
            # Assertions
            self.assertIsInstance(pop_dist, pd.DataFrame)
            self.assertEqual(list(pop_dist.columns), ['age', 'sex', 'count'])
            self.assertEqual(len(pop_dist), 4) # Should filter out 'Other'
            self.assertTrue(pd.api.types.is_integer_dtype(pop_dist['age']))
            self.assertEqual(pop_dist['count'].sum(), 405)

    def test_load_nz_life_table_hazards(self):
        # Sample CSV data mimicking the real file structure
        csv_data = """Sex,Age,nMx
Male,0,0.005
Male,1,0.001
Female,0,0.004
Female,1,0.0009
"""
        # Mock pd.read_csv to use our sample data
        with patch('pandas.read_csv', return_value=pd.read_csv(StringIO(csv_data))):
            hazards = load_nz_life_table_hazards(url="mock_url")

            # Assertions
            self.assertIsInstance(hazards, dict)
            self.assertIn('Male', hazards)
            self.assertIn('Female', hazards)
            self.assertEqual(len(hazards['Male']), 2)
            self.assertEqual(len(hazards['Female']), 2)
            self.assertAlmostEqual(hazards['Male'][0], 0.005)
            self.assertAlmostEqual(hazards['Female'][1], 0.0009)

    def test_apply_scenario_overrides(self):
        base = get_mean_params(DISTRIBUTIONS)
        overrides = {"familial_prop": 0.2, "severity_mild_prop": 0.6}
        updated = apply_scenario_overrides(base, overrides)

        expected_familial = base["familial_prop"] + 0.2
        self.assertAlmostEqual(updated["familial_prop"], expected_familial)
        self.assertAlmostEqual(updated["severity_mild_prop"], 0.6)
        self.assertAlmostEqual(updated["severity_severe_prop"], 0.4)

    def test_load_scenarios_with_grid(self):
        yaml_content = """
scenarios:
  base: {familial_prop: 0.15}
scenario_grid:
  familial_prop: [0.1, 0.2]
  yield_wgs: [0.5, 0.7]
        with open("/tmp/test_scenarios.yaml", "w") as f:
            f.write(yaml_content)

        scenarios = load_scenarios_from_yaml("/tmp/test_scenarios.yaml")
        os.remove("/tmp/test_scenarios.yaml")

        # base scenario + 4 generated combos
        self.assertEqual(len(scenarios), 5)
        self.assertIn("familial_prop_0_1_yield_wgs_0_5", scenarios)
        self.assertEqual(scenarios["familial_prop_0_1_yield_wgs_0_5"], {"familial_prop": 0.1, "yield_wgs": 0.5})

if __name__ == '__main__':
    unittest.main()
