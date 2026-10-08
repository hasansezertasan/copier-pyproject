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
