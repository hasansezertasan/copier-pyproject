# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**This file is a lean router, not an encyclopedia.** It keeps the load-bearing
agent instructions inline and points to the three sources of truth for
everything else — so per-toggle rationale is maintained once, not restated here:

- **`copier.yml` `help:`** — the one-line prompt for each toggle (*what you pick*).
- **[`docs/template-architecture.md`](docs/template-architecture.md)** — what each
  toggle/workflow renders and how the pieces fit (*the reference detail*).
- **[ADRs](docs/adr/)** — why each exists, the trade-offs, the posture (*the why*).

When you add or change a toggle, update `copier.yml` help + its ADR + the detail
in `docs/template-architecture.md` + `README.md`, and add **one** index-line here
— never a multi-line block. See **Adding New Optional Components** below.

## A small glossary

We need to be on the same page with terminology. When communicating, use this
language:

- **you** — the agent reading this file and changing **copier-pyproject** (this
  template repo).
- **we, us, maintainers** — the people building copier-pyproject. These are who
  you are talking to now.
- **user, adopter** — the person who runs `copier copy` to scaffold a new Python
  project from this template. Not the maintainers; not you.
- **template** — the Jinja-templated `template/` tree this repo renders
  (`_subdirectory: template`).
- **generated project, rendered project** — the output of a `copier copy` /
  `copier update` run; the thing the adopter actually works in.
- **toggle** — a boolean `include_*` question in `copier.yml` (e.g. `include_cli`,
  `include_web`).
- **preset** — the `library`/`tool`/`web`/`full` starting point that seeds every
  toggle's default via `preset_map`.
- **component** — an optional generated-project feature or integration a toggle
  enables. The **runnable** components (CLI, web, GUI, TUI, MCP, worker) share a
  launch precedence: the highest-precedence enabled one is the *primary* and owns
  the bare `pkg` command (a console script — or `[project.gui-scripts]` when a
  sole GUI needs a windowless Windows launcher); every other runnable component
  becomes a `pkg <name>` subcommand. The order lives in `copier.yml`'s
  `primary_component` — see ADR-019.
- **`example/`** — the gitignored, locally-generated rendering used to smoke-test
  the template.

## Project Overview

This is a **Copier template** for generating modern Python packages with comprehensive tooling. The `template/` directory contains Jinja2-templated files that are rendered when users run `copier copy` to scaffold new Python projects.

Key architecture:

- Template files use `.jinja` extension and contain variables like `{{github_repo_name}}`, `{{author_full_name}}`, etc.
- Template variables are defined in `copier.yml`
- The `example/` directory is a gitignored, locally-generated rendering (see `.gitignore`); regenerate it from `.example-input.yml` to smoke-test the template. Note: `.example-input.yml` uses the `library` preset (no interface components), so the run commands below for CLI/web/etc. apply only after enabling those options (or to any other generated project)
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

#### Render-and-inspect harness (`tests/`, [ADR-024](docs/adr/024-render-and-inspect-template-test-suite.md))

Always-on repo tests: `copier.run_copy` renders the template into temp dirs (the
`render` fixture, `tests/conftest.py`) and asserts on the output — preset shape,
YAML/TOML validity across presets/brokers/frameworks, and golden-file snapshots
of key artifacts. Runs in `template-ci.yml`'s `render-tests` job. No root Python
project, so deps come from an ephemeral uv env:

```bash
mise run test                # or: uv run --with pytest --with pytest-regressions --with copier pytest tests/
mise run test-golden-update  # regenerate golden files (review the diff), then commit
```

### Working with Generated Projects

Commands for the `example/` directory (or any generated project):

```bash
cd example/

# Install dependencies
uv sync

# Run tests across all Python versions
uv run --locked tox run

# Run style checks (ruff, mypy, basedpyright, ty, pyrefly, zuban, slotscheck, import-linter, taplo, typos, editorconfig-checker, sphinx-lint)
uv run --locked tox run -e style

# Run specific Python version tests
uv run --locked tox run -e 3.10
uv run --locked tox run -e 3.14

# Run a single test file
uv run --locked pytest tests/test_smoke.py -v

# Run worker broker integration tests (if include_worker=true; Docker required).
# On-demand tox env; marked `integration` and excluded from the default suite (ADR-008).
uv run --locked tox run -e integration

# Run the CLI (if include_cli=true)
uv run --locked example version
uv run --locked example info

# Run the web app in dev mode (if include_web=true). Framework-specific:
uv run --locked fastapi dev example.web.app:app                 # web_framework=fastapi
uv run --locked litestar --app=example.web.app:app run          # web_framework=litestar

# Non-primary components are subcommands of the `example` root (ADR-019); the
# *primary* component is launched by bare `example`. The forms below assume each
# is non-primary (e.g. alongside include_cli=true):
uv run --locked example interactive   # TUI  (if include_tui=true)
uv run --locked example gui           # GUI  (if include_gui=true)
uv run --locked example web           # web  (if include_web=true)
uv run --locked example mcp           # MCP  (if include_mcp=true)
uv run --locked example worker        # worker (if include_worker=true)

# Run prek hooks
uv run --locked tox run -e prek

# Build docs / serve locally / check links
uv run --locked tox run -e docs-build
uv run --locked tox run -e docs-server
uv run --locked tox run -e docs-linkcheck

# Profiling (if include_profiling=true)
uv run --locked tox run -e profile
```

### Linting and Git Hooks

This repo uses [prek](https://prek.j178.dev) (a Rust pre-commit replacement)
configured via `prek.toml`.

```bash
# Run hooks on all files
prek run --all-files

# Install the git hooks
prek install
```

## Template Architecture

Full reference for what each toggle, subpackage, devcontainer service, and
workflow renders lives in
[`docs/template-architecture.md`](docs/template-architecture.md). This section
keeps only the Jinja conventions, the toggle/workflow **index**, and the
invariants an agent must not break.

### Jinja2 Template Patterns

1. **Variable Substitution**: `{{github_repo_name}}` renders to the user's repo name
2. **Dynamic File Paths**: `src/{{github_repo_name}}/` creates package directories with user-provided names
3. **TODO Markers**: `TODO @{{github_user}}:` generates actionable TODOs in the rendered project
4. **Raw Blocks**: `{% raw %}${{ github.ref_name }}{% endraw %}` preserves GitHub Actions syntax
5. **Conditional Files**: `{% if condition %}filename{% endif %}.jinja` includes file only when condition is true
6. **Whitespace Control**: Use `{%-` and `-%}` to avoid extra blank lines in rendered output

### Template Variables (copier.yml) — index

Required inputs: `github_user`, `github_repo_name`, `author_full_name`,
`author_email`, `short_description`. Free-form: `package_keywords`,
`repository_topics` (asked only when `include_repo_settings`). Starting point:
`preset` (`library`/`tool`/`web`/`full`, `default: library`; seeds every toggle
default via the hidden `preset_map`, [ADR-016](docs/adr/016-archetype-based-presets.md)).
Choice questions gated on a toggle: `cli_framework` (when `include_cli`),
`web_framework` (when `include_web`), `worker_broker` (when `include_worker`),
and `docs_version_granularity` (`minor`/`major`/`full`, `default: minor`; when
`include_docs`, sets the versioned-docs directory granularity —
[ADR-027](docs/adr/027-versioned-documentation-and-last-updated-stamps.md)).

Optional components and integrations (all boolean; see `copier.yml` help for the
prompt, `docs/template-architecture.md` for what each renders):

| Toggle | One-line | ADR |
| --- | --- | --- |
| `include_cli` | CLI — the `pkg` console root (`cli_framework` = typer or stdlib argparse) | [019](docs/adr/019-components-as-cli-subcommands.md), [020](docs/adr/020-cli-framework-choice.md) |
| `include_web` | Web app (FastAPI/Litestar, `web_framework`) + Dockerfile | — |
| `include_gui` | Tkinter GUI | — |
| `include_tui` | Textual TUI | — |
| `include_mcp` | MCP server | — |
| `include_worker` | FastStream worker (`worker_broker` = kafka/nats/rabbitmq/redis) | [008](docs/adr/008-worker-broker-testing-strategy.md) |
| `include_c_extensions` | Cython + multi-platform wheels | — |
| `include_profiling` | py-spy / scalene / cProfile | — |
| `include_examples` | `examples/` folder with usage stubs (`library`-preset default) | — |
| `include_docs` | Sphinx docs site (`docs/` Sphinx tree, `docs-*` tox envs, docs CI + versioned Pages deploy with a version switcher + per-page "last updated"); **default-on** every preset, off keeps a README-only project. `docs/maintaining/` always ships | [025](docs/adr/025-optional-docs-subsystem.md), [027](docs/adr/027-versioned-documentation-and-last-updated-stamps.md) |
| `include_launcher` | PyCrucible online-first-run launcher | [007](docs/adr/007-standalone-executable-toggles.md) |
| `include_compiler` | Nuitka native-compiled executable | [007](docs/adr/007-standalone-executable-toggles.md) |
| `include_freezer` | PyInstaller offline bundle | [007](docs/adr/007-standalone-executable-toggles.md) |
| `include_pydantic_settings` | pydantic-settings config | — |
| `include_sourcery` | Sourcery config (`.sourcery.yaml`) | [009](docs/adr/009-optional-external-quality-community-integrations.md) |
| `include_sonarcloud` | SonarCloud + `sonar` CI job | [009](docs/adr/009-optional-external-quality-community-integrations.md) |
| `include_all_contributors` | all-contributors config + workflow + README section | [009](docs/adr/009-optional-external-quality-community-integrations.md) |
| `include_smokeshow` | tokenless coverage-HTML host (smokeshow step in the `coverage-combine` job; public repos only) | [026](docs/adr/026-combined-cross-matrix-coverage-and-tokenless-html-host.md) |
| `include_megalinter` | MegaLinter lean-complement CI layer | [013](docs/adr/013-megalinter-opt-in-lean-complement.md) |
| `include_homebrew` | Homebrew tap dispatch (`is_app`-gated) | [017](docs/adr/017-opt-in-homebrew-scoop-distribution.md) |
| `include_scoop` | Scoop bucket dispatch | [017](docs/adr/017-opt-in-homebrew-scoop-distribution.md) |
| `include_repo_settings` | `.github/settings.yml` via Settings App | [018](docs/adr/018-repository-settings-as-code.md) |
| `include_repo_ruleset` | branch-protection `ruleset-sync.yml` (`full` preset) | [021](docs/adr/021-repository-ruleset-as-code.md) |
| Devcontainer: `include_postgres`/`include_redis` (`redis_backend`)/`include_pgadmin`/`include_adminer`/`include_dbeaver`/`include_vpn` | devcontainer services | — |

Always included (no toggle), each detailed in `docs/template-architecture.md`:
release-please-managed `CHANGELOG.md` (no seed file), Codecov upload, Renovate
(shared preset, incl. the `copier` update manager — [ADR-015](docs/adr/015-template-self-versioning-and-copier-update-automation.md)),
`CITATION.cff` + validation, mise, import-linter architecture contract
([ADR-014](docs/adr/014-import-linter-for-architecture-contracts.md)), Commitizen
([ADR-004](docs/adr/004-commitizen-as-commit-helper-not-release-tool.md)),
cobo-managed `.gitignore` ([ADR-012](docs/adr/012-cobo-for-gitignore-generation.md)),
prek hooks (incl. blocking `zizmor` and `detect-secrets` with a committed
`.secrets.baseline`), the tox `style` env as the sole lint/build
orchestrator ([ADR-003](docs/adr/003-tox-as-canonical-lint-runner.md)),
editorconfig-checker, ghalint, `SUPPORT.md`, `.gitattributes`, `.git_archival.txt`,
and `AGENTS.md`/`CLAUDE.md` onboarding files.

### Load-bearing invariants

Do not break these — each is a real footgun with the detail/why in its ADR:

- **No `CHANGELOG.md.jinja` seed.** release-please owns the changelog; a
  scaffold-time seed overwrites and wipes an adopting project's release history.
- **`copier.yml` defines no `_tasks`.** A task forces `copier --trust`, which the
  hosted Renovate App disables, breaking the `copier`-manager auto-update
  ([ADR-015](docs/adr/015-template-self-versioning-and-copier-update-automation.md)).
- **This repo's release-please must keep cutting tags** — those git tags are the
  datasource the generated projects' Renovate `copier` manager consumes (ADR-015).
- **Shipped `template/**` pins are frozen from Renovate** (disabled `packageRules`
  entry). Seed values only; do **not** re-enable, or `copier update` conflicts on
  nearly every release ([ADR-020](docs/adr/020-freeze-shipped-template-pins-from-renovate.md)).
- **Do not hand-edit inside the cobo-sealed `.gitignore` fence** (`# >>> cobo:begin`
  … `# <<< cobo:end sha256=…`) — it breaks the sha256. Regenerate with
  `cobo update && cobo sync` ([ADR-012](docs/adr/012-cobo-for-gitignore-generation.md)).
- **Verify zizmor changes with the prek hook** (`prek run zizmor --all-files`),
  not a bare `uvx zizmor` — the two can pin versions with different
  `dangerous-triggers` behavior; the prek hook is what gates.
- **The console-script precedence lives once** — the `primary_component` computed
  var in `copier.yml` (CLI > GUI > TUI > web > MCP > worker). Derive from it; do
  **not** re-spell it as inline `include_x or include_y …`
  ([ADR-019](docs/adr/019-components-as-cli-subcommands.md)).
- **The `ci.yml` draft guard is all-or-nothing.** Every job — including `check` —
  carries `if: ${{ github.event.pull_request.draft != true }}`, and the
  `pull_request` trigger must keep `ready_for_review` in `types:`. Gating only
  some jobs turns draft PRs *red* (`alls-green` counts a skipped `needs` as a
  failure); dropping `ready_for_review` (not a default type) makes the skip
  permanent. Use `!= true`, never `== false` — the latter also disables CI on
  `push` ([ADR-028](docs/adr/028-asymmetric-ci-matrix-and-draft-pr-skip.md)).
- **Docs deploys must preserve the version-slug directories** (numeric, e.g.
  `0.3/` — no leading `v`). Both `release.yml` `deploy-docs` and the manual
  `gh-pages.yml` build only the current version and re-supply prior versions from
  `gh-pages` via `tools/build_docs.py`; a naive root publish with only
  `clean-exclude: pr-preview/**` would wipe every version directory. The manual
  workflow checks out the latest release tag first (never HEAD). Old versions are
  never rebuilt
  ([ADR-027](docs/adr/027-versioned-documentation-and-last-updated-stamps.md)).

### CI/CD Workflows — index

Detail (jobs, gating, security posture) in `docs/template-architecture.md`.

| Workflow | Purpose | ADR |
| --- | --- | --- |
| `ci.yml` | asymmetric OS/Python matrix + coverage, draft-PR skip; packaging/worker-integration guards | [007](docs/adr/007-standalone-executable-toggles.md), [008](docs/adr/008-worker-broker-testing-strategy.md), [028](docs/adr/028-asymmetric-ci-matrix-and-draft-pr-skip.md) |
| `release.yml` | release-please → build / pypi-publish / executables / docker / docs / sbom / issue-notify | [002](docs/adr/002-release-please-for-release-automation.md), [010](docs/adr/010-pr-docs-previews-and-released-issue-notifications.md) |
| `check-pr-title.yml` | PR title vs Conventional Commits | — |
| `check-linked-issues.yml` | require a linked issue (`no-issue` bypasses) | — |
| `task-completed-check.yml` | fail while PR task-list boxes unticked | — |
| `check-branch-name.yml` | Conventional Branch head-name lint | — |
| `codeql` / `scorecard` / `dependency-review` / `check-security.yml` | supply-chain security passes | — |
| `zizmor.yml` | workflow-hardening SARIF dashboard (non-blocking) | — |
| `docs-preview.yml` | per-PR Sphinx previews under `pr-preview/**` | [010](docs/adr/010-pr-docs-previews-and-released-issue-notifications.md) |
| `docs-linkcheck.yml` | weekly link check (non-blocking) | [011](docs/adr/011-docs-linting-and-cross-platform-filename-safety.md) |
| Renovate `copier` manager | downstream template updates (not a workflow) | [015](docs/adr/015-template-self-versioning-and-copier-update-automation.md) |

Required status checks on generated repos: `check-pr-title`,
`check-linked-issues`, **Validate branch name**, and **Task Completed Checker**.

### Workflow hardening rules

Every generated **and** repo-own workflow follows a strict
[zizmor](https://docs.zizmor.sh/) posture (**regular** persona — Renovate's
`helpers:pinGitHubActionDigests` already SHA-pins every `uses:`). The blocking
gate is the `zizmor` prek hook (runs in CI `hooks` + locally). Keep these so it
stays green when you add or edit a workflow:

- **`persist-credentials: false`** on every `actions/checkout`, no exceptions (the
  docs-push jobs publish via `JamesIves/github-pages-deploy-action`, which
  authenticates from its own `token` input, so they need no `artipacked` ignore).
- **`permissions: {}`** at workflow top-level, with per-job least-privilege grants
  (only `contents: read` for checkout-only jobs, etc.).
- **No untrusted `${{ }}` in `run:` blocks** — pass GitHub context
  (`github.ref_name`/`repository`/`workflow`) via `env:` and read as `"$VAR"`
  (template-injection). The `finalize-release`/`attach-github-release` steps in
  `release.yml` are the known-good reference to copy.
- **Intentional `pull_request_target`** workflows (`check-pr-title`,
  `check-branch-name`, `check-linked-issues`, `task-completed-check`, `label`,
  `issue-manager`) carry a justified `# zizmor: ignore[dangerous-triggers]` — they
  never check out or execute PR code and read untrusted input only via `env:`. Do
  **not** remove these ignores.

### Required Merge Strategy (release-please depends on it)

release-please derives version bumps and changelog sections solely from the
Conventional Commit messages that land on `main`. This template validates the
**PR title** but not in-PR commits, so **both this repo and generated repos must
use "Squash and merge" with the squash commit message set to the PR title** — the
only strategy under which the lint-validated title becomes the commit on `main`.
Merge-commit and rebase-merge promote unvalidated branch commits and cause
release-please to miss releases or bump them incorrectly. release-please also needs **Settings
→ Actions → General → Workflow permissions → Allow GitHub Actions to create and
approve pull requests** enabled.

The generated project's `docs/maintaining/setup.rst` is the one-time "Repository
setup" guide (`[AGENT]`/`[HUMAN]`/`[CHECK]`-tagged, driven by the shipped
`repo-setup` skill — [ADR-022](docs/adr/022-maintainer-setup-as-single-doc-home.md),
[ADR-023](docs/adr/023-repo-setup-skill.md)); keep it in sync when these
requirements change. This repo carries a symmetric repo-local
`.claude/skills/repo-setup/` for its own bootstrap. Bump rules and this repo's own
self-versioning are detailed in `docs/template-architecture.md` and ADR-015.

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

Keep `CLAUDE.md` growth capped: a new toggle updates `copier.yml` help + an ADR +
the detail in `docs/template-architecture.md` + **one** row in the toggle index
above — never a multi-line block here.

1. Add boolean variable to `copier.yml` with `type: bool`, `default`, and `help`
2. If component has choices (like `worker_broker`), add a separate choice variable with `when: "{{ parent_option }}"`
3. Create conditional directory: `template/src/{{github_repo_name}}/{% if include_xxx %}xxx{% endif %}/`
4. Create matching test directory: `template/tests/{% if include_xxx %}xxx{% endif %}/`
5. Update `pyproject.toml.jinja`:
   - Add the runtime dependency to the core `dependencies` list under the
     component's `{% if include_xxx %}` guard — **not** an optional extra: the
     component's console script imports it unconditionally, so `pip install
     <pkg>` must pull it. (`all` stays empty; it exists only so the `dev`
     group's `<pkg>[all]` resolves.)
   - Add the entry point if applicable. If the component is runnable, fold it
     into the console-script precedence in `primary_component` (`copier.yml`); a
     non-primary component gets a `<pkg> <name>` **subcommand** (add a lazy
     `@app.command()` in `cli/app.py.jinja`, guarded on
     `include_xxx and primary_component != 'xxx'`), **not** a `<pkg>-<name>`
     script (see ADR-019). If it is a *new kind* of runnable component, also
     extend `include_console_root` in `copier.yml`. Do not spell out the
     precedence inline anywhere.
   - Add keywords
   - Add the component to the `[tool.importlinter]` `layers` contract (a sibling in the `il_components` list, or — like `cli` — its own orchestrator layer if it imports other components)
6. Add the new toggle to the `full` entry in `copier.yml`'s `preset_map` (and to
   any archetype preset — `library`/`tool`/`web` — whose shape includes it).
   `.example-input.yml` no longer lists individual toggles, so it needs no change.
7. Update `README.md` and add the toggle's detail to `docs/template-architecture.md`
8. Keep the component's coverage at the `fail_under = 99` gate (see
   [ADR-008](docs/adr/008-worker-broker-testing-strategy.md)). Because
   `.example-input.yml` uses the `library` preset (no interface components), a
   component's coverage is only
   validated when you generate it explicitly — do that and run the suite. Unit-test
   the business logic *including reachable error handling* (metadata-failure
   paths are tested via a `_MissingDistribution` monkeypatch stub — see the
   web/cli/gui/tui/mcp tests); only for genuinely untestable blocking
   entrypoints add `# pragma: no cover` to the specific launch/display function
   (as the `main()` entrypoints, the CLI launcher subcommands, the GUI/TUI
   `_display_*` helpers, and the worker lifecycle hooks do). Do **not** add
   blanket `exclude_lines` regexes for these — see the convention below.

### Coverage exclusion convention

Generated projects enforce `fail_under = 99`. Entrypoints that start a blocking
loop (`main()`, `run_server`, real tkinter/textual/uvicorn/stdio code) cannot
run under headless CI, so each carries a per-site `# pragma: no cover` (the
web/MCP/worker `main()` entrypoints and `__main__` dispatchers, the MCP
`run_server`, the CLI `interactive`/`gui`/`web` subcommands, the GUI/TUI
`_display_*` helpers, the worker lifecycle hooks, the c-extension
`except ImportError` fallback, and the worker's module-level metadata
fallback). The logic those entrypoints call is always unit-tested.

Do **not** exclude these via blanket `[tool.coverage.report] exclude_lines`
regexes (`def main\(`, `except PackageNotFoundError`, ...): a regex matching a
`def` line excludes the *entire function body*, so such patterns silently
un-measure any future function with the same name that carries real logic —
and previously masked the tested GUI/TUI `main()` entrypoints and the web 503
handlers. Reachable error handling is tested, not excluded: the web `/version`
and `/info` 503 responses, the CLI metadata-failure exit code, the GUI/TUI
"Version: unknown" degradation, and the MCP error-text response all have unit
tests using a `_MissingDistribution` monkeypatch stub.

Coverage measurement spans two layouts: `src/...` in an editable dev install and
`.../site-packages/...` when tox/CI installs the built wheel/sdist (the tox test
env uses `package = "wheel"`/`"sdist"`). Two config settings must account for this
or the gate silently fails for *every* generated project:

- `[tool.coverage.paths]` must remap the installed tree back to the canonical
  `src/` tree — `{{pkg}} = ["src/{{pkg}}", "*/site-packages/{{pkg}}"]`. Each tox
  Python env installs into its own `site-packages`, so without remapping,
  `coverage combine` keeps a separate copy per env and a version-gated line
  covered in one interpreter but not another counts as missed. This only shows up
  under the full multi-env `tox run`, not a single env or editable `pytest`.
- `omit` globs must be anchored to match both layouts (`*/_version.py`,
  `*/worker/test_integration.py`), not `src/**` — a `src/**` pattern misses the
  installed copy and reports it at 0%. The integration glob is additionally
  directory-anchored so a future `test_integration.py` in another component
  (which *would* run in the default suite) stays measured.

Always verify coverage via the real `tox run` path (installed package, all envs),
never editable `pytest` — both defects are invisible otherwise. See
[ADR-008](docs/adr/008-worker-broker-testing-strategy.md).

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
- **Update Workflow**: Users run `copier update` to pull template changes (automated
  by Renovate's `copier` manager — [ADR-015](docs/adr/015-template-self-versioning-and-copier-update-automation.md))
- **Trust Flag**: Use `--trust` when testing locally (there is no post-copy
  `_tasks`; `git init` is a documented manual step — see the invariant above)
