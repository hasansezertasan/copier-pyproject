"""Markdown doctest configuration for rendered projects (issue #189)."""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

NESTED_README = "# Fixture notes\n\nIllustrative only:\n\n```pycon\n>>> 1 + 1\n3\n```\n"


def _pytest(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run pytest inside a rendered project, reading its own pyproject config.

    The package is not installed into the harness environment, so ``src`` goes
    on ``PYTHONPATH`` -- enough for the README's import example, and it keeps
    the rendered project's real ``addopts``/``testpaths`` in play.
    """
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=root,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )


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


def test_readme_doctest_actually_runs_and_passes(render: Callable[..., Path]) -> None:
    """Execute the rendered README, not just grep it.

    A broken import, a fence swallowed into the expected output, or a
    collection mismatch all look identical to a text assertion.
    """
    root = render(preset="library")

    result = _pytest(root, "README.md")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_markdown_under_tests_is_not_collected(render: Callable[..., Path]) -> None:
    """``--doctest-glob`` matches basenames, so ``tests/`` must opt out.

    Otherwise a fixture-directory README becomes a test the first time it
    contains a ``>>>`` line -- here a deliberately wrong one.
    """
    root = render(preset="library")
    nested = root / "tests" / "sub"
    nested.mkdir(parents=True)
    (nested / "README.md").write_text(NESTED_README, encoding="utf-8")
    (root / "tests" / "README.md").write_text(NESTED_README, encoding="utf-8")

    # Two ``-q`` cancel the rendered ``addopts`` ``-v`` and drop --collect-only
    # to bare node ids.
    result = _pytest(root, "--collect-only", "-q", "-q")

    collected = [line for line in result.stdout.splitlines() if "README.md" in line]
    assert collected == ["README.md::README.md"], result.stdout


def test_prek_pytest_hook_collects_the_readme(render: Callable[..., Path]) -> None:
    """An explicit ``pytest tests`` target would bypass the README testpath."""
    root = render(preset="library")
    prek = (root / "prek.toml").read_text(encoding="utf-8")

    assert 'entry = "uv run --locked pytest"' in prek
