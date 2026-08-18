# Template Architecture Reference

Deep reference for the `copier-pyproject` template — the detail that used to
live in `CLAUDE.md`. `CLAUDE.md` is now a lean router: it keeps the load-bearing
agent instructions inline and points here for the "what gets rendered" detail and
to the [ADRs](adr/) for the "why". Three sources of truth, no duplication:

- **`copier.yml` `help:`** — the one-line prompt shown for each toggle.
- **This page** — what each toggle/workflow renders and how the pieces fit.
- **The ADR** — why it exists, the trade-offs, the posture.

When a toggle's rationale changes, edit the ADR. When what it renders changes,
edit this page and `copier.yml` help. Do not restate either in `CLAUDE.md`.

## Template Variables (copier.yml)

Required inputs:

- `github_user`, `github_repo_name`, `author_full_name`, `author_email`, `short_description`

Free-form metadata:

- `package_keywords` - extra comma-separated PyPI keywords prepended to the generated
  `keywords` list (default empty); the template's own base keywords plus tooling and
  enabled-component keywords are always appended automatically. (The classifiers list
  is still auto-generated from enabled components — it carries a `TODO` marker for the
  generated project's author to fill in project-specific classifiers.)
- `repository_topics` - comma-separated GitHub repository topics (default empty),
  asked and used **only** when `include_repo_settings` is enabled
  (`when: "{{ include_repo_settings }}"`). Rendered into
  `.github/settings.yml` as the `topics:` list (lower-cased, space/underscore
  hyphenated). Left empty, the `topics:` key is omitted entirely so the Settings
  App leaves the repository's existing topics untouched. See
  [ADR-018](adr/018-repository-settings-as-code.md).

Starting point:

- `preset` - `library`/`tool`/`web`/`full`. Seeds the default of every
  `include_*` toggle via the hidden `preset_map` computed variable (`when: false`,
  never stored) — every preset includes `docs`; `library` → `docs` + `examples`;
  `tool` → `docs` + `cli` + `tui` + `pydantic_settings`; `web` → `docs` + `web` +
  `pydantic_settings` + `postgres` + `redis`; `full` → everything. `default:
  library` (the smallest surface, so an unattended `--defaults` run produces a
  plain package with docs). Toggles remain asked and
  stored — the preset only changes defaults; it hides nothing, though
  dependency-gated sub-questions (the DB UIs, web framework, worker broker, redis
  backend) still appear only when their parent toggle is enabled, independent of
  the preset. The `minimal`/`standard`/`custom` presets and the byte-identical
  `--defaults` guarantee were removed in
  [ADR-016](adr/016-archetype-based-presets.md).

Optional components (all boolean):

- `include_cli` - CLI (`cli_framework`: Typer, or standard-library `argparse` for
  a dependency-free command root exposing the same `version`/`info` commands and
  component subcommands — see [ADR-020](adr/020-cli-framework-choice.md))
- `include_web` - Web app + Dockerfile (framework choice: FastAPI or Litestar)
- `include_gui` - Tkinter GUI
- `include_tui` - Textual TUI
- `include_mcp` - MCP (Model Context Protocol) server
- `include_worker` - FastStream message queue worker
- `include_c_extensions` - Cython support with multi-platform wheels
- `include_profiling` - py-spy, scalene, cProfile tools
- `include_launcher` - uv-bootstrap launcher (PyCrucible) — small executable, downloads Python+deps on first run
- `include_compiler` - compiler (Nuitka) — source compiled to a native machine-code executable
- `include_freezer` - offline freezer (PyInstaller) — self-contained bundle, no Python on target

  These three standalone-executable toggles are independent and combinable; each
  maps to one architectural category (launcher / compiler / freezer). See
  [ADR-007](adr/007-standalone-executable-toggles.md).
- `include_examples` - an `examples/` folder with simple and advanced usage stubs
  (enabled by the `library` preset default)
- `include_docs` - the Sphinx documentation subsystem, **`default: true` in every
  preset** (docs-by-default; off is a deliberate opt-out for a README-only
  project). Guards the ten Sphinx-site files under `docs/` (`conf.py`,
  `check_warnings.py`, `expected_warnings.txt`, `index.rst`, `installation.rst`,
  `usage.rst`, `modules.rst`, the `web-interface.rst`/`worker-interface.rst`
  component pages, and the `cli-reference.md` page — those three also on their
  component toggles, the CLI page additionally on `cli_framework == "typer"`), the `docs`
  dependency group, the `docs-build`/`docs-server`/`docs-linkcheck` tox envs, the
  `sphinx-lint` entry in the `style` tox env and prek hook, the `sphinx` keyword,
  the `docs-preview.yml`/`docs-linkcheck.yml`/`gh-pages.yml` workflows and the
  `release.yml` `deploy-docs` job, plus the README docs badge/link, `SUPPORT.md`
  link, `CONTRIBUTING.md` docs section, and `mise` `docs-*` tasks. **Exception:**
  `docs/maintaining/setup.rst` (the maintainer repository-setup guide the
  `repo-setup` skill reads, hard-referenced by README/CONTRIBUTING/`ci.yml`/
  `settings.yml`/`.sourcery.yaml`/`sonar-project.properties`) always ships — only
  its GitHub Pages step is `include_docs`-gated — and with docs off the
  `settings.yml` `homepage` falls back to the repository URL. See
  [ADR-025](adr/025-optional-docs-subsystem.md).
- `include_pydantic_settings` - pydantic-settings for config
- `include_sourcery` - Sourcery AI-refactoring config (`.sourcery.yaml`)
- `include_sonarcloud` - SonarCloud static-analysis (`sonar-project.properties` + a `sonar` CI job)
- `include_all_contributors` - all-contributors config (`.all-contributorsrc`) + README section
- `include_smokeshow` - publish the combined coverage HTML report to a tokenless ephemeral URL via `smokeshow` (a step in the `coverage-combine` CI job; public repos only, `default: false`; see [ADR-026](adr/026-combined-cross-matrix-coverage-and-tokenless-html-host.md))

  These are opt-in integrations kept as toggles (not always-on) precisely to
  preserve the self-contained "green on first push, zero external accounts"
  default: each is off in the base `library`/`tool`/`web` presets (only the `full`
  preset seeds them on), so a plain project never pays for them unasked. `include_smokeshow` needs no account at all (a
  tokenless public-repo-only coverage-HTML mirror in the `coverage-combine` job —
  [ADR-026](adr/026-combined-cross-matrix-coverage-and-tokenless-html-host.md));
  `include_sourcery` (config-only, external App) and
  `include_sonarcloud` (needs a SonarCloud org + `SONAR_TOKEN` secret) require
  out-of-band setup; the `sonar` job mirrors the Codecov opt-in/non-blocking
  pattern (gated on the `SONAR_TOKEN` presence flag, skips fork PRs, visible
  `::notice::` skip when unset, not in the `check` gate). `include_all_contributors`
  is more self-contained: besides `.all-contributorsrc` + the README section, it
  renders an `all-contributors.yml` workflow that runs the all-contributors **CLI**
  (delivered via mise's npm backend, `mise exec -- all-contributors generate`,
  mirroring ghalint; version pinned in `mise.toml` and Renovate-tracked) and opens
  a PR via `peter-evans/create-pull-request` (never pushes to the default branch,
  so `persist-credentials: false` holds), so the bot/App is optional — it only
  needs the *Allow Actions to create PRs* setting release-please already requires.
  See
  [ADR-009](adr/009-optional-external-quality-community-integrations.md).
- `include_megalinter` - MegaLinter as an opt-in extra CI quality layer
  (`mega-linter.yml` + `.mega-linter.yml`), `default: false`.

  Unlike the ADR-009 trio, MegaLinter is a self-contained Docker action needing
  **no** external account — but it was previously shipped **always-on and
  undocumented**, which both violated the fast/self-contained default and
  duplicated prek. Now gated, and when enabled it is a **lean complement**: its
  `ENABLE_LINTERS` is trimmed to only the linters prek/tox do **not** already
  cover — `BASH_SHELLCHECK`, `DOCKERFILE_HADOLINT` (jinja-gated on `include_web`,
  the only config with a Dockerfile), `JSON_JSONLINT` (scoped to skip the
  JSONC-with-comments `devcontainer.json`/`.vscode/*.json`), and
  `COPYPASTE_JSCPD`, and `SPELL_CSPELL` **scoped to `.md`** (a deeper,
  dictionary-driven prose complement to prek's fast whole-tree `typos` — the one
  deliberate overlap, not a replacement) — never
  actionlint/yamllint/markdownlint/editorconfig (prek), never Python (tox), never
  the repository security linters (`check-security.yml` + CodeQL/Scorecard). It runs
  on the smaller **`cupcake` flavor** image, which cuts the dominant image-pull
  cost that made it slow (the effective per-run lever). It runs on every push/PR
  to the default branch — **no paths filter**, because `COPYPASTE_JSCPD` scans
  source so a filter would fire on nearly every PR anyway; an always-run is
  simpler and more predictable. Non-blocking on three levels: `DISABLE_ERRORS:
  true` (reports findings but exits `0`, so a lint nit never posts a red check —
  not just the `check`-gate exclusion and `GITHUB_STATUS_REPORTER: false`). A
  project that wants it to gate can require its code-scanning results via branch
  protection. The job **does** carry
  `security-events: write` and pushes MegaLinter's SARIF
  (`SARIF_REPORTER: true`) to the code-scanning dashboard via
  `github/codeql-action/upload-sarif` — a real Security-tab upload (not just the
  `upload-artifact` archive), best-effort (`continue-on-error`, `if: always()`)
  and mirroring `zizmor.yml`'s free-on-public / GHAS-on-private posture. The
  MegaLinter-only
  `.shellcheckrc` is gated with the toggle; the prek-shared configs
  (`.markdownlint.yml`, `.github/actionlint.yaml`, `.github/yamllint.yaml`) stay
  always-on. See
  [ADR-013](adr/013-megalinter-opt-in-lean-complement.md).
- `include_homebrew` - Homebrew tap distribution, `default: false` and
  `when: "{{ is_app }}"`-gated (only offered for app-like projects, not a
  library). The generated
  project does not build a formula/cask itself: its `release.yml` fires a
  `repository_dispatch` (`update-formula`/`update-cask`) at the owner's own
  `homebrew-tap` repo, which owns the manifest logic via `brew
  bump-formula-pr`/`bump-cask-pr` + `brew update-python-resources`. A
  reference listener workflow + setup guide ships under
  `docs/packaging/homebrew-tap/` for copying into that tap repo. Needs a
  `HOMEBREW_TAP_TOKEN` secret: a fine-grained PAT with **Contents: write**
  only on the tap repo (no `Pull requests` scope — the tap opens its own PR
  with its own `GITHUB_TOKEN`). See
  [ADR-017](adr/017-opt-in-homebrew-scoop-distribution.md).
- `include_scoop` - Scoop bucket distribution (opt-in), the same
  dispatch-not-generation pattern: `release.yml` fires `update-manifest` at
  the owner's own `scoop-bucket` repo, which owns the manifest via its own
  `checkver`/`autoupdate` (or updater script). A reference listener + setup
  guide ships under `docs/packaging/scoop-bucket/`. Needs a
  `SCOOP_BUCKET_TOKEN` secret with the same **Contents: write**-only PAT
  scope. Both toggles pick a binary (Homebrew cask / Scoop binary-zip
  manifest) vs. PyPI (Homebrew formula / Scoop pipx manifest) payload via the
  `primary_executable` precedence (`freezer` > `compiler` > `launcher`; empty
  ⇒ PyPI fallback). See
  [ADR-017](adr/017-opt-in-homebrew-scoop-distribution.md).
- `include_repo_settings` - repository metadata as code: a `.github/settings.yml`
  (description/homepage/topics + squash-merge flags) synced by the "Settings"
  GitHub App, `default: false`. Opt-in like the ADR-009 integrations because the
  App is an external install (and it escalates push→admin — mitigated via the
  shipped CODEOWNERS + "Require review from Code Owners"). Labels are NOT managed
  here — they stay App-free in `labels.yml`/`label-sync.yml`. The "Include in the
  home page" sidebar toggles are not settable via any API (UI-only). See
  [ADR-018](adr/018-repository-settings-as-code.md).
- `include_repo_ruleset` - repository branch protection as code: a
  `.github/rulesets/main.json` (squash-only, linear history, required CI checks —
  the actual job names this template ships, Trivy gated on `include_web`) applied
  by an App-free, idempotent `ruleset-sync.yml` workflow (list → find by name →
  PUT/POST), `default: false` and `full`-preset only. Opt-in and independent of
  `include_repo_settings` (the "Settings" App cannot manage rulesets). The
  workflow needs a `REPO_ADMIN_TOKEN` fine-grained PAT (Administration: read &
  write) — the Actions `GITHUB_TOKEN` has no `administration` scope — and
  warn-and-skips when the secret is absent (ADR-017 posture).
  `required_approving_review_count` is 0 (checks strictly enforced, no
  human-approval requirement, no `bypass_actors`) so solo maintainers and
  release-please/Renovate are not blocked. See
  [ADR-021](adr/021-repository-ruleset-as-code.md).

Framework/broker choices (when parent option is enabled):

- `web_framework` - fastapi/litestar (when `include_web` is true)
- `worker_broker` - kafka/nats/rabbitmq/redis (when `include_worker` is true)

Devcontainer services:

- `include_postgres` - PostgreSQL service
- `include_redis` - Redis/Valkey service
- `redis_backend` - redis/valkey image (when `include_redis` is true)
- `include_pgadmin` - pgAdmin UI (when `include_postgres` is true)
- `include_adminer` - Adminer UI (when `include_postgres` is true)
- `include_dbeaver` - CloudBeaver database management UI
- `include_vpn` - OpenVPN client

Always included (no toggle): a Keep-a-Changelog `CHANGELOG.md` **created and
maintained by release-please** — the template does **not** ship a
`CHANGELOG.md.jinja` seed file. release-please generates `CHANGELOG.md` on its
first release PR (per `changelog-path` in `.github/release-please-config.json`).
Do not re-add a seed template: a scaffold-time `CHANGELOG.md` overwrites the
existing changelog when an already-published project adopts the template via
`copier copy`/`copier update`, wiping its release history (this happened during a
real template adoption). Codecov coverage upload (`.github/codecov.yml` + CI step), Renovate
dependency management (`.github/renovate.json` extends the shared preset
`github>hasansezertasan/renovate-config:python`, which carries the base
`config:recommended` + `helpers:pinGitHubActionDigests` policy and the prek-hook
`customManagers` regex; Dependabot and the `none` opt-out were removed — there is
no longer a `dependency_management` option), a `CITATION.cff`
file with a `validate-citation.yml` workflow (the `include_citation` toggle was
removed — it is now always rendered and validated via
`citation-file-format/cffconvert-github-action`), and mise
(`mise.toml` + devcontainer feature) for tool version management and task
running. Pants and Trunk were removed entirely — the tox `style` env is the sole
lint/build orchestrator (see [ADR-003](adr/003-tox-as-canonical-lint-runner.md)).

**import-linter** enforces the generated package's architecture: one always-on
`layers` contract (in `[tool.importlinter]`) keeps the component group
(`web`/`gui`/`tui`/`mcp`/`worker`) mutually independent, with `cli` as an
orchestrator layer above them (the `{{pkg}}` Typer root, whose subcommands
lazy-import those components to launch them — see ADR-019), all layered above
`core` above `utils`. The `cli` layer is present whenever `include_console_root`
is true (see the entry-points section below), not only when `include_cli` is set.
The component layers are Jinja-conditional on the enabled toggles (omitted when
none are enabled, leaving a `core > utils` contract), so no `ignore_imports` is
needed.
Delivered via the `style` group + a `lint-imports` command run from **both** the
tox `style` env and a prek `local` `system` hook (`uv run --locked --group style
lint-imports`) — the same dual-run, single-version-source pattern as
`basedpyright`, since import-linter is likewise a whole-program analyzer that
needs the installed package and a `grimp` import-graph build. It is **not**
eligible as an upstream prek **repo hook** (those run in an isolated venv without
the project installed); the `local` `system` hook shells out through `uv run`,
which syncs and resolves the package. **slotscheck** (which imports `src/` to
verify `__slots__`) is delivered the same dual-run way and for the same reason —
whereas the redundant type checkers `ty`/`pyrefly`/`zuban` stay style-env-only so
the fast gate carries one representative type checker (basedpyright), not five.
See [ADR-014](adr/014-import-linter-for-architecture-contracts.md).

Also always included (no toggle): structured GitHub issue forms
(`.github/ISSUE_TEMPLATE/bug_report.yml` + `feature_request.yml` + `config.yml`,
the latter disabling blank issues) whose `component` dropdown is Jinja-gated to
only list enabled runnable components (`include_console_root`/`include_cli`/
`include_gui`/`include_tui`/`include_web`/`include_mcp`/`include_worker`), a
`pull_request_template.md` with a real task-list checklist (feeding
`task-completed-check.yml`) and a fillable `Closes #` line (feeding
`check-linked-issues.yml`), a `SUPPORT.md` community-health file (points to
docs/issues/discussions and cross-references `SECURITY.md`/`CONTRIBUTING.md`), a
`.gitattributes` (LF normalization matching the ruff/EditorConfig policy, Linguist
overrides marking `_version.py`/`CHANGELOG.md`/`uv.lock`/`cobo.lock` as generated
and `docs/`
as documentation, `export-ignore` archive hygiene, and an `export-subst` entry
for `.git_archival.txt`), and AI-agent onboarding
files — a concise `AGENTS.md` (the cross-tool standard) plus a `CLAUDE.md` that
`@AGENTS.md`-imports it so there is a single source of truth (no divergent copies).
`AGENTS.md` intentionally carries **no** commit-attribution/`Co-Authored-By` block.

Also always included (no toggle): a `.git_archival.txt` (setuptools-scm's stable
`node`/`node-date`/`describe-name` `$Format:...$` template). Paired with the
`.gitattributes` `export-subst` entry, `git archive`/GitHub source tarballs (the
install flow documented in `docs/installation.rst`) expand it to the real
tag-derived version, so hatch-vcs recovers the correct version without a `.git`
directory instead of stamping the `[tool.hatch.version] fallback-version` literal.
That fallback is kept at the obvious sentinel `0.0.0` (used only when an archive
has no reachable tag), not a plausible-looking `0.1.0`.

Commitizen (Conventional Commit authoring/linting) is **always included** — it
is no longer gated behind an `include_commitizen` option. release-please still
owns versioning/changelog; Commitizen only authors/lints messages (see
[ADR-004](adr/004-commitizen-as-commit-helper-not-release-tool.md)).

The `.gitignore` is **always** managed by
[cobo](https://github.com/hasansezertasan/cobo) (no toggle, like mise/renovate),
replacing the ad-hoc gibo workflow. `template/.gitignore.jinja` is a cobo-sealed
fenced block (`# >>> cobo:begin >>>` … `# <<< cobo:end sha256=… <<<`) of the
macOS/Windows/Linux/VisualStudioCode/Python boilerplates from `github/gitignore`,
followed by the `### Generated by the author` section that carries the
project-specific overrides (the `include_freezer` spec negation and
`include_c_extensions` generated-C ignore live **below** the fence — the fence
must stay verbatim boilerplate). The block is sealed with cobo's **`--eol lf`**
policy (cobo ≥ 0.4.0) so it survives this template's LF-everywhere normalization
(Copier's Jinja render + git `eol=lf`); a byte-exact seal would make `cobo check`
report `locally modified` forever in generated projects. Two lockfiles ship:
root `cobo.lock` (two fragments — `template/.gitignore.jinja` **and** this repo's
own `.gitignore`, which is cobo-managed too as dogfooding) and
`template/cobo.lock` (`path = .gitignore`, shipped to generated projects). cobo
is delivered to generated projects as a mise tool (`pipx:cobo`, Renovate-tracked)
with a `mise run gitignore-check` task and a weekly, non-blocking
`gitignore-drift.yml` workflow (`cobo update && cobo check --strict` on `schedule` +
`workflow_dispatch` only — not in the `check` gate; network-flaky, same posture
as `docs-linkcheck`). **Regenerate** from the repo root with `cobo update && cobo
sync` (re-renders the fenced region in place, preserving the author section and
the `eol = "lf"` policy); refresh `template/cobo.lock` the same way from a scratch
dir dumping with `--eol lf --out .gitignore --lock`. Do **not** hand-edit inside
the fence (it breaks the sha256). See
[ADR-012](adr/012-cobo-for-gitignore-generation.md).

Git hooks are **always included** (there is no `include_precommit`
option). They are run via [prek](https://prek.j178.dev), a Rust-native
pre-commit replacement, configured by a native `prek.toml` (not a
`.pre-commit-config.yaml`). The dependency group is `prek` and contains only
`prek`; both the tox `prek` env (`tox run -e prek`) and the CI `hooks` job invoke
`prek run --all-files`. One of those hooks is `zizmor`
(`zizmorcore/zizmor-pre-commit`), which statically audits the GitHub Actions
workflows — it is the **blocking** half of the workflow-hardening setup (see the
`zizmor.yml` item under CI/CD Workflows below). Because `prek run --all-files`
runs in the CI `hooks` job, a workflow security regression fails CI with no extra
job. NOTE: verify zizmor changes with the **prek hook** (`prek run zizmor
--all-files`), not a bare `uvx zizmor` — the two can pin different zizmor versions
whose default-persona `dangerous-triggers` behavior differs, and the prek hook is
what actually gates generated projects.

**detect-secrets** is a local, pre-commit-stage secret scanner (`local` `system`
hook via `uv run --locked --group style detect-secrets-hook --baseline
.secrets.baseline`) that catches a secret at `git commit` time, before it ever
enters history. It checks changed files against the committed
`.secrets.baseline` (generated with `detect-secrets scan`), so only *new*
potential secrets are flagged — not the already-triaged false positives already
recorded in the baseline. It layers with, and does not replace, the
history-spanning `gitleaks` scan in `check-security.yml` (see Supply-chain
security below): local prevention at the commit stage vs. CI detection across
full git history. A secret that slips a contributor's local hook is still
caught in CI, since `prek run --all-files` runs this hook there too. Baseline
maintenance (triaging a hit, or regenerating the baseline when the tree
legitimately changes shape) is documented for contributors in
`CONTRIBUTING.md`'s "Secret Scanning" section; Renovate tracks the tool version
(the `style` group pin) but cannot manage the baseline's content.

The tox `style` env (backed by the uv-managed `style` dependency group) is the
canonical lint/type-check runner for the full suite; the prek-run `prek.toml` is
the fast local/CI gate. Its hook `rev` pins are kept current by Renovate (a
`customManagers` regex entry supplied by the shared preset
`.github/renovate.json` extends — `github>hasansezertasan/renovate-config:python`
— since Renovate's built-in pre-commit manager only reads
`.pre-commit-config.yaml`). There is no pre-commit.ci integration and no
`sync-with-uv` hook — Renovate owns every bump, including the tools shared with
the uv `style` group.

The tox `style` env is the *single* lint/type-check orchestrator for a generated
project — there is no Pants or Trunk config to drift against it (both were
removed; see [ADR-003](adr/003-tox-as-canonical-lint-runner.md)).

**editorconfig-checker** enforces `.editorconfig` (the source of truth) on the
axes no other tool owns — indent style/size and charset on config/markup files.
It is delivered via the uv `style` group (PyPI wrapper, command `ec`), invoked
in both the tox `style` env and a prek `local` hook. Unlike typos
(whose PyPI wrapper tracks its Go release tags), the `editorconfig-checker`
PyPI wrapper lags the Go releases, so a separate upstream prek `rev` pin would
drift permanently out of sync with the `style` group — hence the `local` hook
(single version source, like `basedpyright`) rather than an upstream repo hook.
Its `.editorconfig-checker.json` disables the checks other tools already own
(trailing whitespace + final newline → prek builtins; line endings →
`.gitattributes`/ruff; `*.py` line length → ruff) and excludes `.rst`/`.md`/`.py`
whose indentation is semantic/marker-relative (Sphinx, markdownlint, and ruff
are their authorities). Adding `.jsonc`/`.cff` to the 2-space `.editorconfig`
glob was a genuine correctness fix it surfaced (both were defaulting to 4).

**ghalint** enforces GitHub Actions workflow *security policy* (a different axis
from actionlint's *correctness*): least-privilege per-job `permissions`,
`persist-credentials: false` on checkouts, per-job `timeout-minutes`, full-length
action SHA pins, and secret-handling policy. It ships **no** PyPI wrapper and
**no** pre-commit hook, so it cannot join the uv `style` group or be a standard
prek repo hook; it is delivered via **mise** (`[tools]`
`"aqua:suzuki-shunsuke/ghalint"`, aqua backend named explicitly) and invoked as a
prek `local` system hook that invokes it through `mise exec -- ghalint run` so
the mise-managed binary resolves deterministically after `mise install` without
requiring an activated mise shell (shims on PATH) — only `mise` itself need be on
PATH. The CI `hooks` job therefore runs `jdx/mise-action` (SHA-pinned) before
`prek run` so both `mise` and the binary exist. All shipped workflows are hardened to pass ghalint's strict
defaults; the only exception is a **web-only** `.github/ghalint.yaml` that
excludes the `job_secrets` policy for exactly the `docker-publish-preflight` and
`docker-publish` jobs (they must expose `DOCKERHUB_USERNAME` at job-env because
GitHub `if:` conditions cannot read the `secrets` context or step-level env).
The two docs-push jobs (`gh-pages.yml` `deploy`, `release.yml`
`deploy-docs`) set `persist-credentials: false` and publish via
`JamesIves/github-pages-deploy-action` (SHA-pinned), which authenticates from its
`token` input (default `github.token`) without ever writing the token into
`.git/config` — replacing the earlier hand-rolled `git remote set-url` +
`ghp-import` push. `.nojekyll` is emitted by the `sphinx.ext.githubpages`
extension at build time (so `_static/` is served), not by the deploy step.

## Generated Project Structure

Root modules in `src/{{github_repo_name}}/`:

- `__init__.py`, `__main__.py`, `__metadata__.py` - Package setup
- `_version.py` - Auto-generated by hatch-vcs (excluded from coverage)

Subpackages (each with `__init__.py` and `app.py`):

- `core/` - Core infrastructure (always included):
  - `dirs.py` - Project directory locations (`~/.<package>`)
  - `logging_setup.py` - Centralized logging
  - `config.py` - Configuration (uses pydantic-settings if enabled). When
    `include_pydantic_settings` is on, the docs build renders a Configuration
    reference straight from the live `Settings` model: `docs/conf.py` loads the
    `sphinxcontrib.autodoc_pydantic` extension and the conditional
    `docs/configuration.rst` page carries an `autopydantic_settings` directive, so
    the documented fields, types, defaults, constraints, and env-var names never
    drift from the model. The docs dependency group gains `autodoc-pydantic` under
    the `include_pydantic_settings` guard.
- `utils/` - Utility functions (always included)
- `cli/` - the `pkg` Typer root (present when `include_console_root`). With
  `include_cli` it is the full CLI (`version`/`info` commands + component
  subcommands); without `include_cli` it is a minimal launcher (component
  subcommands + a default callback, no `version`/`info`). With `include_cli` and
  `cli_framework == "typer"`, the docs build generates a CLI reference straight
  from the live app: `docs/conf.py` shells `typer {{pkg}}.cli.app utils docs`
  into the gitignored `docs/_generated/cli.md`, and the conditional
  `docs/cli-reference.md` page `{include}`s it (heading-demoted) so the
  documented commands/options — including the enabled component subcommands —
  never drift from `--help`. The `sphinx-click` route is unusable here because
  current Typer vendors its own Click (`typer._click`), so `TyperGroup` fails
  `sphinx-click`'s `isinstance(..., click.Command)` check.
  [`sphinxcontrib-typer`](https://github.com/sphinx-contrib/typer) was also
  evaluated — it works, but the build-time generation keeps the CLI reference
  uniform with the worker/web generators and pulls in no extra extension. The
  `argparse` variant has no generated reference
- `web/` - FastAPI/Litestar with `/version` and `/info` endpoints (conditional).
  The docs build emits the web app's [OpenAPI](https://www.openapis.org/) schema
  straight from the live `{{github_repo_name}}.web.app:app` object into the
  gitignored `docs/_generated/openapi.yaml`, and the conditional
  `docs/web-interface.rst` page `literalinclude`s it — a versioned,
  machine-readable HTTP contract (routes, response schemas, status codes) that
  stays in lockstep with the code. Generation is framework-specific: **Litestar**
  uses its first-party CLI (`litestar ... schema openapi --output`), while
  **FastAPI** has no file exporter, so `docs/conf.py` dumps `app.openapi()` to
  `openapi.{json,yaml}` (JSON via the stdlib, YAML via `pyyaml`, added to the
  docs group under the `include_web`+FastAPI guard).
- `gui/` - Tkinter GUI launcher (conditional)
- `tui/` - Textual TUI (conditional)
- `mcp/` - MCP server with `version` and `info` tools (conditional)
- `worker/` - FastStream message queue worker (conditional). The broker is built
  by a `build_broker(url=None)` factory that registers the subscriber/publisher
  and resolves the connection at call time (not import time), so tests can point
  a fresh, self-contained broker at a throwaway instance (e.g. testcontainers)
  without import-order/caching pitfalls; the module still exposes a default
  `broker = build_broker()` for the entry point. See
  [ADR-008](adr/008-worker-broker-testing-strategy.md). The docs build emits the
  worker's [AsyncAPI](https://www.asyncapi.com/) schema straight from the live
  `app` object (`docs/conf.py` shells `faststream docs gen` into the gitignored
  `docs/_generated/asyncapi.yaml`), and the conditional `docs/worker-interface.rst`
  page `literalinclude`s it — a versioned, machine-readable request/response
  contract that stays in lockstep with the code. The docs dependency group gains
  `faststream[cli]` + `pyyaml` under the `include_worker` guard.
- `scripts/worker_probe.py` (conditional on `include_worker`) - a dev-only
  helper that publishes one `VersionRequest` via `build_broker()` and prints
  the `VersionResponse`, importing `REQUESTS_DESTINATION`/`RESPONSES_DESTINATION`
  from `worker/app.py` rather than re-literalizing them. Lives under
  `scripts/` (outside `src/`) so it ships in neither the sdist nor the wheel
  and stays outside coverage/import-linter's reach. Run via the `worker-probe`
  mise task (`mise run worker-probe`) against a broker started by the
  devcontainer or `docker compose`.

Other conditional files:

- `_c_extension.pyx`, `.pxd`, `.pyi` - Cython extension files
- `profile.py` - Profiling script
- `<pkg>.spec` - PyInstaller spec file (conditional on `include_freezer`)

Test packages mirror source structure in `tests/`:

- `tests/cli/`, `tests/web/`, `tests/gui/`, `tests/tui/`, `tests/mcp/`, `tests/worker/` (each conditional)
- `tests/worker/` holds both the in-memory `Test<Broker>` unit tests (always run)
  and a broker round-trip integration test marked `integration` (excluded from
  the default run). Its `broker_url` fixture reads a single seam: if the broker's
  env var (`REDIS_URL`/`NATS_URL`/`KAFKA_BOOTSTRAP_SERVERS`/`RABBITMQ_URL`) is
  set it connects to that live broker directly, otherwise it starts a
  testcontainer (Docker required for the local path). In CI, **redis** and
  **nats** run against a GitHub Actions `services:` container (the runner starts,
  health-gates, and injects the connection before the job), while **kafka** and
  **rabbitmq** stay on testcontainers — a per-broker CI mechanism derived from
  `worker_broker`, no extra question. See
  [ADR-008](adr/008-worker-broker-testing-strategy.md) (incl. the issue #169
  amendment).

Entry points configured in `pyproject.toml` (console-script wiring — see
**[ADR-019](adr/019-components-as-cli-subcommands.md)**): the
highest-precedence enabled component (**CLI > GUI > TUI > web > MCP > worker**)
is the *primary* and owns the bare `pkg` command, wired to `pkg.__main__:main`
(the single entrypoint standalone builds also target). Every *other* enabled
component is exposed as a **subcommand of the `pkg` Typer root**
(`pkg <name>` — `interactive` for the TUI, else the component name), **not** a
separate `pkg-<name>` console script. The precedence lives in **one** place — the
`primary_component` computed variable in `copier.yml` (empty for a library) —
and every template (`pyproject`, `README`, `docs/usage`, `docs/installation`,
`.vscode/launch.json`, tox) derives the primary and each subcommand from it: a
component `X` is a subcommand exactly when `primary_component != "X"`. Do
**not** re-spell the precedence as inline `include_x or include_y …` conditions.

The `pkg` Typer root lives in the `cli/` package. It exists whenever
`include_console_root` (a hidden `when: false` computed var) is true —
`include_cli or (≥2 of gui/tui/web/mcp/worker enabled)`. When `include_cli` is
off but ≥2 components are enabled, `cli/` is a *minimal launcher* (no
`version`/`info`; bare `pkg` launches the primary via an
`@app.callback(invoke_without_command=True)` default, secondaries are
subcommands). A single-component non-CLI app has **no** root and does **not**
pull in `typer` — bare `pkg` launches that component directly via `__main__`.
`include_console_root` is the single source of truth for the `cli/`
package/test-dir guards, the `typer` core dependency, the import-linter `cli`
layer, and the `__main__.py` branch.

- `project.scripts`: bare `pkg = "pkg.__main__:main"` when the primary is a
  console component **or** when a GUI primary shares a console root with other
  components (so the `pkg <name>` subcommands keep a real terminal on Windows).
  No `pkg-<name>` entries are emitted.
- `project.gui-scripts`: `pkg = "pkg.__main__:main"` **only when GUI is the
  sole runnable component** (windowless launcher, no console window on Windows);
  there is never a bare-name collision across the two tables. A non-primary GUI
  is reached via the `pkg gui` subcommand, not a `pkg-gui` gui-script.

The CLI framework choice (Typer) is recorded in
[ADR-020](adr/020-cli-framework-choice.md).

## Devcontainer Structure

The `.devcontainer/docker-compose.yml.jinja` consolidates all services:

- `devcontainer` - Main development container (always included)
  - Uses `ghcr.io/astral-sh/uv:python3.14-bookworm-slim` image directly (no Dockerfile)
  - `devcontainer.json.jinja` features: `git:1` and `mise:1` (both always)
  - When `include_vpn` is true, devcontainer sets `network_mode: "service:vpn"` and depends on the `vpn` service so all traffic routes through the VPN tunnel
  - `depends_on` waits on `condition: service_healthy` for services that define a healthcheck (postgres, redis, kafka, rabbitmq) and `service_started` for the rest (nats, vpn)
- Database services (conditional):
  - `postgres` - PostgreSQL with healthcheck (conditional on `include_postgres`)
  - `redis` - Redis/Valkey with healthcheck (conditional on `include_redis` or a `redis` worker broker; image set by `redis_backend`)
  - `pgadmin` / `adminer` - DB UIs behind the `tools` compose profile (conditional on `include_pgadmin` / `include_adminer`)
- Message broker services (conditional on `include_worker` + `worker_broker`):
  - `kafka` - Bitnami Kafka (KRaft mode), healthcheck via `kafka-topics.sh`
  - `nats` - NATS with JetStream (no healthcheck; minimal image)
  - `rabbitmq` - RabbitMQ with management UI, healthcheck via `rabbitmq-diagnostics`
  - `redis` - Redis (shared with the database `redis` service above)
- `cloudbeaver` - DBeaver CloudBeaver (conditional on `include_dbeaver`)
- `vpn` - OpenVPN client sidecar (conditional on `include_vpn`)
  - Uses `dperson/openvpn-client` with `NET_ADMIN` cap and `/dev/net/tun` device
  - Mounts `./vpn:/vpn` — drop `.ovpn` config + optional `vpn.auth` credentials there
  - Conditional `vpn/` subdir is rendered with a README and `.gitignore` (whitelists README only)
  - Devcontainer shares the vpn service's network namespace via `network_mode`; port forwards must be declared on the `vpn` service rather than `devcontainer`

## Build System

- **Builder**: `hatchling` with `hatch-vcs` plugin
- **Versioning**: Git tags via hatch-vcs; archive/tarball installs recover the
  tag via `.git_archival.txt` (`export-subst`), and the `fallback-version = "0.0.0"`
  sentinel is used only when neither live git metadata nor an expanded
  `.git_archival.txt` is available
- **Build Command**: `uv build`

## CI/CD Workflows

1. **CI** (`ci.yml.jinja`): Matrix tests on Windows/Ubuntu/macOS, Python 3.10-3.14
   - **Cross-matrix coverage** ([ADR-026](adr/026-combined-cross-matrix-coverage-and-tokenless-html-host.md)):
     each matrix cell `coverage combine`s its per-interpreter data, keeps a
     non-gating `coverage report --fail-under=0` for fast per-OS feedback, and
     uploads its raw `.coverage.<os>` as a per-OS artifact
     (`include-hidden-files: true`). A dedicated `coverage-combine` job
     (`needs: ci`, in the `check` gate) downloads every cell, merges once, and is
     the **single** place the `fail_under = 99` gate runs — over the **union** of
     every OS × interpreter cell, not each cell independently. `relative_files =
     true` (pyproject `[tool.coverage.run]`) lets cross-runner paths merge,
     complementing the `[tool.coverage.paths]` remap. The combined `coverage.xml`
     is the single Codecov upload and, when `include_sonarcloud`, the `coverage-xml`
     artifact the `sonar` job consumes (`sonar` now `needs: coverage-combine`).
   - Codecov upload (from `coverage-combine`) runs whenever the repo is public
     **or** a `CODECOV_TOKEN` secret is set — two job-level presence flags gate it
     because the `secrets` context is unavailable in `if:`: `CODECOV_TOKEN_SET`
     (`secrets.CODECOV_TOKEN != ''`) and `REPO_IS_PUBLIC`
     (`!github.event.repository.private`). On a **public** repo the codecov-action
     uploads tokenless, so owner pushes and fork PRs both report coverage with no
     secret; the token is only needed for a **private** repo (or to dodge
     tokenless rate-limits). Only a private repo with no token hits the
     `::notice::` visible skip instead of failing the run — coverage reporting is
     best-effort (the upload step's `fail_ci_if_error` defaults to false), not
     load-bearing for a green build. Setup is documented in the generated
     project's `docs/maintaining/setup.rst` "Repository setup" guide.
   - When `include_smokeshow` is set, `coverage-combine` additionally publishes the
     combined `htmlcov/` to a tokenless ephemeral public URL via
     `smokeshow upload htmlcov` (public repos only) — an account-free browsable
     coverage report alongside Codecov. See ADR-026.
   - When `include_launcher`/`include_freezer`/`include_compiler` are set, adds
     matching `build-{launcher,freezer,compiler}-check` jobs (per-OS, `fail-fast:
     false`) that build the standalone executable on every PR/push — a build-only
     packaging guard so a dep/Python bump that breaks bundling fails against the
     offending diff instead of silently at release time (the test suite never
     exercises the built binary). Each verifies the binary was produced,
     smoke-runs it with `--help` when `include_cli` is set, and uploads a 7-day
     preview artifact. They closely follow the `release.yml` build jobs
     (same setup + build commands), skipping the release-only rename/publish
     steps, and they gate the `check` aggregation job. See
     [ADR-007](adr/007-standalone-executable-toggles.md).
   - When `include_worker` is set, adds a single `worker-integration` job —
     **Ubuntu-only** (Docker is reliably present on GitHub's Ubuntu runners but
     not macOS/Windows) — that runs `tox run -e integration` (an on-demand tox
     env invoking `pytest -m integration`) against a real `worker_broker` started
     via testcontainers. The default OS matrix stays broker-free and fast (the
     `integration` marker is deselected by default via the pytest `addopts`); this
     job is the only thing exercising the real driver, and it gates the `check`
     aggregation job. See [ADR-008](adr/008-worker-broker-testing-strategy.md).
2. **Release + CD** (`release.yml.jinja`): one unified workflow (there is
   no separate `cd.yml`). Standardized on release-please — no longer configurable
   (see [ADR-002](adr/002-release-please-for-release-automation.md)). Jobs:
   - `release-please`: opens/maintains a release PR from Conventional Commits on
     push to `main`; on merge, tags the commit and creates a **draft** GitHub
     Release (`draft: true` in `.github/release-please-config.json`). Exposes
     `release_created`, `tag_name`, `version` as outputs.
   - All later jobs gate on `needs.release-please.outputs.release_created == 'true'`.
   - `build`: builds with uv. When `include_c_extensions` is set, runs as a
     per-platform `fail-fast: false` matrix (Ubuntu/Windows/macOS) producing the
     multi-platform Cython wheels + sdist; `pypi-publish` uploads them all.
   - `pypi-publish`: trusted publishing (`id-token: write`, environment `publish`).
   - `build-launcher` (when `include_launcher`, PyCrucible) / `build-freezer`
     (when `include_freezer`, PyInstaller) / `build-compiler` (when
     `include_compiler`, Nuitka) / `docker-publish` (when
     `include_web`): conditional matrix jobs. The three executable jobs are
     independent `fail-fast: false` matrices producing per-platform artifacts
     named `<repo>-executable-{launcher,freezer,compiler}-<os>`, all caught by
     `attach-github-release`'s `<repo>-executable-*` download pattern (see
     [ADR-007](adr/007-standalone-executable-toggles.md)). Docker tags feed
     `needs.release-please.outputs.tag_name` into the metadata-action `value=`
     because a push-triggered run has no tag ref.
   - `attach-github-release`: uploads artifacts to the still-draft release.
   - `finalize-release`: un-drafts the release and reconciles the phantom
     next-release PR (close + re-dispatch — bounded to one re-run).
   - `deploy-docs` (`needs: finalize-release`): builds the Sphinx docs and
     publishes them via `JamesIves/github-pages-deploy-action`. Lives in
     this workflow rather than reacting to `release: published` because an event
     fired by `finalize-release`'s `GITHUB_TOKEN` cannot trigger another workflow
     (the same loop-prevention rule that forces the `workflow_dispatch`
     re-dispatch above). `gh-pages.yml` is kept only for manual redeploys.
     Docs are built with Sphinx + the Shibuya theme (autodoc API reference),
     not MkDocs (see [ADR-006](adr/006-sphinx-shibuya-for-documentation.md)).
     The `deploy-docs` publish (and the manual `gh-pages.yml`) set
     `clean-exclude: pr-preview/**` so a release never wipes the live PR previews
     `docs-preview.yml` maintains under that path (see ADR-010 below).
   - `notify-released-issues` (`needs: finalize-release`): a single
     `actions/github-script` step that maps the release's commit range
     (previous published tag → this tag) to the PRs that carried it, resolves each
     PR's `closingIssuesReferences`, and comments the release link on those
     issues. Inline (no committed script), best-effort. See
     [ADR-010](adr/010-pr-docs-previews-and-released-issue-notifications.md).
   - Versions come from git tags via hatch-vcs, so release-please never edits a
     static version literal and `uv.lock` cannot desync.
3. **PR title linting** (`check-pr-title.yml`): validates the **PR title** (not
   individual commits) against Conventional Commits via
   `amannn/action-semantic-pull-request`.
4. **Linked-issue check** (`check-linked-issues.yml`): fails a PR that has no
   linked issue (the GitHub *Development* relationship, created by a `Closes #N`
   keyword in the PR body) via `nearform-actions/github-action-check-linked-issues`.
   It checks the real `closingIssuesReferences` relationship, not just body text;
   apply the `no-issue` label to bypass the check. Keep it as a required status
   check alongside `check-pr-title`.
5. **PR task-list completion check** (`task-completed-check.yml`): on
   `pull_request_target` (`opened`/`edited`), runs
   `kentaro-m/task-completed-checker-action` to post a check run that fails while
   any task-list checkbox in the PR description is unticked. Uses
   `pull_request_target` (least-privilege `checks: write` + `pull-requests: read`)
   so the check also runs on fork PRs; wrap throwaway lists in
   `<!-- ignore-task-list-start -->` / `<!-- ignore-task-list-end -->` to skip them.
6. **Branch-name linting** (`check-branch-name.yml`): validates the PR's **head
   branch name** (`github.head_ref`) against the
   [Conventional Branch](https://conventionalbranch.org/) format
   (`<type>/<description>`). Allowed prefixes are exactly the spec's set —
   `feature`/`feat`, `bugfix`/`fix`, `hotfix`, `release`, `chore`, plus the
   AI-agent prefixes `ai`/`copilot`/`cursor`/`claude`/`codex` — **not** the
   broader Conventional Commits type set (`docs`, `style`, `refactor`, etc. are
   commit types, not branch types). It is a dependency-free inline shell regex (no marketplace action — the
   maintained options were either abandoned or on a deprecated Node runtime), run
   under `pull_request_target` with `pull-requests: write` so it can post a sticky
   failure comment on fork PRs, mirroring `check-pr-title.yml`. The `renovate/*`
   and `release-please--*` automation branches are whitelisted so bot PRs are
   never blocked. Branch names never reach `main` (squash-merge uses the PR
   title), so this is repo hygiene — not load-bearing for release-please. Keep it
   as a required status check (context: **Validate branch name**) alongside
   `check-pr-title`, `check-linked-issues`, and **Task Completed Checker**
   (`task-completed-check.yml`).
7. **Supply-chain security** (always included, static workflows):
   - `codeql.yml`: CodeQL analysis on push/PR to `main` + weekly schedule.
   - `scorecard.yml` (`ossf/scorecard-action`): OpenSSF Scorecard on
     `branch_protection_rule`/push/weekly schedule; `publish_results: true` and
     `id-token: write` so the public Scorecard badge (added to the generated
     README) resolves, uploading SARIF to code-scanning. Public repos only.
   - `dependency-review.yml` (`actions/dependency-review-action`): on `pull_request`,
     **fails on high+ severity** vulnerabilities and comments a summary on failure.
   - `check-security.yml.jinja`: an active scanning pass on PR/push to `main` +
     weekly cron, complementing the three above (which are SAST / repo-posture /
     PR-diff). Jobs:
     - `gitleaks` (`gitleaks/gitleaks-action`, always): secret scan over full git
       history (`fetch-depth: 0`) — catches secrets CodeQL does not and reaches
       past commits that GitHub's push protection never guarded. Free for
       personal accounts/public repos; an org must add a `GITLEAKS_LICENSE`
       secret (noted inline in the workflow).
     - `pip-audit` (always): `uv export`s the locked shipped deps
       (`--all-extras --no-dev --no-emit-project --no-hashes`) and audits them
       with `uvx pip-audit`. Component and settings deps are core
       `dependencies` (each console script imports its component
       unconditionally), so a plain export already covers the whole shipped
       tree; `--all-extras` is retained as a harmless safeguard should a future
       extra reintroduce shipped deps (and applies equally to the release `sbom`
       job's export — though that job omits `--no-hashes`, since the SBOM keeps
       per-pin integrity hashes; only pip-audit drops them, as its resolver would
       otherwise demand a hash for every transitive pin).
       Unlike `dependency-review` (PR-diff only, GitHub Advisory
       DB), this re-audits the *entire* resolved tree against the PyPI Advisory
       DB on the weekly cron, so a CVE disclosed *after* a dependency merged is
       caught while it is still pinned.
     - `trivy-image` (**`include_web` only**): builds the generated `Dockerfile`
       and scans the image with `aquasecurity/trivy-action`
       (`severity CRITICAL,HIGH`, `ignore-unfixed: true`, `exit-code: 1`). Gated
       on `include_web` because that is the only configuration that produces a
       Dockerfile; the filesystem-scan overlap with `pip-audit` is deliberately
       avoided (image/OS-layer scanning is the genuine gap).
   These SHA-pin actions like every other workflow (Renovate
   `helpers:pinGitHubActionDigests` keeps them current). This is a standalone
   workflow (like `codeql`/`scorecard`), *not* wired into the `ci.yml` `check`
   aggregation gate. A CycloneDX **SBOM** (`<repo>-sbom.cdx.json`) is generated
   from the locked runtime deps by a `sbom` job in `release.yml` and
   attached to each GitHub Release (via `attach-github-release`), not kept as a
   throwaway CI artifact.
8. **Workflow hardening + zizmor** (always included). Every generated workflow
   follows a strict [zizmor](https://docs.zizmor.sh/) posture, enforced two ways:
   - **Blocking gate:** the `zizmor` prek hook (see the prek section above) runs
     in the CI `hooks` job and locally; it hard-fails on any finding.
   - **Dashboard:** `zizmor.yml` (static, `zizmorcore/zizmor-action`, SHA-pinned)
     uploads SARIF to the Security tab on push/PR to `main`. Non-blocking by
     design (advanced-security mode never fails on findings); least-privilege
     (`permissions: {}` top-level, `security-events: write` on the job) and itself
     passes the audit it runs. Public repos get code scanning free; private repos
     need GitHub Advanced Security, and the upload simply no-ops without it.

   The hardening conventions every workflow (new or edited) must keep so the gate
   stays green are **agent instructions**, so they live inline in `CLAUDE.md`'s
   **Workflow hardening rules** (persist-credentials, top-level `permissions: {}`,
   no untrusted `${{ }}` in `run:`, and the justified
   `# zizmor: ignore[dangerous-triggers]` markers on the intentional
   `pull_request_target` workflows). Do not remove those markers.

   This repo's OWN workflows (`.github/workflows/`) get the same treatment plus a
   `zizmor.yml` dashboard; this repo's `prek.toml` scopes the hook with
   `files = '\.github/workflows/.*\.ya?ml$'` so it audits the template's static
   `.yml` workflows too but skips the un-renderable `*.jinja` templates (whose
   rendered form is audited by the generated project's own hook, and end-to-end by
   rendering a project and running `prek run zizmor --all-files` in it).
9. **PR documentation previews** (`docs-preview.yml`, rendered only when
   `include_docs`, static workflow). On `pull_request`
   (`opened`/`synchronize`/`reopened`/`closed`) it builds the Sphinx docs and hands the lifecycle to `rossjrw/pr-preview-action`
   (`action: auto`): deploy to `pr-preview/pr-<N>/` on `gh-pages` on
   open/update, remove on close, with a sticky preview-URL PR comment throughout.
   Guarded by `if: github.event.pull_request.head.repo.full_name ==
   github.repository` to **same-repo PRs only** — a fork PR's `GITHUB_TOKEN` is
   read-only and cannot deploy, so forks are skipped cleanly (fork support awaits
   the action's v2). Plain `pull_request` (not `pull_request_target`) means no
   `dangerous-triggers` ignore is needed. Not wired into the `check` gate
   (best-effort). Previews live under `pr-preview/**`, disjoint from the root docs
   deploy, and the two `JamesIves` publishes carry `clean-exclude: pr-preview/**`
   so a release never wipes them. See
   [ADR-010](adr/010-pr-docs-previews-and-released-issue-notifications.md).
10. **Docs link check** (`docs-linkcheck.yml`, rendered only when `include_docs`, static workflow).
   Runs Sphinx's `linkcheck` builder on a **weekly cron** + `workflow_dispatch`
   to catch dead links/moved anchors in the docs. Deliberately **not** on
   `pull_request` and **not** in the `check` gate — link checking hits the
   network and is flaky, so it is non-blocking (same posture as
   `check-security.yml`'s cron). A matching on-demand `docs-linkcheck` tox env
   lets maintainers run it locally. Two other docs-lint additions ship alongside
   it: `sphinx-lint` (a `local` prek hook backed by the `style` group + a tox
   `style` command, linting the `.rst` sources) and the `check-case-conflict`
   prek builtin (cross-platform filename-collision guard). See
   [ADR-011](adr/011-docs-linting-and-cross-platform-filename-safety.md).

   The **HTML build itself carries a warning-allowlist gate**: the `docs-build`
   tox env builds with `sphinx-build -w docs/_build/warnings.txt` (write the
   warning stream to a file rather than `-W` failing on the first one), then runs
   `docs/check_warnings.py`, which normalizes the emitted warnings (path prefixes
   stripped back to `docs/`) and diffs them against the committed
   `docs/expected_warnings.txt` allowlist. It fails on **both** unexpected new
   warnings *and* expected ones that stopped being emitted, so the list can't rot.
   The allowlist ships effectively empty (comment header only — zero tolerated
   warnings); a genuinely-unavoidable upstream warning is added as an explicit,
   reviewable line in the same PR rather than suppressed wholesale. This runs in
   the local loop (`tox run -e docs-build`) and in both CI docs builds
   (`docs-preview.yml`, `release.yml`'s `deploy-docs`), complementing
   `sphinx-lint`'s `.rst`-source checks with build-time semantic warnings (missing
   xrefs, autodoc import failures).

Downstream template updates are **not** a shipped workflow — they are handled by
**Renovate's [`copier` manager](https://docs.renovatebot.com/modules/manager/copier/)**
(ADR-015). Renovate (already the canonical updater, and a documented one-time
setup) detects the generated project's `.copier-answers.yml`, watches the template
repo (`_src_path`) via the **`git-tags`** datasource, and when a newer tag exists
runs the real `copier update` and opens a PR with the re-rendered diff. It is on
by default (the shared preset sets no `enabledManagers`), so generated projects
get it via the `.copier-answers.yml` they already ship — nothing added to the
template's `renovate.json`. Renovate's **App token can push `.github/workflows/*`**
(the repo `GITHUB_TOKEN` cannot), so no per-repo update PAT is needed. Two things
make this work and are load-bearing — do not undo them without re-reading ADR-015:
(1) the template's own release-please (below) must keep cutting **tags**, because
the copier manager is tag-based, not HEAD-based; (2) `copier.yml` must define **no
`_tasks`** — any task forces `copier ... --trust`, which the **hosted Mend Renovate
App disables** (`allowScripts` is self-hosted-only), so a task-bearing template
breaks the manager. The former `_tasks: git init` was removed for this reason (the
scaffold instructions now tell the user to `git init`). Caveat: Renovate does not
fail its artifacts check on `copier update` merge conflicts
([renovate#31600](https://github.com/renovatebot/renovate/issues/31600)), so a
copier PR can look mergeable while carrying `<<<<<<<` markers — the generated
project's `docs/maintaining/setup.rst` "Template updates" note says to review
for them.

**Shipped pins under `template/**` are frozen from this repo's Renovate** (a
disabled `packageRules` entry in `.github/renovate.json` matching
`template/**`). This is load-bearing for keeping `copier update` conflict-free —
do **not** re-enable it. The shipped literals — the confirmed conflict source is
the **plain** `template/.github/workflows/*.yml` action SHAs (the `.jinja`-suffixed
files are not matched by Renovate's stock managers), plus any `mise.toml.jinja`
tool versions, `prek.toml.jinja` `rev` pins, or deps a `customManager` reaches —
are *seed values only*: every generated project
ships its own Renovate config and owns those bumps thereafter. If this repo also
bumped them, `copier update`'s 3-way merge would see both the new template render
(*theirs*) and the downstream file (*ours*) having moved the same literal to
different values → a conflict on nearly every release. Freezing keeps
*theirs == base*, so the downstream's Renovate value always wins the merge
cleanly. This repo's OWN root workflows/`prek.toml`/`mise.toml` stay
Renovate-managed (template CI stays current); newly-generated projects start with
slightly-stale-but-valid pins that their own Renovate catches up on the first
run. To ship less-stale seeds, refresh the `template/**` pins deliberately (by
hand or a one-off scoped run) right before cutting a template release — accepting
that a deliberate bump reintroduces conflicts only for projects that had not yet
caught up. See
[ADR-020](adr/020-freeze-shipped-template-pins-from-renovate.md).

## Template self-versioning (this repo, ADR-015)

The template repository **versions itself** with release-please so its changes
produce semver git tags (`v1.0.0`, …). These tags are the **datasource Renovate's
copier manager consumes** in generated projects (see the ADR-015 note above) — so
tagging is load-bearing, not cosmetic. This is distinct from the
`template/`-shipped release-please that versions *generated* projects. Root-level
files: `.github/release-please-config.json` (`release-type: "simple"` — the repo
has no source version file, so it maintains only the manifest + `CHANGELOG.md` +
tag; `draft: false`, no release artifacts to attach),
`.github/release-please-manifest.json` (seeded `{ ".": "0.0.0" }`; release-please
defaults the *first* release to **v1.0.0** regardless of `bump-minor-pre-major` —
add a `Release-As`/`release-as` override for the first PR if a `0.x` start is
wanted), and `.github/workflows/release.yml` (a single `release-please` job on
push to `main`, no build/publish jobs). Do **not** add a build/publish step — the
template is not a distributable package.

**One-time repo setup** (same contract release-please needs everywhere): this
repo must **squash-merge with the commit message set to the PR title** (already
its practice — see the `feat: … (#NNN)` history) so the `check-pr-title`-validated
title is what release-please parses on `main`, and **Settings → Actions → General
→ Workflow permissions → Allow GitHub Actions to create and approve pull
requests** must be enabled so `release.yml` can open its release PR (already
required by the existing PR-opening automation such as `gitignore-drift.yml`).
Enable via `gh repo edit hasansezertasan/copier-pyproject --enable-squash-merge
--enable-merge-commit=false --enable-rebase-merge=false` and
`gh api -X PUT repos/hasansezertasan/copier-pyproject/actions/permissions/workflow
-f default_workflow_permissions=write -F can_approve_pull_request_reviews=true`.
This repo carries a repo-local `.claude/skills/repo-setup/` skill that automates
the walk.

## Required Merge Strategy (release-please depends on it)

release-please derives version bumps and changelog sections solely from the
Conventional Commit messages that land on `main`. This template validates the
**PR title** but not in-PR commits, so generated repos **must use "Squash and
merge" with the squash commit message set to the PR title** — that is the only
strategy under which the lint-validated title becomes the commit on `main`.
Merge-commit and rebase-merge promote unvalidated branch commits and will cause
release-please to miss releases or bump them incorrectly.

Configure each generated repo (Settings → General → Pull Requests):

- Allow squash merging (ideally disable merge commits and rebase merging).
- Set the squash "Default commit message" to **"Pull request title"**.
- Enable **Automatically delete head branches**.
- Keep `check-pr-title` as a required status check.

release-please also needs **Settings → Actions → General → Workflow permissions
→ Allow GitHub Actions to create and approve pull requests** enabled, or it
cannot open/maintain the release PR. Generated repos should additionally enable
**release immutability** (Settings → General). The generated project's
`docs/maintaining/setup.rst` documents all of these as a one-time "Repository
setup" guide (published under **Maintainer guide** in the docs site, and
pointed to from the slimmed contributor-facing `CONTRIBUTING.md`), including
ready-to-run `gh repo edit` / `gh api` commands and the PyPI trusted-publishing
registration, each step tagged `[AGENT]` (scriptable) or `[HUMAN]`
(browser-only) so it doubles as a setup-skill manifest — keep that guide in
sync when these requirements change. See
[ADR-022](adr/022-maintainer-setup-as-single-doc-home.md).

Generated projects also ship a **`repo-setup` skill**
(`template/.claude/skills/repo-setup/SKILL.md` → `.claude/skills/repo-setup/` in
the generated project) — a resume-driver that reads `docs/maintaining/setup.rst`,
runs each step's idempotent **`[CHECK]`** block (exit 0 = already done), auto-runs
red `[AGENT]` steps, and hands off `[HUMAN]` steps — classifying each step as
required / deferred (Pages, pre-first-release) / optional so the walk never
deadlocks and reports every gap at once. The
`[CHECK]` tag is single-sourced in the setup doc alongside `[AGENT]`/`[HUMAN]`
(no separate `steps.yaml`) — **every new setup step must carry one** (a real
idempotent check, a secret-presence check, or an explicit `No scriptable check`
marker). This repo carries a symmetric repo-local `.claude/skills/repo-setup/`
for its own bootstrap (squash-merge policy + the deliberately-divergent
`default_workflow_permissions=write`, not the generated projects' `read`). See
[ADR-023](adr/023-repo-setup-skill.md).

Bump rules follow `.github/release-please-config.json`: `feat` → minor, `fix`/`perf` →
patch, `feat!`/`BREAKING CHANGE` → major — but `bump-minor-pre-major: true`
keeps breaking changes at a minor bump while pre-1.0.

## PyPI Trusted Publishing Setup

For generated projects to publish to PyPI:

1. Go to <https://pypi.org/manage/account/publishing/>
2. Add pending publisher with:
   - PyPI Project Name: `<package-name>`
   - Owner: `<github-username>`
   - Repository: `<repo-name>`
   - Workflow: `release.yml` (the publish step is inline in this workflow,
     so this is the filename PyPI's OIDC check matches — not a reusable `cd.yml`)
   - Environment: `publish`
