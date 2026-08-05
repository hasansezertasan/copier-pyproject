# copier-pyproject

Copier template for a modern, typed Python package/CLI with `uv`, `hatch`, `tox`, and GitHub automation baked in.

## Features

Always included in every generated project:

- **Packaging & workflow** — uv-first with dependency groups (dev, style, test, docs, tool, prek) and tox-uv runners across Python 3.10–3.14; builds via `hatchling`/`hatch-vcs` with versions derived from Git tags.
- **Type safety** — full type hints and a `py.typed` marker, checked by mypy, basedpyright, ty, pyrefly, and zuban.
- **Code quality** — ruff linting/formatting plus vulture, slotscheck, taplo, validate-pyproject, typos, actionlint, editorconfig-checker, and import-linter architecture-contract enforcement.
- **Testing** — pytest with coverage/xdist/reruns (and `.github/codecov.yml`) and parallel execution.
- **Documentation** — a Sphinx scaffold (`docs/index.rst` + `conf.py`) with the Shibuya theme and autodoc API reference, GitHub Pages deployment, and live per-PR previews.
- **CI/CD & release** — matrix tests on macOS/Linux/Windows, trusted-publishing to PyPI, and release automation via release-please, with PR title linting, linked-issue enforcement, and a PR task-list completion check.
- **Security** — CodeQL, OpenSSF Scorecard (with README badge), a dependency-review gate that blocks high-severity vulnerabilities, active scanning (gitleaks, pip-audit, and Trivy for web images), GitHub Actions static analysis (zizmor + ghalint) enforcing least-privilege `permissions`, `persist-credentials: false`, per-job `timeout-minutes`, and full-length action SHA pins — a blocking prek/CI gate plus a zizmor Security-tab dashboard — and a CycloneDX SBOM attached to every release.
- **Repo hygiene** — issue/PR templates, `SECURITY.md`, `SUPPORT.md`, `CODEOWNERS`, `FUNDING`, `LICENSE`, `.gitattributes`, `.dockerignore`, a badge-rich README, and VS Code launch configs (current file, tests, attach, entry points); always-on Commitizen and git hooks (run via prek) and an always-on `CITATION.cff` with a validation workflow.
- **Managed `.gitignore`** — kept in sync with the upstream [github/gitignore](https://github.com/github/gitignore) templates by [cobo](https://github.com/hasansezertasan/cobo), with a weekly drift check.
- **Dependency & template updates** — Renovate manages dependencies and, via its copier manager, opens a `copier update` PR whenever this template publishes a new tag (see [ADR-015](docs/adr/015-template-self-versioning-and-copier-update-automation.md)).
- **AI-agent onboarding** — a concise `AGENTS.md` (the cross-tool standard) plus a `CLAUDE.md` that imports it, so coding agents share a single source of truth.
- **Modern Python** — uv for dependency management, hatch for building, and a devcontainer for reproducible environments.

Opt in per project (see [Inputs](#inputs) for the full list): a Typer CLI, a FastAPI/Litestar web app (container-ready `Dockerfile`), a Tkinter GUI, a Textual TUI, an MCP server, a FastStream worker, Cython C extensions with multi-platform wheel building, profiling tools (py-spy, scalene, cProfile), standalone-executable packaging (PyCrucible / Nuitka / PyInstaller), and extra quality integrations — SonarCloud, Sourcery, all-contributors, and MegaLinter (adds gap checks — shellcheck, hadolint, jsonlint, jscpd clone-detection, and a `.md`-scoped cspell prose pass — not already covered by prek/tox).

## Inputs

Copier will prompt for:

- `github_user`
- `github_repo_name` (valid Python package name: lowercase letters/digits/underscores, starts with a letter, and not a Python reserved keyword — used verbatim as the import package name, so no dashes)
- `author_full_name`
- `author_email`
- `short_description`
- `package_keywords` (extra comma-separated PyPI keywords; tooling/component keywords are added automatically)
- `include_cli` (include Typer CLI)
- `include_web` (include web API)
- `web_framework` (fastapi/litestar - when `include_web` is enabled)
- `include_gui` (include Tkinter GUI)
- `include_tui` (include Textual TUI)
- `include_mcp` (include MCP server support)
- `include_worker` (include message queue worker using FastStream)
- `worker_broker` (kafka/nats/rabbitmq/redis - when `include_worker` is enabled)
- `include_c_extensions` (include C extensions support using Cython)
- `include_profiling` (include profiling and performance tools)
- `include_examples` (include an `examples/` folder with simple and advanced usage stubs)
- `include_launcher` (uv-bootstrap launcher via PyCrucible — small executable, downloads Python+deps on first run)
- `include_compiler` (compiled native executable via Nuitka — source compiled to machine code)
- `include_freezer` (offline freezer via PyInstaller — self-contained bundle, no Python on target)
- `include_pydantic_settings` (use pydantic-settings for configuration)
- `include_megalinter` (opt-in extra CI quality layer; runs gap linters — shellcheck, hadolint, jsonlint, jscpd, and a `.md`-scoped cspell — not covered by prek/tox)
- `include_postgres` (include PostgreSQL service in devcontainer)
- `include_redis` (include Redis/Valkey service in devcontainer)
- `redis_backend` (redis/valkey - when `include_redis` is enabled)
- `include_pgadmin` (include pgAdmin - when `include_postgres` is enabled)
- `include_adminer` (include Adminer - when `include_postgres` is enabled)
- `include_dbeaver` (include CloudBeaver database UI in devcontainer)
- `include_vpn` (include OpenVPN sidecar in devcontainer)

## Scaffold a project

1. Install Copier and uv (e.g., `uvx copier`).
2. Run `copier copy gh:hasansezertasan/copier-pyproject <destination>` (or `copier copy . <destination>` from a local clone).
3. Optionally seed answers with `.example-input.yml` using `--data-file .example-input.yml --defaults`.
4. Initialize git in the destination: `cd <destination> && git init` (the template intentionally defines no Copier tasks, so it does not auto-init — see [ADR-015](docs/adr/015-template-self-versioning-and-copier-update-automation.md)).
5. Open the generated README (rendered from `template/README.md.jinja`) and clear the `TODO @...` markers in `README.md`, `pyproject.toml`, docs, and workflows.

## Adopt into an existing project (Claude Code plugin)

The `copier copy` flow above is for **new** projects. Adopting this template into an **existing or already-published** package is a different job: `copier copy` overwrites source, config, docs, and CI, so it must be run as a migrate-and-reconcile rather than a scaffold.

This repository therefore doubles as a [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) **plugin** that ships an `adopt-copier-pyproject` skill capturing that procedure — the source-skeleton collision, ruff auto-fix source corruption, the release-please/hatch-vcs version clash, the `copier update` 3-way-merge flow, and the placeholder prose the template plants in issue templates and docs. Plugin metadata lives in [`.claude-plugin/`](.claude-plugin) and the skill in [`skills/adopt-copier-pyproject/SKILL.md`](skills/adopt-copier-pyproject/SKILL.md).

### For humans

Install the plugin once from inside Claude Code:

```text
/plugin marketplace add hasansezertasan/copier-pyproject
/plugin install copier-pyproject@copier-pyproject
```

Then, in a Claude Code session opened **inside the package you are adopting the template into**, describe the task (e.g. "adopt copier-pyproject into this project"). Claude follows the skill's procedure and checks in with you at each decision it cannot make alone — the planted `TODO` markers, the issue-template example prose, and the release-please version manifest.

### For agents

Once the plugin is installed the skill is auto-discovered; no explicit invocation is needed. It triggers on its own whenever a task matches its description: adopting `hasansezertasan/copier-pyproject` into an existing package, or reconciling a `copier update` that overwrote source/config. Working directly from a clone (without installing the plugin), an agent can read [`skills/adopt-copier-pyproject/SKILL.md`](skills/adopt-copier-pyproject/SKILL.md) and follow it as a checklist.

> [!NOTE]
> For a brand-new project, ignore the plugin and use [Scaffold a project](#scaffold-a-project) above — the skill is only for adopting the template into code that already exists.

## Generated project quickstart

- Install dependencies: `uv sync`
- Style gate: `uv run --locked tox run -e style`
- Full test suite: `uv run --locked tox run`
- Run the CLI (if included): `uv run --locked <repo-name> version`
- Run the web app (if included): `uv run --locked <repo-name>-web`
- Serve docs locally: `uv run --locked tox run -e docs-server` (deploys via GitHub Pages on release)

`.example-input.yml` provides default values for all template options.

## Release automation

Release automation is standardized on [release-please](https://github.com/googleapis/release-please) (see [ADR-002](docs/adr/002-release-please-for-release-automation.md)). A single unified workflow, `.github/workflows/release.yml`, orchestrates the whole release:

1. On push to `main`, release-please opens a release PR derived from your Conventional Commits.
2. Merging that PR creates the git tag and a **draft** GitHub Release.
3. The same workflow then builds with uv, publishes to PyPI via trusted publishing, attaches the build artifacts to the draft, and only then **un-drafts** the release — so the release is never visible without its artifacts.
4. Once the release is un-drafted, the workflow's `deploy-docs` job builds the Sphinx docs and publishes them with `JamesIves/github-pages-deploy-action`. Docs deploy inline here (rather than via a `release: published` trigger) because an event fired by `GITHUB_TOKEN` cannot start another workflow; `.github/workflows/gh-pages.yml` is kept for manual redeploys only.

CI runs on macOS/Linux/Windows via `.github/workflows/ci.yml.jinja`.

Versions are derived from git tags by hatch-vcs (`dynamic = ["version"]`), so release-please never edits a static version literal and `uv.lock` cannot desync. `bump-minor-pre-major` keeps pre-1.0 projects pre-1.0.

### PyPI Trusted Publishing setup

Enable PyPI once per project for `.github/workflows/release.yml`:

1. Open [Trusted Publisher Management](https://pypi.org/manage/account/publishing/).
2. Under "Add a new pending publisher", pick "GitHub".
3. Set `PyPI Project Name` to your package name.
4. Set `Owner` to your GitHub username.
5. Set `Repository name` to your repo name.
6. Set `Workflow name` to `release.yml`. The PyPI publish step lives in this workflow (not a reusable one), so this is the filename PyPI's OIDC check matches against.
7. Set `Environment name` to `publish` (or your chosen env).
8. Save.

### Coverage reporting setup

CI uploads coverage to Codecov after the test suite runs, integrated in
`.github/workflows/ci.yml`. **On a public repository this needs no setup** — the
codecov-action uploads tokenless, so owner pushes and fork PRs both report
coverage out of the box.

A `CODECOV_TOKEN` is only required for a **private** repository (or to avoid
tokenless rate-limits):

1. Open [Codecov](https://app.codecov.io/) and add your repository.
2. Copy the repository upload token from its Codecov settings.
3. In your GitHub repository, add it as a repository secret named
   `CODECOV_TOKEN` (Settings → Secrets and variables → Actions, or
   `gh secret set CODECOV_TOKEN`).

The upload is best-effort either way: on a private repo with no token, CI records
a notice and skips the upload rather than failing the run. The generated
`CONTRIBUTING.md` documents the same setup for contributors to your project.

### Documentation site and dependency updates

Two more one-time steps are needed after generating a project (both are
documented in full, with copy-paste commands, in the generated
`CONTRIBUTING.md` repository-setup section):

- **GitHub Pages** — on release, the `deploy-docs` job pushes the built Sphinx
  docs to a `gh-pages` branch. Enable Pages once (Source → *Deploy from a
  branch* → `gh-pages` / root) after the first release creates the branch,
  otherwise the docs build but are never served.
- **Renovate** — `.github/renovate.json` is read by the hosted
  [Renovate app](https://github.com/apps/renovate), which must be installed on
  the repository once; until then dependency-update PRs never open.

### Container image publishing (if `include_web` is enabled)

On release, the workflow always publishes multi-arch images (amd64/arm64) to the
GitHub Container Registry (`ghcr.io/<owner>/<repo>`) using the built-in
`GITHUB_TOKEN` — no extra setup required.

Docker Hub publishing is optional, opted into via a pair of repository secrets
(integrated in `.github/workflows/release.yml`):

1. Open [Personal access tokens](https://app.docker.com/settings/personal-access-tokens)
   in your Docker Hub account settings.
2. Click "Generate new token", give it a recognizable description (e.g.
   `<repo> release workflow`), set an expiration date, and select the
   **Read & Write** access permission — Write is required to push; do not
   grant more.
3. Copy the token; it is shown only once.
4. In your GitHub repository, go to Settings → Secrets and variables →
   Actions (or use `gh secret set`) and add two repository secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: The access token from step 3
5. On release, the workflow will build and push multi-arch images
   (amd64/arm64) to `docker.io/<DOCKERHUB_USERNAME>/<repo>` alongside GHCR.
   The namespace follows the Docker Hub account, so it does not need to
   match the GitHub owner.

The secret pair is all-or-nothing: with neither set, the workflow skips Docker
Hub with a notice and publishes to GHCR only; with exactly one set, a preflight
job fails fast and blocks every publish channel (PyPI included) so a
misconfiguration can never produce a partial release. The generated
`CONTRIBUTING.md` documents the same setup for contributors to your project.

### Release steps

Releases are driven by Conventional Commits — you do not draft releases by hand:

1. Land `feat:` / `fix:` commits on `main`. release-please opens (and keeps updating) a release PR with the computed version bump and changelog.
2. Merge the release PR when you want to ship. This creates the git tag and a draft GitHub Release.
3. The `release.yml` workflow then builds the wheel/sdist with uv, publishes to PyPI via trusted publishing, attaches artifacts to the draft, and un-drafts the release.
4. If `include_web` is enabled it also builds and pushes multi-arch Docker images; if any of `include_launcher` (PyCrucible), `include_compiler` (Nuitka), or `include_freezer` (PyInstaller) is enabled it also builds standalone executables for Windows, macOS, and Linux and attaches them to the release.

### Release workflow structure

The unified `release.yml` orchestrates every release job; all jobs after `release-please` run only when a release was created:

```text
release-please ─► build ─┬─► pypi-publish ────────┐
                         ├─► build-launcher ──────┤
                         ├─► build-freezer ───────┼─► attach-github-release ─┐
                         ├─► build-compiler ──────┘                          │
                         │   (if launcher / freezer / compiler)              ▼
                         └─► docker-publish ───────────────────────────────► finalize-release        ► deploy-docs
                             (if web)                                        (un-draft + reconcile)    (sphinx-build + pages-deploy)
```

- **release-please**: Opens/maintains the release PR; on merge, tags and creates the draft release
- **build**: Builds the Python wheel/sdist with uv (matrix per-OS when `include_c_extensions`)
- **pypi-publish**: Publishes to PyPI via trusted publishing
- **build-launcher** / **build-freezer** / **build-compiler**: Build standalone executables for 3 platforms via PyCrucible / PyInstaller / Nuitka respectively (each conditional and independent)
- **docker-publish**: Builds and pushes multi-arch Docker images (conditional)
- **attach-github-release**: Attaches all artifacts to the still-draft release
- **finalize-release**: Un-drafts the release and reconciles the next release PR
- **deploy-docs**: Builds the Sphinx docs and publishes them with `JamesIves/github-pages-deploy-action` after the release is un-drafted (inline, since a `GITHUB_TOKEN`-fired `release: published` event can't trigger a separate workflow)

## Author

This project is maintained by [Hasan Sezer Taşan][author], It's me :wave:

## Disclaimer

This template is not intended to be used for malicious purposes. The author is not responsible for any damage caused by this template. Use at your own risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<!-- Refs -->

[author]: https://github.com/hasansezertasan
