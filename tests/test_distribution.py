"""Opt-in Homebrew tap + Scoop bucket distribution (issue #146).

The generated project no longer renders/pushes the formula/manifest itself; it
fires a cross-repo ``repository_dispatch`` at the author's tap/bucket, which own
the manifest logic (the "keycast" pattern).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

PKG = "example"
USER = "octocat"


def _answers(root: Path) -> dict[str, Any]:
    text = (root / ".copier-answers.yml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _read(root: Path, *parts: str) -> str:
    return (root / Path(*parts)).read_text(encoding="utf-8")


# --- copier toggle behaviour -------------------------------------------------


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


# --- documentation ------------------------------------------------------------


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
    rst = _read(
        render(preset="tool", include_homebrew=True), "docs", "installation.rst"
    )
    assert f"brew install {USER}/tap/{PKG}" in rst


def test_readme_shows_brew_cask_when_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    readme = _read(root, "README.md")
    assert f"brew install --cask {USER}/tap/{PKG}" in readme


def test_installation_rst_shows_brew_cask_when_executable(
    render: Callable[..., Path],
) -> None:
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    rst = _read(root, "docs", "installation.rst")
    assert f"brew install --cask {USER}/tap/{PKG}" in rst


def test_setup_doc_documents_tap_setup(render: Callable[..., Path]) -> None:
    # Maintainer repository setup lives in docs/maintaining/setup.rst (not the
    # contributor-facing CONTRIBUTING.md); see ADR-022.
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    setup = _read(root, "docs", "maintaining", "setup.rst")
    assert "homebrew-tap" in setup
    assert "HOMEBREW_TAP_TOKEN" in setup
    assert "scoop-bucket" in setup
    assert "SCOOP_BUCKET_TOKEN" in setup


def test_setup_doc_omits_tap_setup_when_disabled(
    render: Callable[..., Path],
) -> None:
    setup = _read(render(preset="tool"), "docs", "maintaining", "setup.rst")
    assert "HOMEBREW_TAP_TOKEN" not in setup
    assert "SCOOP_BUCKET_TOKEN" not in setup


# --- producer: cross-repo dispatch jobs --------------------------------------


def test_bump_homebrew_formula_when_no_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True)  # no executable toggle
    text = _read(root, ".github", "workflows", "release.yml")
    wf = yaml.safe_load(text)
    job = wf["jobs"]["bump-homebrew"]
    assert "release-please" in job["needs"]
    assert "finalize-release" in job["needs"]
    assert "HOMEBREW_TAP_TOKEN" in text
    assert "event_type=update-formula" in text
    assert "event_type=update-cask" not in text
    assert f"{USER}/homebrew-tap/dispatches" in text


def test_bump_homebrew_cask_when_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    text = _read(root, ".github", "workflows", "release.yml")
    wf = yaml.safe_load(text)
    assert "bump-homebrew" in wf["jobs"]
    assert "event_type=update-cask" in text
    assert "event_type=update-formula" not in text


def test_release_omits_bump_homebrew_when_disabled(render: Callable[..., Path]) -> None:
    text = _read(render(preset="tool"), ".github", "workflows", "release.yml")
    assert "bump-homebrew" not in text


def test_bump_scoop_dispatches_manifest(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_scoop=True)
    text = _read(root, ".github", "workflows", "release.yml")
    wf = yaml.safe_load(text)
    job = wf["jobs"]["bump-scoop"]
    assert "release-please" in job["needs"]
    assert "finalize-release" in job["needs"]
    assert "SCOOP_BUCKET_TOKEN" in text
    assert "event_type=update-manifest" in text
    assert f"{USER}/scoop-bucket/dispatches" in text


def test_release_omits_bump_scoop_when_disabled(render: Callable[..., Path]) -> None:
    text = _read(render(preset="tool"), ".github", "workflows", "release.yml")
    assert "bump-scoop" not in text


def test_no_dispatch_jobs_or_packaging_when_disabled(
    render: Callable[..., Path],
) -> None:
    root = render(preset="tool")  # neither homebrew nor scoop
    text = _read(root, ".github", "workflows", "release.yml")
    assert "bump-homebrew" not in text
    assert "bump-scoop" not in text
    # The reference bundle renders under docs/packaging/, so that is the path
    # whose absence proves the toggles gated it out.
    assert not (root / "docs" / "packaging").exists()


def _assert_reports_failure(listener: Path) -> None:
    """A dispatch listener grants ``issues: write`` and has a Report failure step."""
    job = yaml.safe_load(listener.read_text(encoding="utf-8"))["jobs"]["update"]
    assert job["permissions"]["issues"] == "write"
    step_names = {step.get("name") for step in job["steps"]}
    assert "Report failure" in step_names
    # The failure step must retry without --label, or a fresh tap/bucket (which
    # has neither label yet) reports nothing — the labeled call would just fail.
    report = next(s for s in job["steps"] if s.get("name") == "Report failure")
    assert report["run"].count("gh issue create") >= 2


def test_packaging_bundle_renders_when_enabled(render: Callable[..., Path]) -> None:
    # Formula path (no executable toggle): homebrew ships the formula listener,
    # scoop ships the manifest listener; the cask listener is gated out.
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    pkg = root / "docs" / "packaging"
    assert (pkg / "homebrew-tap" / "README.md").is_file()
    formula = pkg / "homebrew-tap" / "update-formula-dispatch.yml"
    assert formula.is_file()
    assert not (pkg / "homebrew-tap" / "update-cask-dispatch.yml").exists()
    assert (pkg / "scoop-bucket" / "README.md").is_file()
    manifest = pkg / "scoop-bucket" / "update-manifest-dispatch.yml"
    assert manifest.is_file()
    # Both non-cask listeners surface dispatch failures as issues.
    _assert_reports_failure(formula)
    _assert_reports_failure(manifest)


def test_homebrew_ships_cask_listener_when_executable(
    render: Callable[..., Path],
) -> None:
    # Executable toggle flips the homebrew bundle to the cask listener.
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    tap = root / "docs" / "packaging" / "homebrew-tap"
    cask = tap / "update-cask-dispatch.yml"
    assert cask.is_file()
    assert not (tap / "update-formula-dispatch.yml").exists()
    _assert_reports_failure(cask)


# --- ghalint (reverted to web-only) ------------------------------------------


def test_ghalint_absent_without_web(render: Callable[..., Path]) -> None:
    # brew/scoop no longer need a ghalint exclusion; only web (docker) does.
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    assert not (root / ".github" / "ghalint.yaml").exists()


def test_ghalint_web_only_excludes_docker(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_web=True)
    ghalint = _read(root, ".github", "ghalint.yaml")
    assert "docker-publish" in ghalint
    assert "publish-homebrew" not in ghalint
    assert "publish-scoop" not in ghalint
    parsed = yaml.safe_load(ghalint)
    job_names = {entry["job_name"] for entry in parsed["excludes"]}
    assert job_names == {"docker-publish-preflight", "docker-publish"}
