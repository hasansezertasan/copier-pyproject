"""Delivery of the adoption audit skill through both instruction hosts."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
import yaml


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
@pytest.mark.parametrize("include_ai_rulez", [False, True])
def test_adoption_skill_delivery(
    render: Callable[..., Path], preset: str, include_ai_rulez: bool
) -> None:
    root = render(preset=preset, include_ai_rulez=include_ai_rulez)
    host = ".ai-rulez" if include_ai_rulez else ".claude"
    skill = root / host / "skills" / "template-adoption" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["name"] == "template-adoption"
    assert isinstance(frontmatter["description"], str)
    assert frontmatter["description"]
    assert "{%" not in text
    assert "{{" not in text
    for requirement in (
        "Lost check coverage",
        "retained, replaced, missing",
        "feedback timing",
        "positive/negative file matches",
        "Ruff S and SAST overlap Bandit",
        "cobo-managed `.gitignore`",
        "Ask before removing a check",
        "per-check coverage classifications",
        "Manifest parity (`pyproject.toml`)",
        "a lower rendered pin is a downgrade",
        "Trim template leftovers",
        "manifest-parity map",
        "renovate#31600",
        "release-please-manifest.json",
        "Keeping template version",
        "Initial adoption hazards",
        "ruff check --diff",
        "src/example/__init__.py",
        "TODO @octocat:",
        "example==0.1.0",
        "https://github.com/hasansezertasan/copier-pyproject.git",
    ):
        assert requirement in text
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert f"(./{host}/skills/template-adoption/SKILL.md)" in readme
    assert (root / host / "skills" / "repo-setup" / "SKILL.md").is_file()
    for other in {".claude", ".ai-rulez", ".codex", ".github"} - {host}:
        assert not (root / other / "skills" / "template-adoption").exists()


def test_docs_free_skill_parity(render: Callable[..., Path]) -> None:
    off = render(include_docs=False, include_ai_rulez=False)
    on = render(include_docs=False, include_ai_rulez=True)
    suffix = Path("skills/template-adoption/SKILL.md")
    assert (off / ".claude" / suffix).read_bytes() == (
        on / ".ai-rulez" / suffix
    ).read_bytes()
    # The only setup guide referenced by the skill ships even without Sphinx.
    assert (off / "docs/maintaining/setup.rst").is_file()
    assert (on / "docs/maintaining/setup.rst").is_file()


@pytest.mark.parametrize("include_docs", [False, True])
@pytest.mark.parametrize("include_megalinter", [False, True])
def test_initial_hazards_follow_answers(
    render: Callable[..., Path], include_docs: bool, include_megalinter: bool
) -> None:
    root = render(
        github_repo_name="custom_pkg",
        github_user="maintainer",
        include_docs=include_docs,
        include_megalinter=include_megalinter,
    )
    text = (root / ".claude/skills/template-adoption/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "src/custom_pkg/__init__.py" in text
    assert "TODO @maintainer:" in text
    assert "custom_pkg==0.1.0" in text
    assert ("Docs collide too" in text) is include_docs
    assert ("MegaLinter's cspell" in text) is include_megalinter


@pytest.mark.parametrize("include_ai_rulez", [False, True])
def test_copy_message_routes_before_tools(
    render: Callable[..., Path],
    capsys: pytest.CaptureFixture[str],
    include_ai_rulez: bool,
) -> None:
    render(include_ai_rulez=include_ai_rulez, quiet=False)
    captured = capsys.readouterr()
    message = captured.out + captured.err
    host = ".ai-rulez" if include_ai_rulez else ".claude"
    assert f"Read {host}/skills/template-adoption/SKILL.md" in message
    assert "repo-setup" in message
    assert "docs/maintaining/setup.rst" in message
    assert message.index("Before running tools") < message.index("uv sync")
