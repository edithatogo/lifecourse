#!/usr/bin/env python3
"""Run lightweight repository docs checks.

This validates required documentation files, checks for required sections in the
key docs pages, and verifies internal markdown links resolve to existing files.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "RELEASE.md",
    "CHANGELOG.md",
    "FUTURE_ROADMAP.md",
    "docs/architecture_status.md",
    "docs/stack_strategy.md",
    "docs/stack_change_checklist.md",
    "docs/documentation_plan.md",
    "docs/simulation_engine_status.md",
    "docs/scientific_model_status.md",
    "docs/bindings_versioning.md",
    "docs/bindings_examples.md",
]

REQUIRED_SECTIONS = {
    "docs/bindings_versioning.md": [
        "Versioning Rules",
        "Support Tiers",
        "Documentation Expectations",
    ],
    "RELEASE.md": [
        "Release Dry-Run Prerequisites",
        "Deprecation Policy",
        "Version Workflow",
        "Deferred Scope",
    ],
    "docs/bindings_examples.md": [
        "Python",
        "R",
        "Julia",
        "Go",
        "TypeScript",
        "C#",
        "Rust",
    ],
    "docs/stack_change_checklist.md": [
        "Required Updates",
        "Dependency Classification",
        "Governance Requirements",
        "Track Documentation Expectations",
    ],
    "docs/documentation_plan.md": [
        "Goal",
        "Documentation Map",
        "Documentation Sets",
        "Implementation Plan",
        "Maintenance Rules",
    ],
    "docs/simulation_engine_status.md": [
        "Scope",
        "Taxonomy",
        "Current Production Engine",
        "Future Engine Candidates",
        "Selection Contract",
        "Dependency Policy",
        "Promotion Criteria",
    ],
    "docs/scientific_model_status.md": [
        "Scope",
        "Parameter Provenance",
        "Jurisdiction Evidence",
        "Calibration And Validation",
        "Limitations And Maturity",
    ],
    "docs/architecture_status.md": [
        "Production Defaults",
        "Optional Pilots",
        "Planned Migration Tracks",
        "Documentation Status",
    ],
}

STALE_REFERENCES = {
    "ROADMAP.md": "FUTURE_ROADMAP.md",
}

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _normalize_link_target(target: str) -> str | None:
    target = target.strip()
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    if target.startswith("#"):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split("#", 1)[0]
    return target or None


def _resolve_link_source(doc_path: Path, target: str) -> Path:
    if target.startswith("/"):
        return Path(target)
    return (doc_path.parent / target).resolve()


def _iter_internal_links(content: str) -> list[str]:
    links: list[str] = []
    for raw_target in MARKDOWN_LINK_RE.findall(content):
        normalized = _normalize_link_target(raw_target)
        if normalized is not None:
            links.append(normalized)
    return links


def _check_required_files() -> list[str]:
    errors: list[str] = []
    for relpath in REQUIRED_FILES:
        if not (REPO_ROOT / relpath).exists():
            errors.append(f"missing required docs file: {relpath}")
    return errors


def _check_required_sections() -> list[str]:
    errors: list[str] = []
    for relpath, headings in REQUIRED_SECTIONS.items():
        doc_path = REPO_ROOT / relpath
        content = doc_path.read_text(encoding="utf-8")
        for heading in headings:
            if f"## {heading}" not in content and f"# {heading}" not in content:
                errors.append(f"missing required section {heading!r} in {relpath}")
    return errors


def _check_internal_links() -> list[str]:
    errors: list[str] = []
    docs_to_scan = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "CONTRIBUTING.md",
        REPO_ROOT / "docs" / "architecture_status.md",
        REPO_ROOT / "docs" / "documentation_plan.md",
        REPO_ROOT / "docs" / "simulation_engine_status.md",
        REPO_ROOT / "docs" / "scientific_model_status.md",
        REPO_ROOT / "docs" / "bindings_versioning.md",
        REPO_ROOT / "docs" / "bindings_examples.md",
        REPO_ROOT / "docs" / "stack_strategy.md",
        REPO_ROOT / "docs" / "interchange" / "model_interchange_strategy.md",
        REPO_ROOT / "docs" / "interchange" / "artifact_formats.md",
    ]

    for doc_path in docs_to_scan:
        content = doc_path.read_text(encoding="utf-8")
        for target in _iter_internal_links(content):
            resolved = _resolve_link_source(doc_path, target)
            if resolved.is_dir():
                continue
            if not resolved.exists():
                errors.append(
                    f"broken internal link in {doc_path.relative_to(REPO_ROOT)}: {target}"
                )
    return errors


def _check_stale_references() -> list[str]:
    errors: list[str] = []
    docs_to_scan = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "CONTRIBUTING.md",
        REPO_ROOT / "RELEASE.md",
        REPO_ROOT / "docs" / "architecture_status.md",
        REPO_ROOT / "docs" / "documentation_plan.md",
        REPO_ROOT / "docs" / "simulation_engine_status.md",
        REPO_ROOT / "docs" / "scientific_model_status.md",
        REPO_ROOT / "docs" / "stack_strategy.md",
    ]

    for doc_path in docs_to_scan:
        content = doc_path.read_text(encoding="utf-8")
        for stale, replacement in STALE_REFERENCES.items():
            if stale in content and replacement not in content:
                errors.append(
                    f"stale reference in {doc_path.relative_to(REPO_ROOT)}: {stale} should be {replacement}"
                )
    return errors


def run_checks() -> list[str]:
    errors = []
    errors.extend(_check_required_files())
    errors.extend(_check_required_sections())
    errors.extend(_check_internal_links())
    errors.extend(_check_stale_references())
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the success message.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = run_checks()
    if errors:
        for error in errors:
            print(error)
        return 1
    if not args.quiet:
        print("Docs checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
