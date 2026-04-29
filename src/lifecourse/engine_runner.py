from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast


def run_discrete_time_simulation(
    sampled_params: Any,
    *,
    pop_size: int,
    seed_idx: int | None = None,
    years: list[int] | tuple[int, ...] | None = None,
    debug: bool = False,
) -> tuple[float, float]:
    """Run the maintained discrete-time engine through a typed boundary."""

    from lifecourse.analysis.run_helpers import run_sim  # pyright: ignore[reportUnknownVariableType]  # noqa: I001

    run_sim_fn = cast(Callable[..., tuple[float, float]], run_sim)
    year_list = list(years) if years is not None else None
    return run_sim_fn(
        sampled_params,
        pop_size=pop_size,
        seed_idx=seed_idx,
        years=year_list,
        debug=debug,
    )
