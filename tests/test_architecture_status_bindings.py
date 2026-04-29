from __future__ import annotations

from pathlib import Path

DOC_PATH = Path("docs/architecture_status.md")


def test_architecture_status_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_architecture_status_mentions_binding_boundary() -> None:
    content = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "python remains the reference implementation" in content
    assert "wrapper-first and experimental" in content
    assert "invoke the python reference contract" in content
    assert (
        "rust kernel candidates should stay limited to pure, deterministic kernels"
        in content
    )
    assert "native bindings are deferred" in content
