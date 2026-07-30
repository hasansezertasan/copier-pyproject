# ADR-011: Docs linting (sphinx-lint + linkcheck) and cross-platform filename safety

## Status

Proposed (2026-07). Inspired by a survey of established open-source Python
project repositories, continuing the review that produced
[ADR-009](009-optional-external-quality-community-integrations.md) and
[ADR-010](010-pr-docs-previews-and-released-issue-notifications.md).

## Context

The template already ships a broad lint/type-check suite
([ADR-003](003-tox-as-canonical-lint-runner.md),
[ADR-005](005-five-type-checkers-basedpyright-strict.md)) and a rich Sphinx docs
stack ([ADR-006](006-sphinx-shibuya-for-documentation.md)) whose sources are
reStructuredText. Two small, self-contained gaps remained that surveyed projects
close and this template did not:

1. **No docs linter.** Nothing checks the `.rst` sources for the common markup
   errors Sphinx tolerates silently or reports only as build warnings —
   malformed inline markup, bad cross-reference syntax, missing blank lines
   before literal blocks, trailing whitespace in directives.
2. **No dead-link detection.** Docs accumulate link rot (renamed anchors, moved
   external pages); nothing catches it.
3. **No case-conflict guard.** The CI matrix spans Windows/macOS (case-insensitive
   or case-preserving filesystems) and Linux (case-sensitive). Two files whose
   names differ only in case (`Foo.py`/`foo.py`) build on Linux but collide on
   the other two — a class of breakage none of the existing hooks catch.

All three are covered by mature, dependency-light tooling that needs **no
external account**, so they fit the self-contained default that
[ADR-009](009-optional-external-quality-community-integrations.md) protects —
they are always-on, not toggles.

## Decision

Add three always-on checks, each wired into the existing gate rather than a new
mechanism:

### 1. `sphinx-lint` — reStructuredText linter

Add [`sphinx-lint`](https://github.com/sphinx-contrib/sphinx-lint) to the uv
`style` dependency group, invoke it in the tox `style` env
(`sphinx-lint docs`), and run it in `prek` as a **`local` system hook** backed
by that same group (`uv run --locked --group style sphinx-lint docs`).

The `local`-hook-over-`style`-group choice mirrors `basedpyright` and
`editorconfig-checker` ([ADR-003](003-tox-as-canonical-lint-runner.md)): a single
version pin in the `style` group serves both the tox env and the prek gate, so
there is no second `rev` pin to drift out of sync. `sphinx-lint` is a static
linter (it does not import the project or Sphinx), so it runs without the `docs`
group installed.

### 2. Docs `linkcheck` — on-demand env + weekly workflow

Add a `docs-linkcheck` tox env running Sphinx's built-in
`sphinx-build -b linkcheck`, and a standalone `docs-linkcheck.yml` workflow that
runs it on a **weekly `schedule` cron** and on `workflow_dispatch`.

Link checking hits the network and is inherently flaky (transient 5xx, rate
limits, sites that block CI), so it is deliberately **not** run on `pull_request`
and **not** wired into the `check` aggregation gate — a dead external link must
never block an unrelated merge. The weekly cron surfaces rot as a visible
(non-blocking) workflow result, exactly the posture `check-security.yml`'s cron
uses for its periodic scans; the tox env lets a maintainer run it locally
on demand.

### 3. `check-case-conflict` — cross-platform filename guard

Add the `check-case-conflict` hook (from the `pre-commit-hooks` builtin repo
already used for `check-toml`/`check-yaml`/etc.) to `prek.toml`. It is a
prek-only builtin like its siblings — not added to the tox `style` env, which is
reserved for the type/lint/format tools.

## Consequences

- `pyproject.toml.jinja`: `sphinx-lint` added to the `style` group; a
  `["sphinx-lint", "docs"]` command added to the tox `style` env; a new
  `[tool.tox.env.docs-linkcheck]` env (`docs` group + `all` extra, like
  `docs-build`).
- `prek.toml.jinja`: `check-case-conflict` added to the pre-commit-hooks block;
  a `sphinx-lint` `local` system hook added, scoped to `files = '\.rst$'` so it
  runs only on reStructuredText sources.
- A new static `docs-linkcheck.yml` workflow (`schedule` weekly +
  `workflow_dispatch`), least-privilege (`permissions: {}` top-level,
  `contents: read` on the job), `persist-credentials: false`, SHA-pinned actions,
  per-job `timeout-minutes` — it must pass the same zizmor/ghalint gate as every
  other workflow. Non-blocking, not in the `check` gate.
- The generated docs sources must be `sphinx-lint`-clean and pass `linkcheck`
  against the links the template ships. Verified by rendering a project and
  running `tox -e style` and `tox -e docs-linkcheck`.
- README "Development" / CLAUDE.md gain the `docs-linkcheck` command; CLAUDE.md's
  lint-suite and CI/CD sections note `sphinx-lint`, `check-case-conflict`, and
  the `docs-linkcheck.yml` workflow.
- No new `copier.yml` variable — all three are always rendered.
