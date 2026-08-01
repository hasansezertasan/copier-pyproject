# ADR-013: MegaLinter as an opt-in lean complement

## Status

Proposed (2026-08). Prompted by a real CI run
([hwid#90](https://github.com/hasansezertasan/hwid/actions/runs/30634574244/job/91168813067))
where MegaLinter took ~3 minutes, of which **165 s was pulling the ~8 GB
`oxsecurity/megalinter` image and only 16 s was actual linting**.

## Context

The template shipped MegaLinter as an **always-on** workflow
(`.github/workflows/mega-linter.yml` + `.mega-linter.yml`) that was **documented
nowhere** in `CLAUDE.md`, `README`'s variable list, or `docs/`. Two problems:

1. **It violated the self-contained/fast default.** Every generated project paid
   the multi-GB image pull on every push/PR, whether or not the owner wanted an
   extra linting layer. The template's stated posture is *green on first push,
   zero external accounts, fast* — an always-on heavy CI layer works against that.
2. **It was ~redundant with prek.** Its six enabled linters were
   `ACTION_ACTIONLINT`, `BASH_SHELLCHECK`, `EDITORCONFIG_EDITORCONFIG_CHECKER`,
   `MARKDOWN_MARKDOWNLINT`, `SPELL_CSPELL`, `YAML_YAMLLINT`. Five of these are
   already run by `prek.toml` (actionlint, editorconfig-checker, markdownlint-cli2,
   yamllint, and — for spelling — typos, plus zizmor). Only `BASH_SHELLCHECK` was
   unique; `SPELL_CSPELL` duplicated `typos`. So the layer mostly re-ran, more
   slowly and in a heavier container, checks the fast prek gate already performed.

MegaLinter differs from the ADR-009 integrations (Sourcery, SonarCloud,
all-contributors): it is a **self-contained Docker action** that needs no external
account or secret. So the ADR-009 "requires out-of-band provisioning" rationale
does not apply — a separate decision is warranted.

## Decision

Make MegaLinter an **opt-in** component behind a new `include_megalinter` boolean
(`default: false`), and when enabled, configure it as a **lean complement** to
prek rather than a redundant re-run.

### Opt-in, off by default

`include_megalinter` follows the same `default: false` posture as the ADR-009
toggles, for the same reason: it preserves the fast, self-contained default. An
adopting project (and existing ones via `copier update`) turns it on deliberately.

### Lean set — only what prek/tox do not cover

`ENABLE_LINTERS` is trimmed to genuine gaps, determined by inventorying a
generated project's file types against what prek/tox already lint:

| Enabled | Gap it fills |
| --------- | -------------- |
| `BASH_SHELLCHECK` | standalone shell scripts (actionlint only shellchecks workflow `run:` blocks) |
| `DOCKERFILE_HADOLINT` | the generated Dockerfile — **jinja-gated on `include_web`**, the only config that renders one |
| `JSON_JSONLINT` | the JSON/JSONC config files (otherwise only indent-checked) — scoped to skip the JSONC-with-comments `devcontainer.json`/`.vscode/*.json` |
| `COPYPASTE_JSCPD` | copy-paste / clone detection — a capability neither prek nor tox provides |

Deliberately **not** enabled, to avoid duplication:

- **prek** already runs actionlint, yamllint, markdownlint, editorconfig-checker.
- **typos** (prek) is the single spell-checker; `SPELL_CSPELL` is dropped (no
  two-dictionary drift).
- **tox `style`** covers Python (ruff + five type-checkers + vulture).
- **`check-security.yml`** + CodeQL + Scorecard cover secrets/vuln/SAST, so the
  MegaLinter repository security linters are omitted.

### Speed

- Use the smaller **`cupcake` flavor** image
  (`oxsecurity/megalinter/flavors/cupcake@<sha>`, SHA-pinned, Renovate-tracked),
  which still contains all four enabled linters — the largest, unconditional cut
  to the dominant image-pull cost. This is the effective per-run lever.
- **No paths filter.** An earlier revision paths-filtered the workflow to the
  file types the enabled linters target, but because `COPYPASTE_JSCPD` scans
  source the filter necessarily included `**.py` and so fired on nearly every
  PR — a half-optimization whose only saving was documentation/config-only PRs,
  at the cost of a confusing "why didn't it run here?" surface. The workflow
  therefore runs on every push/PR to the default branch; the `cupcake` flavor
  (not a filter) is what keeps each run cheap.
- Keep `VALIDATE_ALL_CODEBASE: false` on PRs and `cancel-in-progress`.

### Non-blocking

Non-blocking on three levels, so it never gates a merge by default:

- **Exit code:** `DISABLE_ERRORS: true` — MegaLinter reports findings but exits
  `0`, so the job stays green rather than posting a red check on every
  shellcheck/hadolint/jsonlint/jscpd nit. Findings are delivered via the SARIF →
  Security-tab upload and the reports artifact (the `zizmor.yml` dashboard model),
  not by failing CI.
- **Aggregation gate:** not in the `ci.yml` `check` job, so the `alls-green`
  required check never depends on it.
- **Status reporter:** `GITHUB_STATUS_REPORTER: false`, so it posts no commit
  status.

A project that *wants* MegaLinter to gate can require its code-scanning results
via branch protection — an explicit opt-in, not the default.

## Consequences

- New `copier.yml` boolean `include_megalinter` (`default: false`) with `help`
  describing the lean, complementary scope; `.example-input.yml` sets it `false`
  (so its rendered form is only validated when generated explicitly, per the
  CLAUDE.md testing convention).
- Conditional template files:
  `template/.github/workflows/{% if include_megalinter %}mega-linter.yml{% endif %}.jinja`
  and `template/{% if include_megalinter %}.mega-linter.yml{% endif %}.jinja`.
  Both become `.jinja`, so GitHub Actions `${{ … }}` expressions are wrapped in
  `{% raw %}` blocks and the `DOCKERFILE_HADOLINT` entry is jinja-gated on
  `include_web`.
- The MegaLinter-only `.shellcheckrc` is gated:
  `template/.github/linters/{% if include_megalinter %}.shellcheckrc{% endif %}`.
  The MegaLinter-only `.cspell.yml.jinja` is **removed** (cspell dropped).
  The prek-shared configs stay always-on: `.github/linters/.markdownlint.yml`
  (extended by `markdownlint-cli2.yaml`), `.github/actionlint.yaml`,
  `.github/yamllint.yaml`.
- `CLAUDE.md` (Optional components) and `README.md` document the toggle — closing
  the prior gap where MegaLinter was shipped but undocumented.
- No `pyproject.toml` change: MegaLinter is a CI action, not a Python dependency.
- The job carries `security-events: write` and uploads MegaLinter's SARIF
  (`SARIF_REPORTER: true`) to the code-scanning dashboard via
  `github/codeql-action/upload-sarif` — the advertised Security-tab integration
  is a **real** ingest, not just the `upload-artifact` archive. The upload step is
  best-effort (`continue-on-error: true`, `if: always()`), mirroring `zizmor.yml`:
  code scanning is free on public repos and needs GitHub Advanced Security on
  private ones, so it never fails the job when unavailable.
- The generated `mega-linter.yml` stays zizmor/ghalint-green like every workflow
  (`permissions: {}` top-level, per-job least privilege — `contents: read` +
  `security-events: write` — `persist-credentials: false`, `timeout-minutes`,
  SHA-pinned `uses:`).
- More template surface to test: the toggle is exercised on its own and combined
  with `include_web` (for the hadolint conditional), per the CLAUDE.md convention.

## Notes / follow-up

- `.github/linters/.codespellrc` is referenced by nothing in the template — a
  likely dead config worth a separate cleanup, out of scope for this ADR.
