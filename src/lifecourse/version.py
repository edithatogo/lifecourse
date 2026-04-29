from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    """Return the installed package version."""

    try:
        return version("lifecourse")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = get_version()
