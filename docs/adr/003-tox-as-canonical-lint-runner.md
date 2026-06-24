# ADR-003: tox `style` env as the canonical lint/type-check runner

## Status

Accepted

## Context

The template ships several tools that can orchestrate the same linters and type
checkers:

- The tox `style` environment, whose tool versions come from the uv-managed
  `style` dependency group in `pyproject.toml` (the project's single declared
  source of truth for tool versions).
- A `.pre-commit-config.yaml` (run via prek), whose hook `rev:` values pin tool
  versions — though the `sync-with-uv` hook is present to derive them from the uv
  lockfile. (This config was originally gated behind an `include_precommit`
  toggle; it is now always included — see the Decision.)
- An optional Trunk config (`include_trunk`), whose `.trunk/trunk.yaml` pins each
  linter to its own `@version`.
- An optional Pants config (`include_pants`), which carries its own
  `ruff.check` and `taplo` lint backends.

Originally `include_pants` and `include_trunk` defaulted to `true`, so a
default-generated project shipped **three** lint orchestrators (tox, Pants,
Trunk) declaring overlapping tools — `ruff`, `mypy`, `taplo`, `actionlint`,
`vulture`, `typos`, `yamllint` — each pinned in its own place and bumped by its
own mechanism (the dependency-management tool for the uv group, pre-commit.ci
autoupdate or `sync-with-uv` for hooks, `trunk upgrade` for Trunk).

These pins had already drifted in practice. At the time of this decision the same
tool resolved to different versions across orchestrators:

| Tool | tox `style` group | pre-commit | Trunk |
|------|-------------------|-----------|-------|
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
to `false`.

Pre-commit hooks are always included (the `include_precommit` toggle is removed)
and run via prek as a fast local/CI gate — not a second full suite. Their hook
versions are derived from the uv `style` group by the `sync-with-uv` hook, so the
prek gate and the tox suite cannot drift apart. This overlap is deliberate and
version-safe: fast feedback while editing, authoritative coverage in tox.

A default-generated project therefore has exactly one *authoritative* lint suite
(tox `style`, sourced from the uv `style` group) plus a version-synced prek gate —
not three independently-pinned orchestrators. Pants and Trunk remain available as
explicit opt-ins for projects that specifically want them — Pants as a build
system, Trunk for its extra IaC/secret scanners (`checkov`, `trufflehog`,
`hadolint`) that the core suite does not cover.

## Rationale

- **One source of truth.** Tool versions live in the uv `style` dependency group
  and nowhere else by default, so local and CI runs are byte-for-byte the same
  toolchain. Drift between orchestrators cannot occur if there is only one.
- **uv/tox is already the spine.** Generated projects use uv for dependencies and
  tox for the test/style/docs matrix. Making tox the lint runner keeps linting on
  the same spine rather than adding parallel toolchains a contributor must learn.
- **Opt-in, not deleted.** Pants and Trunk solve real problems for some projects
  (monorepo builds; aggregated IaC/secret scanning). Demoting them to opt-in
  removes the default-path duplication without taking the option away.
- **The half-built intent is now consistent.** The `sync-with-uv` pre-commit hook
  already signalled that uv was meant to be the source of truth; Pants and Trunk
  simply floated free of it. This completes that intent.

## Consequences

- A default project no longer ships `pants.toml` or `.trunk/`. Projects that want
  them must pass `include_pants=true` / `include_trunk=true`.
- The always-on prek gate overlaps the tox `style` env by design; `sync-with-uv`
  keeps its hook versions aligned with the uv `style` group, so the overlap costs
  duplicate execution (fast local feedback) but never causes version drift. When a
  contributor additionally opts into Trunk, that orchestrator is expected to be
  narrowed to the scanners the core suite lacks.
- Aggregated linting docs and `AGENTS.md` commands that mention `trunk check` /
  `pants lint ::` remain valid but are now conditional-only ("if configured").
- The number of type checkers invoked by the `style` env (mypy, pyright, ty,
  pyrefly) is a separate concern not addressed here; see future work on trimming
  preview-stage checkers.
