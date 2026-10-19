"""The LICENSE copyright start year is the project's creation year (#424).

``LICENSE`` used to hard-code ``2025-present``, so every project scaffolded
later claimed a start year that was not its own. ``copyright_year`` is a
*visible* question because Copier records only asked questions in
``.copier-answers.yml``: that is what keeps the year fixed across
``copier update`` (a ``when: false`` default is re-evaluated on every run).
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Callable

import copier
import pytest
import yaml

COPYRIGHT_LINE = re.compile(r"^Copyright \(c\) (\d{4})-present Octo Cat <", re.M)


def _license_year(root: Path) -> int:
    match = COPYRIGHT_LINE.search((root / "LICENSE").read_text(encoding="utf-8"))
    assert match, "LICENSE has no '<year>-present' copyright line"
    return int(match.group(1))


def _answers(root: Path) -> dict[str, object]:
    return yaml.safe_load((root / ".copier-answers.yml").read_text(encoding="utf-8"))


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


def _commit_scaffold(root: Path) -> None:
    _git(root, "init")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "Initial scaffold")


def test_default_year_is_the_current_year(render: Callable[..., Path]) -> None:
    before = time.localtime().tm_year
    root = render()
    after = time.localtime().tm_year
    assert _license_year(root) in {before, after}
    assert _answers(root)["copyright_year"] == _license_year(root)


def test_year_can_be_set_and_is_recorded(render: Callable[..., Path]) -> None:
    root = render(copyright_year=2019)
    assert _license_year(root) == 2019
    assert _answers(root)["copyright_year"] == 2019


@pytest.mark.parametrize("year", [0, 99, 10000])
def test_year_must_be_four_digits(render: Callable[..., Path], year: int) -> None:
    with pytest.raises(ValueError, match="four-digit year"):
        render(copyright_year=year)


def test_year_is_stable_across_update(render: Callable[..., Path]) -> None:
    root = render(copyright_year=2019)
    _commit_scaffold(root)

    copier.run_update(
        str(root), vcs_ref="HEAD", defaults=True, overwrite=True, quiet=True
    )

    assert _license_year(root) == 2019
    assert _answers(root)["copyright_year"] == 2019


def test_pre_existing_project_update_prompts_for_the_year(
    render: Callable[..., Path],
) -> None:
    """A v1.13.1 project has no ``copyright_year`` answer and ``2025-present``.

    Copier cannot tell an update from a first copy while computing a question
    default, so the new default (the current year) applies unless the adopter
    answers. Passing the year keeps the existing LICENSE and records the answer.
    """
    root = render(ref="v1.13.1")
    assert _license_year(root) == 2025
    assert "copyright_year" not in _answers(root)
    _commit_scaffold(root)

    copier.run_update(
        str(root),
        vcs_ref="HEAD",
        defaults=True,
        overwrite=True,
        quiet=True,
        data={"copyright_year": 2025},
    )

    assert _license_year(root) == 2025
    assert _answers(root)["copyright_year"] == 2025
