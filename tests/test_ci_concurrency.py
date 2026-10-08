"""Generated CI cancels superseded runs within each PR or ref (issue #345)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
import yaml


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
def test_ci_workflow_concurrency(render: Callable[..., Path], preset: str) -> None:
    project = render(preset=preset)
    workflow = yaml.safe_load(
        (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )

    assert workflow["concurrency"] == {
        "group": (
            "${{ github.workflow }}-"
            "${{ github.event.pull_request.number || github.ref }}"
        ),
        "cancel-in-progress": True,
    }
