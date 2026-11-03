"""
Advanced Performance Profiling for LifeCourseID Microsimulation Model

This module provides comprehensive performance profiling, memory analysis,
and bottleneck detection for simulation runs and analysis pipelines.
"""

import cProfile
import gc
import io
import os
import pstats
import threading
import time
import tracemalloc
from collections import defaultdict
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

import numpy as np
import psutil


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""

    execution_time: float = 0.0
    peak_memory_mb: float = 0.0
    average_memory_mb: float = 0.0
    cpu_percent: float = 0.0
    memory_snapshots: list[dict[str, Any]] = field(default_factory=list)
    function_calls: dict[str, int] = field(default_factory=dict)
    bottlenecks: list[str] = field(default_factory=list)


@dataclass
class ScalabilityMetrics:
    """Container for scalability testing results."""

    population_sizes: list[int] = field(default_factory=list)
    execution_times: list[float] = field(default_factory=list)
    memory_usages: list[float] = field(default_factory=list)
    throughput_rates: list[float] = field(default_factory=list)
    scaling_efficiency: float = 0.0


class PerformanceProfiler:
    """Advanced performance profiler for simulation components."""

    def __init__(
        self, enable_memory_tracking: bool = True, enable_cpu_tracking: bool = True
    ):
        self.enable_memory_tracking = enable_memory_tracking
        self.enable_cpu_tracking = enable_cpu_tracking
        self.process = psutil.Process(os.getpid())
        self._tracemalloc_started = False

    @contextmanager
    def profile_context(self, name: str = "operation"):
        """Context manager for profiling code blocks."""
        metrics = PerformanceMetrics()
        start_time = time.time()

        # Start memory tracking
        if self.enable_memory_tracking:
            tracemalloc.start()
            self._tracemalloc_started = True
            initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        # Start CPU monitoring in background
        cpu_monitor = None
        if self.enable_cpu_tracking:
            cpu_monitor = threading.Thread(
                target=self._monitor_cpu_usage, args=(metrics,)
            )
            cpu_monitor.daemon = True
            cpu_monitor.start()

        try:
            yield metrics
        finally:
            # Stop timing
            metrics.execution_time = time.time() - start_time

            # Stop memory tracking
            if self.enable_memory_tracking and self._tracemalloc_started:
                _current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                self._tracemalloc_started = False

                metrics.peak_memory_mb = peak / 1024 / 1024
                final_memory = self.process.memory_info().rss / 1024 / 1024
                metrics.average_memory_mb = (initial_memory + final_memory) / 2

            # Wait for CPU monitoring to finish
            if cpu_monitor:
                cpu_monitor.join(timeout=1.0)

            # Analyze bottlenecks
            self._analyze_bottlenecks(metrics)

    def profile_function(self, func: Callable) -> Callable:
        """Decorator for profiling functions."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.profile_context(func.__name__) as metrics:
                result = func(*args, **kwargs)
                self._log_metrics(func.__name__, metrics)
                return result

        return wrapper

    def profile_simulation_run(
        self, run_func: Callable, *args, **kwargs
    ) -> dict[str, Any]:
        """Profile a complete simulation run."""
        # Check if profiling is already active
        import sys

        if sys.getprofile() is not None:
            # Profiling already active, just run the function without additional profiling
            with self.profile_context("simulation_run") as metrics:
                result = run_func(*args, **kwargs)
            return {"result": result, "metrics": metrics, "profile": None}

        profiler = cProfile.Profile()
        profiler.enable()

        with self.profile_context("simulation_run") as metrics:
            result = run_func(*args, **kwargs)

        profiler.disable()

        # Analyze profile data
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats(20)  # Top 20 functions
        profile_output = s.getvalue()

        # Extract function call statistics
        metrics.function_calls = self._extract_function_stats(profile_output)

        self._log_metrics("simulation_run", metrics)

        return {"result": result, "metrics": metrics, "profile": profile_output}

    def _monitor_cpu_usage(self, metrics: PerformanceMetrics, interval: float = 0.1):
        """Monitor CPU usage in background thread."""
        cpu_samples = []
        start_time = time.time()

        while time.time() - start_time < 300:  # Max 5 minutes
            try:
                cpu_percent = self.process.cpu_percent(interval=interval)
                memory_mb = self.process.memory_info().rss / 1024 / 1024

                metrics.memory_snapshots.append(
                    {
                        "timestamp": time.time() - start_time,
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_mb,
                    }
                )

                cpu_samples.append(cpu_percent)
                time.sleep(interval)

            except psutil.Error, OSError:
                break

        if cpu_samples:
            metrics.cpu_percent = np.mean(cpu_samples)

    def _analyze_bottlenecks(self, metrics: PerformanceMetrics):
        """Analyze performance data to identify bottlenecks."""
        bottlenecks = []

        # Memory bottleneck detection
        if metrics.peak_memory_mb > 1000:  # > 1GB
            bottlenecks.append(f"High memory usage: {metrics.peak_memory_mb:.1f} MB")

        # CPU bottleneck detection
        if metrics.cpu_percent > 80:
            bottlenecks.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        # Execution time analysis
        if metrics.execution_time > 60:  # > 1 minute
            bottlenecks.append(
                f"Long execution time: {metrics.execution_time:.1f} seconds"
            )

        # Memory growth analysis
        if metrics.memory_snapshots:
            memory_values = [snap["memory_mb"] for snap in metrics.memory_snapshots]
            if len(memory_values) > 1:
                memory_growth = (memory_values[-1] - memory_values[0]) / memory_values[
                    0
                ]
                if memory_growth > 0.5:  # > 50% growth
                    bottlenecks.append(
                        f"Significant memory growth: {memory_growth:.1%}"
                    )

        metrics.bottlenecks = bottlenecks

    def _extract_function_stats(self, profile_output: str) -> dict[str, int]:
        """Extract function call statistics from cProfile output."""
        stats = defaultdict(int)
        lines = profile_output.split("\n")

        for line in lines:
            if line.strip() and not line.startswith(" "):
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        calls = int(parts[0])
                        function_name = " ".join(parts[5:])
                        stats[function_name] = calls
                    except ValueError, IndexError:
                        continue

        return dict(stats)

    def _log_metrics(self, name: str, metrics: PerformanceMetrics):
        """Log performance metrics."""
        print(f"\n=== Performance Profile: {name} ===")
        print(f"Execution Time: {metrics.execution_time:.2f} seconds")
        print(f"Peak Memory: {metrics.peak_memory_mb:.1f} MB")
        print(f"Average Memory: {metrics.average_memory_mb:.1f} MB")
        print(f"CPU Usage: {metrics.cpu_percent:.1f}%")

        if metrics.bottlenecks:
            print("Bottlenecks detected:")
            for bottleneck in metrics.bottlenecks:
                print(f"  - {bottleneck}")

        if metrics.function_calls:
            print("Top function calls:")
            sorted_calls = sorted(
                metrics.function_calls.items(), key=lambda x: x[1], reverse=True
            )
            for func, calls in sorted_calls[:5]:
                print(f"  - {func}: {calls} calls")


class ScalabilityTester:
    """Test scalability across different population sizes and configurations."""

    def __init__(self, profiler: PerformanceProfiler | None = None):
        self.profiler = profiler or PerformanceProfiler()

    def test_population_scalability(
        self,
        run_func: Callable,
        population_sizes: list[int],
        years: list[int],
        **kwargs,
    ) -> ScalabilityMetrics:
        """Test how performance scales with population size."""
        metrics = ScalabilityMetrics()

        print("=== Population Scalability Test ===")

        for pop_size in population_sizes:
            print(f"\nTesting population size: {pop_size:,}")

            # Profile the run
            profile_result = self.profiler.profile_simulation_run(
                run_func, pop_size=pop_size, years=years, **kwargs
            )

            run_metrics = profile_result["metrics"]

            # Record metrics
            metrics.population_sizes.append(pop_size)
            metrics.execution_times.append(run_metrics.execution_time)
            metrics.memory_usages.append(run_metrics.peak_memory_mb)
            metrics.throughput_rates.append(pop_size / run_metrics.execution_time)

            print(f"  Time: {run_metrics.execution_time:.2f}s")
            print(f"  Memory: {run_metrics.peak_memory_mb:.1f} MB")
            print(
                f"  Throughput: {pop_size / run_metrics.execution_time:.0f} individuals/second"
            )

        # Calculate scaling efficiency
        if len(metrics.execution_times) > 1:
            # Linear scaling would be perfect (efficiency = 1.0)
            # Superlinear scaling > 1.0, sublinear scaling < 1.0
            size_ratios = (
                np.array(metrics.population_sizes[1:]) / metrics.population_sizes[0]
            )
            time_ratios = (
                np.array(metrics.execution_times[1:]) / metrics.execution_times[0]
            )
            scaling_efficiency = np.mean(size_ratios / time_ratios)
            metrics.scaling_efficiency = scaling_efficiency

            print(f"\nScaling Efficiency: {scaling_efficiency:.2f}")
            if scaling_efficiency > 0.8:
                print("✓ Good scaling performance")
            elif scaling_efficiency > 0.5:
                print("⚠ Moderate scaling performance")
            else:
                print("✗ Poor scaling performance")

        return metrics

    def test_configuration_scalability(
        self, run_func: Callable, configurations: list[dict], base_config: dict
    ) -> dict[str, ScalabilityMetrics]:
        """Test performance across different configuration settings."""
        results = {}

        print("=== Configuration Scalability Test ===")

        for config_name, config_overrides in configurations.items():
            print(f"\nTesting configuration: {config_name}")

            # Merge configurations
            test_config = base_config.copy()
            test_config.update(config_overrides)

            # Run and profile
            profile_result = self.profiler.profile_simulation_run(
                run_func, **test_config
            )
            results[config_name] = profile_result["metrics"]

            run_metrics = profile_result["metrics"]
            print(f"  Time: {run_metrics.execution_time:.2f}s")
            print(f"  Memory: {run_metrics.peak_memory_mb:.1f} MB")

        return results


class MemoryProfiler:
    """Advanced memory profiling and leak detection."""

    def __init__(self):
        self.snapshots = []

    @contextmanager
    def profile_memory(self, name: str = "memory_profile"):
        """Context manager for detailed memory profiling."""
        tracemalloc.start()
        initial_snapshot = tracemalloc.take_snapshot()

        try:
            yield
        finally:
            final_snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()

            # Analyze memory usage
            stats = final_snapshot.compare_to(initial_snapshot, "lineno")

            print(f"\n=== Memory Profile: {name} ===")
            print("Top memory allocations:")

            for stat in stats[:10]:
                print(
                    f"  {stat.size_diff / 1024 / 1024:.1f} MB: {stat.traceback.format()[-1]}"
                )

            # Check for potential memory leaks
            total_growth = sum(stat.size_diff for stat in stats)
            if total_growth > 50 * 1024 * 1024:  # > 50MB growth
                print(
                    f"⚠ Potential memory leak detected: {total_growth / 1024 / 1024:.1f} MB growth"
                )

    def detect_memory_leaks(
        self, func: Callable, iterations: int = 10
    ) -> dict[str, Any]:
        """Detect memory leaks by running function multiple times."""
        print(f"Testing for memory leaks over {iterations} iterations...")

        memory_usage = []

        for i in range(iterations):
            # Force garbage collection
            gc.collect()

            # Measure memory before
            tracemalloc.start()
            before = tracemalloc.get_traced_memory()[0]

            # Run function
            func()

            # Measure memory after
            after = tracemalloc.get_traced_memory()[0]
            tracemalloc.stop()

            growth = after - before
            memory_usage.append(growth / 1024 / 1024)  # MB

            print(f"  Iteration {i + 1}: {growth / 1024 / 1024:.1f} MB")

        # Analyze trend
        if len(memory_usage) > 1:
            trend = np.polyfit(range(len(memory_usage)), memory_usage, 1)[0]
            if trend > 1.0:  # Growing by more than 1MB per iteration
                print(f"⚠ Memory leak detected: {trend:.2f} MB growth per iteration")
                return {
                    "leak_detected": True,
                    "growth_rate": trend,
                    "usage": memory_usage,
                }
            else:
                print("✓ No significant memory leak detected")
                return {
                    "leak_detected": False,
                    "growth_rate": trend,
                    "usage": memory_usage,
                }

        return {"usage": memory_usage}


# Global profiler instances
_performance_profiler = None
_scalability_tester = None
_memory_profiler = None


def get_performance_profiler() -> PerformanceProfiler:
    """Get the global performance profiler instance."""
    global _performance_profiler
    if _performance_profiler is None:
        _performance_profiler = PerformanceProfiler()
    return _performance_profiler


def get_scalability_tester() -> ScalabilityTester:
    """Get the global scalability tester instance."""
    global _scalability_tester
    if _scalability_tester is None:
        _scalability_tester = ScalabilityTester()
    return _scalability_tester


def get_memory_profiler() -> MemoryProfiler:
    """Get the global memory profiler instance."""
    global _memory_profiler
    if _memory_profiler is None:
        _memory_profiler = MemoryProfiler()
    return _memory_profiler
