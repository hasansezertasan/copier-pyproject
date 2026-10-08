"""Generated hook coverage and generator-owned byte protection."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Callable

import pytest


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
@pytest.mark.parametrize("include_ai_rulez", [False, True])
def test_generated_hook_coverage(
    render: Callable[..., Path], preset: str, include_ai_rulez: bool
) -> None:
    root = render(preset=preset, include_ai_rulez=include_ai_rulez)
    config = tomllib.loads((root / "prek.toml").read_text(encoding="utf-8"))
    hooks = {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}
    expected = {
        "check-executables-have-shebangs",
        "check-symlinks",
        "fix-byte-order-marker",
        "mixed-line-ending",
        "check-xml",
        "check-github-actions",
        "check-github-workflows",
        "check-github-issue-forms",
        "check-github-issue-config",
        "check-renovate",
        "check-dependabot",
    }
    assert expected <= hooks.keys()
    assert config["default_stages"] == ["pre-commit", "pre-push"]
    assert "no-commit-to-branch" not in hooks
    assert "check-json5" not in hooks  # Not an ID in either pinned provider.
    assert "sqlfluff" not in hooks
    assert "djlint" not in hooks
    assert hooks["mixed-line-ending"]["args"] == ["--fix=auto"]
    assert hooks["check-renovate"]["additional_dependencies"] == ["pyjson5"]

    for identifier in ("fix-byte-order-marker", "mixed-line-ending"):
        exclusion = hooks[identifier]["exclude"]
        assert re.search(exclusion, ".gitignore")
        assert not re.search(exclusion, "src/package/__init__.py")
        assert not re.search(exclusion, "nested/.gitignore")
        assert bool(re.search(exclusion, ".continue/prompts/instructions.yaml")) == (
            include_ai_rulez
        )

    issue_config = hooks["check-github-issue-config"]["files"]
    for filename in ("config.yml", "config.yaml"):
        assert re.search(issue_config, f".github/ISSUE_TEMPLATE/{filename}")
    for filename in (
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        "config.yml",
        "nested/.github/ISSUE_TEMPLATE/config.yml",
    ):
        assert not re.search(issue_config, filename)

    for identifier in ("basedpyright", "slotscheck"):
        assert hooks[identifier]["language"] == "system"
        assert hooks[identifier]["entry"].startswith("uv run --locked --group style ")
        assert hooks[identifier]["pass_filenames"] is False
