from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root for adapter and contract scaffolds."""

    return Path(__file__).resolve().parents[2]


def core_api_dir() -> Path:
    return repo_root() / "specs" / "core-api"


def core_api_schema_dir() -> Path:
    return core_api_dir() / "schemas" / "v1"


def core_api_fixture_dir() -> Path:
    return core_api_dir() / "fixtures" / "v1"


def core_api_example_dir() -> Path:
    return core_api_dir() / "examples" / "v1"


def bindings_dir() -> Path:
    return repo_root() / "bindings"


def require_existing_path(path: Path, *, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path
