# ADR-003: tox `style` env as the canonical lint/type-check runner

## Status

Accepted. **Superseded in part (2026-06): Pants and Trunk were removed
entirely** — see the Update note below.

Amended (2026-07): generated projects now also ship a MegaLinter workflow as an
additive CI quality layer for repository/config/documentation checks. tox
`style` remains the authoritative local lint/type-check suite; MegaLinter does
not replace tox or own Python type/lint policy.

## Update (2026-06): Pants and Trunk removed

The opt-in path this ADR established was subsequently dropped. `include_pants`
and `include_trunk` are gone, along with `pants.toml` and `.trunk/`. The tox
`style` env (plus the always-on prek gate) is now the *sole* lint/build
orchestrator a generated project ships, so nothing can drift against it. The
present-tense "remain available as explicit opt-ins" language below is retained
for historical context but no longer holds.

## Context

The template ships several tools that can orchestrate the same linters and type
checkers:

- The tox `style` environment, whose tool versions come from the uv-managed
  `style` dependency group in `pyproject.toml` (the project's single declared
  source of truth for tool versions).
- A native `prek.toml` (run via prek), whose hook `rev` values pin tool
  versions — bumped by a Renovate `customManagers` regex entry. (This config was
  originally gated behind an `include_precommit` toggle; it is now always
  included — see the Decision.)
- An optional Trunk config (`include_trunk`), whose `.trunk/trunk.yaml` pins each
  linter to its own `@version`.
- An optional Pants config (`include_pants`), which carries its own
  `ruff.check` and `taplo` lint backends.

Originally `include_pants` and `include_trunk` defaulted to `true`, so a
default-generated project shipped **three** lint orchestrators (tox, Pants,
Trunk) declaring overlapping tools — `ruff`, `mypy`, `taplo`, `actionlint`,
`vulture`, `typos`, `yamllint` — each pinned in its own place and bumped by its
own mechanism (the dependency-management tool for the uv group, pre-commit.ci
autoupdate or `sync-with-uv` for the prek hooks, `trunk upgrade` for Trunk).

These pins had already drifted in practice. At the time of this decision the same
tool resolved to different versions across orchestrators:

| Tool | tox `style` group | pre-commit | Trunk |
| ------ | ------------------- | ----------- | ------- |
| ruff | `0.14.9` | `0.14.7` | `0.14.7` |
| mypy | `1.19.1` | `1.19.0` | `1.19.0` |
| actionlint | `1.7.9.24` | `1.7.7` | `1.7.9` |

The failure mode is concrete: a contributor can pass `tox -e style` locally and
still fail a different orchestrator in CI on a rule that changed between the two
pinned versions. The duplicated work (the same linters running two or three
times) is pure overhead for a default project.

## Decision

The uv-backed tox `style` environment is the single canonical runner for the
**full** lint/type-check suite. `include_pants` and `include_trunk` now default
to `false` (later removed entirely — see the Update note above).

Git hooks are always included (the `include_precommit` toggle is removed) and run
via prek (configured by a native `prek.toml`) as a fast local/CI gate — not a
second full suite. Both the prek `rev` pins and the uv `style` group are kept
current by Renovate, so the prek gate and the tox suite track the same upstream
releases. This overlap is deliberate: fast feedback while editing, authoritative
coverage in tox.

A default-generated project therefore has exactly one *authoritative* lint suite
(tox `style`, sourced from the uv `style` group) plus a Renovate-maintained prek
gate — not three independently-pinned orchestrators. (At the time of this ADR,
Pants and Trunk were demoted to opt-ins rather than deleted; both were removed
entirely in the 2026-06 update above.)

MegaLinter is intentionally scoped differently: it runs in CI as a repository
quality umbrella over formats that benefit from cross-file checks and reports
(GitHub Actions, Markdown, YAML, shell snippets, editorconfig, and cspell). It
is configured with `APPLY_FIXES: none`, no GitHub comment/status reporters, and
no Python linters/type checkers, so it cannot drift against the uv/tox Python
toolchain or rewrite generated projects during CI.

## Rationale

- **One source of truth.** Tool versions live in the uv `style` dependency group
  and nowhere else by default, so local and CI runs are byte-for-byte the same
  toolchain. Drift between orchestrators cannot occur if there is only one.
- **uv/tox is already the spine.** Generated projects use uv for dependencies and
  tox for the test/style/docs matrix. Making tox the lint runner keeps linting on
  the same spine rather than adding parallel toolchains a contributor must learn.
- **Opt-in, not deleted *(historical — superseded by the 2026-06 update above;
  both were later removed entirely)*.** Pants and Trunk solved real problems for
  some projects (monorepo builds; aggregated IaC/secret scanning). Demoting them
  to opt-in removed the default-path duplication without taking the option
  away — before they were dropped outright.
- **One updater, not many.** Renovate bumps both the uv `style` group and the
  prek `rev` pins; the default project no longer relies on `sync-with-uv`,
  pre-commit.ci, or `trunk upgrade` running in parallel. Pants and Trunk, when
  they were still opt-in, carried their own update mechanisms (historical; both
  were subsequently removed).

## Consequences

- A generated project ships neither `pants.toml` nor `.trunk/` (the
  `include_pants` / `include_trunk` toggles were removed in the update above).
- The always-on prek gate overlaps the tox `style` env by design; Renovate keeps
  both the prek `rev` pins and the uv `style` group current, so the overlap costs
  duplicate execution (fast local feedback) and at most a brief window where two
  Renovate PRs land separately, not sustained version drift. (Historically, when
  a contributor additionally opted into Trunk, that orchestrator was expected to
  be narrowed to the scanners the core suite lacks — moot since Trunk's removal.)
- The `trunk check` / `pants lint ::` commands were removed from `README.md` and
  `AGENTS.md`; there is no longer any Pants/Trunk path to document.
- MegaLinter adds a separate CI workflow and `.mega-linter.yml`. Its reports are
  uploaded as artifacts and `megalinter-reports/` is ignored. The workflow is a
  broad repository/config/documentation signal; contributors should still use
  `tox -e style` / `tox -e prek` for local authoritative checks.
- The number of type checkers invoked by the `style` env (mypy, pyright, ty,
  pyrefly) is a separate concern not addressed here; see future work on trimming
  preview-stage checkers.
