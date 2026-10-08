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


def test_update_preserves_customized_retired_claude_file(
    render: Callable[..., Path],
) -> None:
    """Retiring the wrapper must not erase adopter-authored instructions."""
    root = render(ref="v1.6.0", include_ai_rulez=False)
    claude_file = root / "CLAUDE.md"
    assert claude_file.is_file()
    for args in (("init",), ("add", "."), ("commit", "-m", "Initial scaffold")):
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
    customized = claude_file.read_text(encoding="utf-8") + (
        "\n## Project-specific guidance\n\nKeep our custom deployment workflow.\n"
    )
    claude_file.write_text(customized, encoding="utf-8")
    subprocess.run(
        ["git", "add", "CLAUDE.md"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Template Test",
            "-c",
            "user.email=template-test@example.com",
            "commit",
            "-m",
            "Customize project instructions",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )

    copier.run_update(str(root), vcs_ref="HEAD", defaults=True, overwrite=True, quiet=True)

    assert claude_file.read_text(encoding="utf-8") == customized
    assert not (root / "CLAUDE.md.rej").exists()
