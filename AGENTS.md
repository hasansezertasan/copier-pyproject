# AGENTS.md

## Development Commands

```bash
# Install: uv sync
# Test all: uv run --locked tox run
# Test single: uv run --locked pytest tests/test_file.py -v
# Test version: uv run --locked tox run -e 3.10
# Lint/style: uv run --locked tox run -e style
# Pre-commit: uv run --locked tox run -e pre-commit
# Build: uv build
# Run CLI: uv run --locked <repo-name> version
# Run FastAPI: uv run --locked fastapi dev <repo-name>.web:app
# Serve docs: uv run --only-group docs mkdocs serve
# Trunk check: trunk check (if configured)
# Pants lint: pants lint :: (if configured)
```

## Code Style Guidelines

- **Imports**: Absolute only, grouped stdlib→third-party→local (ruff enforced)
- **Formatting**: Ruff, 88 chars, LF endings
- **Types**: Strict typing required, `from typing import ...`
- **Naming**: snake_case vars/functions, PascalCase classes, UPPER_CASE constants
- **Error Handling**: Specific exceptions with context
- **Structure**: Code in `src/{{github_repo_name}}/`, tests in `tests/`
- **Tools**: Ruff (full rules, complexity ≤5), MyPy/Pyright strict, pytest + coverage, pre-commit
- **Template**: `.jinja` files, `{{variables}}`, `{% raw %}` for Jinja escaping
- **Optional Tools**: Poe (poethepoet) for task running, configurable via `include_poe`; Commitizen for version management, configurable via `include_commitizen`
