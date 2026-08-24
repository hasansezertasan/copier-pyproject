"""Per-component pytest markers render and select correctly (issue #160).

Each enabled component registers a marker in ``[tool.pytest.ini_options]`` and
``tests/conftest.py`` auto-applies it by the test's top-level directory, so
``pytest -m web`` selects a component without per-test decoration. ``core`` is
always present; ``integration`` (ADR-008) rides the same list when the worker is
enabled.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Callable

import pytest


def _marker_names(project: Path) -> list[str]:
    data = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    markers = data["tool"]["pytest"]["ini_options"]["markers"]
    return [m.split(":", 1)[0] for m in markers]


def test_core_marker_always_present(render: Callable[..., Path]) -> None:
    names = _marker_names(render(preset="library"))
    assert "core" in names


def test_integration_marker_only_with_worker(render: Callable[..., Path]) -> None:
    assert "integration" not in _marker_names(render(preset="library"))
    with_worker = render(preset="library", include_worker=True, worker_broker="redis")
    assert "integration" in _marker_names(with_worker)


@pytest.mark.parametrize(
    ("toggle", "marker"),
    [
        ("include_web", "web"),
        ("include_worker", "worker"),
        ("include_mcp", "mcp"),
        ("include_gui", "gui"),
        ("include_tui", "tui"),
    ],
)
def test_component_marker_present_when_enabled(
    render: Callable[..., Path], toggle: str, marker: str
) -> None:
    answers = {"preset": "library", toggle: True}
    if toggle == "include_worker":
        answers["worker_broker"] = "redis"
    names = _marker_names(render(**answers))
    assert marker in names


def test_conftest_auto_marks_web(render: Callable[..., Path]) -> None:
    project = render(preset="library", include_web=True)
    conftest = (project / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "pytest_collection_modifyitems" in conftest
    assert '"web"' in conftest


def test_conftest_marks_root_level_tests_as_core(
    render: Callable[..., Path],
) -> None:
    project = render(preset="library")
    conftest = (project / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert 'else "core"' in conftest
