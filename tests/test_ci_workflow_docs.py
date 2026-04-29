from __future__ import annotations

from pathlib import Path


def test_ci_workflow_runs_repo_docs_checks() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "name: Repo Docs Checks" in workflow
    assert "uv run nox -s docs" in workflow
    assert "Run docs checks" in workflow
