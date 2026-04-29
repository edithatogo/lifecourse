from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release-dry-run.yml"


def test_release_dry_run_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_release_dry_run_workflow_is_publish_safe() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text())
    workflow_text = WORKFLOW_PATH.read_text().lower()

    assert workflow["name"] == "Release Dry Run"
    assert "workflow_dispatch" in workflow["on"]
    assert "pull_request" in workflow["on"]
    assert "pypa/gh-action-pypi-publish" not in workflow_text
    assert "twine upload" not in workflow_text
    assert "id-token: write" not in workflow_text


def test_release_dry_run_workflow_builds_without_publishing() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text())
    jobs = workflow["jobs"]
    release_job = jobs["release-dry-run"]
    step_text = "\n".join(
        " ".join(str(value) for value in step.values()) for step in release_job["steps"]
    )

    assert "astral-sh/setup-uv" in step_text
    assert "uv build" in step_text
    assert "uv run python -m tarfile" in step_text
    assert "uv run python -m zipfile" in step_text
