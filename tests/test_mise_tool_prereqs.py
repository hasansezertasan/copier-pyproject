"""mise-installed Python tools need Python 3.14 and uv before `mise install`.

``pipx:cobo`` requires Python >=3.14, but the runner's system Python is older —
and without uv on PATH mise falls back from ``uvx`` to ``pipx``, which ignores
the mise-managed Python from ``.python-version``. Every workflow that runs
``jdx/mise-action`` must therefore provision ``setup-python`` (pinned to
``.python-version``) and ``setup-uv`` first — the ordering the CI ``hooks`` job
already uses. ``copilot-setup-steps.yml`` ran ``mise-action`` before ``setup-uv``
with no ``setup-python`` at all, and ``gitignore-drift.yml`` ran it with
neither, so both failed installing cobo on fresh runners (issue #369).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml


def _steps(root: Path, workflow: str, job: str) -> list[dict[str, Any]]:
    doc = yaml.safe_load(
        (root / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    )
    return doc["jobs"][job]["steps"]


def _index_of(steps: list[dict[str, Any]], prefix: str) -> int:
    return next(
        i
        for i, step in enumerate(steps)
        if str(step.get("uses", "")).startswith(prefix)
    )


def test_copilot_setup_provisions_python_and_uv_before_mise(
    render: Callable[..., Path],
) -> None:
    steps = _steps(render(), "copilot-setup-steps.yml", "copilot-setup-steps")
    python = _index_of(steps, "actions/setup-python@")
    uv = _index_of(steps, "astral-sh/setup-uv@")
    mise = _index_of(steps, "jdx/mise-action@")
    assert python < mise
    assert uv < mise
    assert steps[python]["with"] == {"python-version-file": ".python-version"}


def test_gitignore_drift_provisions_python_and_uv_before_mise(
    render: Callable[..., Path],
) -> None:
    steps = _steps(render(), "gitignore-drift.yml", "gitignore-drift")
    python = _index_of(steps, "actions/setup-python@")
    uv = _index_of(steps, "astral-sh/setup-uv@")
    mise = _index_of(steps, "jdx/mise-action@")
    assert python < mise
    assert uv < mise
    assert steps[python]["with"] == {"python-version-file": ".python-version"}
