# AGENTS.md

This file provides guidance to coding agents working in this repository.

**This file is a lean router, not an encyclopedia.** It keeps the load-bearing
agent instructions inline and points to the three sources of truth for
everything else — so per-toggle rationale is maintained once, not restated here:

- **`copier.yml` `help:`** — the one-line prompt for each toggle (*what you pick*).
- **[`docs/template-architecture.md`](docs/template-architecture.md)** — what each
  toggle/workflow renders and how the pieces fit (*the reference detail*).
- **[`context/`](context/index.md)** — why each exists, the trade-offs, the
  posture (*the why*), recorded with [Keep the Why](https://keepthewhy.com):
  invoke the `keep-the-why` skill before writing there. The former `docs/adr/`
  archive is deleted — no new ADRs; `context/` entries link the removed records
  by permalink in their `Source` lines.

When you add or change a toggle, update `copier.yml` help + its `context/` entry +
the detail in `docs/template-architecture.md` + `README.md`, and add **one**
index-line here — never a multi-line block. See **Adding New Optional
Components** below.

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
  `primary_component` — see [components as subcommands](context/components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts).
- **`example/`** — the gitignored, locally-generated rendering used to smoke-test
  the template.

## Project Overview

This is a **Copier template** for generating modern Python packages with comprehensive tooling. The `template/` directory contains Jinja2-templated files that are rendered when users run `copier copy` to scaffold new Python projects.

Key architecture:

- Template files use `.jinja` extension and contain variables like `{{github_repo_name}}`, `{{author_full_name}}`, etc.
- Template variables are defined in `copier.yml`
- The `example/` directory is a gitignored, locally-generated rendering (see `.gitignore`); regenerate it from `.example-input.yml` to smoke-test the template. Note: `.example-input.yml` uses the `library` preset (no interface components), so the run commands below for CLI/web/etc. apply only after enabling those options (or to any other generated project)
- Generated projects use uv for dependency management, hatchling for builds, tox for testing, and include full CI/CD automation

## Keep the Why

This project records the reasoning behind its code with the Keep the Why
skill ([Keep the Why](https://keepthewhy.com)) — the `.keep-the-why` file at the project
root is its config. Before doing anything else in a session, whatever the
first request is about, load the `keep-the-why` skill using the agent's
skill tool, or read `.agents/skills/keep-the-why/SKILL.md` and follow it,
including the `references/*.md` files it points to for the situation at hand.

## Development Commands

### Testing the Template

Every render goes through `tools/render.py` ([single render entrypoint](context/template-testing.md#toolsrenderpy-is-the-only-place-the-template-is-rendered)),
never a bare `copier copy`. It already applies `.example-input.yml`, `--defaults`
and overwrite; there is no root Python project, so `uv run` resolves copier from
the script's own PEP 723 metadata.

```bash
# Render into a scratch dir
uv run tools/render.py render /tmp/test-project

# (Re)generate the example project
mise run example

# Render with specific features enabled
uv run tools/render.py render /tmp/test-worker --data include_worker=true --data worker_broker=kafka
```

#### Render-and-inspect harness (`tests/`, [why](context/template-testing.md#render-and-inspect-is-the-fast-matrixed-layer-generate-and-run-stays-separate))

Always-on repo tests: `copier.run_copy` renders the template into temp dirs (the
`render` fixture, `tests/conftest.py`) and asserts on the output — preset shape,
YAML/TOML validity across presets/brokers/frameworks, and golden-file snapshots
of key artifacts. Runs in `template-ci.yml`'s `render-tests` job. No root Python
project, so deps come from an ephemeral uv env:

```bash
mise run test                # or: uv run --with pytest --with pytest-regressions --with pytest-xdist --with copier pytest tests/ -n auto
mise run test-golden-update  # regenerate golden files (review the diff), then commit
```

#### The single render entrypoint (`tools/render.py`, [why](context/template-testing.md#toolsrenderpy-is-the-only-place-the-template-is-rendered))

**Never add another `copier copy` invocation.** `tools/render.py` is the only
place the template is rendered — the `render` fixture, `template-ci.yml`, the
mise tasks and the committed docs artifacts all call it. A new consumer imports
`render()` or calls the CLI.

```bash
uv run tools/render.py render /tmp/x --data preset=full  # one-off render
mise run regenerate   # rewrite docs/generated-project-trees.md (commit the diff)
mise run watch        # re-render .watch-render/ on every save, authoring aid
```

`docs/generated-project-trees.md` is a **committed derived artifact** (the real
file set each preset renders): change what a preset renders → run `mise run
regenerate` or `tests/test_doc_trees.py` fails.

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
uv run --locked tox run -e 3.11
uv run --locked tox run -e 3.14

# Run a single test file
uv run --locked pytest tests/test_smoke.py -v

# Run worker broker integration tests (if include_worker=true; Docker required).
# On-demand tox env; marked `integration` and excluded from the default suite
# (context/testing-strategy.md).
uv run --locked tox run -e integration

# Run the CLI (if include_cli=true)
uv run --locked example version
uv run --locked example info

# Run the web app (if include_web=true). Same verbs for both frameworks
# (context/components.md); `dev` adds autoreload and forces a 127.0.0.1 bind.
uv run --locked example run
uv run --locked example dev
uv run --locked example run other.module:app   # any ASGI app, not just this one

# Non-primary components are subcommands of the `example` root
# (context/components.md); the *primary* component is launched by bare
# `example`. The forms below assume each is non-primary (e.g. alongside
# include_cli=true):
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
`author_email`, `short_description`. Asked once and kept: `copyright_year` (LICENSE start year, [why](context/template-updates.md#the-license-start-year-is-a-visible-copyright_year-question)). Free-form: `package_keywords`,
`repository_topics` (asked only when `include_repo_settings`). Starting point:
`preset` (`library`/`tool`/`web`/`full`, `default: library`; seeds every toggle
default via the hidden `preset_map`, [archetype presets](context/presets.md#archetype-presets-name-project-shapes-library-is-the-default)).
Choice questions gated on a toggle: `cli_framework` (when `include_cli`),
`web_framework` (when `include_web`), `worker_broker` (when `include_worker`),
and `docs_version_granularity` (`minor`/`major`/`full`, `default: minor`; when
`include_docs`, sets the versioned-docs directory granularity —
[version granularity](context/docs-versioning.md#version-granularity-is-a-scaffold-time-question)).

Optional components and integrations (all boolean; see `copier.yml` help for the
prompt, `docs/template-architecture.md` for what each renders):

| Toggle | One-line | Why |
| --- | --- | --- |
| `include_cli` | CLI — the `pkg` console root (`cli_framework` = typer or stdlib argparse) | [components](context/components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts), [components](context/components.md#cli_framework-offers-argparse-beside-typer-the-typer-dependency-is-gated-on-root_uses_typer), [components](context/components.md#launcher-imports-are-guarded-with-exact-match-preflighted-dependency-errors) |
| `include_web` | Web app (FastAPI/Litestar, `web_framework`) + Dockerfile + the `pkg run`/`pkg dev` launch verbs (forces a console root) | [components](context/components.md#the-web-component-gets-run-and-dev-launch-verbs-and-therefore-always-a-console-root) |
| `include_gui` | Tkinter GUI | — |
| `include_tui` | Textual TUI | — |
| `include_mcp` | MCP server | — |
| `include_worker` | FastStream worker (`worker_broker` = kafka/nats/rabbitmq/redis) | [testing-strategy](context/testing-strategy.md#the-worker-exposes-an-env-injectable-broker-factory-lazy-broker-imports-were-rejected) |
| `include_database` | Async database layer (Advanced Alchemy + Alembic; `database_backend` = sqlite/postgres); its own `db` import layer; on in `web`/`full` | [database-layer](context/database-layer.md#the-database-layer-is-async-only-advanced-alchemy-behind-one-include_database-toggle), [database-layer](context/database-layer.md#db-is-a-layer-of-its-own-between-the-components-and-core) |
| `include_c_extensions` | Cython + multi-platform wheels | — |
| `include_profiling` | py-spy / scalene / cProfile | — |
| `include_benchmarks` | pytest-codspeed benchmarks + non-blocking CodSpeed workflow | [external-integrations](context/external-integrations.md#opt-in-benchmarking-with-pytest-codspeed) |
| `include_examples` | `examples/` folder with usage stubs (`library`-preset default) | — |
| `include_docs` | Sphinx docs site (`docs/` Sphinx tree, `docs-*` tox envs, docs CI + versioned Pages deploy with a version switcher + per-page "last updated"); **default-on** every preset, off keeps a README-only project. `REPOSITORY_SETUP.rst` (repo root) always ships | [docs-stack](context/docs-stack.md#the-sphinx-subsystem-is-toggleable-include_docs-default-on-the-maintainer-guide-is-not), [docs-versioning](context/docs-versioning.md#docs-publish-only-the-current-version-and-carry-older-built-versions-forward-from-gh-pages) |
| `include_launcher` | PyCrucible online-first-run launcher | [standalone-executables](context/standalone-executables.md#three-architecture-named-executable-toggles-instead-of-one-brand-toggle) |
| `include_compiler` | Nuitka native-compiled executable | [standalone-executables](context/standalone-executables.md#three-architecture-named-executable-toggles-instead-of-one-brand-toggle) |
| `include_freezer` | PyInstaller offline bundle | [standalone-executables](context/standalone-executables.md#three-architecture-named-executable-toggles-instead-of-one-brand-toggle) |
| `include_pydantic_settings` | pydantic-settings config | — |
| `include_sourcery` | Sourcery config (`.sourcery.yaml`) | [external-integrations](context/external-integrations.md#sourcery-sonarcloud-and-all-contributors-are-independent-opt-in-toggles) |
| `include_sonarcloud` | SonarCloud + `sonar` CI job | [external-integrations](context/external-integrations.md#sourcery-sonarcloud-and-all-contributors-are-independent-opt-in-toggles) |
| `include_all_contributors` | all-contributors config + workflow + README section | [external-integrations](context/external-integrations.md#sourcery-sonarcloud-and-all-contributors-are-independent-opt-in-toggles) |
| `include_smokeshow` | tokenless coverage-HTML host (smokeshow step in the `coverage-combine` job; public repos only) | [ci-topology](context/ci-topology.md#a-tokenless-public-html-coverage-mirror-via-smokeshow) |
| `include_megalinter` | MegaLinter lean-complement CI layer | [lint-orchestration](context/lint-orchestration.md#megalinter-is-an-opt-in-lean-complement-non-blocking-on-three-levels) |
| `include_pypi_publish` | PyPI trusted publishing on release (default-on every preset); off ships GitHub Releases only and gates out a PyPI-backed Homebrew/Scoop | [package-distribution](context/package-distribution.md#optional-pypi-publishing) |
| `include_homebrew` | Homebrew tap dispatch (`can_distribute_natively`-gated) | [package-distribution](context/package-distribution.md#homebrew-and-scoop-are-opt-in-dispatches-the-tap-or-bucket-owns-the-manifest-logic) |
| `include_scoop` | Scoop bucket dispatch | [package-distribution](context/package-distribution.md#homebrew-and-scoop-are-opt-in-dispatches-the-tap-or-bucket-owns-the-manifest-logic) |
| `include_repo_settings` | `.github/settings.yml` via Settings App; installation requires verified code-owner review | [repo-setup](context/repo-setup.md#repository-metadata-via-the-settings-github-app-opt-in-labels-and-branch-protection-stay-out-of-it) |
| `include_repo_ruleset` | branch-protection `ruleset-sync.yml` (`full` preset) | [repo-setup](context/repo-setup.md#branch-protection-as-code-through-an-opt-in-rulesets-sync-workflow) |
| Devcontainer: `include_postgres`/`include_redis` (`redis_backend`)/`include_pgadmin`/`include_adminer`/`include_dbeaver`/`include_vpn` | devcontainer services | — |

Enabling any runnable component also renders `core/app.py`, the single
version/runtime payload every component adapts over — add a fact more than one
interface reports there, never in one of them
([shared application payload](context/components.md#one-application-payload-in-coreapppy-components-are-adapters-over-it)).

Always included (no toggle), each detailed in `docs/template-architecture.md`:
release-please-managed `CHANGELOG.md` (no seed file), Codecov upload, Renovate
(shared preset, incl. the `copier` update manager — [copier-manager updates](context/template-updates.md#renovates-copier-manager-delivers-downstream-updates-the-template-keeps-release-please-as-its-tag-source)),
`CITATION.cff` + validation, mise, import-linter architecture contract
([import-linter architecture contract](context/architecture-contracts.md#one-exhaustive-import-linter-layers-contract-cli-above-independent-components-above-core-above-utils)), Commitizen
([commit helper, not release tool](context/release-automation.md#commitizen-is-a-commit-helper-never-a-release-tool)),
cobo-managed `.gitignore` ([cobo for `.gitignore`](context/gitignore-generation.md#cobo-generates-the-gitignore-with-a-hash-sealed-fence-and-lockfiles)),
prek hooks (incl. blocking `zizmor` and `detect-secrets` with a committed
`.secrets.baseline`), the `.github/yamlfmt.yml` + `.taplo.toml` formatter configs
([formatter-canonical output](context/template-testing.md#generated-files-must-be-formatter-canonical-not-merely-valid)),
the tox `style` env as the sole lint/build
orchestrator ([tox as the canonical lint runner](context/lint-orchestration.md#the-tox-style-env-is-the-sole-authoritative-lint-suite-prek-is-a-fast-gate-not-a-second-suite)),
a style-env-only semgrep SAST pass over `src/`
([semgrep SAST](context/lint-orchestration.md#semgrep-runs-in-the-style-env-against-a-named-registry-ruleset-never-vendored)),
a `deps` dependency-hygiene gate (deptry + creosote, [why](context/lint-orchestration.md#dependency-hygiene-deptry--creosote-is-an-always-on-deps-gate-not-a-toggle)),
editorconfig-checker, ghalint, `SUPPORT.md`, `.gitattributes`, `.git_archival.txt`,
and a hand-written `AGENTS.md` agent onboarding file (per-host agent and
skill files come from [copier-skill-repo](https://github.com/hasansezertasan/copier-skill-repo),
not this template —
[agent instructions](context/agent-instructions.md)).

### Load-bearing invariants

Do not break these — each is a real footgun with the detail/why in its linked
`context/` entry:

- **No `CHANGELOG.md.jinja` seed.** release-please owns the changelog; a
  scaffold-time seed overwrites and wipes an adopting project's release history.
- **`copier.yml` defines no `_tasks`.** A task forces `copier --trust`, which the
  hosted Renovate App disables, breaking the `copier`-manager auto-update
  ([no `_tasks`](context/template-updates.md#copieryml-defines-no-_tasks)).
- **This repo's release-please must keep cutting tags** — those git tags are the
  datasource the generated projects' Renovate `copier` manager consumes
  ([copier-manager updates](context/template-updates.md#renovates-copier-manager-delivers-downstream-updates-the-template-keeps-release-please-as-its-tag-source)).
- **Shipped `template/**` pins are frozen from Renovate** (disabled `packageRules`
  entry). Seed values only; do **not** re-enable, or `copier update` conflicts on
  nearly every release ([frozen template pins](context/template-updates.md#shipped-template-pins-are-frozen-from-this-repositorys-renovate)).
- **Do not hand-edit inside the cobo-sealed `.gitignore` fence** (`# >>> cobo:begin`
  … `# <<< cobo:end sha256=…`) — it breaks the sha256. Regenerate with
  `cobo update && cobo sync` ([cobo for `.gitignore`](context/gitignore-generation.md#cobo-generates-the-gitignore-with-a-hash-sealed-fence-and-lockfiles)).
- **Generated files must be formatter-canonical.** Not merely valid YAML/TOML —
  already in the exact byte form the *generated* project's own formatters emit
  (yamlfmt, taplo, ruff-format, the prek builtins), or the adopter's first
  `prek run --all-files` rewrites them and every `copier update` shows drift they
  never caused. So: folded `>-` scalars on one line, no comment trailing a YAML
  sequence, TOML arrays 2-space one-per-line with a trailing comma, one space
  before a trailing comment, and `{%- … %}` whitespace control so a conditional
  block never leaves >2 blank lines or a blank line at EOF. Guarded per scenario
  by template-ci's "Verify rendered files are formatter-canonical" step (which
  gates on `git diff`, not hook exit codes — taplo used to rewrite files and
  exit 0) plus `tox -e style`'s check-mode taplo/ruff-format
  ([formatter-canonical output](context/template-testing.md#generated-files-must-be-formatter-canonical-not-merely-valid)).
- **Shared Jinja helpers live in `_macros.jinja`** at the repo root — outside
  `_subdirectory`, so it is an input copier can never render into a project.
  Templates import it on their first line. It carries `py_collection()`, which
  emits a tuple/list literal in the byte form ruff-format produces (a second
  hand-rolled copy of that width logic is the drift this replaced —
  [one shared collection macro](context/template-testing.md#collection-literals-are-rendered-through-one-shared-macro)), and
  the `agent_*()` prose macros, the source of the rendered `AGENTS.md`.
  Edit the prose there.
- **One render entrypoint.** `tools/render.py` is the only place `copier.run_copy`
  is called (harness fixture, CI matrix, docs artifacts, watch loop, mise tasks);
  adding a second `copier copy` spelling is the drift this replaced
  ([single render entrypoint](context/template-testing.md#toolsrenderpy-is-the-only-place-the-template-is-rendered)).
- **Verify zizmor changes with the prek hook** (`prek run zizmor --all-files`),
  not a bare `uvx zizmor` — the two can pin versions with different
  `dangerous-triggers` behavior; the prek hook is what gates.
- **The console-script precedence lives once** — the `primary_component` computed
  var in `copier.yml` (CLI > GUI > TUI > web > MCP > worker). Derive from it; do
  **not** re-spell it as inline `include_x or include_y …`
  ([components as subcommands](context/components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts)).
- **A web project always has a console root.** `include_console_root` includes
  `include_web` so `pkg run`/`pkg dev` have somewhere to live; the alternative
  (standalone `pkg-run`/`pkg-dev` scripts) is the second entry scheme the
  [subcommand decision](context/components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts) forbids. Consequence: `sole_component` is never `web`
  ([run/dev launch verbs](context/components.md#the-web-component-gets-run-and-dev-launch-verbs-and-therefore-always-a-console-root)).
- **Per-component coverage scopes must match both layouts.** The per-component
  `coverage report --include`/`--omit` patterns in `ci.yml`'s `coverage-*` jobs
  must match `src/<pkg>/…` (editable) **and** `*/site-packages/…` (installed
  wheel/sdist), so they are `*/`-anchored — a `src/**`-only pattern silently
  reports the installed copy at 0%. Verify via a real `tox run`, never editable
  `pytest` ([per-component CI](context/ci-topology.md#per-component-markers-path-filtered-jobs-and-one-coverage-gate-per-component)).
- **A required status context must actually report, and must actually gate.**
  Four shapes of this bug have shipped: a `[bot]` skip on
  `task-completed-check.yml` left *no* `Task Completed Checker` check run behind;
  then ruleset evaluation stopped honoring those synthetic runs at all (issue
  #418), so the gate now keys on the `Check PR task list` job name with an
  enforce step that re-evaluates the current PR body and fails the job on
  unticked boxes — order-independent, so overlapping runs cannot disagree; the Sphinx warning gate
  lived only in `docs-preview.yml`, which forks skip and nothing requires, so
  `tox -e docs-build` now runs in `ci.yml`'s `docs-doctest` job that `check`
  aggregates (`fetch-depth: 0`, or `sphinx-last-updated-by-git` fails it); and
  the Codecov project status is scoped to `flags: [unit]`, so the upload must
  pass `flags: unit` or the 99% target is never computed. When you add a gate,
  check *which context a protected branch sees* — not that the job runs.
- **Never remove `workflow_dispatch` from `release.yml`.** It looks like a
  publish-escalation surface (a manual run executes the file from the selected
  branch, so the `release_created` guard is not a mitigation), but
  `finalize-release` re-dispatches the workflow with `gh workflow run` to
  reconcile the phantom release PR, and that API requires the trigger. The
  containment is the `publish` environment's deployment-branch policy, which
  GitHub evaluates outside the workflow file — a `REPOSITORY_SETUP.rst` `[AGENT]` step.
- **A failed `gh-pages` fetch must abort, never fall through.** `git fetch
  origin gh-pages:gh-pages || echo ...` swallows a transport error as "branch
  absent"; `build_docs.py` then assembles a site with no prior versions and the
  clean-on-deploy *deletes* every published version. Both deploy paths use an
  `ls-remote --exit-code` guard (exit 2 = absent, anything else aborts), and
  `preserve_from_gh_pages()` raises for a version slug it cannot read back —
  only the `latest` alias is optional
  ([a failed fetch must abort](context/docs-versioning.md#a-failed-gh-pages-fetch-must-abort-never-fall-through-as-branch-absent)).
- **Docs deploys must preserve the version-slug directories** (numeric, e.g.
  `0.3/` — no leading `v`). Both `release.yml` `deploy-docs` and the manual
  `gh-pages.yml` build only the current version and re-supply prior versions from
  `gh-pages` via `tools/build_docs.py`; a naive root publish with only
  `clean-exclude: pr-preview/**` would wipe every version directory. The manual
  workflow checks out the latest *published* release's tag first (via
  `gh api .../releases/latest`, never HEAD and never `git describe`, which would
  pick up a draft release's tag). Old versions are never rebuilt
  ([versioned docs](context/docs-versioning.md#docs-publish-only-the-current-version-and-carry-older-built-versions-forward-from-gh-pages)).

### CI/CD Workflows — index

Detail (jobs, gating, security posture) in `docs/template-architecture.md`.

| Workflow | Purpose | Why |
| --- | --- | --- |
| `ci.yml` | `changes` path-filter → per-component `test-*` + scoped `coverage-*` gates + central `coverage-report`; asymmetric matrix, draft skip, style/CLI, packaging/worker-integration guards | [standalone-executables](context/standalone-executables.md#every-executable-toggle-adds-a-pr-time-build-check-job), [testing-strategy](context/testing-strategy.md#real-broker-integration-tests-testcontainers-locally-per-broker-ci-mechanism), [ci-topology](context/ci-topology.md#per-component-markers-path-filtered-jobs-and-one-coverage-gate-per-component), [ci-topology](context/ci-topology.md#asymmetric-matrix-every-interpreter-on-linux-one-representative-elsewhere-style-and-installed-cli-are-separate-jobs), [ci-topology](context/ci-topology.md#every-generated-ci-job-skips-draft-pull-requests) |
| `release.yml` | release-please → build / pypi-publish / executables / docker / docs / sbom / issue-notify | [release-automation](context/release-automation.md#release-please-is-the-sole-release-orchestrator), [release-automation](context/release-automation.md#released-issue-notifications-are-one-inline-job-in-releaseyml) |
| `check-pr-title.yml` | PR title vs Conventional Commits | — |
| `check-linked-issues.yml` | require a linked issue (`no-issue` bypasses) | — |
| `task-completed-check.yml` | fail while PR task-list boxes unticked | — |
| `check-branch-name.yml` | Conventional Branch head-name lint | — |
| `codeql` / `scorecard` / `dependency-review` / `check-security.yml` | supply-chain security passes | — |
| `zizmor.yml` | workflow-hardening SARIF dashboard (non-blocking) | — |
| `docs-preview.yml` | per-PR Sphinx previews under `pr-preview/**` | [docs-stack](context/docs-stack.md#pr-docs-previews-deploy-to-a-subfolder-of-the-projects-own-gh-pages-same-repo-only) |
| `docs-linkcheck.yml` | weekly link check (non-blocking) | [docs-stack](context/docs-stack.md#sphinx-lint-and-the-case-conflict-hook-are-always-on-link-checking-is-weekly) |
| Renovate `copier` manager | downstream template updates (not a workflow) | [template-updates](context/template-updates.md#renovates-copier-manager-delivers-downstream-updates-the-template-keeps-release-please-as-its-tag-source) |

Required status checks on generated repos (context names, not workflow files):
**check** (`ci.yml`'s aggregate gate — the only one covering the code),
**Validate PR title**, **Validate branch name**, **Verify linked issue**, and
**Check PR task list** (the job — its enforce step fails on unticked boxes).

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

The generated project's `REPOSITORY_SETUP.rst` is the one-time "Repository
setup" guide (`[AGENT]`/`[HUMAN]`/`[CHECK]`-tagged — [maintainer setup guide](context/repo-setup.md#maintainer-repository-setup-has-one-actor-tagged-home-in-the-docs-tree);
no skill is shipped for it, see [repo-setup decision](context/repo-setup.md#a-resume-driven-repo-setup-skill-reads-check-blocks-from-the-setup-doc-no-separate-manifest)); keep it in sync when these
requirements change. This repo's own two-step setup is the pair of `gh`
commands under "One-time repo setup" in `docs/template-architecture.md`; bump
rules and this repo's own self-versioning are detailed there and in
[copier-manager updates](context/template-updates.md#renovates-copier-manager-delivers-downstream-updates-the-template-keeps-release-please-as-its-tag-source).

The adoption and update guidance is not a skill: it is the **Template updates** and **Adopting into an existing project** sections of `REPOSITORY_SETUP.rst`. Generated projects must carry no copier or template provenance outside `.copier-answers.yml`, `README.md` and `REPOSITORY_SETUP.rst` — no links to this repository's docs or issues, no "copier update" prose in comments — which `tests/test_adoption_reference.py` guards.

## Code Style Guidelines

- **Imports**: Absolute only, grouped stdlib→third-party→local (ruff enforced)
- **Formatting**: Ruff, 88 chars, LF endings
- **Types**: Strict typing required, `from typing import ...`
- **Naming**: snake_case vars/functions, PascalCase classes, UPPER_CASE constants
- **Error Handling**: Specific exceptions with context
- **Tools**: Ruff, five type checkers (mypy, basedpyright strict, ty, pyrefly, zuban), pytest + coverage, prek
- **Complexity**: Max cyclomatic complexity of 5 (ruff mccabe)
- **Structure**: Code in `src/{{github_repo_name}}/`, tests in `tests/`

## Template Modification Guidelines

### Adding New Template Files

1. Create file in `template/` with `.jinja` extension
2. For conditional files, use `{% if condition %}filename{% endif %}.jinja` naming
3. Use `{{variable_name}}` for Copier variable substitution
4. Test by regenerating `example/` directory

### Adding New Optional Components

Keep `AGENTS.md` growth capped: a new toggle updates `copier.yml` help + a
`context/` entry (the decision, the rejected alternatives and why — through the
`keep-the-why` skill, not a new ADR) + the detail in
`docs/template-architecture.md` + **one** row in the toggle index above — never a
multi-line block here.

1. Add boolean variable to `copier.yml` with `type: bool`, `default`, and `help`
2. If component has choices (like `worker_broker`), add a separate choice variable with `when: "{{ parent_option }}"`
3. Create conditional directory: `template/src/{{github_repo_name}}/{% if include_xxx %}xxx{% endif %}/`
4. Create matching test directory: `template/tests/{% if include_xxx %}xxx{% endif %}/`
5. Update `pyproject.toml.jinja`:
   - Add the runtime dependency to the core `dependencies` list under the
     component's `{% if include_xxx %}` guard — **not** an optional extra: the
     component's console script imports it unconditionally, so `pip install
     <pkg>` must pull it. Generated projects declare **no**
     `[project.optional-dependencies]` at all ([no empty `all` extra](context/components.md#component-dependencies-are-core-dependencies-there-is-no-empty-all-extra)).
   - Add the entry point if applicable. If the component is runnable, fold it
     into the console-script precedence in `primary_component` (`copier.yml`); a
     non-primary component gets a `<pkg> <name>` **subcommand** (add a lazy
     `@app.command()` in `cli/app.py.jinja`, guarded on
     `include_xxx and primary_component != 'xxx'`), **not** a `<pkg>-<name>`
     script (see [components as subcommands](context/components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts)). If it is a *new kind* of runnable component, also
     extend `include_console_root` in `copier.yml`. Do not spell out the
     precedence inline anywhere.
   - Add keywords
   - Add the component to the `[tool.importlinter]` `layers` contract (a sibling in the `il_components` list, or — like `cli` — its own orchestrator layer if it imports other components)
   - Read the version/info payload from `core/app.py` (`service.version()` /
     `service.info()` / `service.info_or_unknown()`), mapping
     `MetadataUnavailableError` onto the component's own failure. Do **not**
     re-implement the `Distribution.from_name` lookup or the `platform.*`
     payload — that duplication is what the
     [shared application payload](context/components.md#one-application-payload-in-coreapppy-components-are-adapters-over-it) removed.
6. Add the new toggle to the `full` entry in `copier.yml`'s `preset_map` (and to
   any archetype preset — `library`/`tool`/`web` — whose shape includes it).
   `.example-input.yml` no longer lists individual toggles, so it needs no change.
7. Update `README.md` and add the toggle's detail to `docs/template-architecture.md`
8. Test the component's metadata-failure path with the shared
   `missing_metadata` fixture from `tests/conftest.py` (it patches
   `core.app.Distribution`, which every component reads through), not a
   per-module `_MissingDistribution` stub.
9. Keep the component's coverage at the `fail_under = 99` gate (see
   [coverage exclusions](context/testing-strategy.md#coverage-exclusions-are-per-site-pragmas-and-the-globs-must-match-the-installed-layout)). Because
   `.example-input.yml` uses the `library` preset (no interface components), a
   component's coverage is only validated when you generate it explicitly — do that and run the suite. Unit-test
   the business logic *including reachable error handling* (metadata-failure
   paths are tested via the shared `missing_metadata` fixture — see the
   web/cli/gui/tui/mcp tests); only for genuinely untestable irreducible
   blocking calls add `# pragma: no cover` to the specific helper function
   (as the `_run_server`, `_run_app`, and `_stdio_transport` helpers, and the
   `__main__` dispatchers do). Interactive components isolate these
   blocking calls behind injected default drivers/runners so that setup, teardown,
   and CLI dispatching can be driven deterministically under headless CI (see [headless testing](context/testing-strategy.md#interactive-components-expose-injected-driver-seams-so-headless-ci-measures-everything-but-the-blocking-call)).
   Do **not** add blanket `exclude_lines` regexes for these — see the convention below.
10. Wire the component into the per-component marker + path-filter surfaces
   ([per-component CI](context/ci-topology.md#per-component-markers-path-filtered-jobs-and-one-coverage-gate-per-component)), which
   must stay in lockstep: register the marker in `pyproject.toml.jinja`
   `[tool.pytest.ini_options] markers` **and** add its `tests/` dir to
   `tests/conftest.py.jinja` `_COMPONENT_DIRS`; add its `changes` filter + its
   `test-<component>` and scoped `coverage-<component>` jobs in `ci.yml.jinja`
   (all driven by the `comp_names` list — extend that and the loops follow); and
   add its subtree to the `coverage-core` `--omit` list. Verify both gates via a
   real `tox run` on an explicitly-generated project (installed layout).

### Coverage exclusion convention

Generated projects enforce `fail_under = 99`. Entrypoints that start an irreducible
blocking loop (textual event loop, uvicorn server, faststream loop, or stdio
stream) cannot run under headless CI, so each carries a per-site `# pragma: no cover`
restricted to the leaf runner helper (e.g. `_run_server`, `_run_app`, `_stdio_transport`,
along with the top-level `__main__` dispatchers, the c-extension
`except ImportError` fallback, and the worker's module-level metadata fallback).
All surrounding setup, UI widgets, lifecycle hooks, error handlers, and CLI subcommand
dispatchers are tested via injected drivers or headless pilots (see [headless testing](context/testing-strategy.md#interactive-components-expose-injected-driver-seams-so-headless-ci-measures-everything-but-the-blocking-call)).
The logic those entrypoints call is always unit-tested.

Do **not** exclude these via blanket `[tool.coverage.report] exclude_lines`
regexes (`def main\(`, `except PackageNotFoundError`, ...): a regex matching a
`def` line excludes the *entire function body*, so such patterns silently
un-measure any future function with the same name that carries real logic —
and previously masked the tested GUI/TUI `main()` entrypoints and the web 503
handlers. Reachable error handling is tested, not excluded: the web `/version`
and `/info` 503 responses, the CLI metadata-failure exit code, the GUI/TUI
"Version: unknown" degradation, and the MCP error-text response all have unit
tests using the shared `missing_metadata` fixture (`tests/conftest.py`), which
patches `core.app.Distribution` — the one module every component reads metadata
through ([shared application payload](context/components.md#one-application-payload-in-coreapppy-components-are-adapters-over-it)).

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
[coverage exclusions](context/testing-strategy.md#coverage-exclusions-are-per-site-pragmas-and-the-globs-must-match-the-installed-layout).

CI enforces this gate **per component**, not once over a union: the `ci.yml`
`coverage-<component>` jobs each merge their component's OS cells and gate
`fail_under = 99` scoped to that subtree (`--include` for a component,
`--omit` of every component for `coverage-core`); a central non-gating
`coverage-report` job publishes the combined HTML/XML + Codecov. A CLI `--omit`
overrides the pyproject `omit`, so `coverage-core` re-adds `*/_version.py`; the
component gates pass only `--include`, so the config `omit` still shields the
worker integration file. This decomposition (which lets a path-skipped component
keep the merge gate green) is
[per-component CI](context/ci-topology.md#per-component-markers-path-filtered-jobs-and-one-coverage-gate-per-component), superseding
the [single union gate](context/ci-topology.md#a-single-union-coverage-gate-across-the-whole-matrix).

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

1. Running the render harness: `mise run test`
2. Regenerating the example: `mise run example`
3. Running style checks: `cd example && uv run --locked tox run -e style`
4. Running tests: `cd example && uv run --locked tox run`

If the change adds or removes a generated file, also run `mise run regenerate`
and commit the `docs/generated-project-trees.md` diff (`tests/test_doc_trees.py`
fails otherwise).

For features with choices (like `worker_broker`), test multiple combinations:

```bash
uv run tools/render.py render /tmp/test-kafka --data include_worker=true --data worker_broker=kafka
uv run tools/render.py render /tmp/test-rabbitmq --data include_worker=true --data worker_broker=rabbitmq
```

## Copier-Specific Behavior

- **Subdirectory**: `_subdirectory: template` means Copier renders from `template/` not root
- **Answers File**: `{{_copier_conf.answers_file}}.jinja` becomes `.copier-answers.yml`
- **Update Workflow**: Users run `copier update` to pull template changes (automated
  by Renovate's `copier` manager — [copier-manager updates](context/template-updates.md#renovates-copier-manager-delivers-downstream-updates-the-template-keeps-release-please-as-its-tag-source))
- **Trust Flag**: Use `--trust` when testing locally (there is no post-copy
  `_tasks`; `git init` is a documented manual step — see the invariant above)
