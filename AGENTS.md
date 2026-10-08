# AGENTS.md

## Keep the Why

This project records the reasoning behind its code with the Keep the Why
skill ([Keep the Why](https://keepthewhy.com)) — the `.keep-the-why` file at the project
root is its config. Before doing anything else in a session, whatever the
first request is about, load the `keep-the-why` skill using the agent's
skill tool, or read `.agents/skills/keep-the-why/SKILL.md` and follow it,
including the `references/*.md` files it points to for the situation at hand.

## Development Commands

```bash
# Install: uv sync
# Test all: uv run --locked tox run
# Test single: uv run --locked pytest tests/test_file.py -v
# Test version: uv run --locked tox run -e 3.10
# Lint/style: uv run --locked tox run -e style
# Prek hooks: uv run --locked tox run -e prek
# Build: uv build
# Run CLI: uv run --locked <repo-name> version
# Run FastAPI: uv run --locked fastapi dev <repo-name>.web.app:app
# Serve docs: uv run --locked tox run -e docs-server
# Profile: uv run --locked tox run -e profile (if profiling enabled)
```

## Code Style Guidelines

- **Imports**: Absolute only, grouped stdlib→third-party→local (ruff enforced)
- **Formatting**: Ruff, 88 chars, LF endings
- **Types**: Strict typing required, `from typing import ...`
- **Naming**: snake_case vars/functions, PascalCase classes, UPPER_CASE constants
- **Error Handling**: Specific exceptions with context
- **Structure**: Code in `src/{{github_repo_name}}/`, tests in `tests/`
- **Tools**: Ruff (full rules, complexity ≤5), five type checkers (mypy, basedpyright strict, ty, pyrefly, zuban), pytest + coverage, prek
- **Template**: `.jinja` files, `{{variables}}`, `{% raw %}` for Jinja escaping
- **Always included**: mise (tool versions + task running), Codecov coverage upload, a Keep-a-Changelog `CHANGELOG.md`, and Commitizen for Conventional Commit authoring/linting (versioning/changelog are handled by release-please)
