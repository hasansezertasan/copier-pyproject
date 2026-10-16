"""The opt-in ``include_database`` layer (Advanced Alchemy + Alembic).

Off by default (``library``/``tool``), on for ``web``/``full``; the backend only
changes the driver dependency and the default URL; and the layer cannot be
combined with the sync-only test style.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Callable

import pytest

PKG = "example"


def _pyproject(root: Path) -> dict[str, object]:
    return tomllib.loads((root / "pyproject.toml").read_text())


def _dependencies(root: Path) -> list[str]:
    project = _pyproject(root)["project"]
    assert isinstance(project, dict)
    return list(project["dependencies"])


def _layers(root: Path) -> list[str]:
    tool = _pyproject(root)["tool"]
    assert isinstance(tool, dict)
    return tool["importlinter"]["contracts"][0]["layers"]


@pytest.mark.parametrize("preset", ["library", "tool"])
def test_database_is_off_by_default(
    render: Callable[..., Path], preset: str
) -> None:
    root = render(preset=preset)

    assert not (root / "src" / PKG / "db").exists()
    assert not (root / "migrations").exists()
    assert not any("advanced-alchemy" in dep for dep in _dependencies(root))
    assert "db" not in _layers(root)


@pytest.mark.parametrize("preset", ["web", "full"])
def test_web_and_full_presets_enable_the_database(
    render: Callable[..., Path], preset: str
) -> None:
    root = render(preset=preset)

    assert (root / "src" / PKG / "db" / "models.py").is_file()
    assert (root / "migrations" / "env.py").is_file()
    assert (root / "tests" / "db" / "test_db.py").is_file()


@pytest.mark.parametrize(
    ("backend", "driver", "other"),
    [("sqlite", "aiosqlite", "asyncpg"), ("postgres", "asyncpg", "aiosqlite")],
)
def test_backend_selects_the_driver_and_default_url(
    render: Callable[..., Path], backend: str, driver: str, other: str
) -> None:
    root = render(preset="library", include_database=True, database_backend=backend)

    deps = " ".join(_dependencies(root))
    assert "advanced-alchemy" in deps
    assert driver in deps
    assert other not in deps
    config = (root / "src" / PKG / "core" / "config.py").read_text()
    assert f"{driver}" in config


def test_postgres_backend_keeps_sqlite_for_the_test_suite(
    render: Callable[..., Path],
) -> None:
    root = render(
        preset="library", include_database=True, database_backend="postgres"
    )

    project = _pyproject(root)
    groups = project["dependency-groups"]
    assert isinstance(groups, dict)
    assert any("aiosqlite" in dep for dep in groups["test"])


def test_db_is_its_own_layer_between_components_and_core(
    render: Callable[..., Path],
) -> None:
    layers = _layers(render(preset="web"))

    assert layers.index("db") == layers.index("core") - 1
    assert layers.index("db") > layers.index("web")


@pytest.mark.parametrize("framework", ["fastapi", "litestar"])
def test_web_plugin_is_wired_only_with_the_database(
    render: Callable[..., Path], framework: str
) -> None:
    with_db = render(
        preset="web", web_framework=framework, include_database=True
    )
    without_db = render(
        preset="web", web_framework=framework, include_database=False
    )

    assert "/health/db" in (with_db / "src" / PKG / "web" / "app.py").read_text()
    plain = (without_db / "src" / PKG / "web" / "app.py").read_text()
    assert "advanced_alchemy" not in plain
    # The no-database render must stay byte-identical to the pre-toggle shape:
    # no unused ``Depends`` import and two blank lines before a module-level app.
    assert "Depends" not in plain
    if framework == "litestar":
        assert "\n\n\napp = Litestar(" in plain


def test_database_works_without_the_web_component(
    render: Callable[..., Path],
) -> None:
    root = render(preset="library", include_database=True)

    config = (root / "src" / PKG / "db" / "config.py").read_text()
    assert "advanced_alchemy.extensions" not in config


def test_database_rejects_the_synchronous_test_style(
    render: Callable[..., Path],
) -> None:
    with pytest.raises(ValueError, match="async tests"):
        render(preset="library", include_database=True, async_style="none")


def test_alembic_tox_env_runs_the_advanced_alchemy_cli(
    render: Callable[..., Path],
) -> None:
    root = render(preset="library", include_database=True)

    tox = _pyproject(root)["tool"]["tox"]["env"]["alembic"]  # type: ignore[index]
    assert tox["commands"][0][:3] == [
        "alchemy",
        "--config",
        f"{PKG}.db.migrations.config",
    ]


def test_devcontainer_reaches_postgres_by_service_name(
    render: Callable[..., Path],
) -> None:
    """Inside the devcontainer ``127.0.0.1`` is the app, not the service."""
    compose = (
        render(
            preset="library",
            include_database=True,
            database_backend="postgres",
            include_postgres=True,
        )
        / ".devcontainer"
        / "docker-compose.yml"
    ).read_text()
    assert "EXAMPLE_DATABASE_URL" in compose
    assert "@postgres:5432" in compose


def test_devcontainer_leaves_sqlite_alone(render: Callable[..., Path]) -> None:
    compose = (
        render(
            preset="library",
            include_database=True,
            database_backend="sqlite",
            include_postgres=True,
        )
        / ".devcontainer"
        / "docker-compose.yml"
    ).read_text()
    assert "DATABASE_URL" not in compose
