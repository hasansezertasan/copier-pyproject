"""Render harness fixtures for the copier-pyproject template.

The rendering itself lives in ``tools/render.py`` — the single render
entrypoint every consumer shares (ADR-031). This module only wraps it in a
``tmp_path``-scoped fixture; it deliberately holds no ``copier`` call of its
own, so the harness, CI, the committed docs artifacts, and the authoring watch
loop cannot drift apart.

Note: ``tools.render.render`` renders from this repo's git tree at ``HEAD`` and
includes uncommitted working-tree changes (Copier emits a
``DirtyLocalWarning``), so the tests reflect the current working copy of
``copier.yml`` / ``template/``.
"""

from __future__ import annotations

from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pytest

from tools.render import IDENTITY, render as render_project

if TYPE_CHECKING:
    from typing import Any

__all__ = ["IDENTITY", "render"]


@pytest.fixture
def render(tmp_path: Path) -> Callable[..., Path]:
    """Return a ``render(**answers) -> Path`` helper.

    Extra keyword answers override the identity defaults and the preset-driven
    toggle defaults, e.g. ``render(preset="full")`` or
    ``render(include_worker=True, worker_broker="redis")``.
    """

    # Each call gets its own directory. A test that renders two shapes to
    # compare them (e.g. a toggle on vs. off) would otherwise render the second
    # *over* the first and inspect a merged tree, where a file the second shape
    # does not produce is still there from the first — passing assertions that
    # should fail, and failing ones that should pass.
    renders = count(1)

    def _render(**answers: Any) -> Path:
        nth = next(renders)
        suffix = "" if nth == 1 else f"-{nth}"
        return render_project(tmp_path / f"rendered{suffix}", **answers)

    return _render
