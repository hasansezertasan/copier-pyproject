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


@pytest.mark.parametrize("framework", WEB_FRAMEWORKS)
def test_web_framework_render_is_structurally_valid(
    render: Callable[..., Path], framework: str
) -> None:
    root = render(include_web=True, web_framework=framework)
    _assert_all_yaml_parses(root)
    _assert_pyproject_is_toml(root)
