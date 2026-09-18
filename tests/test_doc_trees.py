"""The committed generated-tree page matches a fresh render (#164, #181).

``docs/generated-project-trees.md`` is a *derived* artifact: the real file set
each preset renders, produced by ``tools/render.py regenerate``. This is the
verify half of the generate-and-verify convention (ADR-031) — the same posture
cobo's sha256 fence gives ``.gitignore`` (ADR-012), except the drift here
originates in *this* repo (a toggle that gains or loses a file), so the guard
belongs on the PR that causes it rather than on a weekly cron.

Regenerate with ``mise run regenerate`` and commit the diff — that diff is the
point: "this change adds/removes these files from the `web` preset" is a
review signal no hand-written structure doc ever produced.
"""

from __future__ import annotations

from pathlib import Path

from tools.render import TREE_PAGE, tree_page


def test_generated_tree_page_is_current(tmp_path: Path) -> None:
    committed = TREE_PAGE.read_text(encoding="utf-8")
    assert committed == tree_page(tmp_path), (
        f"{TREE_PAGE.name} is stale — run `mise run regenerate` and commit the diff"
    )
