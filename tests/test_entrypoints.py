"""Console-script wiring: the primary component owns the bare command.

The highest-precedence enabled component (CLI > GUI > TUI > web > MCP > worker)
is wired to the bare ``<pkg>`` command via ``<pkg>.__main__:main``; every other
enabled component keeps a ``<pkg>-<name>`` command. GUI, when primary, lands in
``[project.gui-scripts]`` for a windowless launcher. A component's runtime deps
are core (not an optional extra) because ``__main__`` imports the primary
unconditionally.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Callable

PKG = "example"
COMPONENTS = ("cli", "gui", "tui", "web", "mcp", "worker")


def _pyproject(root: Path) -> dict[str, Any]:
    """Return the ``[project]`` table of the rendered pyproject.toml."""
    with (root / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]


def _only(render: Callable[..., Path], *enabled: str) -> dict[str, Any]:
    """Render with exactly ``enabled`` components on, all others off."""
    toggles = {f"include_{name}": (name in enabled) for name in COMPONENTS}
    return _pyproject(render(preset="custom", **toggles))


def test_tui_only_gets_bare_command(render: Callable[..., Path]) -> None:
    project = _only(render, "tui")
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert "gui-scripts" not in project
    # textual is a core dependency, not an optional extra.
    assert any(dep.startswith("textual") for dep in project["dependencies"])
    assert set(project.get("optional-dependencies", {})) == {"all"}


def test_cli_is_primary_and_tui_keeps_suffix(render: Callable[..., Path]) -> None:
    project = _only(render, "cli", "tui")
    assert project["scripts"] == {
        PKG: f"{PKG}.__main__:main",
        f"{PKG}-tui": f"{PKG}.tui.app:main",
    }


def test_gui_only_uses_gui_scripts_bare(render: Callable[..., Path]) -> None:
    project = _only(render, "gui")
    assert "scripts" not in project
    assert project["gui-scripts"] == {PKG: f"{PKG}.__main__:main"}


def test_cli_gui_splits_console_and_gui_tables(render: Callable[..., Path]) -> None:
    project = _only(render, "cli", "gui")
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert project["gui-scripts"] == {f"{PKG}-gui": f"{PKG}.gui.app:main"}


def test_library_has_no_scripts(render: Callable[..., Path]) -> None:
    project = _only(render)
    assert "scripts" not in project
    assert "gui-scripts" not in project


def test_bare_command_is_unique_across_tables(render: Callable[..., Path]) -> None:
    # Full project: every component enabled -> the bare name must appear exactly
    # once across both script tables (no packaging conflict).
    project = _pyproject(render(preset="full"))
    tables = {**project.get("scripts", {}), **project.get("gui-scripts", {})}
    assert sum(name == PKG for name in tables) == 1
