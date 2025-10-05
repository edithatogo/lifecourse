import warnings
import re
import pytest
from lifecourse.model.population_system import PopulationSystemDask
from lifecourse.model.parameters import sample_params_from_dist, prepare_dask_params, DISTRIBUTIONS


def test_no_unknown_divisions_warning_on_step():
    # Prepare minimal params
    params = prepare_dask_params(sample_params_from_dist(DISTRIBUTIONS, seed=123))
    ps = PopulationSystemDask(20, params, arm="prospective")

    # Convert the specific user warning into an exception to get a stack trace
    warnings.filterwarnings("error", message=r".*unknown divisions.*", category=UserWarning)
    try:
        ps.step(year=params.get('START_YEAR', 2020))
    except Warning as e:
        # Re-raise to allow pytest to show the full stack trace for tracing the source
        raise
    finally:
        # Restore default behavior (avoid affecting other tests)
        warnings.resetwarnings()
