"""Markdown doctest configuration for rendered projects (issue #189)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import tomllib


def test_readme_is_the_only_markdown_doctest_target(
    render: Callable[..., Path],
) -> None:
    root = render(preset="library")
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_config = pyproject["tool"]["pytest"]["ini_options"]

    assert pytest_config["testpaths"] == ["tests", "README.md"]
    assert "--doctest-glob=README.md" in pytest_config["addopts"]
    assert pytest_config["doctest_optionflags"] == (
        "ELLIPSIS IGNORE_EXCEPTION_DETAIL NORMALIZE_WHITESPACE"
    )


def test_readme_ships_a_passing_doctest(render: Callable[..., Path]) -> None:
    readme = (render(preset="library") / "README.md").read_text(encoding="utf-8")

    assert "```pycon\n>>> from example import __doc__" in readme
    assert ">>> isinstance(__doc__, str)\nTrue" in readme
