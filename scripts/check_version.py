from __future__ import annotations

import argparse
import sys
from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]


def read_project_version(pyproject_path: Path = REPO_ROOT / "pyproject.toml") -> str:
    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    return str(project["version"])


def changelog_has_version(
    version: str, changelog_path: Path = REPO_ROOT / "CHANGELOG.md"
) -> bool:
    marker = f"## {version}"
    return marker in changelog_path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release version consistency.")
    parser.add_argument(
        "--allow-unreleased",
        action="store_true",
        help="Allow the current project version to be absent from CHANGELOG.md.",
    )
    args = parser.parse_args()

    version = read_project_version()
    if not args.allow_unreleased and not changelog_has_version(version):
        print(
            f"CHANGELOG.md is missing a '## {version}' section for the package version.",
            file=sys.stderr,
        )
        return 1

    print(f"lifecourse version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
