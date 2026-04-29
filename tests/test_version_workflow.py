from __future__ import annotations

from pathlib import Path

from scripts.check_version import changelog_has_version, read_project_version


def test_read_project_version_from_pyproject(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "example"
version = "1.2.3"
""".strip(),
        encoding="utf-8",
    )

    assert read_project_version(pyproject) == "1.2.3"


def test_changelog_has_matching_version_section(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## 1.2.3\n", encoding="utf-8")

    assert changelog_has_version("1.2.3", changelog)
    assert not changelog_has_version("2.0.0", changelog)
