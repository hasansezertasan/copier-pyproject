"""Issue templates only offer install methods and fields that fit the project.

``uvx``/``pipx`` install and run a console entry point, so they are listed only
when a runnable component exists; the OS field is required only when a command
or compiled code makes the platform matter (issue #368).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

MD_TEMPLATES = ("compatibility", "installation", "performance", "usage")


def _bug_form(root: Path) -> str:
    return (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text("utf-8")


def _os_required(form: str) -> str:
    # Text slicing, not YAML parsing: the CI render harness runs pytest with
    # only pytest + copier available.
    block = form.split("id: os", 1)[1].split("- type:", 1)[0]
    return block.split("required:", 1)[1].strip()


@pytest.mark.parametrize(
    ("answers", "has_command", "os_required"),
    [
        ({}, False, "false"),
        ({"include_c_extensions": True}, False, "true"),
        ({"preset": "tool"}, True, "true"),
        ({"include_worker": True}, True, "true"),
    ],
)
def test_bug_form_matches_project_shape(
    render: Callable[..., Path],
    answers: dict[str, object],
    has_command: bool,
    os_required: str,
) -> None:
    root = render(**answers)
    form = _bug_form(root)
    assert ("- uvx" in form) is has_command
    assert ("- pipx" in form) is has_command
    assert _os_required(form) == os_required
    for name in MD_TEMPLATES:
        md = (root / ".github" / "ISSUE_TEMPLATE" / f"{name}.md").read_text("utf-8")
        assert ("uvx" in md) is has_command, name


def test_bug_form_offers_pep723_skeleton(render: Callable[..., Path]) -> None:
    form = _bug_form(render())
    assert "# /// script" in form
    assert '# dependencies = ["example"]' in form
