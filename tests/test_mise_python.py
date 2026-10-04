"""The dev interpreter follows .python-version unless explicitly overridden."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable

import pytest


@pytest.mark.parametrize("override", [None, "3.13"])
def test_mise_python_follows_version_file(
    render: Callable[..., Path], monkeypatch: pytest.MonkeyPatch, override: str | None
) -> None:
    mise = shutil.which("mise")
    if mise is None:
        pytest.skip("mise is required to resolve its configuration templates")
    root = render()
    monkeypatch.delenv("PYTHON_VERSION", raising=False)
    monkeypatch.setenv("MISE_TRUSTED_CONFIG_PATHS", str(root))
    if override is not None:
        monkeypatch.setenv("PYTHON_VERSION", override)
    # Resolve from a subdirectory as well as the project root; the fallback
    # must be relative to mise.toml, not the shell's working directory.
    for version, cwd in [("3.14", root), ("3.12", root / "src")]:
        (root / ".python-version").write_text(f"{version}\n", encoding="utf-8")
        result = subprocess.run(
            [mise, "ls", "--current", "--json", "python"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        assert json.loads(result.stdout)[0]["requested_version"] == (
            override or version
        )
