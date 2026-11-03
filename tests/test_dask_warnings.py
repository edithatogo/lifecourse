import warnings

from lifecourse.model.parameters import (
    DISTRIBUTIONS,
    prepare_dask_params,
    sample_params_from_dist,
)
from lifecourse.model.population_system import PopulationSystemDask


def test_no_unknown_divisions_warning_on_step():
    # Prepare minimal params
    params = prepare_dask_params(sample_params_from_dist(DISTRIBUTIONS, seed=123))
    ps = PopulationSystemDask(20, params, arm="prospective")

    # Convert the specific user warning into an exception to get a stack trace
    warnings.filterwarnings(
        "error", message=r".*unknown divisions.*", category=UserWarning
    )
    try:
        ps.step(year=params.get("START_YEAR", 2020))
    finally:
        # Restore default behavior (avoid affecting other tests)
        warnings.resetwarnings()
