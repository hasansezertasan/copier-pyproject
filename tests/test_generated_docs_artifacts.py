"""``docs/_generated/`` must be gitignored wherever ``conf.py`` writes into it.

Every docs build shells the live app(s) into ``docs/_generated/`` — the worker's
AsyncAPI, the web app's OpenAPI spec, the Typer CLI reference Markdown. The tree
is build output and is never committed, but the ``.gitignore`` rule used to be
gated on ``include_worker or include_web`` while ``conf.py``'s generator guard
also covers a Typer CLI. A ``tool``-preset project therefore wrote an artifact
nothing ignored, ``git add -A`` swept it in, and the committed copy then failed
``prek run --all-files`` intermittently (issue #299).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

# Every shape whose docs build writes into ``docs/_generated/``.
GENERATING = [
    pytest.param({"include_cli": True, "cli_framework": "typer"}, id="typer-cli"),
    pytest.param({"include_web": True, "web_framework": "fastapi"}, id="fastapi-web"),
    pytest.param({"include_web": True, "web_framework": "litestar"}, id="litestar-web"),
    pytest.param({"include_worker": True, "worker_broker": "redis"}, id="worker"),
]


def _conf_py(root: Path) -> str:
    return (root / "docs" / "conf.py").read_text(encoding="utf-8")


def _gitignore(root: Path) -> str:
    return (root / ".gitignore").read_text(encoding="utf-8")


@pytest.mark.parametrize("answers", GENERATING)
def test_generating_shapes_ignore_the_tree(
    render: Callable[..., Path], answers: dict[str, Any]
) -> None:
    """Every shape whose ``conf.py`` writes the tree must also ignore it.

    Asserting both halves in one test is the point: the defect was the two
    conditions drifting apart, so a test that only checked ``.gitignore`` would
    still pass once a future toggle starts generating without a matching rule.
    """
    root = render(include_docs=True, **answers)
    assert "_generated_dir.mkdir" in _conf_py(root)
    assert "docs/_generated/" in _gitignore(root)


def test_non_generating_shape_ships_neither(render: Callable[..., Path]) -> None:
    """An argparse-only CLI writes nothing, so the rule would be dead weight."""
    root = render(include_docs=True, include_cli=True, cli_framework="argparse")
    assert "_generated_dir" not in _conf_py(root)
    assert "docs/_generated/" not in _gitignore(root)


def test_rule_sits_below_the_cobo_seal(render: Callable[..., Path]) -> None:
    """Inside the sealed block it breaks the sha256 and `cobo update` drops it.

    ``cobo.lock`` marks the fragment ``update = true``, so a rule placed above
    the end marker is regenerated away and the defect silently returns — and
    ``gitignore-drift.yml`` runs only on dispatch and a weekly cron, outside the
    ``check`` aggregation gate, so nothing on the PR would say so. See ADR-012.
    """
    gitignore = _gitignore(render(include_docs=True, include_cli=True))
    assert gitignore.index("docs/_generated/") > gitignore.index("# <<< cobo:end")
