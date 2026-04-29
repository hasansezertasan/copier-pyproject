# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Copier template** for generating modern Python packages with comprehensive tooling. The `template/` directory contains Jinja2-templated files that are rendered when users run `copier copy` to scaffold new Python projects.

Key architecture:

- Template files use `.jinja` extension and contain variables like `{{github_repo_name}}`, `{{author_full_name}}`, etc.
- Template variables are defined in `copier.yml`
- The `example/` directory shows a rendered example using `.example-input.yml` as answers
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

# Run style checks (ruff, mypy, pyright, ty, pyrefly, vulture, slotscheck, taplo, validate-pyproject, typos, actionlint)
uv run --locked tox run -e style

# Run specific Python version tests
uv run --locked tox run -e 3.10
uv run --locked tox run -e 3.14

# Run a single test file
uv run --locked pytest tests/test_smoke.py -v

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

# Run pre-commit hooks
uv run --locked tox run -e pre-commit

# Build docs
uv run --locked tox run -e docs-build

# Serve docs locally
uv run --locked tox run -e docs-server

# Profiling (if include_profiling=true)
uv run --locked tox run -e profile
```

### Linting and Pre-commit

```bash
# Run pre-commit hooks on all files
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
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

Optional components (all boolean):

- `include_cli` - Typer CLI
- `include_web` - Web app + Dockerfile (framework choice: FastAPI or Litestar)
- `include_gui` - Tkinter GUI
- `include_tui` - Textual TUI
- `include_mcp` - MCP (Model Context Protocol) server
- `include_worker` - FastStream message queue worker
- `include_c_extensions` - Cython support with multi-platform wheels
- `include_profiling` - py-spy, scalene, cProfile tools
- `include_pycrucible` - PyCrucible for standalone executables
- `include_pydantic_settings` - pydantic-settings for config

Framework/broker choices (when parent option is enabled):

- `web_framework` - fastapi/litestar (when `include_web` is true)
- `worker_broker` - kafka/nats/rabbitmq/redis (when `include_worker` is true)

Devcontainer services:

- `include_dbeaver` - CloudBeaver database management UI
- `include_vpn` - OpenVPN client

Tooling options:

- `release_automation` - none/release-please/release-it/release-drafter
- `dependency_management` - none/renovate/dependabot
- `include_pants`, `include_codecov`, `include_trunk`
- `include_mise` - mise for tool version management and task running
- `include_commitizen` - Commitizen versioning
- `include_precommit` - pre-commit hooks

### Generated Project Structure

Root modules in `src/{{github_repo_name}}/`:

- `__init__.py`, `__main__.py`, `__metadata__.py` - Package setup
- `_version.py` - Auto-generated by hatch-vcs (excluded from coverage)

Subpackages (each with `__init__.py` and `app.py`):

- `core/` - Core infrastructure (always included):
  - `dirs.py` - Platform-aware directories
  - `logging_setup.py` - Centralized logging
  - `config.py` - Configuration (uses pydantic-settings if enabled)
- `utils/` - Utility functions (always included)
- `cli/` - Typer CLI with `version` and `info` commands (conditional)
- `web/` - FastAPI/Litestar with `/version` and `/info` endpoints (conditional)
- `gui/` - Tkinter GUI launcher (conditional)
- `tui/` - Textual TUI (conditional)
- `mcp/` - MCP server with `version` and `info` tools (conditional)
- `worker/` - FastStream message queue worker (conditional)

Other conditional files:

- `_c_extension.pyx`, `.pxd`, `.pyi` - Cython extension files
- `profile.py` - Profiling script

Test packages mirror source structure in `tests/`:

- `tests/cli/`, `tests/web/`, `tests/gui/`, `tests/tui/`, `tests/mcp/`, `tests/worker/` (each conditional)

Entry points configured in `pyproject.toml`:

- `project.scripts`: `pkg.cli.app:app`, `pkg.tui.app:main`, `pkg.web.app:main`, `pkg.mcp.app:main`, `pkg.worker.app:main`
- `project.gui-scripts`: `pkg.gui.app:main` (launches without terminal)

### Devcontainer Structure

The `.devcontainer/docker-compose.yml.jinja` consolidates all services:

- `devcontainer` - Main development container (always included)
  - Uses `ghcr.io/astral-sh/uv:python3.14-bookworm-slim` image directly (no Dockerfile)
  - `devcontainer.json.jinja` features: `git:1` (always), `mise:1` (when `include_mise`)
  - When `include_vpn` is true, devcontainer sets `network_mode: "service:vpn"` and `depends_on: [vpn]` so all traffic routes through the VPN tunnel
- Message broker services (conditional on `include_worker` + `worker_broker`):
  - `kafka` - Bitnami Kafka (KRaft mode)
  - `nats` - NATS with JetStream
  - `rabbitmq` - RabbitMQ with management UI
  - `redis` - Redis
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
   - Codecov coverage steps are conditional on `include_codecov`
2. **CD** (`cd.yml.jinja`): PyPI trusted publishing on GitHub Release
3. **Build Wheels** (`build-wheels.yml`): Multi-platform Cython wheels (conditional on `include_c_extensions`)
4. **Release automation**: release-please, release-it, or release-drafter (configurable)
5. **PR title linting**: Validates conventional commits format

### PyPI Trusted Publishing Setup

For generated projects to publish to PyPI:

1. Go to https://pypi.org/manage/account/publishing/
2. Add pending publisher with:
   - PyPI Project Name: `<package-name>`
   - Owner: `<github-username>`
   - Repository: `<repo-name>`
   - Workflow: `cd.yml`
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
