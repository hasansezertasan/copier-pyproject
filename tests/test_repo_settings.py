"""``include_repo_settings`` renders ``.github/settings.yml`` for the Settings App.

Guards Part A of the repo-settings-as-code design: the metadata file renders
only when the toggle is on, carries the substituted description/homepage/topics,
and never grows a ``labels:`` block (labels stay App-free in ``labels.yml``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable


def _settings(root: Path) -> Path:
    return root / ".github" / "settings.yml"


def test_repo_settings_absent_by_default(render: Callable[..., Path]) -> None:
    # Default preset is library → toggle off → no file.
    assert not _settings(render()).exists()


def test_repo_settings_absent_when_off(render: Callable[..., Path]) -> None:
    assert not _settings(render(include_repo_settings=False)).exists()


def test_repo_settings_renders_metadata(render: Callable[..., Path]) -> None:
    root = render(include_repo_settings=True)
    text = _settings(root).read_text(encoding="utf-8")
    assert text.startswith("---")
    assert 'description: "A Python project template."' in text
    assert 'homepage: "https://octocat.github.io/example"' in text
    assert "- python" in text
    assert "allow_squash_merge: true" in text
    assert "allow_merge_commit: false" in text
    # Labels are NOT managed by the App (no top-level `labels:` key; the word
    # may still appear in an explanatory comment).
    assert "\nlabels:" not in text


def test_repo_settings_enabled_by_full_preset(render: Callable[..., Path]) -> None:
    assert _settings(render(preset="full")).exists()
