# Generated-project check coverage

This audit records the decisions for issue #351.
It concerns generated projects, not the template repository's own hooks.
The [adoption/update audit](template-adoption.md) must compare these defaults
with the adopter's existing checks before retiring a configuration.

## Default hooks and matching

All new hooks inherit `pre-commit` and `pre-push` stages and also run through
CI's `prek run --all-files` hooks job.
Hook IDs and selectors were verified in the pinned upstream manifests:
[pre-commit-hooks v6.0.0](https://github.com/pre-commit/pre-commit-hooks/blob/v6.0.0/.pre-commit-hooks.yaml)
and [check-jsonschema 0.37.4](https://github.com/python-jsonschema/check-jsonschema/blob/0.37.4/.pre-commit-hooks.yaml).
Absent applicable files make file-scoped hooks no-ops.

| Candidate | Decision and scope |
| --- | --- |
| `check-executables-have-shebangs` | Add: text **and** executable files must start with a shebang. Binary executables are not selected. |
| `check-symlinks` | Add: detect broken symlinks; upstream selects symlinks, not ordinary files. |
| `fix-byte-order-marker` | Add: remove leading UTF-8 BOM from text files. Exclude cobo-owned `.gitignore`, ai-rulez-owned `.continue/prompts/` output, and `.ps1`/`.psm1`/`.psd1` files (case-insensitive) to preserve Windows PowerShell 5.1 encoding detection. |
| `mixed-line-ending` | Add: text files, `--fix=auto`; normalize mixed endings to the dominant ending, but retain consistent CRLF (permitted for `.bat`/`.ps1` by `.editorconfig`). Same generator-owned exclusions as the BOM fixer; PowerShell files remain eligible. This is not enforcement of universal LF. |
| `check-xml` | Add: XML-typed files only; dormant until a project adds XML. |
| `check-github-issue-forms` | Add: YAML under root `.github/ISSUE_TEMPLATE/`, excluding `config.yml` and `config.yaml`; Markdown templates are not selected. |
| `check-github-issue-config` | Add: root `.github/ISSUE_TEMPLATE/config.yml` **or** `config.yaml` (explicit override extends upstream's `.yml`-only match). |
| `check-renovate` | Add: root `renovate.json/json5`, `.github/renovate.json/json5`, `.gitlab/renovate.json/json5`, `.renovaterc`, and `.renovaterc.json/json5`; not `package.json`. Include `pyjson5` for `.json5` parsing. |
| `check-dependabot` | Add: root `.github/dependabot.yml/yaml`; dormant because the template generates Renovate, not Dependabot. |
| `check-github-actions` | Retain: root `action.yml/yaml` or `.github/actions/**/action.yml/yaml` metadata, **not** workflow files. |
| `check-github-workflows` | Add: YAML files immediately under root `.github/workflows/`. Schema validation complements actionlint's workflow expressions/shell checks and zizmor's security analysis; neither action metadata nor the schema alone replaces those checks. |
| `check-json5` | Omit this ID: neither pinned provider supplies it. Retain strict `check-json` for JSON; verified Renovate JSON5 parsing is covered above. Generic JSON5 syntax validation remains an adoption-specific choice requiring a verified provider or a schema-backed local check. |

JSON5 is not synonymous with editor JSONC.
The global hook exclusions for `.devcontainer/devcontainer.json` and
`.vscode/launch.json` remain; do not feed their comments to strict JSON parsing.
For commented `.json` or extensionless `.renovaterc`, an adopter can configure
`check-renovate` with `--force-filetype json5` and `pyjson5`;
strict `check-json` must also exclude the affected JSON file.

[Windows PowerShell 5.1](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding?view=powershell-5.1)
misinterprets BOM-less UTF-8 source containing non-ASCII characters as ANSI.
The BOM exception preserves existing script behavior; it does not prescribe
a project's PowerShell version or replace its EditorConfig encoding policy.

## Retained replacements and feedback timing

| Prior check or proposed alternative | Default decision and limitation |
| --- | --- |
| pyupgrade | Retain Ruff's `UP` rules (`select = ["ALL"]`) instead of adding another fixer. Compare target Python version, ignored rules, and per-file ignores before treating an adopter's pyupgrade invocation as replaced. |
| Bandit | Retain Ruff `S` rules plus semgrep `p/python` over `src` in tox style. They overlap Bandit but do not establish exact rule/config equivalence; preserve adopter-specific Bandit coverage until compared. Semgrep feedback is in style/CI, not a dedicated commit hook. |
| detect-secrets / gitleaks | Retain both: baseline-backed detect-secrets checks local files at commit/push and in CI hooks; gitleaks scans history in separate PR/main-push/weekly CI with full checkout. Detectors, scope, and suppressions differ. |
| Local pre-push pip-audit | Keep CI pip-audit: audit exported locked runtime dependencies, excluding dev dependencies and the project itself. This gives later feedback than pre-push, but avoids a network-backed local gate. An opt-in local audit should use the same export scope and fail on export errors. |
| Local Taplo formatter | Keep tox style's Taplo syntax/format checks for root `*.toml`. `check-toml` is earlier syntax feedback, not formatting; `.lock` files are outside that Taplo glob. An adopter may opt into local formatting with the same config/scope. |
| Isolated basedpyright / slotscheck hooks | Keep local `system` hooks via `uv run --locked --group style`, sharing the project's pinned tooling and installed dependencies. Basedpyright is Python-file-triggered; slotscheck always scans `src` without filenames. An isolated environment without project dependencies is not an equivalent replacement. |

The generated CI `check` aggregate covers hooks and style, with draft PRs skipped.
Separate security jobs such as gitleaks/pip-audit are not in that aggregate;
running them is not proof that their status contexts are required by live
branch protection. This audit does not change repository merge policy.

## Project-specific and policy checks

- **SQLFluff: optional adoption configuration, no new Copier toggle.**
  Preserve it when the project contains SQL.
  Choose dialect, templater, SQL file scope, and lint versus fix behavior from
  the actual project; a PostgreSQL devcontainer alone does not justify it.
  Templated SQL may need extra dependencies and project context.
- **djLint: optional for standalone HTML/template files, no new Copier toggle.**
  Its `djlint` hook selects HTML; `djlint-jinja` selects Jinja and uses the
  Jinja profile. Narrow selection to actual HTML templates: not every `.jinja`
  file contains HTML. Source inspection of
  [djLint](https://github.com/djlint/djLint/tree/1bc6dede9307d97e875d034dfc70ffaa09d1f0b2)
  (`.pre-commit-hooks.yaml`, `src/djlint/lint.py`, `src/djlint/reformat.py`)
  shows whole-file HTML processing, not Python-string extraction.
  It does **not** supply supported lint/format coverage for HTML embedded in
  Python strings; broadening its file filter to Python is not a safe replacement.
- **`no-commit-to-branch`: documented opt-in, omitted by default.**
  It prevents local commits to selected branches (upstream defaults: main/master),
  unlike branch-name CI or Commitizen, which check naming/messages.
  It is always-run and does not take filenames.
  If enabled, CI must explicitly set `SKIP=no-commit-to-branch` for legitimate
  default-branch runs, including template smoke runs; do not infer a CI exemption
  from file filters. Live server-side branch protection remains independent.

No project-specific check should be deleted merely because it is absent from
these defaults. Record gaps, unverified equivalence, and changes in timing in
the adoption report, and obtain the adopter's decision before reducing coverage.

## Regression validation

`tests/test_hook_coverage.py` renders all presets with both instruction hosts
and checks defaults, exclusions, and the explicit issue-config matcher.
Template CI validates generated schemas/hygiene across its render matrix.
Its ai-rulez scenario also runs `tools/verify_hook_coverage.py` through the
rendered project's own prek dependency group in an isolated fixture repository.
The probes exercise malformed inputs, unrelated-file skips, JSON5 parsing,
executable and symlink checks, UTF-8 BOM removal, consistent CRLF preservation,
generator-owned and PowerShell byte preservation, and second-pass convergence.
