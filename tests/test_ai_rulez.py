"""The ai-rulez agent-instruction shape (``include_ai_rulez``, ADR-035).

Two things need guarding, and they pull in opposite directions:

* With the toggle **off** nothing may change — the hand-written ``AGENTS.md`` /
  ``CLAUDE.md`` pair and the Claude-only ``repo-setup`` skill still render.
* With it **on** the template must render the ``.ai-rulez/`` sources and *no*
  generated output: those files are written by ``ai-rulez generate`` in the
  adopter's repository, so a template that also rendered them would put two
  writers on one path (ADR-035 §2).

The harness renders and inspects; it never runs ``ai-rulez`` itself (that needs
the binary and a network fetch — ``template-ci.yml``'s ``ai-rulez`` scenario
covers the generate-and-converge half, ADR-024).
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Callable

import pytest

PKG = "example"
CONFIG = ".ai-rulez/config.toml"
SOURCES = (
    ".ai-rulez/config.toml",
    ".ai-rulez/context/commands.md",
    ".ai-rulez/context/references.md",
    ".ai-rulez/rules/package-structure.md",
    ".ai-rulez/rules/project-conventions.md",
    ".ai-rulez/rules/pull-requests.md",
    ".ai-rulez/skills/repo-setup/SKILL.md",
)
# Everything `ai-rulez generate` writes for the default preset set. None of it
# may come from the template.
GENERATED = (
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    ".claude/skills/repo-setup/SKILL.md",
    ".codex/skills/repo-setup/SKILL.md",
    ".github/skills/repo-setup/SKILL.md",
    # Written *inside* the source tree, and still `generate`'s output: it is the
    # record `ai-rulez clean` reads to retire the host files (ADR-035 §8).
    ".ai-rulez/.generated-manifest.json",
)
# Paths whose bytes ai-rulez owns and whose linters must therefore skip them —
# a violation there is unfixable, since the next `generate` erases the fix.
# Keyed by the host that produces the path (ADR-035 §7).
GENERATOR_OWNED = {
    "cursor": "\\.mdc$",
    "continue-dev": "\\.continue/prompts/",
}


def _config(root: Path) -> dict[str, object]:
    with (root / CONFIG).open("rb") as fh:
        return tomllib.load(fh)


def _body(source: Path) -> str:
    """A rule/context source's prose: frontmatter and its own H1 stripped.

    What is left is exactly what the macro in ``_macros.jinja`` emitted, which
    is what the parity test below compares against ``AGENTS.md``.
    """
    text = source.read_text(encoding="utf-8")
    _, _, after_frontmatter = text.partition("---\n")[2].partition("---\n")
    heading, _, body = after_frontmatter.strip().partition("\n")
    assert heading.startswith("# "), f"{source} must open with an H1"
    return body.strip()


def _agents_section(root: Path, heading: str) -> str:
    """One ``## `` section body of a rendered ``AGENTS.md``."""
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    _, _, rest = text.partition(f"## {heading}\n")
    assert rest, f"AGENTS.md has no '## {heading}' section"
    return rest.partition("\n## ")[0].strip()


def test_default_keeps_the_hand_written_agent_files(render: Callable[..., Path]) -> None:
    root = render()
    assert (root / "AGENTS.md").is_file()
    assert (root / "CLAUDE.md").is_file()
    assert (root / ".claude" / "skills" / "repo-setup" / "SKILL.md").is_file()
    assert not (root / ".ai-rulez").exists()


def test_toggle_renders_sources_and_no_generated_output(
    render: Callable[..., Path],
) -> None:
    root = render(include_ai_rulez=True)
    for source in SOURCES:
        assert (root / source).is_file(), f"{source} not rendered"
    for generated in GENERATED:
        assert not (root / generated).exists(), (
            f"{generated} is ai-rulez output — the template must not render it"
        )


def test_skill_moves_rather_than_duplicating(render: Callable[..., Path]) -> None:
    """The skill has one copy either way: its *path* is what the toggle picks."""
    off = render(include_ai_rulez=False)
    on = render(include_ai_rulez=True)
    claude_only = off / ".claude" / "skills" / "repo-setup" / "SKILL.md"
    every_host = on / ".ai-rulez" / "skills" / "repo-setup" / "SKILL.md"
    assert claude_only.read_text(encoding="utf-8") == every_host.read_text(
        encoding="utf-8"
    )
    assert not (on / ".claude").exists()


def test_config_is_pinned_to_the_posture_the_adr_argues(
    render: Callable[..., Path],
) -> None:
    config = _config(render(include_ai_rulez=True))
    assert config["name"] == PKG
    assert config["version"] == "4.0"
    # cobo owns .gitignore (ADR-012): ai-rulez rewriting it breaks the sha256
    # fence and would hide the files GitHub has to read from the repository.
    assert config["gitignore"] is False
    # Every builtin domain restates or contradicts a CI-enforced gate (ADR-035).
    assert config["builtins"] is False
    assert config["presets"] == ["claude", "codex", "copilot"]
    assert config["header"] == {"timestamp": False}


def test_presets_answer_drives_the_generated_host_set(
    render: Callable[..., Path],
) -> None:
    config = _config(render(include_ai_rulez=True, ai_rulez_presets=["cursor", "amp"]))
    assert config["presets"] == ["cursor", "amp"]


def test_no_host_selected_is_rejected(render: Callable[..., Path]) -> None:
    """Empty presets render a config ai-rulez itself refuses to load.

    Its ``validatePresets`` errors with "at least one preset is required", so
    both ``ai-rulez generate`` and the tox ``style`` env's ``ai-rulez validate``
    would fail from the first run. The prompt-time validator moves that failure
    to the one moment the answer can still be changed.
    """
    with pytest.raises(ValueError, match="Pick at least one host"):
        render(include_ai_rulez=True, ai_rulez_presets=[])


def test_free_text_answers_are_escaped_into_the_config(
    render: Callable[..., Path],
) -> None:
    """A quote or a backslash in the description must not break the TOML.

    Without ``to_json`` the render still "succeeds" and leaves a config no
    parser accepts — the failure only surfaces when an agent tool reads it.
    """
    description = 'A "quoted" \\ backslashed ünïcode description'
    config = _config(render(include_ai_rulez=True, short_description=description))
    assert config["description"] == description


def test_rule_bodies_are_the_same_prose_as_agents_md(
    render: Callable[..., Path],
) -> None:
    """The macro guarantee (ADR-035 §1): one source, two renderings.

    Rendered with a console root and a sibling interface so the conditional
    table rows and both layering paragraphs are covered, not just the bare
    library shape.
    """
    answers = {"include_cli": True, "include_mcp": True}
    hand_written = render(include_ai_rulez=False, **answers)
    sources = render(include_ai_rulez=True, **answers)

    for heading, source in (
        ("Package Structure", "rules/package-structure.md"),
        ("Key Conventions", "rules/project-conventions.md"),
        ("Pull Requests", "rules/pull-requests.md"),
        ("External References", "context/references.md"),
    ):
        assert _body(sources / ".ai-rulez" / source) == _agents_section(
            hand_written, heading
        ), f"{source} drifted from AGENTS.md's '{heading}' section"


def test_toolchain_is_wired_for_both_gates(render: Callable[..., Path]) -> None:
    root = render(include_ai_rulez=True)
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    with (root / "pyproject.toml").open("rb") as fh:
        parsed = tomllib.load(fh)

    # One version source, in a group `dev` does not drag in (ADR-035 §5).
    assert parsed["dependency-groups"]["agents"] == ["ai-rulez==4.11.5"]
    assert "agents" in parsed["tool"]["tox"]["env"]["style"]["dependency_groups"]
    assert ["ai-rulez", "validate"] in parsed["tool"]["tox"]["env"]["style"]["commands"]
    # ... and the fixing hook that regenerates the output.
    prek = (root / "prek.toml").read_text(encoding="utf-8")
    assert 'id = "ai-rulez"' in prek
    assert "uv run --locked --group agents ai-rulez generate" in prek
    # The import-linter comment points at the source, not at a file that only
    # exists after a generate.
    assert ".ai-rulez/rules/package-structure.md" in pyproject


def test_answers_file_stays_lint_clean_with_a_list_answer(
    render: Callable[..., Path],
) -> None:
    """``ai_rulez_presets`` is the template's first list-valued answer.

    Copier writes block sequences unindented, which yamllint's `indentation`
    rule rejects — and the file says NEVER EDIT MANUALLY, so the only "fix"
    would be overwritten by the next `copier update`. The hook must therefore
    skip it, exactly as the yamlfmt hook already does.
    """
    root = render(include_ai_rulez=True)
    answers = (root / ".copier-answers.yml").read_text(encoding="utf-8")
    assert "ai_rulez_presets:\n- claude\n" in answers

    prek = (root / "prek.toml").read_text(encoding="utf-8")
    for hook in ("yamllint", "yamlfmt"):
        line = next(ln for ln in prek.splitlines() if f'id = "{hook}"' in ln)
        assert re.search(r"exclude = \"[^\"]*copier-answers[^\"]*\"", line), (
            f"the {hook} hook must skip the copier-owned answers file"
        )


def test_generator_owned_paths_are_skipped_by_the_linters(
    render: Callable[..., Path],
) -> None:
    """ai-rulez owns some bytes its own project's linters would reject.

    ``cursor`` writes ``.mdc`` (markdown, whose list continuations fail ec's
    indent check) and ``continue-dev`` writes YAML whose generated header
    carries trailing spaces. A *fixing* hook there never converges and a
    *checking* one is unfixable, because the next ``generate`` erases the edit —
    the same bind ``.copier-answers.yml`` is in, so it gets the same answer
    (ADR-035 §7).
    """
    root = render(include_ai_rulez=True)
    prek = (root / "prek.toml").read_text(encoding="utf-8")
    for hook in ("trailing-whitespace", "yamllint", "yamlfmt"):
        line = next(ln for ln in prek.splitlines() if f'id = "{hook}"' in ln)
        assert GENERATOR_OWNED["continue-dev"].replace("\\", "") in line.replace(
            "\\", ""
        ), f"the {hook} hook must skip the ai-rulez-owned .continue/prompts/"

    ec_exclude = json.loads(
        (root / ".editorconfig-checker.json").read_text(encoding="utf-8")
    )["Exclude"]
    for pattern in GENERATOR_OWNED.values():
        assert any(pattern in entry for entry in ec_exclude), (
            f"editorconfig-checker must skip {pattern}"
        )


def test_generator_owned_skips_are_absent_when_the_toggle_is_off(
    render: Callable[..., Path],
) -> None:
    """They are toggle-gated, so the off render stays byte-identical."""
    root = render(include_ai_rulez=False)
    for path in ("prek.toml", ".editorconfig-checker.json"):
        text = (root / path).read_text(encoding="utf-8")
        assert ".continue/prompts" not in text
        assert "mdc" not in text


def test_ci_fails_when_generated_output_was_never_committed(
    render: Callable[..., Path],
) -> None:
    """A fixing hook passes on *untracked* output; this gate is what does not."""
    workflow = (
        render(include_ai_rulez=True) / ".github" / "workflows" / "ci.yml"
    ).read_text(encoding="utf-8")
    assert "--untracked-files=all" in workflow
    assert "ai-rulez generate" in workflow


def test_nothing_is_wired_when_the_toggle_is_off(render: Callable[..., Path]) -> None:
    root = render(include_ai_rulez=False)
    for path in ("pyproject.toml", "prek.toml", ".github/workflows/ci.yml"):
        assert "ai-rulez" not in (root / path).read_text(encoding="utf-8"), (
            f"{path} carries ai-rulez wiring with the toggle off"
        )
