from __future__ import annotations

from pathlib import Path

DOC_PATH = Path("docs/bindings_versioning.md")


def test_bindings_versioning_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_bindings_versioning_doc_covers_policy_terms() -> None:
    content = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "schema contract" in content
    assert "generated clients and wrapper adapters" in content
    assert "reference" in content
    assert "experimental" in content
    assert "smoke-tested" in content
    assert "production-supported" in content
    assert "deprecated" in content
    assert "unsupported" in content
