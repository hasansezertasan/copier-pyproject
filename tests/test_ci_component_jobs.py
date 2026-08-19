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


# --- Task 3: per-component test jobs ------------------------------------------


def test_test_core_job_always_runs(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library")
    assert "test-core" in ci["jobs"]
    # gated only by draft-skip, not by a changes output
    assert "needs.changes.outputs" not in str(ci["jobs"]["test-core"].get("if", ""))


def test_test_web_job_gated_on_web_or_core(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    cond = ci["jobs"]["test-web"]["if"]
    assert "needs.changes.outputs.web == 'true'" in cond
    assert "needs.changes.outputs.core == 'true'" in cond


def test_test_web_selects_web_marker(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    assert '-m "web"' in _job_run(ci["jobs"]["test-web"])


def test_worker_test_job_excludes_integration(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_worker=True, worker_broker="redis")
    assert '-m "worker and not integration"' in _job_run(ci["jobs"]["test-worker"])


def test_core_marker_deselects_components(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True, include_worker=True,
             worker_broker="redis")
    run = _job_run(ci["jobs"]["test-core"])
    # core deselects every enabled component; exact list depends on the preset.
    assert '-m "not (' in run
    assert "web" in run and "worker" in run


def test_check_needs_lists_component_jobs(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    needs = ci["jobs"]["check"]["needs"]
    assert "test-core" in needs
    assert "test-web" in needs


def test_matrix_asymmetric_without_c_extensions(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library")
    include = ci["jobs"]["test-core"]["strategy"]["matrix"]["include"]
    by_os = {row["os"]: row["tox_args"] for row in include}
    assert by_os["ubuntu-latest"] == ""
    assert by_os["macos-latest"] == "-e py"
    assert by_os["windows-latest"] == "-e py"


def test_matrix_full_grid_with_c_extensions(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_c_extensions=True)
    include = ci["jobs"]["test-core"]["strategy"]["matrix"]["include"]
    assert all(row["tox_args"] == "" for row in include)
