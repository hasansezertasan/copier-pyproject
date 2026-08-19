"""Path-filtered per-component CI jobs render correctly (issue #160).

The generated ``ci.yml`` gains a ``changes`` path-filter job, per-component
``test-<component>`` jobs gated on their tree (with a ``core`` escape hatch), and
per-component ``coverage-<component>`` gates that decompose ADR-026's single union
coverage gate. Designed to compose with #159 (asymmetric matrix + draft skip).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml


def _ci(render: Callable[..., Path], **answers: Any) -> dict[str, Any]:
    project = render(**answers)
    text = (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _job_run(job: dict[str, Any]) -> str:
    return "\n".join(step.get("run", "") for step in job.get("steps", []))


# --- Task 2: changes job -------------------------------------------------------


def test_changes_job_present_with_core_output(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library")
    assert "changes" in ci["jobs"]
    assert "core" in ci["jobs"]["changes"]["outputs"]


def test_changes_job_has_web_output_when_web(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    assert "web" in ci["jobs"]["changes"]["outputs"]
