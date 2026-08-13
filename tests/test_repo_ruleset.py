"""``include_repo_ruleset`` renders the repository ruleset + sync workflow.

Guards the branch-protection-as-code design (ADR-021): the ruleset JSON and its
idempotent sync workflow render only when the toggle is on, the JSON is valid
and encodes the fixed review/bypass/merge policy, and the required-status-check
contexts match the workflow job names this template ships (with the Trivy
context gated on ``include_web``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def _ruleset(root: Path) -> Path:
    return root / ".github" / "rulesets" / "main.json"


def _workflow(root: Path) -> Path:
    return root / ".github" / "workflows" / "ruleset-sync.yml"


def _load(root: Path) -> dict[str, Any]:
    return json.loads(_ruleset(root).read_text(encoding="utf-8"))


def _rule(ruleset: dict[str, Any], rule_type: str) -> dict[str, Any]:
    for rule in ruleset["rules"]:
        if rule["type"] == rule_type:
            return rule
    raise AssertionError(f"no {rule_type} rule in ruleset")


def _status_contexts(ruleset: dict[str, Any]) -> list[str]:
    params = _rule(ruleset, "required_status_checks")["parameters"]
    return [c["context"] for c in params["required_status_checks"]]


def test_ruleset_absent_by_default(render: Callable[..., Path]) -> None:
    root = render()  # library preset → toggle off
    assert not _ruleset(root).exists()


def test_ruleset_absent_when_off(render: Callable[..., Path]) -> None:
    assert not _ruleset(render(include_repo_ruleset=False)).exists()


def test_ruleset_present_under_full_preset(render: Callable[..., Path]) -> None:
    assert _ruleset(render(preset="full")).exists()


def test_ruleset_renders_valid_policy(render: Callable[..., Path]) -> None:
    ruleset = _load(render(include_repo_ruleset=True))  # json.loads asserts valid JSON
    assert ruleset["name"] == "Protect main"
    assert ruleset["enforcement"] == "active"
    assert ruleset["bypass_actors"] == []
    assert ruleset["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH"]
    pr = _rule(ruleset, "pull_request")["parameters"]
    assert pr["required_approving_review_count"] == 0
    assert pr["allowed_merge_methods"] == ["squash"]
    rule_types = {r["type"] for r in ruleset["rules"]}
    assert {"deletion", "non_fast_forward", "required_linear_history"} <= rule_types


def test_ruleset_status_contexts_non_web(render: Callable[..., Path]) -> None:
    ruleset = _load(render(include_repo_ruleset=True, include_web=False))
    assert _status_contexts(ruleset) == [
        "check",
        "Validate branch name",
        "Validate PR title",
        "Verify linked issue",
        "Check PR task list",
        "Dependency audit (pip-audit)",
        "Secret scan (gitleaks)",
    ]


def test_ruleset_status_contexts_web_adds_trivy(render: Callable[..., Path]) -> None:
    ruleset = _load(
        render(include_repo_ruleset=True, include_web=True, web_framework="fastapi")
    )
    contexts = _status_contexts(ruleset)
    assert contexts[-1] == "Container image scan (Trivy)"
    assert contexts.count("Container image scan (Trivy)") == 1


def test_sync_workflow_absent_by_default(render: Callable[..., Path]) -> None:
    assert not _workflow(render()).exists()


def test_sync_workflow_present_when_enabled(render: Callable[..., Path]) -> None:
    root = render(include_repo_ruleset=True)
    text = _workflow(root).read_text(encoding="utf-8")
    # Raw-wrapped GitHub Actions syntax must survive rendering verbatim
    # (``${{ ... }}`` legitimately contains ``{{``, so only block tags and the
    # raw wrapper itself are checked for leftover Jinja).
    assert "${{ secrets.REPO_ADMIN_TOKEN }}" in text
    assert "${{ github.repository }}" in text
    assert "{%" not in text
    assert "raw" not in text.split("run:", 1)[0]  # no leftover {%- raw -%} wrapper
    # Hardening markers.
    assert "persist-credentials: false" in text
    assert "permissions: {}" in text


def _contributing(root: Path) -> str:
    return (root / ".github" / "CONTRIBUTING.md").read_text(encoding="utf-8")


def test_contributing_documents_pat_when_enabled(render: Callable[..., Path]) -> None:
    text = _contributing(render(include_repo_ruleset=True))
    assert "REPO_ADMIN_TOKEN" in text
    assert "ruleset-sync.yml" in text


def test_contributing_manual_protection_when_disabled(
    render: Callable[..., Path],
) -> None:
    text = _contributing(render(include_repo_ruleset=False))
    # Falls back to the manual branch-protection instructions.
    assert "branches/main/protection" in text
    assert "REPO_ADMIN_TOKEN" not in text
