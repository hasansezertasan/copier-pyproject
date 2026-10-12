"""mise-installed Python tools need Python and uv before `mise install`.

``pipx:cobo`` requires a Python matching ``.python-version``, but the runner's
system Python is older — and without uv on PATH mise falls back from ``uvx`` to
``pipx``, which ignores the mise-managed Python. Every workflow that runs
``jdx/mise-action`` must therefore provision ``setup-python`` (pinned to
``.python-version``) and ``setup-uv`` first — the ordering the CI ``hooks`` job
already uses. ``copilot-setup-steps.yml`` ran ``mise-action`` before
``setup-uv`` with no ``setup-python`` at all, and ``gitignore-drift.yml`` and
``all-contributors.yml`` ran it with neither, so all three failed installing
cobo on fresh runners (issue #369).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

# Every template workflow that runs a full `mise install` (which always
# includes `pipx:cobo` from mise.toml): (workflow file, job id, render answers
# needed for the file to exist). `all-contributors.yml` is conditional on its
# toggle, so it renders with the `full` preset.
MISE_WORKFLOWS = [
    pytest.param("copilot-setup-steps.yml", "copilot-setup-steps", {}, id="copilot"),
    pytest.param("gitignore-drift.yml", "gitignore-drift", {}, id="gitignore-drift"),
    pytest.param(
        "all-contributors.yml",
        "generate",
        {"preset": "full"},
        id="all-contributors",
    ),
]


def _steps(root: Path, workflow: str, job: str) -> list[dict[str, Any]]:
    doc = yaml.safe_load(
        (root / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    )
    return doc["jobs"][job]["steps"]


def _index_of(steps: list[dict[str, Any]], prefix: str) -> int:
    for i, step in enumerate(steps):
        if str(step.get("uses", "")).startswith(prefix):
            return i
    pytest.fail(f"no step uses {prefix!r} (steps: {[s.get('name') for s in steps]})")


@pytest.mark.parametrize(("workflow", "job", "answers"), MISE_WORKFLOWS)
def test_mise_workflow_provisions_python_and_uv_first(
    render: Callable[..., Path], workflow: str, job: str, answers: dict[str, Any]
) -> None:
    steps = _steps(render(**answers), workflow, job)
    checkout = _index_of(steps, "actions/checkout@")
    python = _index_of(steps, "actions/setup-python@")
    uv = _index_of(steps, "astral-sh/setup-uv@")
    mise = _index_of(steps, "jdx/mise-action@")
    # `python-version-file` only resolves after checkout puts the file on disk.
    assert checkout < python < mise
    assert uv < mise
    assert steps[python].get("with", {}).get("python-version-file") == ".python-version"
