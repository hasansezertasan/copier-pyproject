"""Rendering contract for the opt-in performance-benchmarking scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


def test_benchmarks_are_opt_in(render: Callable[..., Path]) -> None:
    root = render(preset="library")

    assert not (root / "benchmarks").exists()
    assert not (root / ".github" / "workflows" / "benchmarks.yml").exists()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "pytest-codspeed" not in pyproject
    assert '"benchmark:' not in pyproject


def test_benchmark_scaffold_is_separate_and_non_blocking(
    render: Callable[..., Path],
) -> None:
    root = render(include_benchmarks=True)

    benchmark = root / "benchmarks" / "test_version_lookup.py"
    assert benchmark.is_file()
    assert "@pytest.mark.benchmark" in benchmark.read_text(encoding="utf-8")

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'benchmarks = [\n  "pytest-codspeed>=4.0",\n]' in pyproject
    assert "-m 'not benchmark'" in pyproject
    assert "[tool.tox.env.benchmark]" in pyproject
    assert 'dependency_groups = ["test", "benchmarks"]' in pyproject

    workflow = (
        root / ".github" / "workflows" / "benchmarks.yml"
    ).read_text(encoding="utf-8")
    assert "CODSPEED_TOKEN_SET" in workflow
    assert "CodSpeedHQ/action@373d6868929f444bc08d901fd0eb0ad52a8875ea" in workflow
    assert "--group test --group benchmarks" in workflow
    assert "CODSPEED_TOKEN secret is not set" in workflow
    # The job is draft-gated, so leaving draft must start a fresh run.
    assert "draft != true" in workflow
    assert "types: [opened, synchronize, reopened, ready_for_review]" in workflow

    ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "benchmarks" not in ci


def test_benchmarks_only_readme_has_usage_section(render: Callable[..., Path]) -> None:
    """A benchmarks-only project must render the `Usage` anchor its TOC links to."""
    readme = (render(preset="library", include_benchmarks=True) / "README.md").read_text(
        encoding="utf-8"
    )

    assert "- [Usage](#usage)" in readme
    assert "\n## Usage\n" in readme
    assert "\n### Benchmarks\n" in readme
