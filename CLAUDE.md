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
```

### Working with Generated Projects

Commands that would run in a generated project (useful for testing):

```bash
# Navigate to example directory
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

# Run the CLI
uv run --locked <repo-name> version
uv run --locked <repo-name> info

# Run the FastAPI web app
uv run --locked fastapi dev <repo-name>.app:app

# Run pre-commit hooks
uv run --locked tox run -e pre-commit

# Build docs
uv run --locked tox run -e docs-build

# Serve docs locally
uv run --locked tox run -e docs-server
```

### Linting and Pre-commit

```bash
# Run pre-commit hooks on all files
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

## Template Architecture

### Jinja2 Template Structure

The template uses Copier's Jinja2 templating with these key patterns:

1. **Variable Substitution**: `{{github_repo_name}}` renders to the user's repo name
2. **Dynamic File Paths**: `src/{{github_repo_name}}/` creates package directories with user-provided names
3. **TODO Markers**: `TODO @{{github_user}}:` generates actionable TODOs in the rendered project
4. **Raw Blocks**: `{% raw %}${{ github.ref_name }}{% endraw %}` preserves GitHub Actions syntax

### Generated Project Structure

Projects created from this template have:

- **CLI Application**: Typer-based CLI in `cli.py.jinja` with `version` and `info` commands
- **Web Application**: FastAPI stub in `app.py.jinja` with `/version` and `/info` endpoints
- **Core Modules**:
  - `__metadata__.py.jinja`: Project name constant
  - `dirs.py.jinja`: Platform-aware directory management using `platformdirs`
  - `config.py.jinja`: Configuration placeholder
  - `logging_setup.py.jinja`: Centralized logging setup
  - `core.py` and `utils.py`: Empty stubs for user code
- **Entry Points**: Both CLI (`project.scripts`) and GUI (`project.gui-scripts`) entry points configured in `pyproject.toml`

### Dependency Groups

Generated projects use uv dependency groups:

- `dev`: Development dependencies (includes tox, tox-uv, style, test)
- `style`: Linting/formatting tools (ruff, mypy, pyright, ty, pyrefly, vulture, slotscheck, taplo, validate-pyproject, typos, actionlint)
- `test`: Testing tools (pytest, coverage, pytest-xdist, pytest-rerunfailures, pytest-mock, pytest-dependency)
- `docs`: MkDocs for documentation
- `tool`: Project management tools (commitizen, copier, poethepoet)
- `pre-commit`: Pre-commit framework and uv integration

### Build System

- **Builder**: `hatchling` with `hatch-vcs` plugin
- **Versioning**: Git-based versioning (tags) via hatch-vcs, fallback to 0.1.0
- **Version File**: Auto-generated `_version.py` (excluded from coverage)
- **Build Command**: `uv build` creates wheels and sdist

### CI/CD Workflows

Generated projects include GitHub Actions:

1. **CI** (`.github/workflows/ci.yml.jinja`):
   - Runs `uv run --locked tox run` on Windows, Ubuntu, macOS
   - Matrix tests across all supported Python versions (3.10-3.14)
   - Triggered on push to main/master and PRs

2. **CD** (`.github/workflows/cd.yml.jinja`):
   - Triggered on GitHub Release publication
   - Builds with `uv build`
   - Publishes to PyPI using Trusted Publishing (`uv publish --trusted-publishing always`)
   - Attaches build artifacts to GitHub Release
   - Requires `publish` environment with id-token write permissions

3. **Other Workflows**:
   - `check-pr-title.yml.jinja`: Validates PR titles follow conventional commits
   - `release-drafter.yml.jinja`: Auto-generates release notes

### PyPI Trusted Publishing Setup

For generated projects to publish to PyPI:

1. Go to https://pypi.org/manage/account/publishing/
2. Add pending publisher with:
   - PyPI Project Name: `<package-name>`
   - Owner: `<github-username>`
   - Repository: `<repo-name>`
   - Workflow: `cd.yml`
   - Environment: `publish`

## Template Modification Guidelines

### Adding New Template Files

1. Create file in `template/` with `.jinja` extension
2. Use `{{variable_name}}` for Copier variable substitution
3. Test by regenerating `example/` directory
4. Update this CLAUDE.md if the file introduces new architecture

### Modifying Template Variables

1. Edit `copier.yml` to add/change variables
2. Add validation regex if needed (see `github_repo_name` validator)
3. Update all `.jinja` files that reference the variable
4. Regenerate example to verify

### Important Template Conventions

- **Escaping**: Use `{% raw %}{% endraw %}` to preserve Jinja2 syntax in generated files (e.g., for GitHub Actions)
- **File Naming**: Dynamic directories use `{{variable}}` format (e.g., `src/{{github_repo_name}}/`)
- **Comments**: Template-only comments use `{# #}`, generated comments use `#`
- **TODOs**: Use `TODO @{{github_user}}:` pattern for actionable items in generated projects

### Testing Template Changes

Always test changes by:
1. Regenerating the example: `copier copy --data-file .example-input.yml --defaults . example/ --force`
2. Running style checks in example: `cd example && uv run --locked tox run -e style`
3. Running tests in example: `cd example && uv run --locked tox run`

## Copier-Specific Behavior

- **Subdirectory**: `_subdirectory: template` in `copier.yml` means Copier renders from `template/` not root
- **Answers File**: `{{_copier_conf.answers_file}}.jinja` becomes `.copier-answers.yml` for update tracking
- **Update Workflow**: Users can run `copier update` to pull template changes into their project
