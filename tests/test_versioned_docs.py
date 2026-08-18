"""Versioned-docs + last-updated feature (ADR-027) render assertions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

GRANULARITIES = ["minor", "major", "full"]


def test_granularity_question_defaults_to_minor(render: Callable[..., Path]) -> None:
    root = render(include_docs=True)
    build_docs = root / "tools" / "build_docs.py"
    assert build_docs.exists()
    assert 'VERSION_GRANULARITY = "minor"' in build_docs.read_text(encoding="utf-8")


@pytest.mark.parametrize("granularity", GRANULARITIES)
def test_granularity_bakes_into_build_script(
    render: Callable[..., Path], granularity: str
) -> None:
    root = render(include_docs=True, docs_version_granularity=granularity)
    build_docs = (root / "tools" / "build_docs.py").read_text(encoding="utf-8")
    assert f'VERSION_GRANULARITY = "{granularity}"' in build_docs


def test_versions_json_is_gitignored(render: Callable[..., Path]) -> None:
    root = render(include_docs=True)
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    assert "docs/_static/versions.json" in gitignore


def test_no_build_script_without_docs(render: Callable[..., Path]) -> None:
    root = render(include_docs=False)
    assert not (root / "tools" / "build_docs.py").exists()


def test_build_script_is_valid_python(render: Callable[..., Path]) -> None:
    root = render(include_docs=True)
    script = root / "tools" / "build_docs.py"
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_build_script_has_core_symbols(render: Callable[..., Path]) -> None:
    text = (render(include_docs=True) / "tools" / "build_docs.py").read_text(
        encoding="utf-8"
    )
    for symbol in (
        "def slugify(",
        "def existing_versions(",
        "def pick_latest(",
        "def main(",
        "DOCS_BUILD_VERSION_SLUG",
    ):
        assert symbol in text, symbol
    assert "check_warnings" in text
    assert 'refresh" content="0; url=./latest/' in text  # root redirect


def test_conf_py_wires_switcher_and_last_updated(render: Callable[..., Path]) -> None:
    conf = (render(include_docs=True) / "docs" / "conf.py").read_text(encoding="utf-8")
    assert "sphinx_last_updated_by_git" in conf
    assert "versions.json" in conf
    assert "html_context" in conf
    assert "current_version" in conf


def test_docs_group_has_last_updated_dep(render: Callable[..., Path]) -> None:
    pyproject = (render(include_docs=True) / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "sphinx-last-updated-by-git" in pyproject


def test_release_deploy_docs_is_versioned(render: Callable[..., Path]) -> None:
    release = (
        render(include_docs=True) / ".github" / "workflows" / "release.yml"
    ).read_text(encoding="utf-8")
    assert "tools/build_docs.py" in release
    assert "folder: site" in release
    assert "clean-exclude: pr-preview/**" in release
    assert "DOCS_BUILD_VERSION:" in release


def test_manual_gh_pages_is_versioned(render: Callable[..., Path]) -> None:
    workflow = (
        render(include_docs=True) / ".github" / "workflows" / "gh-pages.yml"
    ).read_text(encoding="utf-8")
    assert "tools/build_docs.py" in workflow
    assert "folder: site" in workflow
    assert "DOCS_BUILD_VERSION" in workflow
