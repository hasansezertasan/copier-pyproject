"""The App-free label manifest carries the expected set and stays self-consistent.

Guards Part B: ``labels.yml`` keeps the workflow-required labels
(``no-issue``/``release``) and gains the fuller set, and the ``documentation``
label name agrees (lower-case) between ``labels.yml`` and ``labeler.yml`` so
``actions/labeler`` can apply it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

EXPECTED_LABELS = {
    "no-issue", "release", "bug", "documentation", "duplicate", "enhancement",
    "good first issue", "help wanted", "invalid", "question", "wontfix",
    "automated", "dependencies", "github_actions", "tests", "examples",
}


def _label_names(root: Path) -> set[str]:
    # Parse the `- name: <value>` entries without a YAML dependency (the CI
    # render harness runs pytest with only pytest + copier available).
    text = (root / ".github" / "labels.yml").read_text("utf-8")
    names: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            names.add(stripped[len("- name:") :].strip().strip("\"'"))
    return names


def test_labels_cover_expected_set(render: Callable[..., Path]) -> None:
    assert _label_names(render()) == EXPECTED_LABELS


def test_workflow_required_labels_present(render: Callable[..., Path]) -> None:
    names = _label_names(render())
    assert "no-issue" in names  # check-linked-issues bypass
    assert "release" in names  # applied by labeler.yml head-branch rule


def test_documentation_case_agrees(render: Callable[..., Path]) -> None:
    root = render()
    assert "documentation" in _label_names(root)
    labeler = (root / ".github" / "labeler.yml").read_text("utf-8")
    assert "\ndocumentation:" in labeler
    assert "\nDocumentation:" not in labeler
