# Design: `include_megalinter` — opt-in lean MegaLinter complement

- **Date:** 2026-07-31
- **Status:** Implemented
- **Repo:** `copier-pyproject` template

> **Amendment (2026-08-01):** Two changes during review supersede the body below;
> **[ADR-013](../../../adr/013-megalinter-opt-in-lean-complement.md) is
> authoritative.**
>
> 1. **Paths filter dropped** (affects §3, §File changes, §Risks). Because
>    `COPYPASTE_JSCPD` scans source, the filter fired on nearly every PR anyway
>    (`**.py`), making it a half-optimization with a confusing "why didn't it
>    run?" surface. The workflow now runs on every push/PR to the default branch;
>    the `cupcake` flavor remains the effective per-run cost lever.
> 2. **Non-blocking made real at the exit-code level.** The body's "non-blocking"
>    claim rested only on `check`-gate exclusion + `GITHUB_STATUS_REPORTER: false`,
>    which do not stop a MegaLinter non-zero exit from posting a red check. The
>    config now sets `DISABLE_ERRORS: true`, so findings are report-only
>    (delivered via the SARIF → Security-tab upload), never failing the job.

## Problem

MegaLinter CI is slow. A real run
([hwid#90](https://github.com/hasansezertasan/hwid/actions/runs/30634574244/job/91168813067))
spent **165 s pulling the 8 GB `oxsecurity/megalinter:v9.6.0` image and only 16 s
actually linting** — 88 % of wall-clock is the image pull, not the work.

Two structural issues surfaced while diagnosing it:

1. **MegaLinter is always-on and undocumented.** The template ships
   `template/.github/workflows/mega-linter.yml` and `template/.mega-linter.yml`
   unconditionally, yet MegaLinter appears nowhere in `CLAUDE.md`, `README.md`, or
   `docs/`. It violates the template's "green on first push, self-contained,
   zero external accounts" default by forcing a heavy CI layer on every generated
   project.
2. **It is ~redundant with prek.** Its 6 enabled linters
   (`ACTION_ACTIONLINT`, `BASH_SHELLCHECK`, `EDITORCONFIG_EDITORCONFIG_CHECKER`,
   `MARKDOWN_MARKDOWNLINT`, `SPELL_CSPELL`, `YAML_YAMLLINT`) overlap almost
   entirely with `prek.toml.jinja`, which already runs actionlint, yamllint,
   markdownlint-cli2, editorconfig-checker, typos, and zizmor. Only
   `BASH_SHELLCHECK` is unique; `SPELL_CSPELL` duplicates `typos`.

## Goals

- Make MegaLinter **opt-in** (`include_megalinter`, `default: false`), restoring
  the self-contained default and letting adopters (e.g. hwid) pick it up via
  `copier update`.
- When enabled, make it a **lean complement** to prek — enable only linters prek
  and tox genuinely do *not* cover, plus MegaLinter's SARIF-to-Security-tab
  aggregation — never a redundant re-run.
- **Fix the slowness** so opt-in users get a fast layer.
- **Document** the decision (a new ADR) and the toggle (CLAUDE.md, README).

## Non-goals

- Removing MegaLinter entirely (considered; rejected in favor of a lean opt-in).
- Reworking prek, tox, or `check-security.yml`.
- Cleaning up the orphaned `.github/linters/.codespellrc` (referenced by nothing;
  flagged below as a separate follow-up, out of scope here).

## Decision

### The toggle

Add a `copier.yml` boolean:

```yaml
include_megalinter:
  type: bool
  default: false
  help: >-
    Add MegaLinter as an optional extra CI quality layer (opt-in). It runs only
    linters that prek/tox do not already cover (shellcheck, hadolint, jsonlint,
    jscpd clone-detection) and uploads SARIF findings to the Security tab. Off by
    default to keep the self-contained, fast default (tox/prek remain canonical).
```

### Enabled linters (the lean set)

Only genuine gaps — decided from an inventory of a generated project's file types
against what prek/tox already lint:

| Linter | Gap it fills | Condition |
| ------ | ------------ | --------- |
| `BASH_SHELLCHECK` | No `.sh` files ship today, but latent for scripts users add; actionlint only shellchecks workflow `run:` blocks, not standalone scripts | always (when toggle on); keeps `.shellcheckrc` |
| `DOCKERFILE_HADOLINT` | Nothing lints the generated Dockerfile | **only when `include_web`** (the sole config with a Dockerfile) — jinja-conditional inside `ENABLE_LINTERS` |
| `JSON_JSONLINT` | 8 JSON/JSONC config files are only indent-checked today | always (when toggle on) |
| `COPYPASTE_JSCPD` | Clone/copy-paste detection — a capability the template does not have at all | always (when toggle on) |

**Explicitly not enabled** (a comment in `.mega-linter.yml` states why):

- Python linters — duplicate ruff + five type-checkers + vulture (tox `style`).
- `ACTION_ACTIONLINT`, `YAML_YAMLLINT`, `MARKDOWN_MARKDOWNLINT`,
  `EDITORCONFIG_EDITORCONFIG_CHECKER` — duplicate prek.
- `SPELL_CSPELL` — duplicates `typos` (prek). **cspell is dropped**; `typos`
  stays the single spell-checker (no two-dictionary drift).
- Repository security linters (secretlint/trivy/kics/…) — duplicate
  `check-security.yml` (gitleaks, pip-audit, trivy-image, CodeQL, scorecard,
  dependency-review).

### Speed

- **cupcake flavor.** Change the action reference to
  `oxsecurity/megalinter/flavors/cupcake@<sha>` (SHA-pinned, Renovate-tracked).
  Verified cupcake contains all four enabled linters. Roughly halves the image
  pull versus the full flavor. This is the largest, unconditional win.
- **Paths filter.** Trigger the workflow only when files the enabled linters
  target change — the union: `**.py` (jscpd), `**/Dockerfile*` (hadolint),
  `**.sh` (shellcheck), `**.json` / `**.jsonc` (jsonlint + jscpd), plus the
  workflow and its config files. This skips docs-only / yaml-only / toml-only PRs.
  Because `COPYPASTE_JSCPD` scans source, the filter necessarily includes `**.py`,
  so most substantive PRs still trigger it — the paths filter's savings are on
  documentation/config-only PRs; the cupcake flavor is what cuts the per-run cost.
- Keep `VALIDATE_ALL_CODEBASE: ${{ github.event_name != 'pull_request' }}`
  (already present) and `concurrency … cancel-in-progress: true`.
- Stays **non-blocking**: not in the `ci.yml` `check` aggregation gate,
  `GITHUB_STATUS_REPORTER: false`. Paths-filtering therefore cannot wedge a
  required status check (a skipped run reports no required context).

### File changes

Gate / rename (conditional-filename convention `{% if … %}name{% endif %}.jinja`):

- `template/.github/workflows/mega-linter.yml`
  → `template/.github/workflows/{% if include_megalinter %}mega-linter.yml{% endif %}.jinja`
  (lean config: cupcake flavor + paths filter).
- `template/.mega-linter.yml`
  → `template/{% if include_megalinter %}.mega-linter.yml{% endif %}.jinja`
  (trimmed `ENABLE_LINTERS`; hadolint entry jinja-gated on `include_web`).
- `template/.github/linters/.shellcheckrc`
  → `template/.github/linters/{% if include_megalinter %}.shellcheckrc{% endif %}`
  (shellcheck config — MegaLinter-only).

Remove:

- `template/.github/linters/.cspell.yml.jinja` — cspell dropped; referenced only
  by the old `.mega-linter.yml`, nothing else.

Keep always-on (shared with prek — must **not** be gated):

- `.github/linters/.markdownlint.yml` — `markdownlint-cli2.yaml` does
  `extends: ./.markdownlint.yml`, so prek depends on it.
- `.github/actionlint.yaml` — prek's actionlint auto-discovers it.
- `.github/yamllint.yaml` — prek's yamllint reads it (`-c`).
- `.github/linters/.markdownlint-cli2.yaml`, root `.markdownlint-cli2.jsonc` — prek.
- `.github/linters/.codeql.yml` — CodeQL config.

### Docs & metadata

- **New ADR-013** — "MegaLinter as an opt-in lean complement." Distinct from
  ADR-009 (optional *external* SaaS integrations): MegaLinter is a self-contained
  Docker action needing no external account, so the ADR-009 "requires external
  provisioning" framing does not fit. Rationale to capture: de-duplicate prek,
  preserve the fast self-contained default, gap-fill + SARIF, speed via cupcake +
  paths filter.
- **CLAUDE.md** — add `include_megalinter` to the "Optional components" list
  (MegaLinter is currently undocumented there) and note it in the CI/CD workflows
  section as a non-blocking, opt-in, paths-filtered layer.
- **README.md.jinja** — add the toggle to the optional-components / feature table.
- **`.example-input.yml`** — add `include_megalinter: false` (consistent with it
  disabling every optional component; its rendered form is only validated when
  generated explicitly).
- **No `pyproject.toml` change** — MegaLinter is a CI action, not a Python dep, so
  no optional-dependency, `all` extra, entry point, or keyword changes.

## Testing

Per the CLAUDE.md testing convention (a component's rendered form is only
validated when generated explicitly, since `.example-input.yml` disables it):

1. Render with `--data include_megalinter=true` and confirm the workflow +
   `.mega-linter.yml` + `.shellcheckrc` render, `.cspell.yml` does not, and the
   shared prek configs remain.
2. Render again with `--data include_megalinter=true --data include_web=true` to
   exercise the `DOCKERFILE_HADOLINT` jinja conditional.
3. Render with the toggle **off** (default / `.example-input.yml`) and confirm no
   `mega-linter.yml`, no `.mega-linter.yml`, no `.shellcheckrc`, and that prek's
   shared configs still render.
4. `cd` into a rendered project and run `uv run --locked tox run -e style`;
   confirm `zizmor` (via `prek run zizmor --all-files`) and ghalint stay green on
   the rendered `mega-linter.yml` (least-privilege `permissions`,
   `persist-credentials: false`, `timeout-minutes`, SHA-pinned `uses:`).

## Risks / trade-offs

- **jscpd broadens the paths filter to `**.py`**, so MegaLinter still runs on most
  code PRs; the cupcake flavor (not the filter) is the real per-run speed win.
  Accepted by the user in exchange for gaining clone-detection coverage.
- **cupcake still pulls a multi-language image** for four linters. A smaller custom
  image would be faster but adds build/maintenance surface; cupcake is the
  documented, Renovate-pinnable middle ground.
- **`DOCKERFILE_HADOLINT` gated on `include_web`** means a project that adds a
  Dockerfile by hand later won't get hadolint until they also enable it — an
  acceptable edge case documented in the config comment.

## Follow-up (out of scope)

- `.github/linters/.codespellrc` is referenced by nothing — a likely dead config
  worth a separate cleanup PR.
