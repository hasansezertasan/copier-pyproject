"""Release build-provenance coverage (issue #185)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import yaml


def _release_workflow(root: Path) -> dict[str, object]:
    text = (root / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    return yaml.safe_load(text)


def test_release_attests_distributions(render: Callable[..., Path]) -> None:
    workflow = _release_workflow(render(preset="library"))
    jobs = workflow["jobs"]
    build = jobs["build"]

    assert build["permissions"] == {
        "attestations": "write",
        "contents": "read",
        "id-token": "write",
    }
    attest = next(step for step in build["steps"] if step.get("id") == "attest")
    assert attest["uses"].startswith("actions/attest-build-provenance@")
    assert attest["with"]["subject-path"] == "dist/*"

    attach_steps = jobs["attach-github-release"]["steps"]
    download = next(
        step for step in attach_steps if step.get("name") == "Download provenance bundles"
    )
    assert download["with"]["pattern"] == "build-provenance*"


def test_c_extension_matrix_names_each_bundle(
    render: Callable[..., Path],
) -> None:
    workflow = _release_workflow(
        render(preset="library", include_c_extensions=True)
    )
    steps = workflow["jobs"]["build"]["steps"]
    upload = next(
        step for step in steps if step.get("name") == "Upload provenance bundle"
    )
    assert upload["with"]["name"] == "build-provenance-${{ matrix.os }}"


def test_installation_documents_provenance_verification(
    render: Callable[..., Path],
) -> None:
    root = render(preset="library", include_docs=True)
    installation = (root / "docs" / "installation.rst").read_text(encoding="utf-8")
    assert "gh attestation verify <downloaded-distribution> --repo octocat/example" in installation
    assert "Private and internal repositories require GitHub Enterprise Cloud" in installation
