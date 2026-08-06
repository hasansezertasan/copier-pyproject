"""Opt-in Homebrew tap + Scoop bucket distribution (issue #146)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

PKG = "example"
USER = "octocat"


def _answers(root: Path) -> dict[str, Any]:
    text = (root / ".copier-answers.yml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


def test_full_preset_enables_distribution(render: Callable[..., Path]) -> None:
    answers = _answers(render(preset="full"))
    assert answers["include_homebrew"] is True
    assert answers["include_scoop"] is True


def test_library_never_asks_distribution(render: Callable[..., Path]) -> None:
    # when: is_app is false for a library, so the toggles are never stored.
    answers = _answers(render(preset="library"))
    assert "include_homebrew" not in answers
    assert "include_scoop" not in answers


def test_app_defaults_distribution_off(render: Callable[..., Path]) -> None:
    answers = _answers(render(preset="tool"))  # cli+tui -> is_app true
    assert answers["include_homebrew"] is False
    assert answers["include_scoop"] is False


def _read(root: Path, *parts: str) -> str:
    return (root / Path(*parts)).read_text(encoding="utf-8")


def test_readme_shows_brew_and_scoop_when_enabled(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    readme = _read(root, "README.md")
    assert f"brew install {USER}/tap/{PKG}" in readme
    assert f"scoop install {USER}/{PKG}" in readme


def test_readme_omits_brew_and_scoop_when_disabled(render: Callable[..., Path]) -> None:
    readme = _read(render(preset="tool"), "README.md")
    assert "brew install" not in readme
    assert "scoop install" not in readme


def test_installation_rst_shows_brew_when_enabled(render: Callable[..., Path]) -> None:
    rst = _read(render(preset="tool", include_homebrew=True), "docs", "installation.rst")
    assert f"brew install {USER}/tap/{PKG}" in rst


def test_contributing_documents_tap_setup(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    contributing = _read(root, ".github", "CONTRIBUTING.md")
    assert "homebrew-tap" in contributing
    assert "HOMEBREW_TAP_TOKEN" in contributing
    assert "scoop-bucket" in contributing
    assert "SCOOP_BUCKET_TOKEN" in contributing


def test_contributing_omits_tap_setup_when_disabled(render: Callable[..., Path]) -> None:
    contributing = _read(render(preset="tool"), ".github", "CONTRIBUTING.md")
    assert "HOMEBREW_TAP_TOKEN" not in contributing
    assert "SCOOP_BUCKET_TOKEN" not in contributing


def test_homebrew_binary_formula_when_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    tmpl = _read(root, ".github", "packaging", "homebrew-formula.rb.tmpl")
    assert "@@SHA256_MACOS@@" in tmpl  # binary path
    assert f"{PKG}-freezer-macos" in tmpl  # primary_executable asset
    assert "virtualenv" not in tmpl.lower()


def test_homebrew_pypi_formula_when_no_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True)  # no executable toggle
    tmpl = _read(root, ".github", "packaging", "homebrew-formula.rb.tmpl")
    assert "@@SDIST_SHA256@@" in tmpl  # PyPI path
    assert 'pip", "install"' in tmpl or "pip install" in tmpl


def test_scoop_binary_manifest_when_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_scoop=True, include_compiler=True)
    tmpl = _read(root, ".github", "packaging", "scoop-manifest.json.tmpl")
    assert "@@SHA256_WIN@@" in tmpl
    assert f"{PKG}-compiler-windows.exe" in tmpl


def test_packaging_absent_when_disabled(render: Callable[..., Path]) -> None:
    root = render(preset="tool")
    assert not (root / ".github" / "packaging").exists()


def test_release_has_publish_homebrew_job(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    wf = yaml.safe_load(_read(root, ".github", "workflows", "release.yml"))
    job = wf["jobs"]["publish-homebrew"]
    assert "finalize-release" in job["needs"]
    # gated-on-secret presence flag
    text = _read(root, ".github", "workflows", "release.yml")
    assert "HOMEBREW_TAP_TOKEN_SET" in text
    assert "peter-evans/create-pull-request" in text
    # binary branch downloads the release assets, no PyPI fallback
    assert "gh release download" in text


def test_release_omits_publish_homebrew_when_disabled(
    render: Callable[..., Path],
) -> None:
    text = _read(render(preset="tool"), ".github", "workflows", "release.yml")
    assert "publish-homebrew" not in text


def test_publish_homebrew_pypi_branch(render: Callable[..., Path]) -> None:
    text = _read(
        render(preset="tool", include_homebrew=True),
        ".github",
        "workflows",
        "release.yml",
    )
    # PyPI JSON-API fallback (no executable toggle)
    assert "pypi.org/pypi" in text
    assert "@@SDIST_URL@@".replace("@@", "") in text
    assert "gh release download" not in text


def test_release_has_publish_scoop_job(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_scoop=True, include_compiler=True)
    wf = yaml.safe_load(_read(root, ".github", "workflows", "release.yml"))
    job = wf["jobs"]["publish-scoop"]
    assert "finalize-release" in job["needs"]
    text = _read(root, ".github", "workflows", "release.yml")
    assert "SCOOP_BUCKET_TOKEN_SET" in text or "SCOOP_BUCKET_TOKEN != ''" in text


def test_release_omits_publish_scoop_when_disabled(render: Callable[..., Path]) -> None:
    text = _read(render(preset="tool"), ".github", "workflows", "release.yml")
    assert "publish-scoop" not in text
