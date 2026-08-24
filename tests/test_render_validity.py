"""Structural validity of the rendered output across presets and key toggles.

The cheapest guard against a Jinja mistake — a broken conditional, a
whitespace-control regression in a guarded block — emitting malformed YAML or
TOML in a *conditional* file that the single-preset ``example/`` regeneration
never exercises (issue #182). No installation of the generated project, so the
matrix stays fast.

``yaml`` is available in the render harness as a transitive dependency of
copier; ``tomllib`` is stdlib (3.11+).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

PKG = "example"

# The four archetype presets (ADR-016) — the primary axis hand-regeneration
# misses, since ``.example-input.yml`` only ever renders ``library``.
PRESETS = ["library", "tool", "web", "full"]

# High-signal toggle combinations beyond the presets: one render per broker and
# one per web framework, so every conditional broker/framework branch is
# structurally validated without an exhaustive cross-product.
WORKER_BROKERS = ["kafka", "nats", "rabbitmq", "redis"]
WEB_FRAMEWORKS = ["fastapi", "litestar"]


def _iter_yaml_documents(path: Path) -> None:
    """Parse every YAML document in ``path``; raises on malformed YAML."""
    # ``safe_load_all`` is lazy — force it through ``list`` so multi-document
    # workflow files (``---`` separated) are fully parsed, not just opened.
    list(yaml.safe_load_all(path.read_text(encoding="utf-8")))


def _assert_all_yaml_parses(root: Path) -> None:
    yaml_files = [*root.rglob("*.yml"), *root.rglob("*.yaml")]
    # A render that emits no YAML at all would make this a green no-op; every
    # project ships at least the copier answers file and CI workflows.
    assert yaml_files, "render produced no YAML files to validate"
    for path in yaml_files:
        try:
            _iter_yaml_documents(path)
        except yaml.YAMLError as exc:  # pragma: no cover - failure detail
            pytest.fail(f"invalid YAML in {path.relative_to(root)}: {exc}")


def _assert_pyproject_is_toml(root: Path) -> None:
    tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_renders_pyproject(
    render: Callable[..., Path], preset: str
) -> None:
    root = render(preset=preset)
    assert root.is_dir()
    assert (root / "pyproject.toml").is_file()


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_yaml_is_parseable(
    render: Callable[..., Path], preset: str
) -> None:
    _assert_all_yaml_parses(render(preset=preset))


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_pyproject_is_valid_toml(
    render: Callable[..., Path], preset: str
) -> None:
    _assert_pyproject_is_toml(render(preset=preset))


@pytest.mark.parametrize("broker", WORKER_BROKERS)
def test_worker_broker_render_is_structurally_valid(
    render: Callable[..., Path], broker: str
) -> None:
    root = render(include_worker=True, worker_broker=broker)
    _assert_all_yaml_parses(root)
    _assert_pyproject_is_toml(root)


# The env var each broker's integration seam reads — the single value that must
# agree across ``worker_broker_spec.env``, the CI ``services:`` job ``env:``, and
# the ``integration`` tox env's ``pass_env`` (ADR-008, issue #169).
BROKER_ENV_VARS = {
    "kafka": "KAFKA_BOOTSTRAP_SERVERS",
    "nats": "NATS_URL",
    "rabbitmq": "RABBITMQ_URL",
    "redis": "REDIS_URL",
}

# Expected ``services:`` block per broker, or ``None`` for the brokers that stay
# on in-test testcontainers. ``health_cmd`` is ``None`` where the image ships no
# usable in-container probe and readiness falls to the test's connect-retry.
EXPECTED_CI_SERVICES = {
    "kafka": None,
    "rabbitmq": None,
    "nats": {
        "name": "nats",
        "image": "nats:2.10",
        "port": 4222,
        "health_cmd": None,
        "url": "nats://localhost:4222",
    },
    "redis": {
        "name": "redis",
        "image": "redis:7",
        "port": 6379,
        "health_cmd": "redis-cli ping",
        "url": "redis://localhost:6379",
    },
}


def _worker_integration_job(root: Path) -> dict[str, Any]:
    ci = yaml.safe_load(
        (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    return ci["jobs"]["worker-integration"]


def _assert_ci_service_matches(
    job: dict[str, Any], expected: dict[str, Any]
) -> None:
    """Assert the rendered ``services:`` block matches ``expected`` exactly."""
    services = job["services"]
    assert list(services) == [expected["name"]]
    service = services[expected["name"]]
    assert service["image"] == expected["image"]
    port = expected["port"]
    assert service["ports"] == [f"{port}:{port}"]
    if expected["health_cmd"] is None:
        # Asserted absent, not merely unchecked: a health probe silently
        # appearing (or the null-probe rationale being dropped) is a real change.
        assert "options" not in service
    else:
        assert f'--health-cmd "{expected["health_cmd"]}"' in service["options"]
        assert "--health-interval" in service["options"]


@pytest.mark.parametrize("broker", WORKER_BROKERS)
def test_worker_integration_ci_service_matches_broker_spec(
    render: Callable[..., Path], broker: str
) -> None:
    """redis/nats get a GitHub Actions ``services:`` CI path; kafka/rabbitmq
    stay on testcontainers (issue #169).

    Asserts the whole block — image, published port, health command — not just
    that a ``services:`` key exists, so an edit to ``worker_broker_spec``'s
    ``ci_service`` field cannot silently change what CI runs against.
    """
    job = _worker_integration_job(render(include_worker=True, worker_broker=broker))
    expected = EXPECTED_CI_SERVICES[broker]
    if expected is None:
        assert "services" not in job, f"{broker} should stay on testcontainers"
        assert BROKER_ENV_VARS[broker] not in job.get("env", {})
        return
    _assert_ci_service_matches(job, expected)
    assert job["env"] == {BROKER_ENV_VARS[broker]: expected["url"]}


@pytest.mark.parametrize(
    ("backend", "image", "cli"),
    [("redis", "redis:7", "redis-cli"), ("valkey", "valkey/valkey:8", "valkey-cli")],
)
def test_redis_worker_ci_service_honors_redis_backend(
    render: Callable[..., Path], backend: str, image: str, cli: str
) -> None:
    """The redis ``services:`` container tracks ``redis_backend``, and its image
    and health CLI stay identical to the devcontainer compose service — both read
    the ``redis_image``/``redis_cli`` computed vars, so they cannot drift.
    """
    root = render(
        include_worker=True, worker_broker="redis", redis_backend=backend
    )
    service = _worker_integration_job(root)["services"]["redis"]
    assert service["image"] == image
    assert f'--health-cmd "{cli} ping"' in service["options"]

    compose = yaml.safe_load(
        (root / ".devcontainer" / "docker-compose.yml").read_text(encoding="utf-8")
    )
    compose_redis = compose["services"]["redis"]
    assert compose_redis["image"] == image
    assert compose_redis["healthcheck"]["test"] == ["CMD", cli, "ping"]


@pytest.mark.parametrize("broker", WORKER_BROKERS)
def test_worker_integration_env_seam_agrees_across_ci_and_tox(
    render: Callable[..., Path], broker: str
) -> None:
    """The broker URL env var must be the *same* name in all three places.

    The ``services:`` job ``env:`` sets it, the ``integration`` tox env must
    ``pass_env`` it through to pytest, and the integration test reads it. A
    mismatch in any one of them degrades the services path to a silent
    testcontainers fallback rather than failing loudly (ADR-008, issue #169).
    """
    root = render(include_worker=True, worker_broker=broker)
    env_var = BROKER_ENV_VARS[broker]

    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    integration = pyproject["tool"]["tox"]["env"]["integration"]
    assert integration["pass_env"] == [env_var]

    integration_test = (
        root / "tests" / "worker" / "test_integration.py"
    ).read_text(encoding="utf-8")
    assert f'os.getenv("{env_var}")' in integration_test

    job = _worker_integration_job(root)
    if EXPECTED_CI_SERVICES[broker] is not None:
        assert env_var in job["env"]


@pytest.mark.parametrize("framework", WEB_FRAMEWORKS)
def test_web_framework_render_is_structurally_valid(
    render: Callable[..., Path], framework: str
) -> None:
    root = render(include_web=True, web_framework=framework)
    _assert_all_yaml_parses(root)
    _assert_pyproject_is_toml(root)


def test_docs_off_drops_sphinx_subsystem_but_keeps_setup_guide(
    render: Callable[..., Path],
) -> None:
    """``include_docs=false`` removes the Sphinx site + docs CI/deps but leaves
    the maintainer setup guide and a structurally valid project (ADR-025)."""
    root = render(include_docs=False)
    _assert_all_yaml_parses(root)
    _assert_pyproject_is_toml(root)

    # Sphinx-site files, docs workflows, and the docs dependency group are gone.
    assert not (root / "docs" / "conf.py").exists()
    assert not (root / "docs" / "index.rst").exists()
    wf = root / ".github" / "workflows"
    assert not (wf / "docs-preview.yml").exists()
    assert not (wf / "docs-linkcheck.yml").exists()
    assert not (wf / "gh-pages.yml").exists()
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert "docs" not in pyproject["dependency-groups"]
    tox_envs = pyproject["tool"]["tox"]["env"]
    assert not [name for name in tox_envs if name.startswith("docs-")]

    # No published-metadata reference to the (absent) Pages docs site.
    assert "documentation" not in pyproject["project"]["urls"]
    contributing = (root / ".github" / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "Improving The Documentation" not in contributing

    # The maintainer setup guide always ships; only its Pages step is gated.
    setup = root / "docs" / "maintaining" / "setup.rst"
    assert setup.is_file()
    assert "GitHub Pages" not in setup.read_text(encoding="utf-8")

    # The repo-setup skill drops its docs-only Pages/deploy-docs guidance.
    skill = (root / ".claude" / "skills" / "repo-setup" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "deploy-docs" not in skill
    assert "gh-pages" not in skill


def test_docs_off_omits_component_interface_pages(
    render: Callable[..., Path],
) -> None:
    """Docs-off drops the web/worker Sphinx interface pages (the compound
    ``include_docs and include_*`` filename branch) while the components render."""
    root = render(include_docs=False, include_web=True, include_worker=True)
    _assert_pyproject_is_toml(root)
    assert not (root / "docs" / "web-interface.rst").exists()
    assert not (root / "docs" / "worker-interface.rst").exists()
    # The components themselves are unaffected by include_docs.
    assert (root / "src" / PKG / "web").is_dir()
    assert (root / "src" / PKG / "worker").is_dir()


def test_docs_on_by_default_keeps_sphinx_subsystem(
    render: Callable[..., Path],
) -> None:
    """Docs are on by default (no override), rendering the Sphinx site, workflows,
    and the full Pages documentation URL — a regression guard if the default flips."""
    root = render()  # default preset (library) → include_docs defaults to true
    assert (root / "docs" / "conf.py").is_file()
    assert (root / ".github" / "workflows" / "docs-preview.yml").is_file()
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert "docs" in pyproject["dependency-groups"]
    assert (
        pyproject["project"]["urls"]["documentation"]
        == "https://octocat.github.io/example"
    )


# The guard every ``ci.yml`` job carries so a draft PR runs none of the
# test/coverage/packaging fan-out (ADR-029). Scoped to this workflow: the security
# and docs-preview workflows still run on drafts by design.
DRAFT_GUARD = "github.event.pull_request.draft != true"


def _ci_workflow(root: Path) -> dict[str, Any]:
    return yaml.safe_load(
        (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )


def _ci_test_step(job: dict[str, Any]) -> dict[str, Any]:
    return next(step for step in job["steps"] if step["name"] == "Run the tests")


def test_ci_matrix_is_asymmetric_by_default(render: Callable[..., Path]) -> None:
    """Full interpreter depth on Linux, one representative interpreter elsewhere.

    Asserted as the exact list, not merely "``tox_args`` exists": the whole point
    of ADR-029 is *which* cell runs which depth, and a silent flip back to a
    uniform grid (or to a single-interpreter Linux cell, which would gut
    interpreter coverage) must fail here.
    """
    job = _ci_workflow(render())["jobs"]["ci"]
    assert job["strategy"]["matrix"]["include"] == [
        {"os": "ubuntu-latest", "tox_args": ""},
        {"os": "macos-latest", "tox_args": "-e py"},
        {"os": "windows-latest", "tox_args": "-e py"},
    ]
    assert (
        _ci_test_step(job)["run"] == "uv run --locked tox run ${{ matrix.tox_args }}"
    )


def test_cli_env_still_runs_on_every_os(render: Callable[..., Path]) -> None:
    """``cli`` is appended to the non-Linux cells whenever ``include_cli``.

    Unlike ``style``, the ``cli`` env is *not* OS-independent: its command is the
    **installed** console script, and script generation is per-OS (Windows
    ``.exe`` shims, ``[project.gui-scripts]`` — ADR-019). The pytest suite drives
    the CLI *in process*, never through the installed script, so ``tox -e cli`` is
    the only thing in CI that runs it. Narrowing these cells back to
    a bare ``-e py`` would let a Windows-only entry-point break merge green in a
    ``tool``-preset project (which renders no launcher/freezer/compiler job to
    catch it), so pin it here. See ADR-029.
    """
    job = _ci_workflow(render(preset="tool"))["jobs"]["ci"]
    assert job["strategy"]["matrix"]["include"] == [
        {"os": "ubuntu-latest", "tox_args": ""},
        {"os": "macos-latest", "tox_args": "-e py,cli"},
        {"os": "windows-latest", "tox_args": "-e py,cli"},
    ]


def test_c_extensions_restores_the_full_grid(render: Callable[..., Path]) -> None:
    """The one carve-out: a compiled extension makes every OS × interpreter pair a
    distinct ABI-specific build, so every cell runs the whole ``env_list``
    (ADR-029)."""
    job = _ci_workflow(render(include_c_extensions=True))["jobs"]["ci"]
    assert job["strategy"]["matrix"]["include"] == [
        {"os": "windows-latest", "tox_args": ""},
        {"os": "ubuntu-latest", "tox_args": ""},
        {"os": "macos-latest", "tox_args": ""},
    ]


def test_every_ci_job_is_gated_on_draft_prs(render: Callable[..., Path]) -> None:
    """*Every* job — including ``check``.

    ``re-actors/alls-green`` counts a skipped ``needs`` job as a failure, so
    gating the work jobs while leaving ``check`` to run would turn every draft PR
    red. The ``full`` preset is used so the conditional jobs (executables,
    worker, sonar) are present too.
    """
    workflow = _ci_workflow(render(preset="full"))
    for name, job in workflow["jobs"].items():
        assert DRAFT_GUARD in job.get("if", ""), f"job {name} is not draft-gated"
    # Pre-existing job conditions must be preserved and `&&`-composed with the
    # draft guard, not replaced — and not `||`-composed, which would let draft
    # jobs run whenever the other operand is true.
    assert workflow["jobs"]["sonar"]["if"] == (
        "${{ github.event.pull_request.head.repo.fork != true"
        f" && {DRAFT_GUARD} }}}}"
    )
    assert workflow["jobs"]["check"]["if"] == f"${{{{ always() && {DRAFT_GUARD} }}}}"


def test_ci_reruns_when_a_pr_leaves_draft(render: Callable[..., Path]) -> None:
    """``ready_for_review`` is not a default ``pull_request`` type, and without it
    the draft guard would permanently skip CI for a PR opened as a draft.

    Read out of the parsed document rather than matched as a raw substring, so a
    reformat of the flow sequence by yamlfmt does not fail the test. PyYAML
    resolves the ``on`` key to the boolean ``True`` (YAML 1.1), hence the
    ``[True]`` index.
    """
    triggers = _ci_workflow(render())[True]["pull_request"]["types"]
    assert triggers == ["opened", "synchronize", "reopened", "ready_for_review"]


def test_documentation_examples_are_rendered_and_checked(
    render: Callable[..., Path],
) -> None:
    """Docs examples are literal-included modules covered by every quality gate."""
    root = render()
    example = root / "docs" / "examples" / "version_lookup.py"
    assert example.is_file()
    assert "def version_lookup()" in example.read_text(encoding="utf-8")

    usage = (root / "docs" / "usage.rst").read_text(encoding="utf-8")
    assert ".. literalinclude:: examples/version_lookup.py" in usage

    test = (root / "tests" / "test_docs_examples.py").read_text(encoding="utf-8")
    assert "test_all_documentation_examples_are_importable" in test
    assert "test_version_lookup_example_uses_the_installed_distribution" in test
    assert 'EXAMPLES_DIR.rglob("*.py")' in test

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    parsed_pyproject = tomllib.loads(pyproject)
    sdist_include = parsed_pyproject["tool"]["hatch"]["build"]["targets"]["sdist"][
        "include"
    ]
    assert "/docs/examples" in sdist_include
    for checker_scope in (
        'files = ["src", "docs/examples"]',
        'include = ["src/example", "docs/examples"]',
        'include = ["src", "tests", "docs/examples"]',
        'project-includes = ["src", "docs/examples"]',
        '"docs/examples",',
    ):
        assert checker_scope in pyproject
    assert '[tool.tox.env.docs-doctest]' in pyproject
    assert '"docs-doctest",' in pyproject
    assert '"sphinx.ext.doctest",' in (root / "docs" / "conf.py").read_text(
        encoding="utf-8"
    )


def test_docs_off_omits_documentation_examples_and_checks(
    render: Callable[..., Path],
) -> None:
    """The docs toggle owns the complete tested-examples subsystem."""
    root = render(include_docs=False)
    assert not (root / "docs" / "examples").exists()
    assert not (root / "docs" / "version_lookup.py").exists()
    assert not (root / "tests" / "test_docs_examples.py").exists()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "docs/examples" not in pyproject
    assert "docs-doctest" not in pyproject
