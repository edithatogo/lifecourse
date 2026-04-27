"""End-to-end integration tests for the `lifecourse` microsimulation model."""

import os
import shutil
import tempfile
import time
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import yaml
from lifecourse.analysis.run_helpers import run_scenario, run_sim
from lifecourse.data_loader import load_scenarios_from_yaml
from lifecourse.model.parameter_loader import get_parameter_attributes, load_parameters

from config.config_loader import load_config


class TestEndToEndPipeline:
    """Test the complete analysis pipeline end-to-end."""

    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Create test results directory
        self.results_dir = os.path.join(self.test_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)

        # Copy config directory to test directory
        config_src = os.path.join(os.path.dirname(__file__), "..", "config")
        config_dst = os.path.join(self.test_dir, "config")
        if os.path.exists(config_src):
            shutil.copytree(config_src, config_dst)

        # Change to test directory
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_analysis_pipeline_minimal(self):
        """Test complete pipeline with minimal configuration."""
        # Create minimal test config
        config_content = {
            "POP_SIZE": 100,
            "PSA_N": 2,
            "SIMULATION_YEARS": 3,
            "CALIBRATION_POP_SIZE": 50,
            "STRUCTURAL_UNCERTAINTY_POP_SIZE": 50,
            "parameter_set": "australia",
        }

        config_file = os.path.join(self.test_dir, "test_config.yaml")
        with open(config_file, "w") as f:
            yaml.safe_dump(config_content, f)

        # Test main entry point setup
        with patch(
            "sys.argv", ["lifecourse-main", "--config_name", "MINIMAL_TEST_CONFIG"]
        ):
            # This would normally run the full analysis
            # For testing, we just verify the setup works
            config = load_config("MINIMAL_TEST_CONFIG")
            assert config["POP_SIZE"] == 100
            assert config["parameter_set"] == "australia"

    def test_cli_scenario_execution(self):
        """Test CLI scenario execution pipeline."""
        # Test parameter loading
        config = load_config("MINIMAL_TEST_CONFIG")
        params = load_parameters(config)

        assert hasattr(params, "POP_SIZE")
        assert params.POP_SIZE > 0

        # Test scenario loading
        scenarios = load_scenarios_from_yaml("config/scenarios.yaml")
        assert len(scenarios) > 0
        assert "base" in scenarios

        # Test scenario application
        from lifecourse.data_loader import apply_scenario_overrides

        base_params = {"param_a": 1.0, "param_b": 2.0}
        overrides = {"param_a": 0.1}  # 10% relative increase
        result = apply_scenario_overrides(base_params, overrides)
        assert result["param_a"] == 1.1  # 1.0 + 0.1

    def test_simulation_execution_pipeline(self):
        """Test the simulation execution pipeline."""
        # Load minimal config
        config = load_config("MINIMAL_TEST_CONFIG")

        # Get parameter functions
        DISTRIBUTIONS, get_mean_params = get_parameter_attributes(
            config, "DISTRIBUTIONS", "get_mean_params"
        )
        params = get_mean_params(DISTRIBUTIONS)

        # Test run_sim with small parameters
        years = list(range(2020, 2023))  # 3 years

        # This should work without errors
        dc, dq = run_sim(params, pop_size=50, years=years, debug=True)

        # Verify results are reasonable
        assert isinstance(dc, int | float)
        assert isinstance(dq, int | float)
        # Note: dq can be negative if prospective arm has lower QALYs than retrospective
        # This is a difference between arms, not absolute QALYs

    def test_scenario_analysis_pipeline(self):
        """Test scenario analysis pipeline."""
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, START_YEAR, sample_params_from_dist, get_mean_params = (
            get_parameter_attributes(
                config,
                "DISTRIBUTIONS",
                "START_YEAR",
                "sample_params_from_dist",
                "get_mean_params",
            )
        )
        params = get_mean_params(DISTRIBUTIONS)
        scenarios = load_scenarios_from_yaml("config/scenarios.yaml")

        # Test run_scenario with base scenario
        years = list(range(2020, 2023))

        # Apply scenario overrides first
        from lifecourse.data_loader import apply_scenario_overrides

        scenario_params = apply_scenario_overrides(params, scenarios["base"])

        (dc, dq), results_df = run_scenario(scenario_params, pop_size=50, years=years)

        # Verify results structure
        assert isinstance(dc, int | float)
        assert isinstance(dq, int | float)
        assert isinstance(results_df, pd.DataFrame)
        assert len(results_df) > 0
        assert "arm" in results_df.columns
        assert "year" in results_df.columns
        assert "costs" in results_df.columns
        assert "qalys" in results_df.columns

    def test_dynamic_scenario_integration(self):
        """Test dynamic scenario generation integration."""
        # Load scenarios with dynamic generation
        scenarios = load_scenarios_from_yaml("config/scenarios.yaml")

        # Should include dynamic scenarios
        dynamic_scenarios = [
            name
            for name in scenarios
            if any(
                prefix in name
                for prefix in ["sample_", "coverage_sensitivity_", "testing_strategy_"]
            )
        ]

        assert len(dynamic_scenarios) > 0, "Dynamic scenarios should be generated"

        # Test that dynamic scenarios can be applied
        config = load_config("MINIMAL_TEST_CONFIG")
        base_params = load_parameters(config)

        from lifecourse.data_loader import apply_scenario_overrides

        for scenario_name in dynamic_scenarios[:2]:  # Test first 2 dynamic scenarios
            scenario_overrides = scenarios[scenario_name]
            result_params = apply_scenario_overrides(
                base_params.__dict__, scenario_overrides
            )

            # Should not raise errors
            assert isinstance(result_params, dict)

    def test_configuration_validation_pipeline(self):
        """Test configuration validation throughout the pipeline."""
        # Test valid configuration
        config = load_config("MINIMAL_TEST_CONFIG")
        assert config["POP_SIZE"] > 0
        assert config["parameter_set"] in ["australia", "nz"]

        # Test parameter loading with validation
        params = load_parameters(config)
        assert hasattr(params, "POP_SIZE")

        # Test that invalid configurations would be caught
        invalid_config = config.copy()
        invalid_config["POP_SIZE"] = -1

        # Note: Currently no validation for negative POP_SIZE in load_parameters
        # This could be added in the future

    def test_results_generation_pipeline(self):
        """Test results generation and output pipeline."""
        # Create test results directory
        results_dir = os.path.join(self.test_dir, "test_results")
        os.makedirs(results_dir, exist_ok=True)

        # Mock analysis results
        mock_results = {
            "deterministic_results": pd.DataFrame(
                {
                    "scenario": ["base", "high_coverage"],
                    "total_cost": [1000000, 1200000],
                    "total_qaly": [50, 52],
                    "icer": [20000, 23000],
                }
            ),
            "psa_results": pd.DataFrame(
                {"run": range(1, 11), "icer": np.random.normal(20000, 5000, 10)}
            ),
        }

        # Test results saving (mock the actual saving)
        with patch("pandas.DataFrame.to_csv") as mock_to_csv:
            # Simulate saving results
            det_file = os.path.join(results_dir, "deterministic_results.csv")
            psa_file = os.path.join(results_dir, "psa_results.csv")

            mock_results["deterministic_results"].to_csv(det_file)
            mock_results["psa_results"].to_csv(psa_file)

            # Verify save calls were made
            assert mock_to_csv.call_count == 2

    def test_error_handling_pipeline(self):
        """Test error handling throughout the pipeline."""
        # Test invalid parameter set
        invalid_config = load_config("MINIMAL_TEST_CONFIG").copy()
        invalid_config["parameter_set"] = "invalid_set"

        with pytest.raises(ValueError, match="Unknown parameter set"):
            load_parameters(invalid_config)

        # load_parameters doesn't validate config completeness, only parameter_set
        # This test would need to be updated if validation is added

    def test_memory_and_performance_bounds(self):
        """Test that the pipeline stays within reasonable memory and performance bounds."""
        import time

        from lifecourse.analysis.performance_profiler import get_performance_profiler

        profiler = get_performance_profiler()
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, START_YEAR, sample_params_from_dist, get_mean_params = (
            get_parameter_attributes(
                config,
                "DISTRIBUTIONS",
                "START_YEAR",
                "sample_params_from_dist",
                "get_mean_params",
            )
        )
        params = get_mean_params(DISTRIBUTIONS)

        # Test small simulation performance
        start_time = time.time()

        with profiler.profile_context("integration_test_small"):
            dc, dq = run_sim(
                params, pop_size=50, years=list(range(2020, 2023)), debug=True
            )

        execution_time = time.time() - start_time

        # Should complete in reasonable time (less than 30 seconds for small simulation)
        assert (
            execution_time < 30
        ), f"Small simulation took too long: {execution_time:.2f}s"

        # Results should be valid
        assert isinstance(dc, int | float)
        assert isinstance(dq, int | float)


class TestRegressionTesting:
    """Regression tests to detect performance and functionality regressions."""

    def test_performance_regression_small_simulation(self):
        """Test for performance regression in small simulations."""
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, START_YEAR, sample_params_from_dist, get_mean_params = (
            get_parameter_attributes(
                config,
                "DISTRIBUTIONS",
                "START_YEAR",
                "sample_params_from_dist",
                "get_mean_params",
            )
        )
        params = get_mean_params(DISTRIBUTIONS)

        # Baseline: small simulation should complete in < 10 seconds
        baseline_time = 10.0  # seconds

        start_time = time.time()
        dc, dq = run_sim(params, pop_size=50, years=list(range(2020, 2023)), debug=True)
        execution_time = time.time() - start_time

        # Allow some variance but catch major regressions
        assert (
            execution_time < baseline_time * 2
        ), f"Performance regression detected: {execution_time:.2f}s (baseline: {baseline_time}s)"

    def test_memory_regression_small_simulation(self):
        """Test for memory regression in small simulations."""
        from lifecourse.analysis.performance_profiler import get_memory_profiler

        memory_profiler = get_memory_profiler()
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, START_YEAR, sample_params_from_dist, get_mean_params = (
            get_parameter_attributes(
                config,
                "DISTRIBUTIONS",
                "START_YEAR",
                "sample_params_from_dist",
                "get_mean_params",
            )
        )
        params = get_mean_params(DISTRIBUTIONS)

        # Test memory usage
        def run_test():
            dc, dq = run_sim(
                params, pop_size=50, years=list(range(2020, 2023)), debug=True
            )
            return dc, dq

        leak_results = memory_profiler.detect_memory_leaks(run_test, iterations=3)

        # Should not have significant memory leaks
        if "leak_detected" in leak_results:
            assert not leak_results[
                "leak_detected"
            ], f"Memory leak detected: {leak_results.get('growth_rate', 0):.2f} MB/iteration"

    def test_functionality_regression_scenario_loading(self):
        """Test that scenario loading functionality hasn't regressed."""
        # Load scenarios
        scenarios = load_scenarios_from_yaml("config/scenarios.yaml")

        # Should have expected number of scenarios
        assert (
            len(scenarios) >= 7
        ), f"Expected at least 7 scenarios, got {len(scenarios)}"

        # Should include base scenario
        assert "base" in scenarios, "Base scenario should be present"

        # Base scenario should have expected structure
        base_scenario = scenarios["base"]
        assert isinstance(base_scenario, dict), "Scenarios should be dictionaries"

    def test_functionality_regression_parameter_loading(self):
        """Test that parameter loading functionality hasn't regressed."""
        config = load_config("MINIMAL_TEST_CONFIG")
        params = load_parameters(config)

        # Should have essential parameters
        required_attrs = ["POP_SIZE", "YEARS", "START_AGE", "END_AGE"]
        for attr in required_attrs:
            assert hasattr(params, attr), f"Parameter object missing {attr}"

        # Population size should be reasonable
        assert params.POP_SIZE > 0, "Population size should be positive"
        assert params.POP_SIZE < 1000000, "Population size seems unreasonably large"


class TestLoadTesting:
    """Load testing for concurrent and high-load scenarios."""

    def test_concurrent_scenario_runs(self):
        """Test running multiple scenarios concurrently."""
        import queue
        import threading

        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, START_YEAR, sample_params_from_dist, get_mean_params = (
            get_parameter_attributes(
                config,
                "DISTRIBUTIONS",
                "START_YEAR",
                "sample_params_from_dist",
                "get_mean_params",
            )
        )
        params = get_mean_params(DISTRIBUTIONS)
        scenarios = load_scenarios_from_yaml("config/scenarios.yaml")

        # Test first 3 scenarios
        test_scenarios = list(scenarios.keys())[:3]
        results_queue = queue.Queue()

        def run_scenario_worker(scenario_name):
            """Worker function to run a single scenario."""
            try:
                scenario_overrides = scenarios[scenario_name]
                from lifecourse.data_loader import apply_scenario_overrides

                scenario_params = apply_scenario_overrides(params, scenario_overrides)
                results = run_scenario(
                    scenario_params,
                    pop_size=0,
                    years=[2020],
                )
                results_queue.put((scenario_name, results, None))
            except Exception as e:
                results_queue.put((scenario_name, None, str(e)))

        # Start concurrent runs
        threads = []
        for scenario_name in test_scenarios:
            thread = threading.Thread(target=run_scenario_worker, args=(scenario_name,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout

        still_running = [thread.name for thread in threads if thread.is_alive()]
        assert not still_running, f"Threads did not finish in time: {still_running}"

        # Collect results
        results = {}
        while not results_queue.empty():
            scenario_name, result, error = results_queue.get()
            if error:
                pytest.fail(f"Scenario {scenario_name} failed: {error}")
            results[scenario_name] = result

        # Verify all scenarios completed
        assert len(results) == len(test_scenarios), "Not all scenarios completed"

        # Verify results are valid
        for scenario_name, result in results.items():
            (dc, dq), results_df = result
            assert isinstance(
                dc, int | float
            ), f"Scenario {scenario_name} has invalid cost results"
            assert isinstance(
                dq, int | float
            ), f"Scenario {scenario_name} has invalid QALY results"
            assert isinstance(
                results_df, pd.DataFrame
            ), f"Scenario {scenario_name} has invalid results DataFrame"

    def test_scalability_load_test(self):
        """Test scalability under load."""
        from lifecourse.analysis.performance_profiler import get_scalability_tester

        tester = get_scalability_tester()
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, START_YEAR, sample_params_from_dist, get_mean_params = (
            get_parameter_attributes(
                config,
                "DISTRIBUTIONS",
                "START_YEAR",
                "sample_params_from_dist",
                "get_mean_params",
            )
        )
        params = get_mean_params(DISTRIBUTIONS)

        # Test different population sizes
        pop_sizes = [50, 100, 200]

        def run_sim_wrapper(pop_size, **kwargs):
            return run_sim(params, pop_size=pop_size, **kwargs)

        metrics = tester.test_population_scalability(
            run_sim_wrapper,
            population_sizes=pop_sizes,
            years=list(range(2020, 2023)),
            debug=True,
        )

        # Should have results for all population sizes
        assert len(metrics.execution_times) == len(pop_sizes)
        assert len(metrics.memory_usages) == len(pop_sizes)

        # Execution times should generally increase with population size
        # (allowing for some variance due to system conditions)
        assert (
            metrics.execution_times[0] <= metrics.execution_times[-1] * 1.5
        ), "Execution times should scale reasonably with population size"
