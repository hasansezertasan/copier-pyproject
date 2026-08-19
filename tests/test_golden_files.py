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


def _extract_job(workflow: str, job: str) -> str:
    """Return the text of one job block from a rendered workflow.

    Slices from the job key to the next top-level job key, so the snapshot keeps
    the block's comments — the rationale for the ``services:`` shape is written
    in comments, and a reviewer needs those in the diff.
    """
    lines = workflow.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith(f"  {job}:"))
    end = next(
        (
            i
            for i, line in enumerate(lines[start + 1 :], start=start + 1)
            # A sibling job key: exactly two spaces of indent, then content.
            if line.startswith("  ")
            and not line.startswith("   ")
            and line.strip()
        ),
        len(lines),
    )
    return "".join(lines[start:end])


def test_worker_integration_job_snapshot_redis(
    render: Callable[..., Path],
    file_regression: FileRegressionFixture,
) -> None:
    """Snapshot the ``services:``-backed worker integration job (issue #169).

    The ``full`` preset renders a kafka worker, so without this the whole
    ``services:`` path — the CI mechanism for redis/nats — is unsnapshotted.
    Scoped to the one job rather than all of ``ci.yml`` to keep the golden signal
    rather than churn.
    """
    root = render(include_worker=True, worker_broker="redis")
    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    file_regression.check(
        _extract_job(workflow, "worker-integration"),
        extension=".yml",
        basename="ci_worker_integration_redis",
    )
