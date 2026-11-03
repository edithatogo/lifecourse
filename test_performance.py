#!/usr/bin/env python3

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lifecourseid.analysis.run_helpers import run_sim
from lifecourseid.model.parameters import DISTRIBUTIONS, get_mean_params


def test_performance():
    # Get mean parameters
    mean_params = get_mean_params(DISTRIBUTIONS)

    # Test with a small simulation
    print("Running performance test with small simulation...")
    start_time = time.time()

    # Run a small simulation to test performance
    dc, dq = run_sim(
        mean_params, pop_size=1000, years=list(range(2020, 2025)), debug=False
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"dCost: {dc}")
    print(f"dQALY: {dq}")
    print(f"ICER: {dc / dq if dq != 0 else 0}")
    print(f"Execution time: {elapsed_time:.2f} seconds")

    # Check if performance is reasonable (less than 30 seconds for small simulation)
    if elapsed_time < 30:
        print("SUCCESS: Performance is acceptable")
        return True
    else:
        print("WARNING: Performance may need further optimization")
        return False


if __name__ == "__main__":
    test_performance()
