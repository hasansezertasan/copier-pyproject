"""Optional PyPI publishing (``include_pypi_publish``, issue #382).

Rationale: context/package-distribution.md.

Off keeps releases on GitHub Releases only: no ``pypi-publish`` job, no PyPI
setup step, install docs that point at the Git repository, and no Homebrew /
Scoop tap that would install from PyPI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

PKG = "example"
USER = "octocat"
GIT_URL = f"git+https://github.com/{USER}/{PKG}"


def _answers(root: Path) -> dict[str, Any]:
    return yaml.safe_load((root / ".copier-answers.yml").read_text(encoding="utf-8"))


def _read(root: Path, *parts: str) -> str:
    return (root / Path(*parts)).read_text(encoding="utf-8")


def _release_jobs(root: Path) -> dict[str, Any]:
    workflow = yaml.safe_load(_read(root, ".github", "workflows", "release.yml"))
    return workflow["jobs"]


def _needs(job: dict[str, Any]) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


def _assert_needs_resolve(jobs: dict[str, Any]) -> None:
    """Every ``needs`` entry names a job that was rendered."""
    for name, job in jobs.items():
        missing = set(_needs(job)) - set(jobs)
        assert not missing, f"{name} needs unrendered job(s) {sorted(missing)}"


def _ancestors(jobs: dict[str, Any], name: str) -> set[str]:
    """Every job ``name`` waits for, directly or through another job."""
    seen: set[str] = set()
    stack = _needs(jobs[name])
    while stack:
        job = stack.pop()
        if job not in seen:
            seen.add(job)
            stack.extend(_needs(jobs[job]))
    return seen


def _assert_release_graph(jobs: dict[str, Any]) -> None:
    _assert_needs_resolve(jobs)
    # attach-github-release downloads build's artifacts, so it must wait for it.
    assert "build" in _ancestors(jobs, "attach-github-release")


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
def test_every_preset_publishes_to_pypi(
    render: Callable[..., Path], preset: str
) -> None:
    root = render(preset=preset)
    assert _answers(root)["include_pypi_publish"] is True
    jobs = _release_jobs(root)
    assert "pypi-publish" in jobs
    assert "pypi-publish" in _needs(jobs["attach-github-release"])
    assert "pypi-publish" in _needs(jobs["finalize-release"])
    _assert_release_graph(jobs)


def test_off_drops_the_publish_job_but_keeps_the_release(
    render: Callable[..., Path],
) -> None:
    # include_web exercises the docker-publish branch of finalize-release's needs.
    root = render(preset="web", include_pypi_publish=False)
    jobs = _release_jobs(root)
    assert "pypi-publish" not in jobs
    _assert_release_graph(jobs)
    assert _needs(jobs["finalize-release"]) == [
        "release-please",
        "attach-github-release",
        "docker-publish",
    ]
    # The build still mints attestations in the main-only publish environment,
    # and the distributions are still attached to the GitHub Release.
    assert jobs["build"]["environment"] == "publish"
    workflow = _read(root, ".github", "workflows", "release.yml")
    assert "gh-action-pypi-publish" not in workflow
    assert "pypi.org" not in workflow


def test_off_points_library_docs_at_the_git_repository(
    render: Callable[..., Path],
) -> None:
    # No executable either, so only build orders attach-github-release.
    root = render(preset="library", include_pypi_publish=False)
    _assert_release_graph(_release_jobs(root))
    readme = _read(root, "README.md")
    assert "pypi.org" not in readme
    assert "img.shields.io/pypi" not in readme
    assert "## Analysis" not in readme
    assert f"uv add {GIT_URL}" in readme
    assert f"pip install {GIT_URL}" in readme
    assert "publishes it to GitHub Releases only" in readme
    rst = _read(root, "docs", "installation.rst")
    assert f"uv add {GIT_URL}" in rst
    assert "PyPI publication attestations" not in rst


def test_off_drops_pypi_from_setup_material(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_pypi_publish=False)
    readme = _read(root, "README.md")
    assert f"uv tool install {GIT_URL}" in readme
    assert f"uvx --from {GIT_URL} {PKG}" in readme
    setup = _read(root, "REPOSITORY_SETUP.rst")
    assert "PyPI trusted publishing" not in setup
    assert "pending publisher" not in setup
    # The environment's branch policy still guards attestation minting.
    assert "Restrict the ``publish`` environment to ``main``" in setup
    skill = _read(root, ".claude", "skills", "repo-setup", "SKILL.md")
    assert "PyPI" not in skill
    assert "trusted publishing" not in _read(root, ".github", "CONTRIBUTING.md")


def test_off_without_executable_never_asks_for_homebrew_or_scoop(
    render: Callable[..., Path],
) -> None:
    # A formula and a pipx manifest install from PyPI, so with neither PyPI nor
    # an executable there is nothing for a tap or bucket to point at.
    root = render(
        preset="full",
        include_pypi_publish=False,
        include_freezer=False,
        include_compiler=False,
        include_launcher=False,
    )
    answers = _answers(root)
    assert "include_homebrew" not in answers
    assert "include_scoop" not in answers
    assert not (root / "docs" / "packaging").exists()
    jobs = _release_jobs(root)
    assert "bump-homebrew" not in jobs
    assert "bump-scoop" not in jobs


def test_off_with_executable_keeps_homebrew_and_scoop(
    render: Callable[..., Path],
) -> None:
    # A cask / binary manifest is fetched from the GitHub Release instead.
    root = render(preset="full", include_pypi_publish=False)
    answers = _answers(root)
    assert answers["include_homebrew"] is True
    assert answers["include_scoop"] is True
    release = _read(root, ".github", "workflows", "release.yml")
    assert "event_type=update-cask" in release
    assert "event_type=update-formula" not in release
    assert "bump-scoop" in release
