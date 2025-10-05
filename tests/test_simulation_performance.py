"""
Performance test for basic simulation runs.

This module tests that the simulation completes within reasonable time bounds.
"""

import time
import pytest

from lifecourse.model.parameters import DISTRIBUTIONS, get_mean_params
from lifecourse.analysis.run_helpers import run_sim


@pytest.mark.slow
def test_simulation_performance():
    """Test that a small simulation completes within acceptable time."""
    # Get mean parameters
    mean_params = get_mean_params(DISTRIBUTIONS)

    # Test with a small simulation
    start_time = time.time()

    # Run a small simulation to test performance
    dc, dq = run_sim(
        mean_params, pop_size=1000, years=list(range(2020, 2025)), debug=False
    )

    elapsed_time = time.time() - start_time

    # Verify results are numeric
    assert isinstance(dc, (int, float)), "dCost should be numeric"
    assert isinstance(dq, (int, float)), "dQALY should be numeric"

    # Verify ICER can be calculated
    if dq != 0:
        icer = dc / dq
        assert isinstance(icer, (int, float)), "ICER should be numeric"

    # Check if performance is reasonable (less than 60 seconds for small simulation)
    assert (
        elapsed_time < 60
    ), f"Simulation took {elapsed_time:.2f}s, expected < 60s for 1000 population over 5 years"
