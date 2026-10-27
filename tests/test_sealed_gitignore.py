"""The cobo-sealed ``.gitignore`` is copied verbatim, never rendered.

Jinja's lexer rewrites a lone carriage return to a line feed, so a ``.jinja``
suffix on the sealed file split the macOS ``Icon[<CR>]`` class in two and made
``cobo check`` report the block as locally modified in every generated project
(context/gitignore-generation.md).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

TEMPLATE_GITIGNORE = Path(__file__).parent.parent / "template" / ".gitignore"
SEALED_CR_PATTERNS = (b"Icon[\r]", b".HFS+ Private Directory Data[\r]")


def test_template_gitignore_is_a_plain_file() -> None:
    """No ``.jinja`` suffix and no Jinja syntax: copier copies it byte for byte."""
    source = TEMPLATE_GITIGNORE.read_bytes()
    assert b"{{" not in source
    assert b"{%" not in source
    assert not TEMPLATE_GITIGNORE.with_name(".gitignore.jinja").exists()


def test_render_keeps_the_sealed_lone_carriage_returns(
    render: Callable[..., Path],
) -> None:
    rendered = (render() / ".gitignore").read_bytes()
    assert rendered.count(b"\r") == 2
    for pattern in SEALED_CR_PATTERNS:
        assert pattern in rendered


def test_render_is_the_template_file_unchanged(render: Callable[..., Path]) -> None:
    for preset in ("library", "full"):
        rendered = (render(preset=preset) / ".gitignore").read_bytes()
        assert rendered == TEMPLATE_GITIGNORE.read_bytes()


def test_template_ignore_does_not_hide_template_sources(
    render: Callable[..., Path],
) -> None:
    """The file doubles as a live ignore for ``template/``; negations rescue.

    Without them the sealed Node ``.env.*`` and ``.vscode/*`` rules silently drop
    ``.env.example`` and the ``.vscode`` configs from fresh renders. The rescues
    name those files exactly rather than ``!*.jinja``, which would also make a
    stray ``.env.production.jinja`` trackable in a generated project.
    """
    root = render(preset="full")
    assert (root / ".env.example").is_file()
    assert (root / ".vscode" / "extensions.json").is_file()
    assert "!*.jinja" not in TEMPLATE_GITIGNORE.read_text(encoding="utf-8")


def test_no_tracked_template_file_is_ignored() -> None:
    """A new collision shows up here instead of as a file missing from renders."""
    ignored = subprocess.run(
        ["git", "ls-files", "-ci", "--exclude-standard", "template"],
        cwd=TEMPLATE_GITIGNORE.parents[1],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert ignored == []
