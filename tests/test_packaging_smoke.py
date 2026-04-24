from __future__ import annotations

import subprocess
import sys


def test_project_can_build_distributions() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--sdist"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
