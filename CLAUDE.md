# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Copier template** for generating modern Python packages with comprehensive tooling. The `template/` directory contains Jinja2-templated files that are rendered when users run `copier copy` to scaffold new Python projects.

Key architecture:

- Template files use `.jinja` extension and contain variables like `{{github_repo_name}}`, `{{author_full_name}}`, etc.
- Template variables are defined in `copier.yml`
- The `example/` directory is a gitignored, locally-generated rendering (see `.gitignore`); regenerate it from `.example-input.yml` to smoke-test the template. Note: `.example-input.yml` disables every optional component, so the run commands below for CLI/web/etc. apply only after enabling those options (or to any other generated project)
- Generated projects use uv for dependency management, hatchling for builds, tox for testing, and include full CI/CD automation

## Development Commands

### Testing the Template

```bash
# Install dependencies
uv sync

# Test rendering with example inputs (dry run)
copier copy --data-file .example-input.yml --defaults . /tmp/test-project

# Actually generate the example project
copier copy --data-file .example-input.yml --defaults . example/

# Force regenerate (overwrites existing)
copier copy --data-file .example-input.yml --defaults . example/ --force

# Test with specific features enabled
copier copy --data-file .example-input.yml --data include_worker=true --data worker_broker=kafka --defaults --trust . /tmp/test-worker --force
```

### Working with Generated Projects

Commands for the `example/` directory (or any generated project):

```bash
cd example/

# Install dependencies
uv sync

# Run tests across all Python versions
uv run --locked tox run

# Run style checks (ruff, mypy, basedpyright, ty, pyrefly, zuban, vulture, slotscheck, taplo, validate-pyproject, typos, actionlint)
uv run --locked tox run -e style

# Run specific Python version tests
uv run --locked tox run -e 3.10
uv run --locked tox run -e 3.14

# Run a single test file
uv run --locked pytest tests/test_smoke.py -v

# Run worker broker integration tests (if include_worker=true; Docker required).
# On-demand tox env; marked `integration` and excluded from the default suite (ADR-008).
uv run --locked tox run -e integration

# Run the CLI (if include_cli=true)
uv run --locked example version
uv run --locked example info

# Run the FastAPI/Litestar web app (if include_web=true)
uv run --locked fastapi dev example.web.app:app

# Run the TUI (if include_tui=true)
uv run --locked example-tui

# Run the GUI (if include_gui=true)
uv run --locked example-gui

# Run the MCP server (if include_mcp=true)
uv run --locked example-mcp

# Run the worker (if include_worker=true)
uv run --locked example-worker

# Run prek hooks
uv run --locked tox run -e prek

# Build docs
uv run --locked tox run -e docs-build

# Serve docs locally
uv run --locked tox run -e docs-server

# Profiling (if include_profiling=true)
uv run --locked tox run -e profile
```

### Linting and Git Hooks

This repo uses [prek](https://prek.j178.dev) (a Rust pre-commit replacement)
configured via `prek.toml`.

```bash
# Run hooks on all files
prek run --all-files

# Install the git hooks
prek install
```

## Template Architecture

### Jinja2 Template Patterns

1. **Variable Substitution**: `{{github_repo_name}}` renders to the user's repo name
2. **Dynamic File Paths**: `src/{{github_repo_name}}/` creates package directories with user-provided names
3. **TODO Markers**: `TODO @{{github_user}}:` generates actionable TODOs in the rendered project
4. **Raw Blocks**: `{% raw %}${{ github.ref_name }}{% endraw %}` preserves GitHub Actions syntax
5. **Conditional Files**: `{% if condition %}filename{% endif %}.jinja` includes file only when condition is true
6. **Whitespace Control**: Use `{%-` and `-%}` to avoid extra blank lines in rendered output

### Template Variables (copier.yml)

Required inputs:

- `github_user`, `github_repo_name`, `author_full_name`, `author_email`, `short_description`

Free-form metadata:

- `package_keywords` - extra comma-separated PyPI keywords prepended to the generated
  `keywords` list (default empty); the template's own base keywords plus tooling and
  enabled-component keywords are always appended automatically. (The classifiers list
  is still auto-generated from enabled components — it carries a `TODO` marker for the
  generated project's author to fill in project-specific classifiers.)

Optional components (all boolean):

- `include_cli` - Typer CLI
- `include_web` - Web app + Dockerfile (framework choice: FastAPI or Litestar)
- `include_gui` - Tkinter GUI
- `include_tui` - Textual TUI
- `include_mcp` - MCP (Model Context Protocol) server
- `include_worker` - FastStream message queue worker
- `include_c_extensions` - Cython support with multi-platform wheels
- `include_profiling` - py-spy, scalene, cProfile tools
- `include_launcher` - uv-bootstrap launcher (PyCrucible) — small executable, downloads Python+deps on first run
- `include_compiler` - compiler (Nuitka) — source compiled to a native machine-code executable
- `include_freezer` - offline freezer (PyInstaller) — self-contained bundle, no Python on target

  These three standalone-executable toggles are independent and combinable; each
  maps to one architectural category (launcher / compiler / freezer). See
  [ADR-007](../docs/adr/007-standalone-executable-toggles.md).
- `include_pydantic_settings` - pydantic-settings for config

Framework/broker choices (when parent option is enabled):

- `web_framework` - fastapi/litestar (when `include_web` is true)
- `worker_broker` - kafka/nats/rabbitmq/redis (when `include_worker` is true)

Devcontainer services:

- `include_postgres` - PostgreSQL service
- `include_redis` - Redis/Valkey service
- `redis_backend` - redis/valkey image (when `include_redis` is true)
- `include_pgadmin` - pgAdmin UI (when `include_postgres` is true)
- `include_adminer` - Adminer UI (when `include_postgres` is true)
- `include_dbeaver` - CloudBeaver database management UI
- `include_vpn` - OpenVPN client

Always included (no toggle): a Keep-a-Changelog `CHANGELOG.md` (maintained by
release-please), Codecov coverage upload (`.github/codecov.yml` + CI step), Renovate
dependency management (`.github/renovate.json` — Dependabot and the `none` opt-out were
removed; there is no longer a `dependency_management` option), a `CITATION.cff`
file with a `validate-citation.yml` workflow (the `include_citation` toggle was
removed — it is now always rendered and validated via
`citation-file-format/cffconvert-github-action`), and mise
(`mise.toml` + devcontainer feature) for tool version management and task
running. Pants and Trunk were removed entirely — the tox `style` env is the sole
lint/build orchestrator (see [ADR-003](../docs/adr/003-tox-as-canonical-lint-runner.md)).

Also always included (no toggle): a `SUPPORT.md` community-health file (points to
docs/issues/discussions and cross-references `SECURITY.md`/`CONTRIBUTING.md`), a
`.gitattributes` (LF normalization matching the ruff/EditorConfig policy, Linguist
overrides marking `_version.py`/`CHANGELOG.md`/`uv.lock` as generated and `docs/`
as documentation, and `export-ignore` archive hygiene), and AI-agent onboarding
files — a concise `AGENTS.md` (the cross-tool standard) plus a `CLAUDE.md` that
`@AGENTS.md`-imports it so there is a single source of truth (no divergent copies).
`AGENTS.md` intentionally carries **no** commit-attribution/`Co-Authored-By` block.

Commitizen (Conventional Commit authoring/linting) is **always included** — it
is no longer gated behind an `include_commitizen` option. release-please still
owns versioning/changelog; Commitizen only authors/lints messages (see
[ADR-004](../docs/adr/004-commitizen-as-commit-helper-not-release-tool.md)).

Git hooks are **always included** (there is no `include_precommit`
option). They are run via [prek](https://prek.j178.dev), a Rust-native
pre-commit replacement, configured by a native `prek.toml` (not a
`.pre-commit-config.yaml`). The dependency group is `prek` and contains only
`prek`; both the tox `prek` env (`tox run -e prek`) and the CI `hooks` job invoke
`prek run --all-files`.

The tox `style` env (backed by the uv-managed `style` dependency group) is the
canonical lint/type-check runner for the full suite; the prek-run `prek.toml` is
the fast local/CI gate. Its hook `rev` pins are kept current by Renovate (a
`customManagers` regex entry in `.github/renovate.json`, since Renovate's built-in
pre-commit manager only reads `.pre-commit-config.yaml`). There is no
pre-commit.ci integration and no `sync-with-uv` hook — Renovate owns every
bump, including the tools shared with the uv `style` group.

The tox `style` env is the *single* lint/type-check orchestrator for a generated
project — there is no Pants or Trunk config to drift against it (both were
removed; see [ADR-003](../docs/adr/003-tox-as-canonical-lint-runner.md)).

### Generated Project Structure

Root modules in `src/{{github_repo_name}}/`:

- `__init__.py`, `__main__.py`, `__metadata__.py` - Package setup
- `_version.py` - Auto-generated by hatch-vcs (excluded from coverage)

Subpackages (each with `__init__.py` and `app.py`):

- `core/` - Core infrastructure (always included):
  - `dirs.py` - Project directory locations (`~/.<package>`)
  - `logging_setup.py` - Centralized logging
  - `config.py` - Configuration (uses pydantic-settings if enabled)
- `utils/` - Utility functions (always included)
- `cli/` - Typer CLI with `version` and `info` commands (conditional)
- `web/` - FastAPI/Litestar with `/version` and `/info` endpoints (conditional)
- `gui/` - Tkinter GUI launcher (conditional)
- `tui/` - Textual TUI (conditional)
- `mcp/` - MCP server with `version` and `info` tools (conditional)
- `worker/` - FastStream message queue worker (conditional). The broker is built
  by a `build_broker(url=None)` factory that registers the subscriber/publisher
  and resolves the connection at call time (not import time), so tests can point
  a fresh, self-contained broker at a throwaway instance (e.g. testcontainers)
  without import-order/caching pitfalls; the module still exposes a default
  `broker = build_broker()` for the entry point. See
  [ADR-008](../docs/adr/008-worker-broker-testing-strategy.md).

Other conditional files:

- `_c_extension.pyx`, `.pxd`, `.pyi` - Cython extension files
- `profile.py` - Profiling script
- `<pkg>.spec` - PyInstaller spec file (conditional on `include_freezer`)

Test packages mirror source structure in `tests/`:

- `tests/cli/`, `tests/web/`, `tests/gui/`, `tests/tui/`, `tests/mcp/`, `tests/worker/` (each conditional)
- `tests/worker/` holds both the in-memory `Test<Broker>` unit tests (always run)
  and a testcontainers-backed integration test marked `integration` (excluded
  from the default run, Docker required); see
  [ADR-008](../docs/adr/008-worker-broker-testing-strategy.md).

Entry points configured in `pyproject.toml`:

- `project.scripts`: `pkg.cli.app:app`, `pkg.tui.app:main`, `pkg.web.app:main`, `pkg.mcp.app:main`, `pkg.worker.app:main`
- `project.gui-scripts`: `pkg.gui.app:main` (launches without terminal)

### Devcontainer Structure

The `.devcontainer/docker-compose.yml.jinja` consolidates all services:

- `devcontainer` - Main development container (always included)
  - Uses `ghcr.io/astral-sh/uv:python3.14-bookworm-slim` image directly (no Dockerfile)
  - `devcontainer.json.jinja` features: `git:1` and `mise:1` (both always)
  - When `include_vpn` is true, devcontainer sets `network_mode: "service:vpn"` and depends on the `vpn` service so all traffic routes through the VPN tunnel
  - `depends_on` waits on `condition: service_healthy` for services that define a healthcheck (postgres, redis, kafka, rabbitmq) and `service_started` for the rest (nats, vpn)
- Database services (conditional):
  - `postgres` - PostgreSQL with healthcheck (conditional on `include_postgres`)
  - `redis` - Redis/Valkey with healthcheck (conditional on `include_redis` or a `redis` worker broker; image set by `redis_backend`)
  - `pgadmin` / `adminer` - DB UIs behind the `tools` compose profile (conditional on `include_pgadmin` / `include_adminer`)
- Message broker services (conditional on `include_worker` + `worker_broker`):
  - `kafka` - Bitnami Kafka (KRaft mode), healthcheck via `kafka-topics.sh`
  - `nats` - NATS with JetStream (no healthcheck; minimal image)
  - `rabbitmq` - RabbitMQ with management UI, healthcheck via `rabbitmq-diagnostics`
  - `redis` - Redis (shared with the database `redis` service above)
- `cloudbeaver` - DBeaver CloudBeaver (conditional on `include_dbeaver`)
- `vpn` - OpenVPN client sidecar (conditional on `include_vpn`)
  - Uses `dperson/openvpn-client` with `NET_ADMIN` cap and `/dev/net/tun` device
  - Mounts `./vpn:/vpn` — drop `.ovpn` config + optional `vpn.auth` credentials there
  - Conditional `vpn/` subdir is rendered with a README and `.gitignore` (whitelists README only)
  - Devcontainer shares the vpn service's network namespace via `network_mode`; port forwards must be declared on the `vpn` service rather than `devcontainer`

### Build System

- **Builder**: `hatchling` with `hatch-vcs` plugin
- **Versioning**: Git tags via hatch-vcs, fallback to 0.1.0
- **Build Command**: `uv build`

### CI/CD Workflows

1. **CI** (`ci.yml.jinja`): Matrix tests on Windows/Ubuntu/macOS, Python 3.10-3.14
   - Codecov coverage upload is gated on the `CODECOV_TOKEN` secret: a job-level
     `CODECOV_TOKEN_SET` presence flag (the `secrets` context is unavailable in
     `if:`) gates the upload step, and when the secret is unset an Ubuntu-only
     `::notice::` records a visible skip instead of failing the run — coverage
     reporting is opt-in/best-effort, not load-bearing for a green build.
     Forked-PR runs (which never receive secrets) still run the upload so the
     codecov-action's tokenless fallback reports coverage for external
     contributors; only same-repo runs with no token hit the visible skip.
     Setup is documented in the generated `CONTRIBUTING.md` repository-setup section.
   - When `include_launcher`/`include_freezer`/`include_compiler` are set, adds
     matching `build-{launcher,freezer,compiler}-check` jobs (per-OS, `fail-fast:
     false`) that build the standalone executable on every PR/push — a build-only
     packaging guard so a dep/Python bump that breaks bundling fails against the
     offending diff instead of silently at release time (the test suite never
     exercises the built binary). Each verifies the binary was produced,
     smoke-runs it with `--help` when `include_cli` is set, and uploads a 7-day
     preview artifact. They closely follow the `release-please.yml` build jobs
     (same setup + build commands), skipping the release-only rename/publish
     steps, and they gate the `check` aggregation job. See
     [ADR-007](../docs/adr/007-standalone-executable-toggles.md).
   - When `include_worker` is set, adds a single `worker-integration` job —
     **Ubuntu-only** (Docker is reliably present on GitHub's Ubuntu runners but
     not macOS/Windows) — that runs `tox run -e integration` (an on-demand tox
     env invoking `pytest -m integration`) against a real `worker_broker` started
     via testcontainers. The default OS matrix stays broker-free and fast (the
     `integration` marker is deselected by default via the pytest `addopts`); this
     job is the only thing exercising the real driver, and it gates the `check`
     aggregation job. See [ADR-008](../docs/adr/008-worker-broker-testing-strategy.md).
2. **Release + CD** (`release-please.yml.jinja`): one unified workflow (there is
   no separate `cd.yml`). Standardized on release-please — no longer configurable
   (see [ADR-002](../docs/adr/002-release-please-for-release-automation.md)). Jobs:
   - `release-please`: opens/maintains a release PR from Conventional Commits on
     push to `main`; on merge, tags the commit and creates a **draft** GitHub
     Release (`draft: true` in `.github/release-please-config.json`). Exposes
     `release_created`, `tag_name`, `version` as outputs.
   - All later jobs gate on `needs.release-please.outputs.release_created == 'true'`.
   - `build`: builds with uv. When `include_c_extensions` is set, runs as a
     per-platform `fail-fast: false` matrix (Ubuntu/Windows/macOS) producing the
     multi-platform Cython wheels + sdist; `pypi-publish` uploads them all.
   - `pypi-publish`: trusted publishing (`id-token: write`, environment `publish`).
   - `build-launcher` (when `include_launcher`, PyCrucible) / `build-freezer`
     (when `include_freezer`, PyInstaller) / `build-compiler` (when
     `include_compiler`, Nuitka) / `docker-publish` (when
     `include_web`): conditional matrix jobs. The three executable jobs are
     independent `fail-fast: false` matrices producing per-platform artifacts
     named `<repo>-executable-{launcher,freezer,compiler}-<os>`, all caught by
     `attach-github-release`'s `<repo>-executable-*` download pattern (see
     [ADR-007](../docs/adr/007-standalone-executable-toggles.md)). Docker tags feed
     `needs.release-please.outputs.tag_name` into the metadata-action `value=`
     because a push-triggered run has no tag ref.
   - `attach-github-release`: uploads artifacts to the still-draft release.
   - `finalize-release`: un-drafts the release and reconciles the phantom
     next-release PR (close + re-dispatch — bounded to one re-run).
   - `deploy-docs` (`needs: finalize-release`): builds the Sphinx docs and runs
     `ghp-import` to publish them. Lives in
     this workflow rather than reacting to `release: published` because an event
     fired by `finalize-release`'s `GITHUB_TOKEN` cannot trigger another workflow
     (the same loop-prevention rule that forces the `workflow_dispatch`
     re-dispatch above). `gh-pages.yml` is kept only for manual redeploys.
     Docs are built with Sphinx + the Shibuya theme (autodoc API reference),
     not MkDocs (see [ADR-006](../docs/adr/006-sphinx-shibuya-for-documentation.md)).
   - Versions come from git tags via hatch-vcs, so release-please never edits a
     static version literal and `uv.lock` cannot desync.
3. **PR title linting** (`check-pr-title.yml`): validates the **PR title** (not
   individual commits) against Conventional Commits via
   `amannn/action-semantic-pull-request`.
4. **Linked-issue check** (`check-linked-issues.yml`): fails a PR that has no
   linked issue (the GitHub *Development* relationship, created by a `Closes #N`
   keyword in the PR body) via `nearform-actions/github-action-check-linked-issues`.
   It checks the real `closingIssuesReferences` relationship, not just body text;
   apply the `no-issue` label to bypass the check. Keep it as a required status
   check alongside `check-pr-title`.
5. **PR task-list completion check** (`task-completed-check.yml`): on
   `pull_request_target` (`opened`/`edited`), runs
   `kentaro-m/task-completed-checker-action` to post a check run that fails while
   any task-list checkbox in the PR description is unticked. Uses
   `pull_request_target` (least-privilege `checks: write` + `pull-requests: read`)
   so the check also runs on fork PRs; wrap throwaway lists in
   `<!-- ignore-task-list-start -->` / `<!-- ignore-task-list-end -->` to skip them.
6. **Branch-name linting** (`check-branch-name.yml`): validates the PR's **head
   branch name** (`github.head_ref`) against the
   [Conventional Branch](https://conventionalbranch.org/) format
   (`<type>/<description>`). Allowed prefixes are exactly the spec's set —
   `feature`/`feat`, `bugfix`/`fix`, `hotfix`, `release`, `chore`, plus the
   AI-agent prefixes `ai`/`copilot`/`cursor`/`claude`/`codex` — **not** the
   broader Conventional Commits type set (`docs`, `style`, `refactor`, etc. are
   commit types, not branch types). It is a dependency-free inline shell regex (no marketplace action — the
   maintained options were either abandoned or on a deprecated Node runtime), run
   under `pull_request_target` with `pull-requests: write` so it can post a sticky
   failure comment on fork PRs, mirroring `check-pr-title.yml`. The `renovate/*`
   and `release-please--*` automation branches are whitelisted so bot PRs are
   never blocked. Branch names never reach `main` (squash-merge uses the PR
   title), so this is repo hygiene — not load-bearing for release-please. Keep it
   as a required status check (context: **Validate branch name**) alongside
   `check-pr-title`, `check-linked-issues`, and **Task Completed Checker**
   (`task-completed-check.yml`).
7. **Supply-chain security** (always included, static workflows):
   - `codeql.yml`: CodeQL analysis on push/PR to `main` + weekly schedule.
   - `scorecard.yml` (`ossf/scorecard-action`): OpenSSF Scorecard on
     `branch_protection_rule`/push/weekly schedule; `publish_results: true` and
     `id-token: write` so the public Scorecard badge (added to the generated
     README) resolves, uploading SARIF to code-scanning. Public repos only.
   - `dependency-review.yml` (`actions/dependency-review-action`): on `pull_request`,
     **fails on high+ severity** vulnerabilities and comments a summary on failure.
   - `check-security.yml.jinja`: an active scanning pass on PR/push to `main` +
     weekly cron, complementing the three above (which are SAST / repo-posture /
     PR-diff). Jobs:
     - `gitleaks` (`gitleaks/gitleaks-action`, always): secret scan over full git
       history (`fetch-depth: 0`) — catches secrets CodeQL does not and reaches
       past commits that GitHub's push protection never guarded. Free for
       personal accounts/public repos; an org must add a `GITLEAKS_LICENSE`
       secret (noted inline in the workflow).
     - `pip-audit` (always): `uv export`s the locked shipped deps
       (`--all-extras --no-dev --no-emit-project --no-hashes`) and audits them
       with `uvx pip-audit`. `--all-extras` is load-bearing: this template keeps
       component dependencies under `[project.optional-dependencies]` extras with
       an empty base `dependencies = []`, so an export without it is empty and
       the audit/SBOM silently cover nothing. `--all-extras` applies equally to
       the release `sbom` job's export — though that job omits `--no-hashes`
       (the SBOM keeps per-pin integrity hashes; only pip-audit drops them, since
       its resolver would otherwise demand a hash for every transitive pin).
       Unlike `dependency-review` (PR-diff only, GitHub Advisory
       DB), this re-audits the *entire* resolved tree against the PyPI Advisory
       DB on the weekly cron, so a CVE disclosed *after* a dependency merged is
       caught while it is still pinned.
     - `trivy-image` (**`include_web` only**): builds the generated `Dockerfile`
       and scans the image with `aquasecurity/trivy-action`
       (`severity CRITICAL,HIGH`, `ignore-unfixed: true`, `exit-code: 1`). Gated
       on `include_web` because that is the only configuration that produces a
       Dockerfile; the filesystem-scan overlap with `pip-audit` is deliberately
       avoided (image/OS-layer scanning is the genuine gap).
   These SHA-pin actions like every other workflow (Renovate
   `helpers:pinGitHubActionDigests` keeps them current). This is a standalone
   workflow (like `codeql`/`scorecard`), *not* wired into the `ci.yml` `check`
   aggregation gate. A CycloneDX **SBOM** (`<repo>-sbom.cdx.json`) is generated
   from the locked runtime deps by a `sbom` job in `release-please.yml` and
   attached to each GitHub Release (via `attach-github-release`), not kept as a
   throwaway CI artifact.

### Required Merge Strategy (release-please depends on it)

release-please derives version bumps and changelog sections solely from the
Conventional Commit messages that land on `main`. This template validates the
**PR title** but not in-PR commits, so generated repos **must use "Squash and
merge" with the squash commit message set to the PR title** — that is the only
strategy under which the lint-validated title becomes the commit on `main`.
Merge-commit and rebase-merge promote unvalidated branch commits and will cause
release-please to miss releases or bump them incorrectly.

Configure each generated repo (Settings → General → Pull Requests):

- Allow squash merging (ideally disable merge commits and rebase merging).
- Set the squash "Default commit message" to **"Pull request title"**.
- Enable **Automatically delete head branches**.
- Keep `check-pr-title` as a required status check.

release-please also needs **Settings → Actions → General → Workflow permissions
→ Allow GitHub Actions to create and approve pull requests** enabled, or it
cannot open/maintain the release PR. Generated repos should additionally enable
**release immutability** (Settings → General). The generated
`CONTRIBUTING.md` documents all of these as a one-time "Repository setup"
section, including ready-to-run `gh repo edit` / `gh api` commands and the PyPI
trusted-publishing registration — keep that section in sync when these
requirements change.

Bump rules follow `.github/release-please-config.json`: `feat` → minor, `fix`/`perf` →
patch, `feat!`/`BREAKING CHANGE` → major — but `bump-minor-pre-major: true`
keeps breaking changes at a minor bump while pre-1.0.

### PyPI Trusted Publishing Setup

For generated projects to publish to PyPI:

1. Go to <https://pypi.org/manage/account/publishing/>
2. Add pending publisher with:
   - PyPI Project Name: `<package-name>`
   - Owner: `<github-username>`
   - Repository: `<repo-name>`
   - Workflow: `release-please.yml` (the publish step is inline in this workflow,
     so this is the filename PyPI's OIDC check matches — not a reusable `cd.yml`)
   - Environment: `publish`

## Code Style Guidelines

- **Imports**: Absolute only, grouped stdlib→third-party→local (ruff enforced)
- **Formatting**: Ruff, 88 chars, LF endings
- **Types**: Strict typing required, `from typing import ...`
- **Naming**: snake_case vars/functions, PascalCase classes, UPPER_CASE constants
- **Complexity**: Max cyclomatic complexity of 5 (ruff mccabe)
- **Structure**: Code in `src/{{github_repo_name}}/`, tests in `tests/`

## Template Modification Guidelines

### Adding New Template Files

1. Create file in `template/` with `.jinja` extension
2. For conditional files, use `{% if condition %}filename{% endif %}.jinja` naming
3. Use `{{variable_name}}` for Copier variable substitution
4. Test by regenerating `example/` directory

### Adding New Optional Components

1. Add boolean variable to `copier.yml` with `type: bool`, `default`, and `help`
2. If component has choices (like `worker_broker`), add a separate choice variable with `when: "{{ parent_option }}"`
3. Create conditional directory: `template/src/{{github_repo_name}}/{% if include_xxx %}xxx{% endif %}/`
4. Create matching test directory: `template/tests/{% if include_xxx %}xxx{% endif %}/`
5. Update `pyproject.toml.jinja`:
   - Add optional dependency
   - Add to `all` extras
   - Add entry point if applicable
   - Add keywords
6. Update `.example-input.yml` with the new option
7. Update `README.md` with documentation
8. Keep the component's coverage at the `fail_under = 99` gate (see
   [ADR-008](../docs/adr/008-worker-broker-testing-strategy.md)). Because
   `.example-input.yml` disables every component, a component's coverage is only
   validated when you generate it explicitly — do that and run the suite. Unit-test
   the business logic *including reachable error handling* (metadata-failure
   paths are tested via a `_MissingDistribution` monkeypatch stub — see the
   web/cli/gui/tui/mcp tests); only for genuinely untestable blocking
   entrypoints add `# pragma: no cover` to the specific launch/display function
   (as the `main()` entrypoints, the CLI launcher subcommands, the GUI/TUI
   `_display_*` helpers, and the worker lifecycle hooks do). Do **not** add
   blanket `exclude_lines` regexes for these — see the convention below.

### Coverage exclusion convention

Generated projects enforce `fail_under = 99`. Entrypoints that start a blocking
loop (`main()`, `run_server`, real tkinter/textual/uvicorn/stdio code) cannot
run under headless CI, so each carries a per-site `# pragma: no cover` (the
web/MCP/worker `main()` entrypoints and `__main__` dispatchers, the MCP
`run_server`, the CLI `interactive`/`gui`/`web` subcommands, the GUI/TUI
`_display_*` helpers, the worker lifecycle hooks, the c-extension
`except ImportError` fallback, and the worker's module-level metadata
fallback). The logic those entrypoints call is always unit-tested.

Do **not** exclude these via blanket `[tool.coverage.report] exclude_lines`
regexes (`def main\(`, `except PackageNotFoundError`, ...): a regex matching a
`def` line excludes the *entire function body*, so such patterns silently
un-measure any future function with the same name that carries real logic —
and previously masked the tested GUI/TUI `main()` entrypoints and the web 503
handlers. Reachable error handling is tested, not excluded: the web `/version`
and `/info` 503 responses, the CLI metadata-failure exit code, the GUI/TUI
"Version: unknown" degradation, and the MCP error-text response all have unit
tests using a `_MissingDistribution` monkeypatch stub.

Coverage measurement spans two layouts: `src/...` in an editable dev install and
`.../site-packages/...` when tox/CI installs the built wheel/sdist (the tox test
env uses `package = "wheel"`/`"sdist"`). Two config settings must account for this
or the gate silently fails for *every* generated project:

- `[tool.coverage.paths]` must remap the installed tree back to the canonical
  `src/` tree — `{{pkg}} = ["src/{{pkg}}", "*/site-packages/{{pkg}}"]`. Each tox
  Python env installs into its own `site-packages`, so without remapping,
  `coverage combine` keeps a separate copy per env and a version-gated line
  covered in one interpreter but not another counts as missed. This only shows up
  under the full multi-env `tox run`, not a single env or editable `pytest`.
- `omit` globs must be anchored to match both layouts (`*/_version.py`,
  `*/worker/test_integration.py`), not `src/**` — a `src/**` pattern misses the
  installed copy and reports it at 0%. The integration glob is additionally
  directory-anchored so a future `test_integration.py` in another component
  (which *would* run in the default suite) stays measured.

Always verify coverage via the real `tox run` path (installed package, all envs),
never editable `pytest` — both defects are invisible otherwise. See
[ADR-008](../docs/adr/008-worker-broker-testing-strategy.md).

### Modifying Template Variables

1. Edit `copier.yml` to add/change variables
2. Add validation regex if needed (see `github_repo_name` validator)
3. Update all `.jinja` files that reference the variable
4. Regenerate example to verify

### Template Conventions

- **Escaping**: Use `{% raw %}{% endraw %}` for GitHub Actions syntax
- **Comments**: Template-only comments use `{# #}`, generated comments use `#`
- **TODOs**: Use `TODO @{{github_user}}:` pattern for actionable items
- **Whitespace**: Use `{%-` and `-%}` to eliminate blank lines from conditionals

### Testing Template Changes

Always test changes by:

1. Regenerating the example: `copier copy --data-file .example-input.yml --defaults . example/ --force`
2. Running style checks: `cd example && uv run --locked tox run -e style`
3. Running tests: `cd example && uv run --locked tox run`

For features with choices (like `worker_broker`), test multiple combinations:

```bash
copier copy --data-file .example-input.yml --data include_worker=true --data worker_broker=kafka --defaults --trust . /tmp/test-kafka --force
copier copy --data-file .example-input.yml --data include_worker=true --data worker_broker=rabbitmq --defaults --trust . /tmp/test-rabbitmq --force
```

## Copier-Specific Behavior

- **Subdirectory**: `_subdirectory: template` means Copier renders from `template/` not root
- **Answers File**: `{{_copier_conf.answers_file}}.jinja` becomes `.copier-answers.yml`
- **Update Workflow**: Users run `copier update` to pull template changes
- **Post-copy Task**: `git init` runs automatically after scaffolding
- **Trust Flag**: Use `--trust` when testing locally to run post-copy tasks
