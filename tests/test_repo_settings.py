"""``include_repo_settings`` renders ``.github/settings.yml`` for the Settings App.

Guards Part A of the repo-settings-as-code design: the metadata file renders
only when the toggle is on, carries the substituted description/homepage/topics,
and never grows a ``labels:`` block (labels stay App-free in ``labels.yml``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest


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
    assert "allow_squash_merge: true" in text
    assert "allow_merge_commit: false" in text
    # No `repository_topics` answer → the `topics:` key is omitted so the App
    # leaves existing repository topics untouched.
    assert "topics:" not in text
    # Labels are NOT managed by the App (no top-level `labels:` key; the word
    # may still appear in an explanatory comment).
    assert "\nlabels:" not in text


def test_repo_settings_topics_from_answer(render: Callable[..., Path]) -> None:
    root = render(
        include_repo_settings=True,
        repository_topics="Data Science, ETL_Pipeline, python",
    )
    text = _settings(root).read_text(encoding="utf-8")
    assert "  topics:" in text
    # Each topic is lower-cased and space/underscore-hyphenated.
    assert '- "data-science"' in text
    assert '- "etl-pipeline"' in text
    assert '- "python"' in text


def test_repo_settings_enabled_by_full_preset(render: Callable[..., Path]) -> None:
    assert _settings(render(preset="full")).exists()


@pytest.mark.parametrize("include_repo_ruleset", [False, True])
def test_settings_installation_requires_enforced_owner_review(
    render: Callable[..., Path], include_repo_ruleset: bool
) -> None:
    """Both protection paths must enforce the safeguard before App installation."""
    root = render(include_repo_settings=True, include_repo_ruleset=include_repo_ruleset)
    guide = (root / "docs/maintaining/setup.rst").read_text(encoding="utf-8")
    settings_section = guide.split('Repository settings ("Settings" App)', 1)[1]
    assert settings_section.index("**[CHECK]** Prerequisite") < settings_section.index(
        "**[HUMAN]**"
    )
    assert "If the check fails or cannot be verified, defer installation" in guide
    if include_repo_ruleset:
        ruleset = json.loads((root / ".github/rulesets/main.json").read_text())
        review = next(
            rule for rule in ruleset["rules"] if rule["type"] == "pull_request"
        )
        assert review["parameters"]["require_code_owner_review"] is True
        assert "/rules/branches/main" in settings_section
    else:
        protection = json.loads(
            guide.split("<<'JSON'\n", 1)[1].split("\n   JSON", 1)[0]
        )
        assert (
            protection["required_pull_request_reviews"]["require_code_owner_reviews"]
            is True
        )
        assert "/branches/main/protection" in settings_section
