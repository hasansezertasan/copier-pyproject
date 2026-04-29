# ADR-001: Use Copier as the Templating Engine

## Status

Accepted

## Context

When creating a Python project template, the main templating tools available are:

1. **Cookiecutter** — The original and most popular Python project templating tool. Large ecosystem of community templates. However, it lacks native template update/sync capabilities — once a project is generated, pulling upstream template changes requires manual work.

2. **Cruft** — A wrapper around Cookiecutter that adds `cruft update` and `cruft check` for syncing downstream projects with upstream template changes. Limited by Cookiecutter's internals since it's a wrapper, not a native solution.

3. **Copier** — A newer tool with native template update support (`copier update`), Jinja2 templating, conditional file inclusion via filename patterns, answer files for reproducibility, and post-copy tasks.

4. **Yeoman** — JavaScript-based scaffolding tool. Not Python-native, heavier runtime dependency.

5. **GitHub Template Repositories** — Simple but no variable substitution or conditional logic.

## Decision

Use **Copier** as the templating engine.

## Rationale

- **Native update support**: `copier update` is a first-class feature, not a bolt-on. This is critical for a template that evolves over time — users can pull new features, CI improvements, and dependency updates.
- **Conditional file paths**: Copier supports `{% if condition %}filename{% endif %}.jinja` patterns for conditional file inclusion, which is cleaner than Cookiecutter's hooks-based approach.
- **Answer files**: `.copier-answers.yml` tracks how a project was generated, enabling reproducible updates.
- **Jinja2 with extensions**: Full Jinja2 support including whitespace control, raw blocks (essential for GitHub Actions syntax), and template inheritance.
- **Active development**: Copier is actively maintained and aligns with the modern Python ecosystem (uv, hatchling).
- **Industry trend**: Projects like Substrate (Superlinear) have migrated from Cookiecutter/Cruft to Copier. Academic literature (2026) confirms Copier as a prominent evolution of Cookiecutter.

## Consequences

- Users need `copier` installed (via `pip install copier` or `pipx install copier`)
- Template syntax differs slightly from Cookiecutter (e.g., `copier.yml` vs `cookiecutter.json`)
- Smaller community template ecosystem compared to Cookiecutter, but growing
- Users benefit from `copier update` to pull template improvements over time
