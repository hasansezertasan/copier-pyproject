"""Generated hook coverage and sealed-file byte protection."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Callable

import pytest


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
def test_generated_hook_coverage(
    render: Callable[..., Path], preset: str
) -> None:
    root = render(preset=preset)
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
    assert config["default_stages"] == ["pre-commit"]
    assert hooks["pip-audit"]["stages"] == ["pre-push"]
    assert "uvx pip-audit" in hooks["pip-audit"]["entry"]
    assert "ruff-check" in hooks
    assert "ruff" not in hooks  # Legacy alias upstream.
    assert "no-commit-to-branch" not in hooks
    assert "check-json5" not in hooks  # Not an ID in either pinned provider.
    repos = {repo["repo"] for repo in config["repos"]}
    assert "https://github.com/pre-commit/mirrors-mypy" not in repos
    assert hooks["mypy"]["entry"] == "uv run --locked --group style mypy"
    assert hooks["mypy"]["pass_filenames"] is False
    assert "sqlfluff" not in hooks
    assert "djlint" not in hooks
    assert hooks["mixed-line-ending"]["args"] == ["--fix=auto"]
    assert hooks["check-renovate"]["additional_dependencies"] == ["pyjson5"]
    for filename in ("script.ps1", "module.psm1", "data.psd1", "SCRIPT.PS1"):
        assert re.search(hooks["fix-byte-order-marker"]["exclude"], filename)
    assert not re.search(hooks["fix-byte-order-marker"]["exclude"], "notes.ps1.txt")

    for identifier in ("fix-byte-order-marker", "mixed-line-ending"):
        exclusion = hooks[identifier]["exclude"]
        assert re.search(exclusion, ".gitignore")
        assert not re.search(exclusion, "src/package/__init__.py")
        assert not re.search(exclusion, "nested/.gitignore")

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
