"""The App-free label manifest carries the expected set and stays self-consistent.

Guards Part B: ``labels.yml`` keeps the workflow-required labels
(``no-issue``/``release``) and gains the fuller set, and the ``documentation``
label name agrees (lower-case) between ``labels.yml`` and ``labeler.yml`` so
``actions/labeler`` can apply it.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

EXPECTED_LABELS = {
    "no-issue",
    "release",
    "bug",
    "documentation",
    "duplicate",
    "enhancement",
    "good first issue",
    "help wanted",
    "invalid",
    "question",
    "wontfix",
    "automated",
    "dependencies",
    "github_actions",
    "tests",
    "examples",
    "area:core",
    "area:cli",
    "area:gui",
    "area:tui",
    "area:web",
    "area:mcp",
    "area:worker",
    "area:docs",
    "area:ci",
    "area:deps",
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


def test_area_labels_have_matching_rules(render: Callable[..., Path]) -> None:
    root = render(preset="full")
    names = _label_names(root)
    labeler = (root / ".github" / "labeler.yml").read_text("utf-8")
    area_labels = {name for name in names if name.startswith("area:")}
    assert area_labels == {
        "area:core",
        "area:cli",
        "area:gui",
        "area:tui",
        "area:web",
        "area:mcp",
        "area:worker",
        "area:docs",
        "area:ci",
        "area:deps",
    }
    for label in area_labels:
        assert f"\n{label}:" in labeler


def test_area_component_rules_only_render_for_included_components(
    render: Callable[..., Path],
) -> None:
    labeler = (render(preset="library") / ".github" / "labeler.yml").read_text("utf-8")
    assert "\narea:core:" in labeler
    assert "\narea:docs:" in labeler
    assert "\narea:ci:" in labeler
    assert "\narea:deps:" in labeler
    for component in ("cli", "gui", "tui", "web", "mcp", "worker"):
        assert f"\narea:{component}:" not in labeler


def test_area_docs_includes_ai_rulez_when_enabled(
    render: Callable[..., Path],
) -> None:
    labeler = (render(include_ai_rulez=True) / ".github" / "labeler.yml").read_text(
        "utf-8"
    )
    assert "['docs/**', '.ai-rulez/**', '*.md', '*.rst']" in labeler


def test_area_core_color_is_a_string(render: Callable[..., Path]) -> None:
    labels = (render() / ".github" / "labels.yml").read_text("utf-8")
    assert 'color: "5319e7"' in labels
