# copier-pyproject

Copier template for a modern, typed Python package/CLI with `uv`, `hatch`, `tox`, and GitHub automation baked in.

## What this template includes

- uv-first workflow with dependency groups (dev, style, test, docs, tool, pre-commit) and tox-uv runners across Python 3.10–3.14; builds via `hatchling`/`hatch-vcs` with versions from Git tags.
- Optional components: Typer CLI entrypoint, FastAPI web app, Textual TUI, Tkinter GUI, C extensions via Cython with multi-platform wheel building, profiling tools (py-spy, scalene, cProfile), logging/config modules, type hints, and a `py.typed` marker plus corresponding tests; container-ready `Dockerfile`.
- QA stack: pytest with coverage/xdist/reruns (and `.codecov.yml`), ruff, mypy, pyright, ty, pyrefly, vulture, slotscheck, taplo, validate-pyproject, typos, actionlint.
- Docs and site: MkDocs scaffold (`docs/index.md`) with GitHub Pages deploy workflow.
- Automation and hygiene: CI/CD workflows (matrix tests, trusted-publishing to PyPI, gh-pages), configurable release automation (release-please/release-it/release-drafter), PR title linting, issue/PR templates, dependency management (Renovate/Dependabot), optional Commitizen, pre-commit (with pre-commit-uv), devcontainer, VS Code launch config, gitignore, FUNDING, and LICENSE.
- Extra tooling: Optional Trunk config (hadolint/markdownlint/etc.), Pants config, `.dockerignore`, badge-rich README template, and enhanced VS Code launch.json for debugging (current file, tests, attach, entry points).

## Inputs

Copier will prompt for:

- `github_user`
- `github_repo_name` (lowercase letters/digits/dashes, starts with a letter)
- `author_full_name`
- `author_email`
- `short_description`
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
- `include_pycrucible` (include PyCrucible for standalone executables)
- `include_pydantic_settings` (use pydantic-settings for configuration)
- `release_automation` (none/release-please/release-it/release-drafter)
- `dependency_management` (none/renovate/dependabot)
- `include_changelog` (include CHANGELOG.md)
- `include_citation` (include CITATION.cff)
- `include_pants` (include Pants build system)
- `include_codecov` (include Codecov configuration)
- `include_mise` (include mise for tool version management and task running)
- `include_trunk` (include Trunk linting/formatting)
- `include_commitizen` (include Commitizen)
- `include_precommit` (use pre-commit hooks)

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
- Run the FastAPI app (if included): `uv run --locked fastapi dev <repo-name>.web:app`
- Serve docs locally: `uv run --only-group docs mkdocs serve` (deploys via GitHub Pages on release)
- Optional tooling: `trunk check` for aggregated linting (if configured); `pants lint ::` for Pants-based linting (if configured).

`.example-input.yml` provides default values for all template options.

## Release automation

Publishing a GitHub release triggers `.github/workflows/cd.yml.jinja` to build with uv and push to PyPI using trusted publishing. Docs deploy from releases via `.github/workflows/gh-pages.yml`, and CI runs on macOS/Linux/Windows via `.github/workflows/ci.yml.jinja`.

If you prefer release PRs or manual bumping, `release-please-config.json` and `.release-it.json` are provided alongside release-drafter.

### PyPI Trusted Publishing setup

Enable PyPI once per project for `.github/workflows/cd.yml`:

1. Open [Trusted Publisher Management](https://pypi.org/manage/account/publishing/).
2. Under "Add a new pending publisher", pick "GitHub".
3. Set `PyPI Project Name` to your package name.
4. Set `Owner` to your GitHub username.
5. Set `Repository name` to your repo name.
6. Set `Workflow name` to `cd.yml` (or your workflow filename).
7. Set `Environment name` to `publish` (or your chosen env).
8. Save.

### Docker Hub setup (if `include_web` is enabled)

Enable Docker Hub publishing (integrated in `.github/workflows/cd.yml`):

1. Create a [Docker Hub Access Token](https://hub.docker.com/settings/security).
2. In your GitHub repository, go to Settings → Secrets and variables → Actions.
3. Add two repository secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Your Docker Hub access token
4. On release, the workflow will build and push multi-arch images (amd64/arm64) to Docker Hub.

### Release steps

1. Draft a GitHub Release (tag = version).
2. Update `CHANGELOG.md` with the new version details.
3. Publish the release.
4. `cd.yml` will build the wheel/sdist with uv, publish to PyPI via trusted publishing, and upload artifacts to the GitHub Release.
5. If `include_web` is enabled, `cd.yml` also builds and pushes Docker images to Docker Hub.
6. If `include_pycrucible` is enabled, `cd.yml` also builds standalone executables for Windows, macOS, and Linux.

### CD workflow structure

The unified `cd.yml` orchestrates all release jobs:

```text
build ─────┬──► pypi-publish ──────────────────────┐
           │                                       │
           ├──► build-executables (if pycrucible) ─┼──► attach-github-release
           │    (parallel: ubuntu/windows/macos)   │
           │                                       │
           └──► docker-publish (if web) ───────────┘
                (pushes to Docker Hub independently)
```

- **build**: Builds the Python wheel/sdist with uv
- **pypi-publish**: Publishes to PyPI via trusted publishing
- **build-executables**: Builds standalone executables for 3 platforms (conditional)
- **docker-publish**: Builds and pushes multi-arch Docker images (conditional)
- **attach-github-release**: Attaches all artifacts to the GitHub Release

## Author

This project is maintained by [Hasan Sezer Taşan][author], It's me :wave:

## Disclaimer

This template is not intended to be used for malicious purposes. The author is not responsible for any damage caused by this template. Use at your own risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<!-- Refs -->

[author]: https://github.com/hasansezertasan
