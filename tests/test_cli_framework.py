"""``cli_framework`` choice: Typer adds a dependency; argparse is stdlib-only.

Both variants keep the same bare console command and the same ``version`` /
``info`` contract. The argparse variant also lets a framework-free CLI flip
``is_app`` on, which is what makes Homebrew/Scoop packaging reachable for an
otherwise library-shaped project.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Callable

PKG = "example"


def _pyproject(root: Path) -> dict[str, Any]:
    """Return the ``[project]`` table of the rendered pyproject.toml."""
    with (root / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]


def _cli_source(root: Path) -> str:
    """Return the rendered console-root app module source."""
    return (root / "src" / PKG / "cli" / "app.py").read_text(encoding="utf-8")


def test_typer_cli_declares_typer_dependency(render: Callable[..., Path]) -> None:
    root = render(preset="library", include_cli=True, cli_framework="typer")
    project = _pyproject(root)
    assert any(dep.startswith("typer") for dep in project["dependencies"])
    assert "import typer" in _cli_source(root)
    # The bare command is unchanged by the framework choice.
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}


def test_argparse_cli_has_no_typer_dependency(render: Callable[..., Path]) -> None:
    root = render(preset="library", include_cli=True, cli_framework="argparse")
    project = _pyproject(root)
    assert not any(dep.startswith("typer") for dep in project.get("dependencies", []))
    source = _cli_source(root)
    assert "import argparse" in source
    assert "import typer" not in source
    assert project["scripts"] == {PKG: f"{PKG}.__main__:main"}


def test_argparse_cli_unlocks_homebrew_packaging(
    render: Callable[..., Path],
) -> None:
    # The point of the feature: a framework-free CLI is still an app, so the
    # is_app-gated Homebrew toggle is reachable and its answer persists — with
    # no Typer dependency dragged in.
    root = render(
        preset="library",
        include_cli=True,
        cli_framework="argparse",
        include_homebrew=True,
    )
    assert (root / "docs" / "packaging" / "homebrew-tap").is_dir()
    project = _pyproject(root)
    assert not any(dep.startswith("typer") for dep in project.get("dependencies", []))


def test_argparse_multicomponent_root_has_subcommands_no_typer(
    render: Callable[..., Path],
) -> None:
    # With CLI + other components, the argparse root still dispatches each
    # non-primary component as a subcommand, and still pulls in no Typer.
    root = render(
        preset="library",
        include_cli=True,
        cli_framework="argparse",
        include_web=True,
        include_worker=True,
    )
    source = _cli_source(root)
    assert "import typer" not in source
    assert 'add_parser("web"' in source
    assert 'add_parser("worker"' in source
    project = _pyproject(root)
    assert not any(dep.startswith("typer") for dep in project.get("dependencies", []))
