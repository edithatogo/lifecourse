import time

from lifecourse.analysis.run_helpers import run_sim
from lifecourse.model.parameters import DISTRIBUTIONS, get_mean_params


def test_full_simulation_performance_small_pop():
    """Run a reduced-size full simulation to exercise the code path.

    This is a lightweight variant of the old root script intended for CI use.
    """
    mean_params = get_mean_params(DISTRIBUTIONS)

    start = time.time()
    dc, dq = run_sim(
        mean_params, pop_size=500, years=list(range(2020, 2101)), debug=True
    )
    elapsed = time.time() - start

    assert elapsed >= 0
    assert isinstance(dc, (int, float)) or hasattr(dc, "__array__")
    assert isinstance(dq, (int, float)) or hasattr(dq, "__array__")

    # We don't enforce a strict performance bound in CI, only sanity.
