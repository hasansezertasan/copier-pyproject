"""Preset behavior: each preset seeds the expected component set.

These guard the two silent-drift risks in ``copier.yml``'s ``preset_map``:
``custom`` diverging from the historical defaults (which would break the
byte-identical ``--defaults`` guarantee) and ``full`` not enabling everything.
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


def test_core_and_utils_always_present(render: Callable[..., Path]) -> None:
    root = render(preset="minimal")
    assert (root / "src" / PKG / "core").is_dir()
    assert (root / "src" / PKG / "utils").is_dir()


def test_preset_minimal_has_no_components(render: Callable[..., Path]) -> None:
    assert _components(render(preset="minimal")) == set()


def test_preset_custom_matches_historical_defaults(
    render: Callable[..., Path],
) -> None:
    # custom == the template's pre-preset defaults: cli/web/gui/tui on, rest off.
    assert _components(render(preset="custom")) == {"cli", "web", "gui", "tui"}


def test_preset_default_is_custom(render: Callable[..., Path]) -> None:
    # No preset supplied → defaults to custom → same component set.
    assert _components(render()) == {"cli", "web", "gui", "tui"}


def test_preset_full_enables_all_components(render: Callable[..., Path]) -> None:
    root = render(preset="full")
    assert _components(root) == set(COMPONENTS)
    # Non-component full-only markers: c-extensions and MegaLinter render only
    # when their toggle is on, so their presence proves full reaches past the
    # interface components.
    assert (root / "src" / PKG / "_c_extension.pyx").exists()
    assert (root / ".github" / "workflows" / "mega-linter.yml").exists()
