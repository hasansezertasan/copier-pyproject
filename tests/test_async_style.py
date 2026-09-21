"""Rendered async-test runner configuration (issue #193)."""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("style", "dependency", "mode"),
    [
        ("none", None, None),
        ("asyncio", "pytest-asyncio>=0.23.0", "strict"),
        ("anyio", "anyio[trio]>=4.0", None),
    ],
)
def test_async_style_wires_only_its_test_dependency(
    render: Callable[..., Path], style: str, dependency: str | None, mode: str | None
) -> None:
    root = render(async_style=style)
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    test_dependencies = pyproject["dependency-groups"]["test"]
    pytest_options = pyproject["tool"]["pytest"]["ini_options"]

    assert ("pytest-asyncio>=0.23.0" in test_dependencies) is (
        dependency == "pytest-asyncio>=0.23.0"
    )
    assert ("anyio[trio]>=4.0" in test_dependencies) is (
        dependency == "anyio[trio]>=4.0"
    )
    assert pytest_options.get("asyncio_mode") == mode


def test_anyio_style_renders_both_backend_fixture_and_marker(
    render: Callable[..., Path],
) -> None:
    root = render(include_mcp=True, async_style="anyio")
    conftest = (root / "tests" / "conftest.py").read_text(encoding="utf-8")
    mcp_tests = (root / "tests" / "mcp" / "test_app.py").read_text(encoding="utf-8")

    assert 'params=["asyncio", "trio"]' in conftest
    assert "@pytest.mark.anyio" in mcp_tests


def test_anyio_style_pins_only_asyncio_native_component_tests(
    render: Callable[..., Path],
) -> None:
    root = render(include_tui=True, include_worker=True, async_style="anyio")
    worker_tests = (root / "tests" / "worker" / "test_app.py").read_text(
        encoding="utf-8"
    )
    tui_tests = (root / "tests" / "tui" / "test_app.py").read_text(
        encoding="utf-8"
    )
    integration_tests = (
        root / "tests" / "worker" / "test_integration.py"
    ).read_text(encoding="utf-8")

    conftest = (root / "tests" / "conftest.py").read_text(encoding="utf-8")

    backend_pin = 'pytest.mark.parametrize("anyio_backend", ["asyncio"])'
    assert worker_tests.count(backend_pin) == 4
    assert integration_tests.count(backend_pin) == 1
    assert tui_tests.count(backend_pin) == 1
    assert "anyio_backend" not in conftest


def test_async_components_default_to_asyncio_and_use_explicit_markers(
    render: Callable[..., Path],
) -> None:
    root = render(include_tui=True)
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    tui_tests = (root / "tests" / "tui" / "test_app.py").read_text(encoding="utf-8")

    assert "pytest-asyncio>=0.23.0" in pyproject["dependency-groups"]["test"]
    assert pyproject["tool"]["pytest"]["ini_options"]["asyncio_mode"] == "strict"
    assert "@pytest.mark.asyncio" in tui_tests


def test_anyio_library_omits_unused_service_and_empty_type_checking(
    render: Callable[..., Path],
) -> None:
    root = render(async_style="anyio")
    conftest = (root / "tests" / "conftest.py").read_text(encoding="utf-8")

    assert "service" not in conftest
    assert "anyio_backend" not in conftest
    assert "if TYPE_CHECKING:\n    import pytest" in conftest


def test_anyio_cli_omits_unused_backend_fixture(
    render: Callable[..., Path],
) -> None:
    root = render(include_cli=True, async_style="anyio")
    conftest = (root / "tests" / "conftest.py").read_text(encoding="utf-8")

    assert "anyio_backend" not in conftest
    assert "service" in conftest


@pytest.mark.parametrize(
    "component_kwargs",
    [
        {"include_tui": True},
        {"include_worker": True},
    ],
)
def test_anyio_shadowed_fixtures_omitted_from_conftest(
    render: Callable[..., Path], component_kwargs: dict[str, bool]
) -> None:
    root = render(async_style="anyio", **component_kwargs)
    conftest = (root / "tests" / "conftest.py").read_text(encoding="utf-8")

    assert "anyio_backend" not in conftest


@pytest.mark.parametrize(
    ("style", "expected_imports", "forbidden_imports", "has_smoke_test"),
    [
        ("none", [], ["anyio", "asyncio", "sniffio"], False),
        ("asyncio", ["import asyncio"], ["anyio", "sniffio"], True),
        ("anyio", ["import anyio.lowlevel", "import sniffio"], ["import asyncio"], True),
    ],
)
def test_web_async_style_imports_and_smoke_test(
    render: Callable[..., Path],
    style: str,
    expected_imports: list[str],
    forbidden_imports: list[str],
    has_smoke_test: bool,
) -> None:
    root = render(include_web=True, async_style=style)
    web_tests = (root / "tests" / "web" / "test_app.py").read_text(encoding="utf-8")

    for item in expected_imports:
        assert item in web_tests
    for item in forbidden_imports:
        assert item not in web_tests
    assert ("def test_async_test_runner_is_available" in web_tests) is has_smoke_test
