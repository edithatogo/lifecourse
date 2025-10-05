#!/usr/bin/env python3

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lifecourse.model.parameters import DISTRIBUTIONS, get_mean_params
from lifecourse.analysis.run_helpers import run_sim


def test_full_simulation():
    # Get mean parameters
    mean_params = get_mean_params(DISTRIBUTIONS)

    # Test with a full simulation (but smaller population for testing)
    print("Running full simulation test (81 years, smaller population)...")
    start_time = time.time()

    # Run a full simulation with reduced population size
    dc, dq = run_sim(
        mean_params, pop_size=1000, years=list(range(2020, 2101)), debug=False
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"dCost: {dc}")
    print(f"dQALY: {dq}")
    print(f"ICER: {dc/dq if dq != 0 else 0}")
    print(f"Execution time: {elapsed_time:.2f} seconds")

    # Check if performance is reasonable (less than 2 minutes for full simulation with reduced population)
    if elapsed_time < 120:
        print("SUCCESS: Full simulation performance is acceptable")
        return True
    else:
        print("WARNING: Full simulation performance may need further optimization")
        return False


if __name__ == "__main__":
    test_full_simulation()
