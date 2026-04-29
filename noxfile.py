from __future__ import annotations

import nox

nox.options.default_venv_backend = "none"
nox.options.sessions = ["lint", "typecheck", "version", "docs", "tests", "build"]


def _uv(session: nox.Session, *args: str) -> None:
    session.run("uv", *args, external=True)


@nox.session
def lint(session: nox.Session) -> None:
    """Run formatting and lint checks for maintained code."""

    _uv(session, "run", "ruff", "format", "--check", "src", "config", "tests")
    _uv(session, "run", "ruff", "check", "src", "config", "tests")


@nox.session
def typecheck(session: nox.Session) -> None:
    """Run strict static type checks for the maintained typed slice."""

    _uv(session, "run", "basedpyright")


@nox.session
def version(session: nox.Session) -> None:
    """Check release version metadata consistency."""

    _uv(session, "run", "python", "scripts/check_version.py")


@nox.session
def docs(session: nox.Session) -> None:
    """Run repository docs checks."""

    _uv(session, "run", "python", "scripts/check_docs.py")


@nox.session
def tests(session: nox.Session) -> None:
    """Run the project test suite with coverage."""

    _uv(session, "run", "pytest")


@nox.session
def build(session: nox.Session) -> None:
    """Build package artifacts."""

    _uv(session, "build")


@nox.session
def mutation(session: nox.Session) -> None:
    """Run the scoped mutation test baseline."""

    _uv(session, "run", "mutmut", "run")


@nox.session
def profile(session: nox.Session) -> None:
    """Run representative profiling workloads through Scalene."""

    _uv(
        session,
        "run",
        "scalene",
        "--cli",
        "--profile-all",
        "scripts/profile_workloads.py",
        "--workload",
        "all",
    )
