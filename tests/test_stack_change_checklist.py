from __future__ import annotations

from pathlib import Path

DOC_PATH = Path("docs/stack_change_checklist.md")


def test_stack_change_checklist_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_stack_change_checklist_doc_covers_required_updates() -> None:
    content = DOC_PATH.read_text(encoding="utf-8").lower()

    for term in [
        "architecture_status",
        "stack_strategy",
        "conductor/tech-stack",
        "readme.md",
        "changelog.md",
        "dependency classification",
        "core",
        "optional",
        "experimental",
        "deferred",
    ]:
        assert term in content
