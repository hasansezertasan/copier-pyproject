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


# --- Task 4: coverage decomposition -------------------------------------------


def test_coverage_core_job_omits_components(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    run = _job_run(ci["jobs"]["coverage-core"])
    assert "--fail-under=99" in run
    assert "--omit=" in run
    assert "/web/*" in run  # web src omitted from the core gate
    assert "/tests/web/*" in run  # web tests omitted too (source_pkgs includes tests)
    assert "*/_version.py" in run  # re-added because --omit overrides config omit


def test_coverage_web_job_includes_only_web(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    run = _job_run(ci["jobs"]["coverage-web"])
    assert "--include=" in run
    assert "/web/*" in run
    assert "/tests/web/*" in run
    assert "--fail-under=99" in run


def test_coverage_web_gated_on_web_or_core(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    cond = ci["jobs"]["coverage-web"]["if"]
    assert "needs.changes.outputs.web == 'true'" in cond
    assert "needs.changes.outputs.core == 'true'" in cond


def test_coverage_report_job_is_non_gating(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_web=True)
    assert "coverage-report" in ci["jobs"]
    assert "coverage-combine" not in ci["jobs"]
    run = _job_run(ci["jobs"]["coverage-report"])
    assert "--fail-under=0" in run
    assert "coverage xml" in run


def test_check_and_sonar_reference_new_coverage_jobs(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="full")
    needs = ci["jobs"]["check"]["needs"]
    assert "coverage-core" in needs
    assert "coverage-report" in needs
    assert "coverage-combine" not in needs
    assert ci["jobs"]["sonar"]["needs"] == "coverage-report"


# --- Task 5: worker-integration gate ------------------------------------------


def test_worker_integration_gated_on_worker_or_core(render: Callable[..., Path]) -> None:
    ci = _ci(render, preset="library", include_worker=True, worker_broker="redis")
    job = ci["jobs"]["worker-integration"]
    assert "changes" in job["needs"]
    assert "needs.changes.outputs.worker == 'true'" in job["if"]
    assert "needs.changes.outputs.core == 'true'" in job["if"]


# --- PR #259 review fixes -----------------------------------------------------


def test_changes_job_has_pull_requests_read(render: Callable[..., Path]) -> None:
    # dorny/paths-filter uses the REST API on pull_request events (needs
    # pull-requests: read), regardless of the checkout.
    ci = _ci(render, preset="library")
    assert ci["jobs"]["changes"]["permissions"].get("pull-requests") == "read"


def test_core_filter_includes_utils(render: Callable[..., Path]) -> None:
    # The always-present shared `utils` layer must force the full fan-out.
    ci = _ci(render, preset="library")
    filters = _job_run(ci["jobs"]["changes"]) + str(ci["jobs"]["changes"])
    steps = ci["jobs"]["changes"]["steps"]
    with_block = next(s for s in steps if s.get("id") == "filter")["with"]["filters"]
    assert "utils/**" in with_block


def test_coverage_report_has_draft_guard(render: Callable[..., Path]) -> None:
    # On a draft PR all deps are skipped; without the draft guard `!cancelled()`
    # still runs the job with no coverage data and `coverage combine` fails.
    ci = _ci(render, preset="library", include_web=True)
    cond = ci["jobs"]["coverage-report"]["if"]
    assert "github.event.pull_request.draft != true" in cond
    assert "!cancelled()" in cond
