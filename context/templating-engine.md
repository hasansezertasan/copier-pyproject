# Templating engine

## Copier over Cookiecutter, Cruft, Yeoman and GitHub template repositories

**Id:** 25fa2def-a118-4f60-9117-89ab50da4cf2
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-001 (`docs/adr/001-copier-over-cookiecutter.md`)
**Revisit when:** `copier update` stops being a first-class feature, or a Python-native alternative gains native template-update support

Copier renders this template. Generated projects carry a `.copier-answers.yml`
and pull later template changes with `copier update`.

**Reason:** native update support matters most for a template that keeps
evolving — adopters pull new features, CI improvements and dependency updates
instead of re-applying them by hand. Conditional file inclusion via filename
patterns is cleaner than hook-based approaches, the answers file makes updates
reproducible, and full Jinja2 (whitespace control, raw blocks for GitHub Actions
syntax) is required by the workflow templates. Copier is actively maintained and
aligned with the uv/hatchling ecosystem the generated projects use.

**Rejected alternative:** Cookiecutter — the largest ecosystem, but no native
update/sync; pulling upstream changes is manual work.

**Rejected alternative:** Cruft — adds `cruft update`/`cruft check` on top of
Cookiecutter, but as a wrapper it is limited by Cookiecutter's internals.

**Rejected alternative:** Yeoman — JavaScript-based, not Python-native, heavier
runtime dependency.

**Rejected alternative:** GitHub template repositories — no variable
substitution and no conditional logic.

**Consequence:** adopters need `copier` installed; the template ecosystem is
smaller than Cookiecutter's; syntax differs slightly (`copier.yml`).
