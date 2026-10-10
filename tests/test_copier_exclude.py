"""``copier.yml``'s ``_exclude`` keeps copier's defaults and the dropped paths.

``_exclude`` *replaces* copier's built-in exclude list, so the file re-lists
those defaults; if copier adds one, a template that only names its own paths
would start rendering files the default list exists to keep out.

The dropped-path entries stop ``copier update`` from deleting an adopter's copy
of a module the template no longer renders (#321). copier honors them on update
only from 9.10.3, so ``_min_copier_version`` must not drop below it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

import copier
import yaml
from copier._template import DEFAULT_EXCLUDE
from packaging.version import Version

COPIER_YML = Path(__file__).parent.parent / "copier.yml"


def _config() -> dict[str, object]:
    """The parsed ``copier.yml``."""
    return yaml.safe_load(COPIER_YML.read_text(encoding="utf-8"))


def _exclude() -> list[str]:
    """The ``_exclude`` list from ``copier.yml``."""
    return _config()["_exclude"]


def test_exclude_keeps_copier_defaults() -> None:
    assert set(DEFAULT_EXCLUDE) <= set(_exclude())


def test_exclude_protects_dropped_placeholders() -> None:
    exclude = _exclude()
    assert "src/{{ github_repo_name }}/utils/app.py" in exclude
    assert (
        "{% if not primary_component %}"
        "src/{{ github_repo_name }}/core/app.py{% endif %}"
    ) in exclude


def test_min_copier_version_honors_exclude_on_update() -> None:
    """Below 9.10.3, ``copier update`` deletes an edited excluded path."""
    assert Version(str(_config()["_min_copier_version"])) >= Version("9.10.3")


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Template Test",
            "-c",
            "user.email=template-test@example.com",
            *args,
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_retired_claude_file_is_not_excluded() -> None:
    """Claude Code reads ``AGENTS.md`` natively, so the wrapper is not kept."""
    assert "CLAUDE.md" not in _exclude()


def test_update_removes_unchanged_retired_claude_file(
    render: Callable[..., Path],
) -> None:
    """An untouched ``@AGENTS.md`` wrapper from v1.6.0 is deleted on update."""
    root = render(ref="v1.6.0", include_ai_rulez=False)
    assert (root / "CLAUDE.md").is_file()
    _git(root, "init")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "Initial scaffold")

    copier.run_update(str(root), vcs_ref="HEAD", defaults=True, overwrite=True, quiet=True)

    assert not (root / "CLAUDE.md").exists()
    assert (root / "AGENTS.md").is_file()
