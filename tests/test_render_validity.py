"""Structural validity of the rendered output across presets and key toggles.

The cheapest guard against a Jinja mistake — a broken conditional, a
whitespace-control regression in a guarded block — emitting malformed YAML or
TOML in a *conditional* file that the single-preset ``example/`` regeneration
never exercises (issue #182). No installation of the generated project, so the
matrix stays fast.

``yaml`` is available in the render harness as a transitive dependency of
copier; ``tomllib`` is stdlib (3.11+).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Callable

import pytest
import yaml

PKG = "example"

# The four archetype presets (ADR-016) — the primary axis hand-regeneration
# misses, since ``.example-input.yml`` only ever renders ``library``.
PRESETS = ["library", "tool", "web", "full"]

# High-signal toggle combinations beyond the presets: one render per broker and
# one per web framework, so every conditional broker/framework branch is
# structurally validated without an exhaustive cross-product.
WORKER_BROKERS = ["kafka", "nats", "rabbitmq", "redis"]
WEB_FRAMEWORKS = ["fastapi", "litestar"]


def _iter_yaml_documents(path: Path) -> None:
    """Parse every YAML document in ``path``; raises on malformed YAML."""
    # ``safe_load_all`` is lazy — force it through ``list`` so multi-document
    # workflow files (``---`` separated) are fully parsed, not just opened.
    list(yaml.safe_load_all(path.read_text(encoding="utf-8")))


def _assert_all_yaml_parses(root: Path) -> None:
    yaml_files = [*root.rglob("*.yml"), *root.rglob("*.yaml")]
    # A render that emits no YAML at all would make this a green no-op; every
    # project ships at least the copier answers file and CI workflows.
    assert yaml_files, "render produced no YAML files to validate"
    for path in yaml_files:
        try:
            _iter_yaml_documents(path)
        except yaml.YAMLError as exc:  # pragma: no cover - failure detail
            pytest.fail(f"invalid YAML in {path.relative_to(root)}: {exc}")


def _assert_pyproject_is_toml(root: Path) -> None:
    tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_renders_pyproject(
    render: Callable[..., Path], preset: str
) -> None:
    root = render(preset=preset)
    assert root.is_dir()
    assert (root / "pyproject.toml").is_file()


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_yaml_is_parseable(
    render: Callable[..., Path], preset: str
) -> None:
    _assert_all_yaml_parses(render(preset=preset))


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_pyproject_is_valid_toml(
    render: Callable[..., Path], preset: str
) -> None:
    _assert_pyproject_is_toml(render(preset=preset))


@pytest.mark.parametrize("broker", WORKER_BROKERS)
def test_worker_broker_render_is_structurally_valid(
    render: Callable[..., Path], broker: str
) -> None:
    root = render(include_worker=True, worker_broker=broker)
    _assert_all_yaml_parses(root)
    _assert_pyproject_is_toml(root)


@pytest.mark.parametrize(
    ("broker", "expect_service"),
    [("redis", True), ("nats", True), ("kafka", False), ("rabbitmq", False)],
)
def test_worker_integration_uses_services_only_for_light_brokers(
    render: Callable[..., Path], broker: str, expect_service: bool
) -> None:
    """redis/nats get a GitHub Actions ``services:`` CI path; kafka/rabbitmq
    stay on testcontainers (issue #169). The env var the services path sets is
    the seam the integration fixture reads."""
    root = render(include_worker=True, worker_broker=broker)
    ci = yaml.safe_load(
        (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    job = ci["jobs"]["worker-integration"]
    env_var = {
        "redis": "REDIS_URL",
        "nats": "NATS_URL",
    }.get(broker)
    if expect_service:
        assert "services" in job, f"{broker} should use a services: container"
        assert env_var in job.get("env", {})
    else:
        assert "services" not in job, f"{broker} should stay on testcontainers"


@pytest.mark.parametrize("framework", WEB_FRAMEWORKS)
def test_web_framework_render_is_structurally_valid(
    render: Callable[..., Path], framework: str
) -> None:
    root = render(include_web=True, web_framework=framework)
    _assert_all_yaml_parses(root)
    _assert_pyproject_is_toml(root)


def test_docs_off_drops_sphinx_subsystem_but_keeps_setup_guide(
    render: Callable[..., Path],
) -> None:
    """``include_docs=false`` removes the Sphinx site + docs CI/deps but leaves
    the maintainer setup guide and a structurally valid project (ADR-025)."""
    root = render(include_docs=False)
    _assert_all_yaml_parses(root)
    _assert_pyproject_is_toml(root)

    # Sphinx-site files, docs workflows, and the docs dependency group are gone.
    assert not (root / "docs" / "conf.py").exists()
    assert not (root / "docs" / "index.rst").exists()
    wf = root / ".github" / "workflows"
    assert not (wf / "docs-preview.yml").exists()
    assert not (wf / "docs-linkcheck.yml").exists()
    assert not (wf / "gh-pages.yml").exists()
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert "docs" not in pyproject["dependency-groups"]
    tox_envs = pyproject["tool"]["tox"]["env"]
    assert not [name for name in tox_envs if name.startswith("docs-")]

    # No published-metadata reference to the (absent) Pages docs site.
    assert "documentation" not in pyproject["project"]["urls"]
    contributing = (root / ".github" / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "Improving The Documentation" not in contributing

    # The maintainer setup guide always ships; only its Pages step is gated.
    setup = root / "docs" / "maintaining" / "setup.rst"
    assert setup.is_file()
    assert "GitHub Pages" not in setup.read_text(encoding="utf-8")

    # The repo-setup skill drops its docs-only Pages/deploy-docs guidance.
    skill = (root / ".claude" / "skills" / "repo-setup" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "deploy-docs" not in skill
    assert "gh-pages" not in skill


def test_docs_off_omits_component_interface_pages(
    render: Callable[..., Path],
) -> None:
    """Docs-off drops the web/worker Sphinx interface pages (the compound
    ``include_docs and include_*`` filename branch) while the components render."""
    root = render(include_docs=False, include_web=True, include_worker=True)
    _assert_pyproject_is_toml(root)
    assert not (root / "docs" / "web-interface.rst").exists()
    assert not (root / "docs" / "worker-interface.rst").exists()
    # The components themselves are unaffected by include_docs.
    assert (root / "src" / PKG / "web").is_dir()
    assert (root / "src" / PKG / "worker").is_dir()


def test_docs_on_by_default_keeps_sphinx_subsystem(
    render: Callable[..., Path],
) -> None:
    """Docs are on by default (no override), rendering the Sphinx site, workflows,
    and the full Pages documentation URL — a regression guard if the default flips."""
    root = render()  # default preset (library) → include_docs defaults to true
    assert (root / "docs" / "conf.py").is_file()
    assert (root / ".github" / "workflows" / "docs-preview.yml").is_file()
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert "docs" in pyproject["dependency-groups"]
    assert (
        pyproject["project"]["urls"]["documentation"]
        == "https://octocat.github.io/example"
    )
