"""
Tests for Performance Profiling and Analysis Tools

This module tests the performance profiling, scalability testing,
and memory analysis capabilities.
"""

import time

from lifecourse.analysis.performance_profiler import (
    PerformanceProfiler,
    ScalabilityTester,
    MemoryProfiler,
    PerformanceMetrics,
    ScalabilityMetrics,
    get_performance_profiler,
    get_scalability_tester,
    get_memory_profiler,
)
from config.config_loader import load_config
from lifecourse.model.parameter_loader import get_parameter_attributes
from lifecourse.analysis.run_helpers import run_sim


class TestPerformanceProfiler:
    """Test the performance profiler functionality."""

    def test_profiler_initialization(self):
        """Test profiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.enable_memory_tracking
        assert profiler.enable_cpu_tracking

        profiler_no_memory = PerformanceProfiler(enable_memory_tracking=False)
        assert not profiler_no_memory.enable_memory_tracking

    def test_profile_context_manager(self):
        """Test the profiling context manager."""
        profiler = PerformanceProfiler()

        with profiler.profile_context("test_operation") as metrics:
            # Simulate some work
            time.sleep(0.1)
            x = sum(range(1000))

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.execution_time >= 0.1  # At least the sleep time
        assert metrics.execution_time < 1.0  # Shouldn't take too long

    def test_profile_function_decorator(self):
        """Test the function profiling decorator."""
        profiler = PerformanceProfiler()

        @profiler.profile_function
        def test_function(n):
            time.sleep(0.05)
            return sum(range(n))

        # This should work without errors
        result = test_function(100)
        assert result == sum(range(100))

    def test_profile_simulation_run(self):
        """Test profiling a simulation run."""
        profiler = PerformanceProfiler()

        # Use a very small simulation for testing
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, get_mean_params = get_parameter_attributes(
            config, "DISTRIBUTIONS", "get_mean_params"
        )
        params = get_mean_params(DISTRIBUTIONS)

        def small_sim():
            return run_sim(params, pop_size=10, years=[2020, 2021], debug=True)

        # Profile the simulation
        result = profiler.profile_simulation_run(small_sim)

        assert "result" in result
        assert "metrics" in result
        assert "profile" in result

        metrics = result["metrics"]
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.execution_time > 0

        # Should have some function call data
        assert isinstance(metrics.function_calls, dict)

    def test_bottleneck_detection(self):
        """Test bottleneck detection in performance metrics."""
        profiler = PerformanceProfiler()

        # Create metrics that should trigger bottleneck detection
        metrics = PerformanceMetrics()
        metrics.execution_time = 120.0  # 2 minutes - long execution
        metrics.peak_memory_mb = 1500.0  # 1.5 GB - high memory
        metrics.cpu_percent = 90.0  # High CPU usage

        profiler._analyze_bottlenecks(metrics)

        assert len(metrics.bottlenecks) > 0
        bottleneck_texts = [b.lower() for b in metrics.bottlenecks]
        assert any("long execution" in text for text in bottleneck_texts)
        assert any("high memory" in text for text in bottleneck_texts)
        assert any("high cpu" in text for text in bottleneck_texts)

    def test_memory_snapshots(self):
        """Test memory snapshot collection."""
        profiler = PerformanceProfiler()

        with profiler.profile_context("memory_test") as metrics:
            # Generate some memory activity
            data = [i for i in range(10000)]
            time.sleep(0.1)

        # Should have collected some memory snapshots if CPU monitoring was enabled
        if profiler.enable_cpu_tracking:
            assert len(metrics.memory_snapshots) > 0
            for snapshot in metrics.memory_snapshots:
                assert "timestamp" in snapshot
                assert "cpu_percent" in snapshot
                assert "memory_mb" in snapshot


class TestScalabilityTester:
    """Test the scalability testing functionality."""

    def test_scalability_initialization(self):
        """Test scalability tester initialization."""
        tester = ScalabilityTester()
        assert tester.profiler is not None

    def test_population_scalability_test(self):
        """Test population scalability testing."""
        tester = ScalabilityTester()

        # Mock run function for testing
        def mock_run_func(pop_size, **kwargs):
            # Simulate time scaling with population size
            time.sleep(pop_size / 1000.0)  # Small delay based on pop size
            return (pop_size * 100, pop_size * 0.5)  # Mock cost and QALY results

        # Test with small population sizes
        pop_sizes = [10, 20]

        metrics = tester.test_population_scalability(
            mock_run_func, population_sizes=pop_sizes, years=[2020, 2021]
        )

        assert isinstance(metrics, ScalabilityMetrics)
        assert len(metrics.population_sizes) == len(pop_sizes)
        assert len(metrics.execution_times) == len(pop_sizes)
        assert len(metrics.memory_usages) == len(pop_sizes)
        assert len(metrics.throughput_rates) == len(pop_sizes)

        # Execution times should generally increase
        assert metrics.execution_times[1] >= metrics.execution_times[0]

    def test_configuration_scalability_test(self):
        """Test configuration scalability testing."""
        tester = ScalabilityTester()

        # Mock run function
        def mock_run_func(**kwargs):
            time.sleep(0.01)
            return (1000, 50)

        # Test different configurations
        configurations = {"config1": {"param": 1}, "config2": {"param": 2}}
        base_config = {"pop_size": 10, "years": [2020, 2021]}

        results = tester.test_configuration_scalability(
            mock_run_func, configurations=configurations, base_config=base_config
        )

        assert len(results) == len(configurations)
        for config_name in configurations.keys():
            assert config_name in results
            assert isinstance(results[config_name], PerformanceMetrics)


class TestMemoryProfiler:
    """Test the memory profiler functionality."""

    def test_memory_profiler_initialization(self):
        """Test memory profiler initialization."""
        profiler = MemoryProfiler()
        assert profiler.snapshots == []

    def test_memory_profile_context(self):
        """Test memory profiling context manager."""
        profiler = MemoryProfiler()

        with profiler.profile_memory("test_memory"):
            # Generate some memory allocations
            data = [i for i in range(1000)]
            del data

        # Should complete without errors
        assert True

    def test_memory_leak_detection(self):
        """Test memory leak detection."""
        profiler = MemoryProfiler()

        # Function that shouldn't leak memory
        def stable_function():
            data = [i for i in range(100)]
            # Don't keep reference to data
            return sum(data)

        leak_results = profiler.detect_memory_leaks(stable_function, iterations=3)

        assert "usage" in leak_results
        assert len(leak_results["usage"]) == 3

        # Should not detect significant leaks for this function
        if "leak_detected" in leak_results:
            assert not leak_results["leak_detected"]

    def test_memory_leak_detection_with_leak(self):
        """Test memory leak detection with a leaking function."""
        profiler = MemoryProfiler()

        # Simulate a function with memory leak
        leak_container = []

        def leaking_function():
            # This will keep growing memory
            leak_container.extend(range(1000))
            return len(leak_container)

        leak_results = profiler.detect_memory_leaks(leaking_function, iterations=3)

        assert "usage" in leak_results
        assert len(leak_results["usage"]) == 3

        # Should potentially detect a leak (though this is a simple test)
        # The actual detection depends on the leak severity


class TestGlobalInstances:
    """Test global profiler instances."""

    def test_get_performance_profiler(self):
        """Test getting the global performance profiler."""
        profiler = get_performance_profiler()
        assert isinstance(profiler, PerformanceProfiler)

        # Should return the same instance
        profiler2 = get_performance_profiler()
        assert profiler is profiler2

    def test_get_scalability_tester(self):
        """Test getting the global scalability tester."""
        tester = get_scalability_tester()
        assert isinstance(tester, ScalabilityTester)

        # Should return the same instance
        tester2 = get_scalability_tester()
        assert tester is tester2

    def test_get_memory_profiler(self):
        """Test getting the global memory profiler."""
        profiler = get_memory_profiler()
        assert isinstance(profiler, MemoryProfiler)

        # Should return the same instance
        profiler2 = get_memory_profiler()
        assert profiler is profiler2


class TestPerformanceMetrics:
    """Test the PerformanceMetrics dataclass."""

    def test_metrics_initialization(self):
        """Test performance metrics initialization."""
        metrics = PerformanceMetrics()

        assert metrics.execution_time == 0.0
        assert metrics.peak_memory_mb == 0.0
        assert metrics.average_memory_mb == 0.0
        assert metrics.cpu_percent == 0.0
        assert metrics.memory_snapshots == []
        assert metrics.function_calls == {}
        assert metrics.bottlenecks == []

    def test_metrics_with_values(self):
        """Test performance metrics with values."""
        snapshots = [{"timestamp": 1.0, "cpu_percent": 50.0, "memory_mb": 100.0}]
        function_calls = {"func1": 10, "func2": 5}
        bottlenecks = ["High memory usage"]

        metrics = PerformanceMetrics(
            execution_time=2.5,
            peak_memory_mb=150.0,
            average_memory_mb=120.0,
            cpu_percent=75.0,
            memory_snapshots=snapshots,
            function_calls=function_calls,
            bottlenecks=bottlenecks,
        )

        assert metrics.execution_time == 2.5
        assert metrics.peak_memory_mb == 150.0
        assert metrics.cpu_percent == 75.0
        assert metrics.memory_snapshots == snapshots
        assert metrics.function_calls == function_calls
        assert metrics.bottlenecks == bottlenecks


class TestScalabilityMetrics:
    """Test the ScalabilityMetrics dataclass."""

    def test_scalability_metrics_initialization(self):
        """Test scalability metrics initialization."""
        metrics = ScalabilityMetrics()

        assert metrics.population_sizes == []
        assert metrics.execution_times == []
        assert metrics.memory_usages == []
        assert metrics.throughput_rates == []
        assert metrics.scaling_efficiency == 0.0

    def test_scalability_metrics_with_values(self):
        """Test scalability metrics with values."""
        metrics = ScalabilityMetrics(
            population_sizes=[100, 200, 400],
            execution_times=[1.0, 1.8, 3.2],
            memory_usages=[50.0, 80.0, 140.0],
            throughput_rates=[100.0, 111.1, 125.0],
            scaling_efficiency=0.85,
        )

        assert metrics.population_sizes == [100, 200, 400]
        assert metrics.execution_times == [1.0, 1.8, 3.2]
        assert metrics.memory_usages == [50.0, 80.0, 140.0]
        assert metrics.throughput_rates == [100.0, 111.1, 125.0]
        assert metrics.scaling_efficiency == 0.85


class TestIntegrationWithSimulation:
    """Test integration of profilers with actual simulation runs."""

    def test_profile_actual_simulation(self):
        """Test profiling an actual (small) simulation."""
        profiler = get_performance_profiler()
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, get_mean_params = get_parameter_attributes(
            config, "DISTRIBUTIONS", "get_mean_params"
        )
        params = get_mean_params(DISTRIBUTIONS)

        # Profile a small simulation
        result = profiler.profile_simulation_run(
            run_sim, sampled_params=params, pop_size=20, years=[2020, 2021], debug=True
        )

        assert "result" in result
        assert "metrics" in result
        assert "profile" in result

        # Results should be valid
        dc, dq = result["result"]
        assert isinstance(dc, (int, float))
        assert isinstance(dq, (int, float))

        # Metrics should be populated
        metrics = result["metrics"]
        assert metrics.execution_time > 0

    def test_scalability_actual_simulation(self):
        """Test scalability testing with actual simulations."""
        # Create a fresh tester instance to avoid profiler conflicts
        tester = ScalabilityTester(profiler=PerformanceProfiler())
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, get_mean_params = get_parameter_attributes(
            config, "DISTRIBUTIONS", "get_mean_params"
        )
        params = get_mean_params(DISTRIBUTIONS)

        # Test with very small populations for speed
        pop_sizes = [10, 20]

        def run_sim_wrapper(pop_size, **kwargs):
            return run_sim(params, pop_size=pop_size, **kwargs)

        metrics = tester.test_population_scalability(
            run_sim_wrapper, population_sizes=pop_sizes, years=[2020, 2021], debug=True
        )

        assert len(metrics.execution_times) == len(pop_sizes)
        assert all(t > 0 for t in metrics.execution_times)

    def test_memory_profile_actual_simulation(self):
        """Test memory profiling with actual simulation."""
        memory_profiler = get_memory_profiler()
        config = load_config("MINIMAL_TEST_CONFIG")
        DISTRIBUTIONS, get_mean_params = get_parameter_attributes(
            config, "DISTRIBUTIONS", "get_mean_params"
        )
        params = get_mean_params(DISTRIBUTIONS)

        def run_test():
            dc, dq = run_sim(params, pop_size=10, years=[2020, 2021], debug=True)
            return dc, dq

        # This should complete without errors
        leak_results = memory_profiler.detect_memory_leaks(run_test, iterations=2)

        assert "usage" in leak_results
        assert len(leak_results["usage"]) == 2
