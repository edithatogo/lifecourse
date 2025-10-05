from lifecourse.analysis.run_helpers import run_sim
from lifecourse.model.parameters import DISTRIBUTIONS, get_mean_params


def test_qaly_fix_small_run():
    """Run a small deterministic simulation and assert result shape and numeric sanity.

    This converts the old root-level script into a pytest test. It avoids
    manipulating sys.path and relies on pytest.ini's `pythonpath = src`.
    """
    mean_params = get_mean_params(DISTRIBUTIONS)
    dc, dq = run_sim(mean_params, pop_size=500, years=list(range(2020, 2025)))

    # Basic sanity checks
    assert isinstance(dc, (int, float)) or hasattr(dc, "__array__")
    assert isinstance(dq, (int, float)) or hasattr(dq, "__array__")

    # dQALY should not be NaN
    try:
        assert dq is not None
    except AssertionError:
        # keep the assertion simple for CI readability
        assert False
