"""Preset behavior: each archetype preset seeds the expected component set.

Guards the silent-drift risks in ``copier.yml``'s ``preset_map`` (ADR-016):
the default preset changing, an archetype seeding the wrong components, or
``full`` no longer enabling everything.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

PKG = "example"
COMPONENTS = ("cli", "web", "gui", "tui", "mcp", "worker")


def _components(root: Path) -> set[str]:
    """The set of optional component packages present under ``src/<pkg>/``."""
    src = root / "src" / PKG
    return {name for name in COMPONENTS if (src / name).is_dir()}


def _pyproject(root: Path) -> str:
    return (root / "pyproject.toml").read_text(encoding="utf-8")


def test_core_and_utils_always_present(render: Callable[..., Path]) -> None:
    root = render(preset="library")
    assert (root / "src" / PKG / "core").is_dir()
    assert (root / "src" / PKG / "utils").is_dir()


def test_preset_library_seeds_examples_only(render: Callable[..., Path]) -> None:
    root = render(preset="library")
    assert _components(root) == set()
    assert (root / "examples").is_dir()


def test_preset_default_is_library(render: Callable[..., Path]) -> None:
    # No preset supplied → defaults to library → no components, examples on.
    root = render()
    assert _components(root) == set()
    assert (root / "examples").is_dir()


def test_preset_tool_seeds_cli_tui_and_settings(
    render: Callable[..., Path],
) -> None:
    root = render(preset="tool")
    assert _components(root) == {"cli", "tui"}
    assert not (root / "examples").exists()
    assert "pydantic-settings" in _pyproject(root)


def test_preset_web_seeds_web_settings_and_db(
    render: Callable[..., Path],
) -> None:
    root = render(preset="web")
    assert _components(root) == {"web"}
    assert "pydantic-settings" in _pyproject(root)
    compose = (root / ".devcontainer" / "docker-compose.yml").read_text(
        encoding="utf-8"
    )
    assert "postgres:" in compose


def test_preset_full_enables_all_components(render: Callable[..., Path]) -> None:
    root = render(preset="full")
    assert _components(root) == set(COMPONENTS)
    # Non-component full-only markers: c-extensions and MegaLinter render only
    # when their toggle is on, so their presence proves full reaches past the
    # interface components.
    assert (root / "src" / PKG / "_c_extension.pyx").exists()
    assert (root / ".github" / "workflows" / "mega-linter.yml").exists()
