# copier-pyproject

Copier template for a modern, typed Python package/CLI with `uv`, `hatch`, `tox`, and GitHub automation baked in.

## What this template includes

- uv-first workflow with dependency groups (dev, style, test, docs, tool, prek) and tox-uv runners across Python 3.10–3.14; builds via `hatchling`/`hatch-vcs` with versions from Git tags.
- Optional components: Typer CLI entrypoint, FastAPI web app, Textual TUI, Tkinter GUI, C extensions via Cython with multi-platform wheel building, profiling tools (py-spy, scalene, cProfile), logging/config modules, type hints, and a `py.typed` marker plus corresponding tests; container-ready `Dockerfile`.
- QA stack: pytest with coverage/xdist/reruns (and `.github/codecov.yml`), ruff, mypy, basedpyright, ty, pyrefly, zuban, vulture, slotscheck, taplo, validate-pyproject, typos, actionlint.
- Docs and site: Sphinx scaffold (`docs/index.rst` + `conf.py`) with the Shibuya theme, autodoc API reference, and a GitHub Pages deploy workflow.
- Automation and hygiene: CI/CD workflows (matrix tests, trusted-publishing to PyPI, gh-pages), release automation via release-please, PR title linting, linked-issue enforcement, PR task-list completion check, issue/PR templates, `SECURITY.md` policy, `CODEOWNERS`, dependency management (Renovate), always-on Commitizen and git hooks (run via prek), always-on `CITATION.cff` with a validation workflow, devcontainer, VS Code launch config, gitignore, FUNDING, and LICENSE.
- Extra tooling: `.dockerignore`, badge-rich README template, and enhanced VS Code launch.json for debugging (current file, tests, attach, entry points).

## Inputs

Copier will prompt for:

- `github_user`
- `github_repo_name` (lowercase letters/digits/dashes, starts with a letter)
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
- `include_launcher` (uv-bootstrap launcher via PyCrucible — small executable, downloads Python+deps on first run)
- `include_compiler` (compiled native executable via Nuitka — source compiled to machine code)
- `include_freezer` (offline freezer via PyInstaller — self-contained bundle, no Python on target)
- `include_pydantic_settings` (use pydantic-settings for configuration)
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
4. Open the generated README (rendered from `template/README.md.jinja`) and clear the `TODO @...` markers in `README.md`, `pyproject.toml`, docs, and workflows.

## Generated project quickstart

- Install dependencies: `uv sync`
- Style gate: `uv run --locked tox run -e style`
- Full test suite: `uv run --locked tox run`
- Run the CLI (if included): `uv run --locked <repo-name> version`
- Run the web app (if included): `uv run --locked <repo-name>-web`
- Serve docs locally: `uv run --locked tox run -e docs-server` (deploys via GitHub Pages on release)

`.example-input.yml` provides default values for all template options.

## Release automation

Release automation is standardized on [release-please](https://github.com/googleapis/release-please) (see [ADR-002](docs/adr/002-release-please-for-release-automation.md)). A single unified workflow, `.github/workflows/release-please.yml`, orchestrates the whole release:

1. On push to `main`, release-please opens a release PR derived from your Conventional Commits.
2. Merging that PR creates the git tag and a **draft** GitHub Release.
3. The same workflow then builds with uv, publishes to PyPI via trusted publishing, attaches the build artifacts to the draft, and only then **un-drafts** the release — so the release is never visible without its artifacts.
4. Once the release is un-drafted, the workflow's `deploy-docs` job builds the Sphinx docs and publishes them with `ghp-import`. Docs deploy inline here (rather than via a `release: published` trigger) because an event fired by `GITHUB_TOKEN` cannot start another workflow; `.github/workflows/gh-pages.yml` is kept for manual redeploys only.

CI runs on macOS/Linux/Windows via `.github/workflows/ci.yml.jinja`.

Versions are derived from git tags by hatch-vcs (`dynamic = ["version"]`), so release-please never edits a static version literal and `uv.lock` cannot desync. `bump-minor-pre-major` keeps pre-1.0 projects pre-1.0.

### PyPI Trusted Publishing setup

Enable PyPI once per project for `.github/workflows/release-please.yml`:

1. Open [Trusted Publisher Management](https://pypi.org/manage/account/publishing/).
2. Under "Add a new pending publisher", pick "GitHub".
3. Set `PyPI Project Name` to your package name.
4. Set `Owner` to your GitHub username.
5. Set `Repository name` to your repo name.
6. Set `Workflow name` to `release-please.yml`. The PyPI publish step lives in this workflow (not a reusable one), so this is the filename PyPI's OIDC check matches against.
7. Set `Environment name` to `publish` (or your chosen env).
8. Save.

### Container image publishing (if `include_web` is enabled)

On release, the workflow always publishes multi-arch images (amd64/arm64) to the
GitHub Container Registry (`ghcr.io/<owner>/<repo>`) using the built-in
`GITHUB_TOKEN` — no extra setup required.

Docker Hub publishing is optional, opted into via a pair of repository secrets
(integrated in `.github/workflows/release-please.yml`):

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
3. The `release-please.yml` workflow then builds the wheel/sdist with uv, publishes to PyPI via trusted publishing, attaches artifacts to the draft, and un-drafts the release.
4. If `include_web` is enabled it also builds and pushes multi-arch Docker images; if any of `include_launcher` (PyCrucible), `include_compiler` (Nuitka), or `include_freezer` (PyInstaller) is enabled it also builds standalone executables for Windows, macOS, and Linux and attaches them to the release.

### Release workflow structure

The unified `release-please.yml` orchestrates every release job; all jobs after `release-please` run only when a release was created:

```text
release-please ─► build ─┬─► pypi-publish ────────┐
                         ├─► build-launcher ──────┤
                         ├─► build-freezer ───────┼─► attach-github-release ─┐
                         ├─► build-compiler ──────┘                          │
                         │   (if launcher / freezer / compiler)              ▼
                         └─► docker-publish ───────────────────────────────► finalize-release        ► deploy-docs
                             (if web)                                        (un-draft + reconcile)    (sphinx-build + ghp-import)
```

- **release-please**: Opens/maintains the release PR; on merge, tags and creates the draft release
- **build**: Builds the Python wheel/sdist with uv (matrix per-OS when `include_c_extensions`)
- **pypi-publish**: Publishes to PyPI via trusted publishing
- **build-launcher** / **build-freezer** / **build-compiler**: Build standalone executables for 3 platforms via PyCrucible / PyInstaller / Nuitka respectively (each conditional and independent)
- **docker-publish**: Builds and pushes multi-arch Docker images (conditional)
- **attach-github-release**: Attaches all artifacts to the still-draft release
- **finalize-release**: Un-drafts the release and reconciles the next release PR
- **deploy-docs**: Builds the Sphinx docs and publishes them with `ghp-import` after the release is un-drafted (inline, since a `GITHUB_TOKEN`-fired `release: published` event can't trigger a separate workflow)

## Author

This project is maintained by [Hasan Sezer Taşan][author], It's me :wave:

## Disclaimer

This template is not intended to be used for malicious purposes. The author is not responsible for any damage caused by this template. Use at your own risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<!-- Refs -->

[author]: https://github.com/hasansezertasan
