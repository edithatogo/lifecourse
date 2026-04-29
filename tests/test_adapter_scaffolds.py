from __future__ import annotations

from pathlib import Path

import pytest
from lifecourse.adapter_paths import (
    bindings_dir,
    core_api_example_dir,
    core_api_fixture_dir,
    core_api_schema_dir,
    repo_root,
    require_existing_path,
)


def test_adapter_paths_resolve_repo_root() -> None:
    assert repo_root().name == "lifecourse"
    assert core_api_schema_dir().exists()
    assert core_api_fixture_dir().exists()
    assert core_api_example_dir().exists()


def test_bindings_scaffold_root_exists() -> None:
    assert bindings_dir().exists()


def test_adapter_scaffold_readmes_exist() -> None:
    expected = [
        "README.md",
        "r/README.md",
        "julia/README.md",
        "go/README.md",
        "typescript/README.md",
        "csharp/README.md",
        "rust/README.md",
    ]

    for relpath in expected:
        assert (bindings_dir() / relpath).exists()


def test_adapter_scaffold_missing_path_reports_helpfully(tmp_path: Path) -> None:
    missing = tmp_path / "schemas" / "v1" / "model-run-request.schema.json"

    with pytest.raises(FileNotFoundError, match="schema not found"):
        require_existing_path(missing, label="schema")
