"""Render harness for the copier-pyproject template.

Renders the template with Copier's Python API into a temporary directory and
exposes a ``render`` fixture that returns the rendered project root.

Note: with ``vcs_ref="HEAD"`` Copier renders from this repo's git tree and
includes uncommitted working-tree changes (it emits a ``DirtyLocalWarning``),
so the tests reflect the current working copy of ``copier.yml`` / ``template/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

import copier
import pytest

if TYPE_CHECKING:
    from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Required questions (no defaults) — supplied so renders stay non-interactive.
IDENTITY = {
    "github_user": "octocat",
    "github_repo_name": "example",
    "author_full_name": "Octo Cat",
    "author_email": "octo@example.com",
}


@pytest.fixture
def render(tmp_path: Path) -> Callable[..., Path]:
    """Return a ``render(**answers) -> Path`` helper.

    Extra keyword answers override the identity defaults and the preset-driven
    toggle defaults, e.g. ``render(preset="full")`` or
    ``render(include_worker=True, worker_broker="redis")``.
    """

    def _render(**answers: Any) -> Path:
        dst = tmp_path / "rendered"
        copier.run_copy(
            str(REPO_ROOT),
            str(dst),
            data={**IDENTITY, **answers},
            defaults=True,
            overwrite=True,
            vcs_ref="HEAD",
            quiet=True,
        )
        return dst

    return _render
