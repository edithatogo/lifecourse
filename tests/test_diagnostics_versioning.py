from __future__ import annotations

import logging
from importlib.metadata import version

import lifecourse
import pytest
from lifecourse.diagnostics import configure_logging
from lifecourse.version import get_version


def test_package_exports_installed_version() -> None:
    assert lifecourse.__version__ == version("lifecourse")
    assert get_version() == version("lifecourse")


def test_configure_logging_uses_debug_level_when_requested() -> None:
    level = configure_logging(debug=True, force=True)

    assert level == logging.DEBUG
    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="Unknown log level"):
        configure_logging(level="verbose")
