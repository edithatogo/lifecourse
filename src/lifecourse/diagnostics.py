from __future__ import annotations

import logging
import os
from typing import Literal

LogLevelName = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(
    *,
    level: str | int | None = None,
    debug: bool = False,
    force: bool = False,
) -> int:
    """Configure standard-library logging for CLI and batch runs."""

    resolved_level = _resolve_log_level(level=level, debug=debug)
    logging.basicConfig(
        level=resolved_level,
        format=DEFAULT_LOG_FORMAT,
        force=force,
    )
    return resolved_level


def _resolve_log_level(*, level: str | int | None, debug: bool) -> int:
    if isinstance(level, int):
        return level

    if level is None:
        level = os.getenv("LIFECOURSE_LOG_LEVEL")

    if level is None:
        return logging.DEBUG if debug else logging.INFO

    normalized = level.upper()
    if normalized not in logging.getLevelNamesMapping():
        valid_levels = ", ".join(LogLevelName.__args__)
        raise ValueError(
            f"Unknown log level '{level}'. Expected one of: {valid_levels}"
        )
    return logging.getLevelNamesMapping()[normalized]
