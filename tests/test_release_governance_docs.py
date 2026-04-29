from __future__ import annotations

from pathlib import Path

RELEASE_PATH = Path("RELEASE.md")


def test_release_governance_doc_exists() -> None:
    assert RELEASE_PATH.exists()


def test_release_governance_doc_covers_dry_run_and_deprecation() -> None:
    content = RELEASE_PATH.read_text(encoding="utf-8").lower()

    assert "release dry-run prerequisites" in content
    for registry in [
        "pypi",
        "crates.io",
        "npm",
        "nuget",
        "cran",
        "julia registry",
        "go module tooling",
    ]:
        assert registry in content

    assert "deprecation policy" in content
    assert "warning period" in content
    assert "compatibility windows" in content
    assert "deprecated surfaces remain available" in content
