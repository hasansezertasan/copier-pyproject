"""Adoption and update guidance lives in ``REPOSITORY_SETUP.rst``, not a skill.

Generated projects also carry no copier or template provenance outside the
answers file, the README and the setup guide.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import pytest
import yaml

# Root files that may say how the project was generated.
_ALLOWED = {
    Path(".copier-answers.yml"),
    Path("README.md"),
    Path("REPOSITORY_SETUP.rst"),
}
# The answers file's name is referenced by tool configs that must exclude it.
_ANSWERS_FILE = re.compile(r"\.copier-answers\.yml")
_PROVENANCE = re.compile(
    r"copier|scaffolded (?:from|by|at|with)|scaffold time|this template"
    r"|template update|hasansezertasan\.github\.io",
    re.IGNORECASE,
)


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
def test_no_skills_ship(render: Callable[..., Path], preset: str) -> None:
    root = render(preset=preset)
    for host in (".claude", ".ai-rulez", ".codex", ".github", ".agents"):
        assert not (root / host / "skills").exists()


@pytest.mark.parametrize("include_docs", [False, True])
@pytest.mark.parametrize("include_megalinter", [False, True])
def test_adoption_hazards_follow_answers(
    render: Callable[..., Path], include_docs: bool, include_megalinter: bool
) -> None:
    root = render(
        github_repo_name="custom_pkg",
        github_user="maintainer",
        include_docs=include_docs,
        include_megalinter=include_megalinter,
    )
    text = (root / "REPOSITORY_SETUP.rst").read_text(encoding="utf-8")
    for requirement in (
        "Adopting into an existing project",
        "ruff check --diff",
        "src/custom_pkg/__init__.py",
        "TODO @maintainer:",
        "custom_pkg==0.1.0",
        "release-please-manifest.json",
        "Keeping template version",
        "renovate#31600",
        "Lost check coverage",
        "Manifest parity",
        "https://github.com/hasansezertasan/copier-pyproject.git",
    ):
        assert requirement in text
    assert ("Docs collide too" in text) is include_docs
    assert ("MegaLinter's cspell" in text) is include_megalinter


def test_copy_message_routes_before_tools(
    render: Callable[..., Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    render(quiet=False)
    captured = capsys.readouterr()
    message = captured.out + captured.err
    assert "Adopting into an existing project" in message
    assert "template-adoption" not in message
    assert "repo-setup" not in message
    assert "REPOSITORY_SETUP.rst" in message
    assert message.index("Before running tools") < message.index("uv sync")


@pytest.mark.parametrize(
    "data",
    [
        {
            "preset": "full",
            "include_freezer": True,
            "include_megalinter": True,
            "include_sonarcloud": True,
            "include_all_contributors": True,
        },
        {
            "preset": "full",
            "include_docs": False,
            "include_sourcery": True,
        },
        {"preset": "library"},
        {
            "preset": "tool",
            "include_launcher": True,
            "include_compiler": True,
            "include_homebrew": True,
            "include_scoop": True,
            "include_repo_settings": True,
            "include_repo_ruleset": True,
        },
        {"preset": "web", "include_megalinter": True, "include_smokeshow": True},
    ],
    ids=["full-extras", "full-no-docs", "library", "tool-exe", "web"],
)
def test_no_copier_provenance_outside_allowed_files(
    render: Callable[..., Path], data: dict[str, object]
) -> None:
    root = render(**data)
    offenders: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or rel in _ALLOWED or rel.name == "uv.lock":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        text = _ANSWERS_FILE.sub("", re.sub(r"\\+\.", ".", text))
        offenders.extend(
            f"{rel}:{number}: {line.strip()[:100]}"
            for number, line in enumerate(text.splitlines(), 1)
            if _PROVENANCE.search(line)
        )
    assert offenders == []
