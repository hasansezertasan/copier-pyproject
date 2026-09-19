"""The gates that only fail *silently* when they regress.

Each assertion here stands for a defect where CI stayed green while the gate it
names stopped gating, or a destructive deploy lost its guard (issues #300/#301):
a required status context that reports nothing, a Sphinx warning check that runs
where nothing requires it, a swallowed ``git fetch`` failure that deletes the
published documentation archive.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable


def _read(root: Path, *parts: str) -> str:
    return root.joinpath(*parts).read_text(encoding="utf-8")


def test_task_check_publishes_its_required_context_for_bots(
    render: Callable[..., Path],
) -> None:
    """The `[bot]` skip must leave the required check run behind, green.

    The required context is the ``Task Completed Checker`` check run the action
    creates — not the job name — so a bare skip leaves no context at all and
    blocks every Renovate/release PR forever.
    """
    workflow = _read(render(), ".github", "workflows", "task-completed-check.yml")
    assert "-f name='Task Completed Checker'" in workflow
    assert "-f conclusion=success" in workflow
    assert workflow.count("endsWith(github.event.pull_request.user.login, '[bot]')") == 2


def test_warning_gate_runs_in_a_check_aggregated_job(
    render: Callable[..., Path],
) -> None:
    """The `-W`-equivalent build must sit under ``check``, the required context.

    ``docs-doctest`` alone is ``sphinx-build -b doctest`` with no warning gate,
    and ``docs-preview.yml`` is skipped for forks and required by nothing — so
    without ``docs-build`` here, broken references pass every required check.
    """
    ci = _read(render(include_docs=True), ".github", "workflows", "ci.yml")
    docs_job = ci.split("  docs-doctest:", 1)[1].split("\n  cli-installed:", 1)[0]
    assert "tox run -e docs-build" in docs_job
    # sphinx-last-updated-by-git warns "Git clone too shallow" on a depth-1
    # clone, and the gate above turns every such warning into an error.
    assert "fetch-depth: 0" in docs_job
    assert ", docs-doctest" in ci.split("\n  check:", 1)[1]


def test_codecov_upload_carries_the_flag_its_status_is_scoped_to(
    render: Callable[..., Path],
) -> None:
    """An upload with no flag matches no flag-scoped status, so the gate is inert."""
    root = render()
    codecov = _read(root, ".github", "codecov.yml")
    ci = _read(root, ".github", "workflows", "ci.yml")
    assert "- unit" in codecov  # coverage.status.project.default.flags
    assert "flags: unit" in ci


def test_gh_pages_fetch_distinguishes_absent_from_broken(
    render: Callable[..., Path],
) -> None:
    """``git fetch || echo`` would turn a transport error into an empty archive.

    ``build_docs.py`` then assembles a site with no prior versions and the
    clean-on-deploy removes every published version directory from ``gh-pages``.
    """
    root = render(include_docs=True)
    for name in ("gh-pages.yml", "release.yml"):
        workflow = _read(root, ".github", "workflows", name)
        assert "git fetch origin gh-pages:gh-pages || echo" not in workflow
        assert "ls-remote --exit-code --heads origin gh-pages" in workflow
        # persist-credentials: false leaves raw git unauthenticated, so on a
        # private repo both the probe and the fetch need the token supplied
        # per-invocation — otherwise the guard aborts every deploy.
        assert 'http.https://github.com/.extraheader=$auth' in workflow
        assert "GH_TOKEN:" in workflow


def test_manual_redeploy_targets_a_published_release(
    render: Callable[..., Path],
) -> None:
    """A draft release's tag exists from the merge; ``releases/latest`` excludes it.

    The interpreter setup must also follow the tag checkout, or a redeploy
    rebuilds tagged docs on whatever ``main`` has since bumped to.
    """
    workflow = _read(render(include_docs=True), ".github", "workflows", "gh-pages.yml")
    assert 'tag="$(gh api "repos/${GITHUB_REPOSITORY}/releases/latest"' in workflow
    assert 'tag="$(git describe' not in workflow
    assert workflow.index("Check out the latest release tag") < workflow.index(
        "Set up Python"
    )
    # The tag carries the docs sources to rebuild, but build_docs.py is
    # orchestration — keep this revision's, or a project that adopts a template
    # update before its next release redeploys with the tagged (unhardened) one.
    assert 'git checkout "$dispatch_ref" -- tools/build_docs.py' in workflow


def test_build_docs_refuses_to_drop_a_published_version(
    render: Callable[..., Path],
) -> None:
    """Version slugs come from a ``ls-tree`` of the branch, so they provably exist."""
    source = _read(render(include_docs=True), "tools", "build_docs.py")
    assert 'preserve_from_gh_pages(name, out, ref, required=name != "latest")' in source
    assert "raise RuntimeError(_PRESERVE_FAILED_MSG" in source


def test_cli_launch_input_offers_only_unsplittable_values(
    render: Callable[..., Path],
) -> None:
    """VS Code drops an input into ONE ``args`` element; debugpy never splits it.

    So the prompt has to be constrained to single-token commands the project
    actually renders — a free-text default of ``""`` fails on first launch.
    """
    launch = _read(render(preset="full"), ".vscode", "launch.json")
    assert '"type": "promptString"' not in launch
    options = re.search(r'"options": \[(.*?)\]', launch)
    assert options is not None
    assert json.loads(f"[{options.group(1)}]") == [
        "version",
        "info",
        "run",
        "dev",
        "interactive",
        "gui",
        "web",
        "mcp",
        "worker",
    ]
    assert '"${input:command}"' in launch


def test_setup_doc_requires_the_aggregate_ci_context(
    render: Callable[..., Path],
) -> None:
    """Without ``check``, a PR whose whole suite failed still satisfies protection."""
    setup = _read(
        render(include_repo_ruleset=False), "docs", "maintaining", "setup.rst"
    )
    assert '"contexts": ["check", "Validate PR title"' in setup
    # The two ordering traps that make the documented protection unsatisfiable.
    assert "Apply protection *after* the first merge" in setup
    assert "Release PRs need a manual nudge" in setup


def test_setup_doc_contains_the_publish_environment_policy(
    render: Callable[..., Path],
) -> None:
    """`workflow_dispatch` runs the file from any branch; the environment does not."""
    root = render()
    setup = _read(root, "docs", "maintaining", "setup.rst")
    assert "environments/publish/deployment-branch-policies" in setup
    # `gh api -f` sends "false"/"true" as JSON *strings*; the environments API
    # types both as booleans, so these two must use the typed -F form.
    assert "-F 'deployment_branch_policy[protected_branches]=false'" in setup
    assert "-F 'deployment_branch_policy[custom_branch_policies]=true'" in setup
    # Policies are a separate collection the environment PUT does not clear, so
    # a pre-existing wildcard would stay eligible beside `main`. Delete first,
    # and assert the collection is exactly one `main` branch policy.
    assert "-X DELETE" in setup
    assert '== ["branch:main"]' in setup
    assert "DO NOT REMOVE workflow_dispatch" in _read(
        root, ".github", "workflows", "release.yml"
    )
