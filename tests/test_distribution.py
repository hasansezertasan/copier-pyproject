"""Opt-in Homebrew tap + Scoop bucket distribution (issue #146)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

PKG = "example"
USER = "octocat"


def _answers(root: Path) -> dict[str, Any]:
    text = (root / ".copier-answers.yml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


def test_full_preset_enables_distribution(render: Callable[..., Path]) -> None:
    answers = _answers(render(preset="full"))
    assert answers["include_homebrew"] is True
    assert answers["include_scoop"] is True


def test_library_never_asks_distribution(render: Callable[..., Path]) -> None:
    # when: is_app is false for a library, so the toggles are never stored.
    answers = _answers(render(preset="library"))
    assert "include_homebrew" not in answers
    assert "include_scoop" not in answers


def test_app_defaults_distribution_off(render: Callable[..., Path]) -> None:
    answers = _answers(render(preset="tool"))  # cli+tui -> is_app true
    assert answers["include_homebrew"] is False
    assert answers["include_scoop"] is False
