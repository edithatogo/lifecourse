from __future__ import annotations

from scripts.check_docs import (
    REPO_ROOT,
    REQUIRED_FILES,
    REQUIRED_SECTIONS,
    run_checks,
)


def test_docs_check_required_files_and_sections_exist() -> None:
    assert REQUIRED_FILES
    assert REQUIRED_SECTIONS


def test_docs_check_passes() -> None:
    assert run_checks() == []


def test_documentation_plan_has_status_map() -> None:
    content = (REPO_ROOT / "docs" / "documentation_plan.md").read_text(encoding="utf-8")
    assert "## Documentation Map" in content
    for label in ["`current`", "`experimental`", "`planned`", "`deferred`"]:
        assert label in content
    for section in [
        "User docs",
        "Contributor docs",
        "Architecture docs",
        "Scientific/model docs",
        "API/contract docs",
        "Release docs",
        "Generated docs site",
    ]:
        assert section in content


def test_docs_check_flags_stale_roadmap_reference(tmp_path, monkeypatch) -> None:
    from scripts import check_docs

    for relpath in [
        "README.md",
        "CONTRIBUTING.md",
        "RELEASE.md",
        "docs/architecture_status.md",
        "docs/documentation_plan.md",
        "docs/stack_strategy.md",
    ]:
        docs_file = tmp_path / relpath
        docs_file.parent.mkdir(parents=True, exist_ok=True)
        docs_file.write_text("placeholder\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "See ROADMAP.md for details.\n", encoding="utf-8"
    )

    original_root = check_docs.REPO_ROOT
    try:
        check_docs.REPO_ROOT = tmp_path
        monkeypatch.setattr(check_docs, "_check_required_files", lambda: [])
        monkeypatch.setattr(check_docs, "_check_required_sections", lambda: [])
        monkeypatch.setattr(check_docs, "_check_internal_links", lambda: [])
        assert any("stale reference" in msg for msg in check_docs.run_checks())
    finally:
        check_docs.REPO_ROOT = original_root
