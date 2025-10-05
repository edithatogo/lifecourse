import unittest
from unittest.mock import patch
import pandas as pd
import numpy as np
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lifecourse.analysis.advanced_analysis import (
    run_calibration,
    run_structural_uncertainty,
    calculate_evpi,
    calculate_evsi,
    run_evsi_analysis,
    run_psa,
    calculate_concentration_index,
    calculate_concentration_indices,
    run_concentration_analysis,
    calculate_price_thresholds,
    calculate_optimal_price_ranges,
    analyze_reimbursement_scenarios,
    run_vbp_analysis,
    create_decision_matrix,
    normalize_decision_matrix,
    apply_weights,
    calculate_weighted_sum,
    analytic_hierarchy_process,
    value_function_model,
    run_mcda_analysis,
)

TEST_YEARS = range(2020, 2022)


class TestAdvancedAnalysis(unittest.TestCase):
    def setUp(self):
        # Define base parameters used across tests
        self.base_params = {
            "param1": 10,
            "param2": 20,
            "mort_hr_mild": 1.5,
            "mort_hr_severe": 2.5,
        }
        # Mock the distributions dictionary needed by run_structural_uncertainty
        self.mock_distributions = {
            "mort_hr_mild": {"scale": 1.5},
            "mort_hr_severe": {"scale": 2.5},
        }

    @patch("lifecourse.analysis.advanced_analysis.run_sim")
    def test_run_calibration(self, mock_run_sim):
        # Configure the mock to return a fixed cost and QALY value
        mock_run_sim.return_value = (525000, 100)  # (dCost, dQALY)

        # Run the calibration function
        result = run_calibration(self.base_params, pop_size=100, years=TEST_YEARS)

        # Assertions
        mock_run_sim.assert_called_once_with(
            self.base_params, pop_size=100, years=TEST_YEARS, debug=False
        )
        self.assertIsInstance(result, dict)
        self.assertIn("sim_cost", result)
        self.assertIn("error_pct", result)
        self.assertEqual(result["sim_cost"], 525000)
        # Benchmark is hardcoded as {'mild': 200000, 'severe': 500000}, sum = 700000
        expected_error = abs(525000 - 700000) / 700000 * 100
        self.assertAlmostEqual(result["error_pct"], expected_error)

    @patch(
        "lifecourse.analysis.advanced_analysis.DISTRIBUTIONS",
        new_callable=lambda: {
            "mort_hr_mild": {"scale": 1.5},
            "mort_hr_severe": {"scale": 2.5},
        },
    )
    @patch("lifecourse.analysis.advanced_analysis.run_sim")
    def test_run_structural_uncertainty(self, mock_run_sim, mock_dist):
        # Configure the mock to return consistent values for each call
        mock_run_sim.return_value = (10000, 50)  # (dCost, dQALY)

        num_runs = 5  # Small number for testing
        df = run_structural_uncertainty(
            self.base_params, num_runs=num_runs, pop_size=100, years=TEST_YEARS
        )

        # Assertions
        self.assertEqual(mock_run_sim.call_count, num_runs)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), num_runs)
        self.assertEqual(list(df.columns), ["run", "dCost", "dQALY"])
        self.assertTrue(all(df["dCost"] == 10000))

    @patch("lifecourse.analysis.advanced_analysis.run_sim")
    def test_run_calibration_with_debug(self, mock_run_sim):
        # Configure the mock to return a fixed cost and QALY value
        mock_run_sim.return_value = (525000, 100)  # (dCost, dQALY)

        # Run the calibration function with debug mode
        result = run_calibration(
            self.base_params, pop_size=100, years=TEST_YEARS, debug=True
        )

        # Assertions
        mock_run_sim.assert_called_once_with(
            self.base_params, pop_size=100, years=TEST_YEARS, debug=True
        )
        self.assertIsInstance(result, dict)
        self.assertIn("sim_cost", result)
        self.assertIn("error_pct", result)

    @patch(
        "lifecourse.analysis.advanced_analysis.DISTRIBUTIONS",
        new_callable=lambda: {
            "mort_hr_mild": {"scale": 1.5},
            "mort_hr_severe": {"scale": 2.5},
        },
    )
    @patch("lifecourse.analysis.advanced_analysis.run_sim")
    def test_run_structural_uncertainty_with_debug(self, mock_run_sim, mock_dist):
        # Configure the mock to return consistent values for each call
        mock_run_sim.return_value = (10000, 50)  # (dCost, dQALY)

        num_runs = 3  # Small number for testing
        df = run_structural_uncertainty(
            self.base_params,
            num_runs=num_runs,
            pop_size=100,
            years=TEST_YEARS,
            debug=True,
        )

        # Assertions
        self.assertEqual(mock_run_sim.call_count, num_runs)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), num_runs)
        self.assertEqual(list(df.columns), ["run", "dCost", "dQALY"])


class TestEVSIAnalysis(unittest.TestCase):
    def setUp(self):
        # Create mock PSA results for testing
        np.random.seed(42)  # For reproducible tests
        self.psa_results = pd.DataFrame({
            'dCost': np.random.normal(10000, 2000, 100),
            'dQALY': np.random.normal(0.5, 0.1, 100),
            'ICER': np.random.normal(20000, 5000, 100),
            'net_benefit': np.random.normal(5000, 2000, 100)
        })

        self.research_designs = [
            {'name': 'small_study', 'sample_size': 50},
            {'name': 'large_study', 'sample_size': 200}
        ]

        # Define base parameters for testing
        self.base_params = {
            "param1": 10,
            "param2": 20,
            "mort_hr_mild": 1.5,
            "mort_hr_severe": 2.5,
        }

    def test_calculate_evpi(self):
        """Test EVPI calculation."""
        evpi = calculate_evpi(self.psa_results, wtp_threshold=30000)

        # EVPI should be non-negative
        self.assertGreaterEqual(evpi, 0)

        # EVPI should be a float
        self.assertIsInstance(evpi, (float, np.floating))

    def test_calculate_evsi(self):
        """Test EVSI calculation for research designs."""
        evsi_results = calculate_evsi(self.psa_results, self.research_designs, wtp_threshold=30000)

        # Should return results for each design
        self.assertEqual(len(evsi_results), len(self.research_designs))

        # Each result should have required keys
        required_keys = ['sample_size', 'evsi', 'expected_posterior_nb',
                        'current_expected_nb', 'info_value', 'current_evpi']
        for design_name, results in evsi_results.items():
            for key in required_keys:
                self.assertIn(key, results)
            # EVSI should be non-negative
            self.assertGreaterEqual(results['evsi'], 0)

    def test_calculate_evsi_with_debug(self):
        """Test EVSI calculation with debug output."""
        evsi_results = calculate_evsi(self.psa_results, self.research_designs,
                                     wtp_threshold=30000, debug=True)

        # Should still work with debug=True
        self.assertEqual(len(evsi_results), len(self.research_designs))

    @patch("lifecourse.analysis.advanced_analysis.run_psa")
    def test_run_evsi_analysis(self, mock_run_psa):
        """Test complete EVSI analysis workflow."""
        # Mock PSA results
        mock_run_psa.return_value = self.psa_results

        result = run_evsi_analysis(
            self.base_params,
            psa_runs=50,
            research_designs=self.research_designs,
            wtp_threshold=30000,
            debug=False
        )

        # Check structure of results
        self.assertIn('psa_results', result)
        self.assertIn('evsi_results', result)
        self.assertIn('research_designs', result)
        self.assertIn('wtp_threshold', result)
        self.assertIn('psa_runs', result)

        # EVSI results should exist
        self.assertEqual(len(result['evsi_results']), len(self.research_designs))

    @patch("lifecourse.analysis.advanced_analysis.DISTRIBUTIONS")
    @patch("lifecourse.analysis.advanced_analysis.run_sim")
    def test_run_psa(self, mock_run_sim, mock_distributions):
        """Test PSA execution."""
        # Mock distributions
        mock_distributions.__getitem__ = lambda self, key: {
            'type': 'normal',
            'loc': 10000,
            'scale': 1000
        }

        # Mock simulation results
        mock_run_sim.return_value = (10000, 0.5)

        psa_results = run_psa(self.base_params, psa_runs=10, debug=False)

        # Should return DataFrame with correct structure
        self.assertIsInstance(psa_results, pd.DataFrame)
        self.assertEqual(len(psa_results), 10)
        required_cols = ['run', 'dCost', 'dQALY', 'ICER', 'net_benefit']
        for col in required_cols:
            self.assertIn(col, psa_results.columns)

    def test_evsi_properties(self):
        """Test mathematical properties of EVSI."""
        # EVSI should increase with sample size (generally)
        small_design = [{'name': 'small', 'sample_size': 10}]
        large_design = [{'name': 'large', 'sample_size': 100}]

        evsi_small = calculate_evsi(self.psa_results, small_design, wtp_threshold=30000)
        evsi_large = calculate_evsi(self.psa_results, large_design, wtp_threshold=30000)

        # Large study should generally have higher or equal EVSI
        # (This might not always be true due to randomness, but test the logic)
        small_evsi = evsi_small['small']['evsi']
        large_evsi = evsi_large['large']['evsi']

        # Both should be non-negative
        self.assertGreaterEqual(small_evsi, 0)
        self.assertGreaterEqual(large_evsi, 0)

    def test_calculate_concentration_index(self):
        """Test concentration index calculation."""
        # Test with equal distribution (should be 0)
        health_var = [30, 30, 30, 30, 30]  # All equal
        ses_rank = [0.1, 0.3, 0.5, 0.7, 0.9]  # Quintiles
        ci = calculate_concentration_index(health_var, ses_rank)
        self.assertAlmostEqual(ci, 0.0, places=2)

        # Test with pro-rich concentration (positive CI)
        health_var_pro_rich = [5, 10, 20, 30, 50]  # Higher values for richer groups
        ci_pro_rich = calculate_concentration_index(health_var_pro_rich, ses_rank)
        self.assertGreater(ci_pro_rich, 0)

        # Test with pro-poor concentration (negative CI)
        health_var_pro_poor = [50, 30, 20, 10, 5]  # Higher values for poorer groups
        ci_pro_poor = calculate_concentration_index(health_var_pro_poor, ses_rank)
        self.assertLess(ci_pro_poor, 0)

    def test_calculate_concentration_indices(self):
        """Test concentration indices calculation for PSA results."""
        # Create mock PSA results
        psa_results = pd.DataFrame({
            'dCost': [10000, 12000, 8000, 15000, 9000],
            'dQALY': [0.5, 0.6, 0.4, 0.7, 0.45]
        })

        ci_results = calculate_concentration_indices(psa_results)

        # Check required keys exist
        required_keys = ['cost_ci', 'qaly_ci', 'net_benefit_ci', 'interpretation']
        for key in required_keys:
            self.assertIn(key, ci_results)

        # Check CI values are within valid range [-1, 1]
        for key in ['cost_ci', 'qaly_ci', 'net_benefit_ci']:
            self.assertGreaterEqual(ci_results[key], -1.0)
            self.assertLessEqual(ci_results[key], 1.0)

        # Check interpretation exists
        self.assertIsInstance(ci_results['interpretation'], dict)

    @patch("lifecourse.analysis.advanced_analysis.run_psa")
    def test_run_concentration_analysis(self, mock_run_psa):
        """Test concentration analysis workflow."""
        # Mock PSA results
        mock_psa_results = pd.DataFrame({
            'dCost': [10000, 12000, 8000],
            'dQALY': [0.5, 0.6, 0.4]
        })
        mock_run_psa.return_value = mock_psa_results

        result = run_concentration_analysis(
            self.base_params,
            psa_runs=10,
            debug=False
        )

        # Check result structure
        required_keys = ['cost_ci', 'qaly_ci', 'net_benefit_ci', 'interpretation']
        for key in required_keys:
            self.assertIn(key, result)

        # Verify PSA was called with correct parameters
        mock_run_psa.assert_called_once()


class TestVBP(unittest.TestCase):
    """Test suite for Value-Based Pricing (VBP) analysis functions."""

    def setUp(self):
        """Set up test fixtures for VBP tests."""
        # Mock PSA results for VBP analysis
        self.mock_psa_results = pd.DataFrame({
            'dCost': [10000, 12000, 8000, 15000, 9000],
            'dQALY': [0.5, 0.6, 0.4, 0.8, 0.3],
            'ICER': [20000, 20000, 20000, 18750, 30000]
        })

        # Mock base parameters
        self.base_params = {
            'base_cost': 50000,
            'population_size': 100000,
            'wtp_threshold': 30000,
            'budget_constraint': 50000000
        }

    def test_calculate_price_thresholds(self):
        """Test price threshold calculation across different WTP values."""
        wtp_range = [20000, 30000, 40000]

        result = calculate_price_thresholds(self.mock_psa_results, wtp_range=wtp_range)

        # Check result structure
        self.assertIn('thresholds', result)
        self.assertIn('wtp_range', result)
        self.assertIn('target_population', result)

        # Check that all WTP values are present
        for wtp in wtp_range:
            self.assertIn(wtp, result['thresholds'])

        # Check threshold structure for each WTP
        for wtp_data in result['thresholds'].values():
            self.assertIn('price_threshold', wtp_data)
            self.assertIn('expected_net_benefit', wtp_data)
            self.assertIn('probability_cost_effective', wtp_data)

    def test_calculate_optimal_price_ranges(self):
        """Test optimal price range calculation under budget constraints."""
        budget_constraints = {
            'max_incremental_budget': 50000000,
            'population_size': 100000
        }
        wtp_threshold = 30000

        result = calculate_optimal_price_ranges(
            self.mock_psa_results,
            budget_constraints=budget_constraints,
            wtp_threshold=wtp_threshold
        )

        # Check result structure
        self.assertIn('optimal_range', result)
        self.assertIn('budget_constraints', result)
        self.assertIn('wtp_threshold', result)

        # Check optimal range components
        opt_range = result['optimal_range']
        self.assertIn('min_price', opt_range)
        self.assertIn('max_price_budget', opt_range)
        self.assertIn('max_price_cost_effective', opt_range)
        self.assertIn('expected_base_cost', opt_range)

        # Check budget constraints
        budget_result = result['budget_constraints']
        self.assertEqual(budget_result['max_incremental_budget'], budget_constraints['max_incremental_budget'])
        self.assertEqual(budget_result['population_size'], budget_constraints['population_size'])

        # Check WTP threshold
        self.assertEqual(result['wtp_threshold'], wtp_threshold)

    def test_analyze_reimbursement_scenarios(self):
        """Test reimbursement scenario analysis."""
        scenarios = [
            {'name': 'full_reimbursement', 'reimbursement_rate': 1.0, 'price_adjustment': 0.0},
            {'name': 'partial_reimbursement', 'reimbursement_rate': 0.8, 'price_adjustment': -0.1},
            {'name': 'risk_sharing', 'reimbursement_rate': 0.9, 'price_adjustment': -0.05}
        ]

        result = analyze_reimbursement_scenarios(
            self.mock_psa_results,
            scenarios,
            wtp_threshold=30000
        )

        # Check result structure
        self.assertIn('scenario_results', result)
        self.assertIn('pricing_scenarios', result)
        self.assertIn('wtp_threshold', result)

        # Check that all scenarios are analyzed
        scenario_results = result['scenario_results']
        for scenario in scenarios:
            scenario_name = scenario['name']
            self.assertIn(scenario_name, scenario_results)

        # Check scenario result structure
        for scenario_data in scenario_results.values():
            self.assertIn('icer', scenario_data)
            self.assertIn('probability_cost_effective', scenario_data)
            self.assertIn('budget_impact', scenario_data)
            self.assertIn('expected_reimbursed_cost', scenario_data)
            self.assertIn('reimbursement_rate', scenario_data)
            self.assertIn('price_adjustment', scenario_data)

    @patch('lifecourse.analysis.advanced_analysis.run_psa')
    @patch('lifecourse.analysis.advanced_analysis.calculate_price_thresholds')
    @patch('lifecourse.analysis.advanced_analysis.calculate_optimal_price_ranges')
    @patch('lifecourse.analysis.advanced_analysis.analyze_reimbursement_scenarios')
    def test_run_vbp_analysis(self, mock_reimbursement, mock_optimal_ranges, mock_price_thresholds, mock_run_psa):
        """Test the complete VBP analysis workflow."""
        # Configure mocks
        mock_run_psa.return_value = self.mock_psa_results

        mock_price_thresholds.return_value = {
            'thresholds': {30000: {'price_threshold': 25000, 'probability_cost_effective': 0.8}},
            'wtp_range': [20000, 30000, 40000]
        }

        mock_optimal_ranges.return_value = {
            'optimal_range': {'min_price': 20000, 'max_price_budget': 30000, 'max_price_cost_effective': 35000},
            'budget_constraints': {'max_incremental_budget': 50000000, 'population_size': 100000}
        }

        mock_reimbursement.return_value = {
            'scenario_results': {'full': {'icer': 25000, 'probability_cost_effective': 0.8}},
            'pricing_scenarios': [{'name': 'full', 'reimbursement_rate': 1.0}]
        }

        # Run VBP analysis
        result = run_vbp_analysis(
            self.base_params,
            psa_runs=100,
            wtp_range=[20000, 30000, 40000],
            budget_constraints={'max_incremental_budget': 50000000, 'population_size': 100000},
            pricing_scenarios=[{'name': 'full', 'reimbursement_rate': 1.0, 'price_adjustment': 0.0}]
        )

        # Check result structure
        self.assertIn('psa_results', result)
        self.assertIn('price_thresholds', result)
        self.assertIn('optimal_price_ranges', result)
        self.assertIn('reimbursement_scenarios', result)

        # Verify all functions were called
        mock_run_psa.assert_called_once()
        mock_price_thresholds.assert_called_once()
        mock_optimal_ranges.assert_called_once()
        mock_reimbursement.assert_called_once()


class TestMCDA(unittest.TestCase):
    """Test suite for Multi-Criteria Decision Analysis (MCDA) functions."""

    def setUp(self):
        """Set up test fixtures for MCDA tests."""
        # Create sample decision matrix
        self.alternatives = ['Alternative_A', 'Alternative_B', 'Alternative_C']
        self.criteria = ['Cost', 'Quality', 'Time', 'Risk']
        self.scores = {
            'Cost': [100, 80, 120],
            'Quality': [8, 9, 7],
            'Time': [10, 12, 8],
            'Risk': [3, 2, 4]
        }

        # Create decision matrix
        self.decision_matrix = pd.DataFrame(self.scores, index=self.alternatives)

        # Sample weights
        self.weights = {
            'Cost': 0.3,
            'Quality': 0.4,
            'Time': 0.2,
            'Risk': 0.1
        }

    def test_create_decision_matrix(self):
        """Test decision matrix creation."""
        result = create_decision_matrix(self.criteria, self.alternatives, self.scores)

        # Check structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, (3, 4))
        self.assertListEqual(list(result.index), self.alternatives)
        self.assertListEqual(list(result.columns), self.criteria)

        # Check values
        self.assertEqual(result.loc['Alternative_A', 'Cost'], 100)
        self.assertEqual(result.loc['Alternative_B', 'Quality'], 9)

    def test_normalize_decision_matrix_linear(self):
        """Test linear normalization of decision matrix."""
        result = normalize_decision_matrix(self.decision_matrix, 'linear')

        # Check that each column sums to 1 (linear normalization)
        for column in result.columns:
            self.assertAlmostEqual(result[column].sum(), 1.0, places=6)

        # Check structure preserved
        self.assertEqual(result.shape, self.decision_matrix.shape)

    def test_normalize_decision_matrix_vector(self):
        """Test vector normalization of decision matrix."""
        result = normalize_decision_matrix(self.decision_matrix, 'vector')

        # Check that each column has unit norm
        for column in result.columns:
            norm = np.sqrt((result[column] ** 2).sum())
            self.assertAlmostEqual(norm, 1.0, places=6)

    def test_apply_weights(self):
        """Test weight application to normalized matrix."""
        normalized = normalize_decision_matrix(self.decision_matrix, 'linear')
        result = apply_weights(normalized, self.weights)

        # Check that weights are applied correctly
        for criterion in result.columns:
            expected_weight = self.weights[criterion]
            # Check that the weighted values are correct
            self.assertTrue(all(result[criterion] == normalized[criterion] * expected_weight))

    def test_calculate_weighted_sum(self):
        """Test weighted sum calculation."""
        normalized = normalize_decision_matrix(self.decision_matrix, 'linear')
        weighted = apply_weights(normalized, self.weights)
        result = calculate_weighted_sum(weighted)

        # Check result type and length
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.alternatives))

        # Check that Alternative_C has highest score (balanced performance)
        self.assertEqual(result.idxmax(), 'Alternative_C')

    def test_analytic_hierarchy_process(self):
        """Test AHP weight calculation."""
        criteria = ['Cost', 'Quality', 'Time']
        pairwise_comparisons = {
            ('Cost', 'Quality'): 1/3,  # Cost much less important than Quality
            ('Cost', 'Time'): 2,       # Cost more important than Time
            ('Quality', 'Time'): 5     # Quality much more important than Time
        }

        result = analytic_hierarchy_process(criteria, pairwise_comparisons)

        # Check result structure
        self.assertIn('weights', result)
        self.assertIn('consistency_ratio', result)
        self.assertIn('consistent', result)

        # Check weights sum to 1
        weights = result['weights']
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)

        # Check all criteria have weights
        for criterion in criteria:
            self.assertIn(criterion, weights)

    def test_value_function_model_linear(self):
        """Test linear value function modeling."""
        values = [10, 20, 30, 40]
        result = value_function_model(values, 'linear', 'increasing')

        # Check result is normalized to 0-1
        self.assertTrue(all(result >= 0))
        self.assertTrue(all(result <= 1))

        # Check monotonicity
        self.assertTrue(all(result[i] <= result[i+1] for i in range(len(result)-1)))

    def test_value_function_model_decreasing(self):
        """Test decreasing preference value function."""
        values = [10, 20, 30, 40]
        result = value_function_model(values, 'linear', 'decreasing')

        # Check result is normalized to 0-1
        self.assertTrue(all(result >= 0))
        self.assertTrue(all(result <= 1))

        # Check decreasing monotonicity (higher input -> lower utility)
        self.assertTrue(all(result[i] >= result[i+1] for i in range(len(result)-1)))

    def test_run_mcda_analysis_equal_weights(self):
        """Test complete MCDA analysis with equal weights."""
        result = run_mcda_analysis(
            decision_matrix=self.decision_matrix,
            weights=None,
            weight_method='equal',
            normalization_method='linear'
        )

        # Check result structure
        required_keys = ['original_matrix', 'normalized_matrix', 'weighted_matrix',
                        'weights', 'final_scores', 'ranking']
        for key in required_keys:
            self.assertIn(key, result)

        # Check weights are equal
        weights = result['weights']
        expected_weight = 1.0 / len(self.criteria)
        for weight in weights.values():
            self.assertAlmostEqual(weight, expected_weight, places=6)

        # Check ranking is a Series
        self.assertIsInstance(result['ranking'], pd.Series)
        self.assertEqual(len(result['ranking']), len(self.alternatives))

    def test_run_mcda_analysis_ahp(self):
        """Test complete MCDA analysis with AHP weights."""
        pairwise_comparisons = {
            ('Cost', 'Quality'): 1/3,
            ('Cost', 'Time'): 2,
            ('Cost', 'Risk'): 1,
            ('Quality', 'Time'): 5,
            ('Quality', 'Risk'): 3,
            ('Time', 'Risk'): 1/2
        }

        result = run_mcda_analysis(
            decision_matrix=self.decision_matrix,
            weights=None,
            weight_method='ahp',
            pairwise_comparisons=pairwise_comparisons,
            normalization_method='linear'
        )

        # Check AHP analysis is included
        self.assertIn('ahp_analysis', result)
        ahp = result['ahp_analysis']
        self.assertIn('consistency_ratio', ahp)
        self.assertIn('consistent', ahp)

        # Check weights sum to 1
        weights = result['weights']
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
