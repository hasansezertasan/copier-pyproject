"""Golden-file snapshots for the highest-value rendered artifacts (issue #182).

An unintended change to a core rendered file (a stray Jinja edit, a
whitespace-control regression, a reordered dependency block) becomes a
reviewable diff here instead of silent drift. Scoped deliberately to a *few*
stable artifacts — the rendered ``pyproject.toml`` for the ``library`` and
``full`` presets, the two extremes of the toggle space — so the snapshots stay
signal, not churn.

Snapshots live in ``tests/test_golden_files/`` and are regenerated with::

    uv run --with pytest --with pytest-regressions --with copier \\
        pytest tests/test_golden_files.py --force-regen

or via ``mise run test-golden-update``. Review the resulting diff before
committing — a legitimate template change updates the golden; an unexpected one
is the regression this suite exists to catch.

``file_regression`` comes from ``pytest-regressions``; the render harness
installs it alongside ``pytest`` (see ``.github/workflows/template-ci.yml``).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pytest_regressions.file_regression import FileRegressionFixture


def _check_pyproject(
    render: Callable[..., Path],
    file_regression: FileRegressionFixture,
    *,
    preset: str,
) -> None:
    root = render(preset=preset)
    file_regression.check(
        (root / "pyproject.toml").read_text(encoding="utf-8"),
        extension=".toml",
        basename=f"pyproject_{preset}",
    )


def test_pyproject_snapshot_library(
    render: Callable[..., Path],
    file_regression: FileRegressionFixture,
) -> None:
    _check_pyproject(render, file_regression, preset="library")


def test_pyproject_snapshot_full(
    render: Callable[..., Path],
    file_regression: FileRegressionFixture,
) -> None:
    _check_pyproject(render, file_regression, preset="full")
