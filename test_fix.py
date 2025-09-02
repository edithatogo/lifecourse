#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lifecourseid.analysis.run_helpers import run_sim
from lifecourseid.model.parameters import DISTRIBUTIONS, get_mean_params


def test_qaly_fix():
    # Get mean parameters
    mean_params = get_mean_params(DISTRIBUTIONS)

    # Run a small simulation to test the fix
    print("Running test simulation...")
    dc, dq = run_sim(mean_params, pop_size=1000, years=list(range(2020, 2025)))

    print(f"dCost: {dc}")
    print(f"dQALY: {dq}")
    print(f"ICER: {dc/dq if dq != 0 else 0}")

    # Check if dQALY is positive (as expected)
    if dq > 0:
        print("SUCCESS: dQALY is positive as expected")
        return True
    else:
        print("FAILURE: dQALY is still negative")
        return False


if __name__ == "__main__":
    test_qaly_fix()
