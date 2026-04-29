from __future__ import annotations

from pathlib import Path

DOC_PATH = Path("docs/bindings_examples.md")


def test_bindings_examples_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_bindings_examples_doc_covers_all_scaffolds() -> None:
    content = DOC_PATH.read_text(encoding="utf-8").lower()

    for label in ["python", "r", "julia", "go", "typescript", "c#", "rust"]:
        assert f"## {label}" in content

    assert "installation assumptions" in content
    assert "minimal run" in content
    assert "expected output" in content
    assert "limitations" in content
    assert "wrapper-first" in content
