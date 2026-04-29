from __future__ import annotations

from scripts.check_docs import REQUIRED_FILES, REQUIRED_SECTIONS, run_checks


def test_docs_check_required_files_and_sections_exist() -> None:
    assert REQUIRED_FILES
    assert REQUIRED_SECTIONS


def test_docs_check_passes() -> None:
    assert run_checks() == []
