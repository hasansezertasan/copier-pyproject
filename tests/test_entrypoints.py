"""Console-script wiring: the primary component owns the bare command.

The highest-precedence enabled component (CLI > GUI > TUI > web > MCP > worker)
is wired to the bare ``<pkg>`` command via ``<pkg>.__main__:main``. Every other
enabled component is exposed as a **subcommand of the ``<pkg>`` Typer root**
(``<pkg> <name>``; ``interactive`` for the TUI) rather than a separate
``<pkg>-<name>`` console script (see ADR-019). GUI, when primary, lands in
``[project.gui-scripts]`` for a windowless launcher; a non-primary GUI is the
``<pkg> gui`` subcommand instead. A component's runtime deps are core (not an
optional extra) because ``__main__``/the console root imports the primary
unconditionally.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Callable

import pytest

PKG = "example"
COMPONENTS = ("cli", "gui", "tui", "web", "mcp", "worker")


def _pyproject(root: Path) -> dict[str, Any]:
    """Return the ``[project]`` table of the rendered pyproject.toml."""
    with (root / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]


def _render_only(render: Callable[..., Path], *enabled: str) -> Path:
    """Render with exactly ``enabled`` components on, all others off."""
    toggles = {f"include_{name}": (name in enabled) for name in COMPONENTS}
    return render(preset="library", **toggles)


def _only(render: Callable[..., Path], *enabled: str) -> dict[str, Any]:
    """Return the ``[project]`` table for a render with exactly ``enabled`` on."""
    return _pyproject(_render_only(render, *enabled))


def _cli_source(root: Path) -> str:
    """Return the rendered ``cli/app.py`` source (the ``<pkg>`` Typer root)."""
    return (root / "src" / PKG / "cli" / "app.py").read_text(encoding="utf-8")


def test_tui_only_gets_bare_command(render: Callable[..., Path]) -> None:
    project = _only(render, "tui")
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert "gui-scripts" not in project
    # textual is a core dependency, not an optional extra.
    assert any(dep.startswith("textual") for dep in project["dependencies"])
    assert set(project.get("optional-dependencies", {})) == {"all"}


def test_cli_primary_exposes_tui_as_subcommand(render: Callable[..., Path]) -> None:
    # CLI is primary; the TUI is a `<pkg> interactive` subcommand, not a
    # `<pkg>-tui` console script. Only the bare command is registered.
    root = _render_only(render, "cli", "tui")
    project = _pyproject(root)
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert "gui-scripts" not in project
    assert "def interactive()" in _cli_source(root)


def test_gui_only_uses_gui_scripts_bare(render: Callable[..., Path]) -> None:
    project = _only(render, "gui")
    assert "scripts" not in project
    assert project["gui-scripts"] == {PKG: f"{PKG}.__main__:main"}


def test_cli_primary_exposes_gui_as_subcommand(render: Callable[..., Path]) -> None:
    # CLI is primary; a non-primary GUI is the `<pkg> gui` subcommand, not a
    # windowless `<pkg>-gui` gui-script. No gui-scripts table is emitted.
    root = _render_only(render, "cli", "gui")
    project = _pyproject(root)
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert "gui-scripts" not in project
    assert "def gui()" in _cli_source(root)


def test_library_has_no_scripts(render: Callable[..., Path]) -> None:
    project = _only(render)
    assert "scripts" not in project
    assert "gui-scripts" not in project


@pytest.mark.parametrize("component", ["web", "mcp", "worker"])
def test_console_component_only_gets_bare_command(
    render: Callable[..., Path], component: str
) -> None:
    # When a console component (not CLI/GUI/TUI, already covered) is the sole
    # enabled one, it is the primary: bare command in [project.scripts], no
    # gui-scripts, and its runtime dep is core rather than an optional extra.
    project = _only(render, component)
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert "gui-scripts" not in project
    assert project["dependencies"], "primary component deps must be core"
    assert set(project.get("optional-dependencies", {})) == {"all"}


def test_gui_primary_with_secondaries_no_collision(
    render: Callable[..., Path],
) -> None:
    # GUI primary (CLI off) + secondaries: the bare name lands in gui-scripts
    # (windowless launcher) and tui/web are subcommands of the shared console
    # root, so no `<pkg>-<name>` scripts are emitted at all.
    root = _render_only(render, "gui", "tui", "web")
    project = _pyproject(root)
    assert project["gui-scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert "scripts" not in project
    src = _cli_source(root)
    assert "def interactive()" in src
    assert "def web()" in src
    # The launcher's default callback launches the primary (gui), which is
    # therefore NOT also a named subcommand.
    assert "@app.callback(invoke_without_command=True)" in src
    assert f"from {PKG}.gui.app import main" in src
    assert "def gui()" not in src
    # The bare name is in exactly one table.
    assert (PKG in project.get("gui-scripts", {})) ^ (PKG in project.get("scripts", {}))


def test_no_cli_launcher_wires_default_and_subcommands(
    render: Callable[..., Path],
) -> None:
    # No CLI + >=2 components -> a minimal launcher root: bare `<pkg>` launches
    # the primary (web) via the default callback, the secondary (mcp) is a
    # subcommand, no version/info commands exist, and typer is a core dep even
    # though include_cli is off.
    root = _render_only(render, "web", "mcp")
    project = _pyproject(root)
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert "gui-scripts" not in project
    assert any(dep.startswith("typer") for dep in project["dependencies"])
    src = _cli_source(root)
    assert "@app.callback(invoke_without_command=True)" in src
    assert f"from {PKG}.web.app import main" in src  # default launches primary
    assert "def web()" not in src  # primary is not a named subcommand
    assert "def mcp()" in src  # secondary is
    assert "def show_version()" not in src  # minimal launcher: no CLI commands
    assert "def info()" not in src


def test_single_component_non_cli_has_no_console_root(
    render: Callable[..., Path],
) -> None:
    # A single non-CLI component has no shared launcher: no `cli/` package, no
    # `typer` dependency, and `__main__` launches it directly.
    root = _render_only(render, "web")
    project = _pyproject(root)
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}
    assert not (root / "src" / PKG / "cli").exists()
    assert not any(dep.startswith("typer") for dep in project["dependencies"])


def test_pydantic_settings_is_core_dependency(render: Callable[..., Path]) -> None:
    # core.config imports pydantic-settings unconditionally when enabled, so it
    # belongs in core dependencies (not an optional extra) even for a component-
    # less library.
    toggles = {f"include_{name}": False for name in COMPONENTS}
    project = _pyproject(
        render(preset="library", include_pydantic_settings=True, **toggles)
    )
    assert "scripts" not in project  # library: no runnable component
    assert any(
        dep.startswith("pydantic-settings") for dep in project["dependencies"]
    )
    assert set(project.get("optional-dependencies", {})) <= {"all"}


def test_bare_command_is_unique_across_tables(render: Callable[..., Path]) -> None:
    # Full project: every component enabled -> the bare name must appear in
    # exactly one of the two script tables (never both, which is a packaging
    # conflict; never neither). Count per-table rather than merging with **,
    # which would silently collapse a duplicate key and mask a collision.
    root = render(preset="full")
    project = _pyproject(root)
    in_scripts = PKG in project.get("scripts", {})
    in_gui = PKG in project.get("gui-scripts", {})
    assert in_scripts ^ in_gui
    # No `<pkg>-<name>` console scripts survive: only the bare name is registered.
    assert all("-" not in name for name in project.get("scripts", {}))
    assert all("-" not in name for name in project.get("gui-scripts", {}))
    # Every non-primary component (CLI is primary in `full`) is a Typer
    # subcommand of the root instead.
    src = _cli_source(root)
    for name in ("interactive", "gui", "web", "mcp", "worker"):
        assert f"def {name}()" in src
